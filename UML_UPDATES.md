# UML Diagram Updates - MCP Multi-Agent Workflow

## Summary
Both UML diagrams have been updated to reflect the Model Context Protocol (MCP) multi-agent workflow implementation.

## Changes to `basicStructure.uml`

### Frontend Package
- **Added:** `[Workflow UI]` component
  - Connected to Search component via "Agent Mode"

### Backend API Package
- **Added:** `[Workflow Endpoints]` component
  - Handles `/workflow/start`, `/workflow/status`, `/workflow/list`

### Backend Services Package
- **Added:** `[Agent Coordinator]` component
  - Orchestrates the multi-agent workflow
- **Added:** `[MCP Server]` component
  - Runs as separate subprocess, exposes RAG tools via JSON-RPC

### Storage Package
- **Added:** `[Workflow State]` storage
  - In-memory workflow state tracking

### New Connections
- `FE_Workflow --> BE_WorkflowEP` : POST /workflow/start, GET /workflow/status
- `BE_WorkflowEP --> BE_AgentCoord` : coordinate agents
- `BE_AgentCoord --> BE_MCPServer` : JSON-RPC (subprocess)
- `BE_AgentCoord --> STORE_Workflows` : workflow state (memory)
- `BE_MCPServer --> STORE_Vectors` : query via RAG tools
- `BE_AgentCoord --> EXT_LLM` : agent reasoning
- `BE_MCPServer --> EXT_LLM` : tool execution
- `BE_MCPServer --> EXT_EMB` : search embeddings

---

## Changes to `structure.uml`

### Frontend Package
- **Added:** `[Workflow.tsx]` component
  - WorkflowTrigger and WorkflowPanel components
  - Connected: `FE_Search --> FE_Workflow : agent mode toggle`
  - Styles: `FE_Workflow --> FE_CSS`

### Backend Package
- **Added:** `[agents.py]` - Agent coordinator implementation
- **Added:** `[mcp_server.py]` - MCP server subprocess
- **Added:** `[mcp_tools.py]` - Tool definitions

### New Connections in Backend
- `BE_API --> BE_Agents` : start/get workflow
- `BE_Agents --> BE_MCPServer` : spawn subprocess
- `BE_MCPServer --> BE_MCPTools` : tool definitions
- `BE_MCPServer --> BE_RAG` : RAGEngine for tools

### Frontend API Calls
- **Added:** `FE_Workflow --> BE_API : POST /workflow/start`
- **Added:** `FE_Workflow --> BE_API : GET /workflow/status/{id}`
- **Added:** `FE_Workflow --> BE_API : GET /workflow/list`

### Detailed Endpoints
- **Added:** `POST /workflow/start` (EP_WF_START)
- **Added:** `GET /workflow/status/{id}` (EP_WF_STATUS)
- **Added:** `GET /workflow/list` (EP_WF_LIST)

### Endpoint Implementations
- `EP_WF_START --> BE_Agents : start_workflow(query, user_id)`
- `EP_WF_STATUS --> BE_Agents : get_workflow(workflow_id)`
- `EP_WF_LIST --> BE_Agents : list user workflows`

### Multi-Agent Workflow Components
New component section added:
- **AgentCoordinator** - Main workflow orchestrator
- **Planner Agent** - Step 1: Analyze query and plan
- **Retriever Agent** - Step 2: Search documents
- **Responder Agent** - Step 3: Generate answer
- **MCPClient** - Communicates with MCP server

### Agent Flow
```
AGENT_COORD --> AGENT_PLAN : step 1
AGENT_COORD --> AGENT_RETRIEVE : step 2
AGENT_COORD --> AGENT_RESPOND : step 3
AGENT_COORD --> AGENT_MCP_CLIENT : spawn subprocess

AGENT_PLAN --> EXT_LLM : create plan
AGENT_RETRIEVE --> AGENT_MCP_CLIENT : search_docs
AGENT_RESPOND --> AGENT_MCP_CLIENT : answer_question

AGENT_MCP_CLIENT --> BE_MCPServer : JSON-RPC (stdio)
```

### MCP Server Tool Handlers
New components:
- `handle_search_docs` (MCP_SEARCH) → similarity_search on ChromaDB
- `handle_list_user_docs` (MCP_LIST) → listUserFiles
- `handle_answer_question` (MCP_ANSWER) → query RAG
- `handle_get_doc_summary` (MCP_SUMMARY) → get chunks

---

## Architecture Highlights

### Separation of Concerns
- **Frontend**: WorkflowTrigger polls for status updates
- **Backend API**: Workflow endpoints manage async execution
- **Agent Coordinator**: Orchestrates 3-step agent workflow
- **MCP Server**: Runs as separate process, provides RAG tools via JSON-RPC

### Communication Pattern
```
Frontend (polling) 
    ↓
FastAPI Endpoints 
    ↓
Agent Coordinator (async) 
    ↓
MCP Client (subprocess spawn) 
    ↓
MCP Server (JSON-RPC stdio) 
    ↓
RAG Engine & ChromaDB
```

### Data Flow
1. User clicks "Run Multi-Agent" in UI
2. Frontend POSTs to `/workflow/start` → returns workflow_id
3. Frontend polls `/workflow/status/{id}` every second
4. Backend spawns MCP server subprocess
5. Agents (Planner → Retriever → Responder) execute in sequence
6. Each agent calls MCP tools (search_docs, answer_question, etc.)
7. MCP server queries RAG engine and returns results
8. Workflow completes, frontend displays final answer with agent steps

---

## Viewing the Diagrams

To generate PNG/SVG from the .uml files:

```bash
# Install PlantUML
brew install plantuml

# Generate diagrams
plantuml basicStructure.uml
plantuml structure.uml
```

Or use online viewer: http://www.plantuml.com/plantuml/uml/
