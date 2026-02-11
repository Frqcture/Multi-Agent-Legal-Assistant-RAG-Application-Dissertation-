"""
MCP Server - Model Context Protocol Server
Runs as a separate process and exposes tools for agents to call.
Uses stdio transport for communication.
"""

import asyncio
import json
import sys
import os
from typing import Dict, Optional

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_tools import get_tool_definitions, ToolResult
from index import RAGEngine
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings


class MCPServer:
    """
    MCP Server that handles tool calls from agents.
    Communicates via JSON-RPC over stdio.
    """

    def __init__(self):
        self.rag_engine: Optional[RAGEngine] = None
        self.embedding_model = OllamaEmbeddings(model="embeddinggemma")
        self._init_rag()

    def _init_rag(self):
        """Initialize RAG engine lazily."""
        try:
            self.rag_engine = RAGEngine()
        except Exception as e:
            print(f"Warning: Could not initialize RAG engine: {e}", file=sys.stderr)

    def _get_vectorstore(self) -> Optional[Chroma]:
        """Get vectorstore instance."""
        if self.rag_engine:
            return self.rag_engine.vectorstore
        return None

    async def handle_search_docs(self, params: Dict) -> ToolResult:
        """Search documents using semantic similarity."""
        query = params.get("query", "")
        user_id = params.get("user_id", "")
        top_k = params.get("top_k", 5)

        if not query or not user_id:
            return ToolResult(False, None, "Missing required parameters: query and user_id")

        try:
            vectorstore = self._get_vectorstore()
            if not vectorstore:
                return ToolResult(False, None, "Vectorstore not available")

            # Convert user_id to int for metadata matching (stored as int during ingestion)
            try:
                user_id_int = int(user_id)
            except ValueError:
                user_id_int = user_id

            # Search with user filter
            results = vectorstore.similarity_search(
                query,
                k=top_k,
                filter={"user_id": user_id_int}
            )

            chunks = []
            for doc in results:
                chunks.append({
                    "content": doc.page_content[:500],  # Truncate for response
                    "source": doc.metadata.get("document_name", "Unknown"),
                    "page": doc.metadata.get("page_number", "?"),
                    "score": getattr(doc, "score", None)
                })

            return ToolResult(True, {
                "query": query,
                "num_results": len(chunks),
                "chunks": chunks
            })

        except Exception as e:
            return ToolResult(False, None, str(e))

    async def handle_list_user_docs(self, params: Dict) -> ToolResult:
        """List all documents for a user."""
        user_id = params.get("user_id", "")

        if not user_id:
            return ToolResult(False, None, "Missing required parameter: user_id")

        try:
            if not self.rag_engine:
                return ToolResult(False, None, "RAG engine not available")

            # Convert user_id to int for metadata matching
            try:
                user_id_int = int(user_id)
            except ValueError:
                user_id_int = user_id

            files = self.rag_engine.listUserFiles(userId=user_id_int)
            return ToolResult(True, {
                "user_id": user_id,
                "files": files,
                "count": len(files)
            })

        except Exception as e:
            return ToolResult(False, None, str(e))

    async def handle_get_doc_summary(self, params: Dict) -> ToolResult:
        """Get summary of a specific document."""
        user_id = params.get("user_id", "")
        filename = params.get("filename", "")

        if not user_id or not filename:
            return ToolResult(False, None, "Missing required parameters: user_id and filename")

        try:
            vectorstore = self._get_vectorstore()
            if not vectorstore:
                return ToolResult(False, None, "Vectorstore not available")

            # Convert user_id to int for metadata matching
            try:
                user_id_int = int(user_id)
            except ValueError:
                user_id_int = user_id

            # Get all chunks for this document
            results = vectorstore.get(
                where={
                    "$and": [
                        {"user_id": user_id_int},
                        {"document_name": filename}
                    ]
                },
                include=["documents", "metadatas"]
            )

            if not results["documents"]:
                return ToolResult(False, None, f"Document '{filename}' not found")

            # Return first few chunks as summary context
            preview = "\n---\n".join(results["documents"][:3])

            return ToolResult(True, {
                "filename": filename,
                "num_chunks": len(results["documents"]),
                "preview": preview[:1000]
            })

        except Exception as e:
            return ToolResult(False, None, str(e))

    async def handle_answer_question(self, params: Dict) -> ToolResult:
        """Generate answer using RAG."""
        question = params.get("question", "")
        user_id = params.get("user_id", "")
        context = params.get("context", "")

        if not question or not user_id:
            return ToolResult(False, None, "Missing required parameters: question and user_id")

        try:
            if not self.rag_engine:
                return ToolResult(False, None, "RAG engine not available")

            # Convert user_id to int for metadata matching
            try:
                user_id_int = int(user_id)
            except ValueError:
                user_id_int = user_id

            answer = self.rag_engine.query(question, userId=user_id_int)

            return ToolResult(True, {
                "question": question,
                "answer": answer
            })

        except Exception as e:
            return ToolResult(False, None, str(e))

    async def call_tool(self, tool_name: str, params: Dict) -> ToolResult:
        """Route tool call to appropriate handler."""
        handlers = {
            "search_docs": self.handle_search_docs,
            "list_user_docs": self.handle_list_user_docs,
            "get_doc_summary": self.handle_get_doc_summary,
            "answer_question": self.handle_answer_question
        }

        handler = handlers.get(tool_name)
        if not handler:
            return ToolResult(False, None, f"Unknown tool: {tool_name}")

        return await handler(params)

    async def handle_request(self, request: Dict) -> Dict:
        """Handle incoming JSON-RPC request."""
        method = request.get("method", "")
        params = request.get("params", {})
        req_id = request.get("id")

        response = {"jsonrpc": "2.0", "id": req_id}

        if method == "initialize":
            response["result"] = {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "rag-mcp-server", "version": "1.0.0"}
            }

        elif method == "tools/list":
            response["result"] = {"tools": get_tool_definitions()}

        elif method == "tools/call":
            tool_name = params.get("name", "")
            tool_args = params.get("arguments", {})
            result = await self.call_tool(tool_name, tool_args)
            response["result"] = {
                "content": [{"type": "text", "text": json.dumps(result.to_dict())}]
            }

        elif method == "ping":
            response["result"] = {"status": "ok"}

        else:
            response["error"] = {"code": -32601, "message": f"Method not found: {method}"}

        return response

    async def run_stdio(self):
        """Run server with stdio transport."""
        print("MCP Server starting...", file=sys.stderr)

        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)

        writer_transport, writer_protocol = await asyncio.get_event_loop().connect_write_pipe(
            asyncio.streams.FlowControlMixin, sys.stdout
        )
        writer = asyncio.StreamWriter(writer_transport, writer_protocol, reader, asyncio.get_event_loop())

        while True:
            try:
                line = await reader.readline()
                if not line:
                    break

                request = json.loads(line.decode().strip())
                response = await self.handle_request(request)
                writer.write((json.dumps(response) + "\n").encode())
                await writer.drain()

            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}", file=sys.stderr)
            except Exception as e:
                print(f"Error: {e}", file=sys.stderr)


async def main():
    server = MCPServer()
    await server.run_stdio()


def test_mode():
    """Run a quick test to verify MCP server can initialize."""
    print("Testing MCP Server initialization...")
    server = MCPServer()
    print("✓ MCP Server initialized successfully")
    print(f"✓ RAG Engine: {'Available' if server.rag_engine else 'Not available'}")
    print(f"✓ Tools available: {[t['name'] for t in get_tool_definitions()]}")
    print("\nNote: The MCP server is automatically spawned by the workflow system.")
    print("You don't need to run it manually. Just start the FastAPI backend and use Agent Mode in the UI.")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_mode()
    else:
        asyncio.run(main())
