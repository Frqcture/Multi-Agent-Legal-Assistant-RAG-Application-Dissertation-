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
    used_web_search: bool = False
    web_sources: List[Dict] = field(default_factory=list)

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
            "completed_at": self.completed_at,
            "used_web_search": self.used_web_search,
            "web_sources": self.web_sources,
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
        """Planner agent: List available docs and set a plan without an LLM call."""
        step = AgentStep(
            agent=AgentRole.PLANNER,
            message="Analysing available documents..."
        )
        workflow.steps.append(step)

        docs_result = await self.mcp_client.call_tool("list_user_docs", {
            "user_id": workflow.user_id
        })

        step.tool_calls.append({"tool": "list_user_docs", "args": {"user_id": workflow.user_id}})
        step.tool_results.append(docs_result)

        if docs_result.get("success"):
            files = docs_result.get("data", {}).get("files", [])
            if files:
                step.message = f"Plan: search {len(files)} document(s) — {', '.join(files)}"
            else:
                step.message = "Plan: no documents found — will fall back to web search."
        else:
            step.message = "Plan: will search documents and synthesise an answer."

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

        # Minimum relevance threshold: Chroma returns L2/cosine distances where
        # lower = more similar. A score above this means the docs are a poor match.
        RELEVANCE_THRESHOLD = 1.5

        if search_result.get("success"):
            data = search_result.get("data", {})
            num_results = data.get("num_results", 0)
            chunks = data.get("chunks", [])
            best_score = data.get("best_score")

            doc_is_relevant = (
                num_results > 0
                and best_score is not None
                and best_score < RELEVANCE_THRESHOLD
            )

            if doc_is_relevant:
                sources = set()
                for chunk in chunks:
                    sources.add(f"{chunk.get('source', 'Unknown')} (p.{chunk.get('page', '?')})")
                step.message = (
                    f"Found {num_results} relevant chunks from: {', '.join(sources)} "
                    f"(best score: {best_score:.3f})"
                )
                workflow._retrieved_context = chunks
            else:
                score_info = f" (best score: {best_score:.3f})" if best_score is not None else ""
                step.message = (
                    f"Documents did not contain sufficiently relevant information{score_info}. "
                    "Falling back to web search..."
                )
                workflow._retrieved_context = []
                await self._run_web_search_fallback(workflow, step)
        else:
            step.message = "Document search failed. Falling back to web search..."
            workflow._retrieved_context = []
            await self._run_web_search_fallback(workflow, step)

    async def _run_web_search_fallback(self, workflow: WorkflowState, retriever_step: AgentStep):
        """Fallback to web search directly (not via MCP subprocess) using a thread
        executor so the synchronous DDGS call never blocks the asyncio event loop.
        """
        retriever_step.tool_calls.append({
            "tool": "search_web",
            "args": {"query": workflow.query}
        })

        try:
            from ddgs import DDGS

            loop = asyncio.get_event_loop()
            raw = await loop.run_in_executor(
                None,
                lambda: list(DDGS().text(workflow.query, max_results=5))
            )

            results = [
                {
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", "")[:400],
                }
                for r in (raw or [])
            ]

            tool_result = {"success": True, "num_results": len(results), "results": results}
            retriever_step.tool_results.append(tool_result)

            if results:
                workflow.used_web_search = True
                workflow.web_sources = results
                workflow._retrieved_context = [
                    {
                        "content": r.get("snippet", ""),
                        "source": r.get("title", "Web"),
                        "page": r.get("url", ""),
                        "is_web": True,
                    }
                    for r in results
                ]
                retriever_step.message += f" Web search returned {len(results)} results."
            else:
                retriever_step.tool_results.append({"success": False, "error": "No web results returned"})
                retriever_step.message += " Web search returned no results."
                workflow._retrieved_context = []

        except ImportError:
            retriever_step.tool_results.append({"success": False, "error": "duckduckgo_search not installed"})
            retriever_step.message += " Web search unavailable (package missing)."
            workflow._retrieved_context = []
        except Exception as e:
            retriever_step.tool_results.append({"success": False, "error": str(e)})
            retriever_step.message += f" Web search failed: {e}"
            workflow._retrieved_context = []

    async def _run_responder(self, workflow: WorkflowState):
        """Responder agent: Generate final answer using already-retrieved context."""
        step = AgentStep(
            agent=AgentRole.RESPONDER,
            message="Generating response with citations..."
        )
        workflow.steps.append(step)

        context = getattr(workflow, "_retrieved_context", [])

        if not context:
            workflow.answer = "I couldn't find relevant information in your documents or on the web to answer this question."
            step.message = "No context available for response."
            return

        is_web = any(c.get("is_web") for c in context)

        if is_web:
            context_text = "\n\n".join([
                f"[Web: {c.get('source', 'Unknown')} – {c.get('page', '')}]: {c.get('content', '')}"
                for c in context
            ])
            web_note = (
                "\n\n---\n"
                "**Note:** Your uploaded documents did not contain sufficient information to answer this query. "
                "The above answer was generated using a live web search."
            )
            system_prompt = (
                "You are a helpful legal assistant. "
                "The user's documents did not contain the answer, so web search results are provided instead. "
                "Answer clearly and cite each source as [Source Name](URL)."
            )
        else:
            context_text = "\n\n".join([
                f"--- SOURCE: [{c.get('source', 'Unknown')}, Page {c.get('page', '?')}] ---\n{c.get('content', '')}"
                for c in context
            ])
            web_note = ""
            system_prompt = (
                "You are a helpful legal assistant that answers questions strictly using the provided context. "
                "Every claim must be followed by a reference: [document_name, page_number]. "
                "If the context doesn't contain the answer, say so."
            )

        response = self.llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Context:\n{context_text}\n\nQuestion: {workflow.query}")
        ])

        workflow.answer = response.content + web_note
        step.message = "Response generated from web search results." if is_web else "Response generated with citations."


# Singleton coordinator instance
_coordinator: Optional[AgentCoordinator] = None


def get_coordinator() -> AgentCoordinator:
    """Get or create the agent coordinator singleton."""
    global _coordinator
    if _coordinator is None:
        _coordinator = AgentCoordinator()
    return _coordinator
