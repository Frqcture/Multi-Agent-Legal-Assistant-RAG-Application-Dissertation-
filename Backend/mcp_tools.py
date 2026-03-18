"""
MCP Tool Definitions
Wraps existing RAG and ingest capabilities as MCP-compatible tools.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class ToolResult:
    """Standard result from an MCP tool call."""

    success: bool
    data: Any
    error: Optional[str] = None

    def to_dict(self) -> Dict:
        return {"success": self.success, "data": self.data, "error": self.error}


@dataclass
class ToolDefinition:
    """Definition of an MCP tool."""

    name: str
    description: str
    parameters: Dict[str, Any]
    required: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": self.parameters,
                "required": self.required,
            },
        }


# Tool definitions for MCP server
TOOL_DEFINITIONS = [
    ToolDefinition(
        name="search_docs",
        description="Search user's documents using semantic similarity. Returns relevant chunks with source citations.",
        parameters={
            "query": {"type": "string", "description": "The search query"},
            "user_id": {"type": "string", "description": "User ID for isolation"},
            "top_k": {
                "type": "integer",
                "description": "Number of results to return",
                "default": 5,
            },
        },
        required=["query", "user_id"],
    ),
    ToolDefinition(
        name="list_user_docs",
        description="List all documents uploaded by a specific user.",
        parameters={"user_id": {"type": "string", "description": "User ID"}},
        required=["user_id"],
    ),
    ToolDefinition(
        name="get_doc_summary",
        description="Get a summary of a specific document's content.",
        parameters={
            "user_id": {"type": "string", "description": "User ID"},
            "filename": {"type": "string", "description": "Document filename"},
        },
        required=["user_id", "filename"],
    ),
    ToolDefinition(
        name="answer_question",
        description="Generate an answer to a question using RAG with citations.",
        parameters={
            "question": {"type": "string", "description": "The question to answer"},
            "user_id": {
                "type": "string",
                "description": "User ID for document isolation",
            },
            "context": {
                "type": "string",
                "description": "Optional additional context",
                "default": "",
            },
        },
        required=["question", "user_id"],
    ),
    ToolDefinition(
        name="search_web",
        description="Search the web for information when user documents don't contain the answer. Returns a list of web results with titles, URLs, and snippets.",
        parameters={
            "query": {"type": "string", "description": "The search query"},
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results to return",
                "default": 5,
            },
        },
        required=["query"],
    ),
]


def get_tool_definitions() -> List[Dict]:
    """Return all tool definitions as dicts."""
    return [t.to_dict() for t in TOOL_DEFINITIONS]
