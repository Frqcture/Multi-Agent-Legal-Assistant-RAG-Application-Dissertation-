"""
Multi-Agent Coordinator
Implements a simple planner → retriever → responder workflow
that communicates with the MCP server via subprocess.
"""

import asyncio
import json
import subprocess
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
import os

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage


class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentRole(str, Enum):
    PLANNER = "planner"
    RETRIEVER = "retriever"
    RESPONDER = "responder"


@dataclass
class AgentStep:
    """A single step in the agent workflow."""
    agent: AgentRole
    message: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    tool_calls: List[Dict] = field(default_factory=list)
    tool_results: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "agent": self.agent.value,
            "message": self.message,
            "timestamp": self.timestamp,
            "tool_calls": self.tool_calls,
            "tool_results": self.tool_results
        }


@dataclass
class WorkflowState:
    """State of a running workflow."""
    workflow_id: str
    query: str
    user_id: str
    status: WorkflowStatus = WorkflowStatus.PENDING
    steps: List[AgentStep] = field(default_factory=list)
    answer: Optional[str] = None
    error: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "workflow_id": self.workflow_id,
            "query": self.query,
            "user_id": self.user_id,
            "status": self.status.value,
            "steps": [s.to_dict() for s in self.steps],
            "answer": self.answer,
            "error": self.error,
            "created_at": self.created_at,
            "completed_at": self.completed_at
        }


class MCPClient:
    """Client for communicating with MCP server subprocess."""

    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.request_id = 0

    async def start(self):
        """Start the MCP server subprocess."""
        mcp_server_path = os.path.join(os.path.dirname(__file__), "mcp_server.py")

        self.process = subprocess.Popen(
            ["python3", mcp_server_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        # Initialize connection
        await self._send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "agent-coordinator", "version": "1.0.0"}
        })

    async def stop(self):
        """Stop the MCP server subprocess."""
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=5)
            self.process = None

    async def _send_request(self, method: str, params: Dict) -> Dict:
        """Send JSON-RPC request to MCP server."""
        if not self.process:
            raise RuntimeError("MCP server not started")

        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params
        }

        self.process.stdin.write(json.dumps(request) + "\n")
        self.process.stdin.flush()

        # Read response (with timeout)
        response_line = self.process.stdout.readline()
        if not response_line:
            raise RuntimeError("No response from MCP server")

        return json.loads(response_line)

    async def call_tool(self, tool_name: str, arguments: Dict) -> Dict:
        """Call a tool on the MCP server."""
        response = await self._send_request("tools/call", {
            "name": tool_name,
            "arguments": arguments
        })

        if "error" in response:
            return {"success": False, "error": response["error"]["message"]}

        # Parse the content
        content = response.get("result", {}).get("content", [])
        if content and content[0].get("type") == "text":
            return json.loads(content[0]["text"])

        return {"success": False, "error": "Invalid response format"}

    async def list_tools(self) -> List[Dict]:
        """List available tools."""
        response = await self._send_request("tools/list", {})
        return response.get("result", {}).get("tools", [])


class AgentCoordinator:
    """
    Coordinates multiple agents to answer a question.
    Uses MCP tools for document access.
    """

    def __init__(self):
        self.llm = ChatOllama(model="gemma3:4b", temperature=0.1)
        self.mcp_client = MCPClient()
        # In-memory workflow store (use Redis/DB for production)
        self.workflows: Dict[str, WorkflowState] = {}

    async def run_query(self, query: str, user_id: str) -> WorkflowState:
        """Run the full agent pipeline synchronously and return the completed state."""
        workflow_id = str(uuid.uuid4())
        workflow = WorkflowState(
            workflow_id=workflow_id,
            query=query,
            user_id=user_id,
            status=WorkflowStatus.PENDING
        )
        self.workflows[workflow_id] = workflow
        await self._run_workflow(workflow_id)
        return workflow

    async def start_workflow(self, query: str, user_id: str) -> str:
        """Start a new workflow and return workflow ID."""
        workflow_id = str(uuid.uuid4())
        workflow = WorkflowState(
            workflow_id=workflow_id,
            query=query,
            user_id=user_id,
            status=WorkflowStatus.PENDING
        )
        self.workflows[workflow_id] = workflow

        # Start async execution
        asyncio.create_task(self._run_workflow(workflow_id))

        return workflow_id

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowState]:
        """Get workflow state by ID."""
        return self.workflows.get(workflow_id)

    async def _run_workflow(self, workflow_id: str):
        """Execute the multi-agent workflow."""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return

        workflow.status = WorkflowStatus.RUNNING

        try:
            # Start MCP client
            await self.mcp_client.start()

            # Step 1: Planner agent
            await self._run_planner(workflow)

            # Step 2: Retriever agent
            await self._run_retriever(workflow)

            # Step 3: Responder agent
            await self._run_responder(workflow)

            workflow.status = WorkflowStatus.COMPLETED
            workflow.completed_at = datetime.now().isoformat()

        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            workflow.error = str(e)
            workflow.completed_at = datetime.now().isoformat()

        finally:
            await self.mcp_client.stop()

    async def _run_planner(self, workflow: WorkflowState):
        """Planner agent: Analyze query and plan tool usage."""
        step = AgentStep(
            agent=AgentRole.PLANNER,
            message="Analyzing query and planning approach..."
        )
        workflow.steps.append(step)

        # Get available docs to inform planning
        docs_result = await self.mcp_client.call_tool("list_user_docs", {
            "user_id": workflow.user_id
        })

        step.tool_calls.append({"tool": "list_user_docs", "args": {"user_id": workflow.user_id}})
        step.tool_results.append(docs_result)

        if docs_result.get("success"):
            files = docs_result.get("data", {}).get("files", [])
            file_list = ", ".join(files) if files else "No documents found"

            # Use LLM to create a plan
            plan_prompt = f"""You are a planning agent. Analyze this query and create a brief plan.

Query: {workflow.query}
Available documents: {file_list}

Create a 1-2 sentence plan for how to answer this query using the available documents.
Focus on what to search for and how to structure the answer."""

            plan_response = self.llm.invoke([
                SystemMessage(content="You are a concise planning agent."),
                HumanMessage(content=plan_prompt)
            ])

            step.message = f"Plan: {plan_response.content}"
        else:
            step.message = "Plan: Will search documents and synthesize an answer."

    async def _run_retriever(self, workflow: WorkflowState):
        """Retriever agent: Search for relevant information."""
        step = AgentStep(
            agent=AgentRole.RETRIEVER,
            message="Searching documents for relevant information..."
        )
        workflow.steps.append(step)

        # Search documents
        search_result = await self.mcp_client.call_tool("search_docs", {
            "query": workflow.query,
            "user_id": workflow.user_id,
            "top_k": 5
        })

        step.tool_calls.append({
            "tool": "search_docs",
            "args": {"query": workflow.query, "top_k": 5}
        })
        step.tool_results.append(search_result)

        if search_result.get("success"):
            data = search_result.get("data", {})
            num_results = data.get("num_results", 0)
            chunks = data.get("chunks", [])

            # Summarize what was found
            sources = set()
            for chunk in chunks:
                sources.add(f"{chunk.get('source', 'Unknown')} (p.{chunk.get('page', '?')})")

            step.message = f"Found {num_results} relevant chunks from: {', '.join(sources)}"

            # Store context for responder
            workflow._retrieved_context = chunks
        else:
            step.message = "No relevant information found in documents."
            workflow._retrieved_context = []

    async def _run_responder(self, workflow: WorkflowState):
        """Responder agent: Generate final answer with citations."""
        step = AgentStep(
            agent=AgentRole.RESPONDER,
            message="Generating response with citations..."
        )
        workflow.steps.append(step)

        # Use MCP tool to generate answer
        answer_result = await self.mcp_client.call_tool("answer_question", {
            "question": workflow.query,
            "user_id": workflow.user_id
        })

        step.tool_calls.append({
            "tool": "answer_question",
            "args": {"question": workflow.query}
        })
        step.tool_results.append(answer_result)

        if answer_result.get("success"):
            answer = answer_result.get("data", {}).get("answer", "")
            workflow.answer = answer
            step.message = "Response generated with citations."
        else:
            # Fallback: use LLM directly with retrieved context
            context = getattr(workflow, "_retrieved_context", [])
            if context:
                context_text = "\n\n".join([
                    f"[{c.get('source', 'Unknown')}, p.{c.get('page', '?')}]: {c.get('content', '')}"
                    for c in context
                ])

                response = self.llm.invoke([
                    SystemMessage(content="You are a helpful assistant. Answer based on the context provided. Cite sources."),
                    HumanMessage(content=f"Context:\n{context_text}\n\nQuestion: {workflow.query}")
                ])

                workflow.answer = response.content
                step.message = "Response generated from retrieved context."
            else:
                workflow.answer = "I couldn't find relevant information in your documents to answer this question."
                step.message = "No context available for response."


# Singleton coordinator instance
_coordinator: Optional[AgentCoordinator] = None


def get_coordinator() -> AgentCoordinator:
    """Get or create the agent coordinator singleton."""
    global _coordinator
    if _coordinator is None:
        _coordinator = AgentCoordinator()
    return _coordinator
