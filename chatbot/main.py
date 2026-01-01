"""
================================================================================
DEVOPS GENAI CHATBOT - FASTAPI WEB SERVER
================================================================================
Multi-Agent AI-powered DevOps Assistant with:
- REST API endpoints
- WebSocket real-time chat
- Web UI
- Tool integrations
- PostgreSQL database for persistent storage
- File upload support (PDF, text, images)

Run: uvicorn chatbot.main:app --reload --port 8000
================================================================================
"""

import os
import sys
import json
import asyncio
import uuid
import logging
from datetime import datetime
from typing import Optional, Dict, List, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request, Query, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.devops_agents import (
    DEVOPS_AGENT_CONFIGS,
    get_agent_for_query,
    get_agent_config,
    get_all_agent_names,
    get_agents_by_category
)

# Database imports (with fallback for missing dependencies)
try:
    from database import DatabaseManager, ChatRepository, FileRepository, HostRepository
    DATABASE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Database module not available: {e}")
    DATABASE_AVAILABLE = False
    DatabaseManager = None
    ChatRepository = None
    FileRepository = None
    HostRepository = None

# File loader imports
try:
    from file_loader import FileProcessor
    FILE_LOADER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"File loader module not available: {e}")
    FILE_LOADER_AVAILABLE = False
    FileProcessor = None

# Initialize FastAPI app
app = FastAPI(
    title="DevOps GenAI Chatbot",
    description="Multi-Agent AI-powered DevOps Assistant",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
class ChatState:
    def __init__(self):
        self.conversations: Dict[str, List[Dict]] = {}
        self.agent_instances: Dict[str, Any] = {}
        self.config = self._load_config()
        self._init_agents()
        self._init_database()
        self._init_file_processor()

    def _load_config(self) -> Dict:
        """Load configuration from config.json or environment variables"""
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except FileNotFoundError:
            config = {
                "anthropic": {
                    "api_key": "",
                    "model": "claude-3-haiku-20240307"
                },
                "max_tokens": 4096,
                "temperature": 0.7
            }

        # Override with environment variable if set
        env_api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if env_api_key:
            if "anthropic" not in config:
                config["anthropic"] = {}
            config["anthropic"]["api_key"] = env_api_key

        return config

    def _init_database(self):
        """Initialize database connection and repositories"""
        self.db_manager = None
        self.chat_repo = None
        self.file_repo = None
        self.host_repo = None
        self.db_enabled = False

        if not DATABASE_AVAILABLE:
            logger.warning("Database module not available - using in-memory storage")
            return

        try:
            self.db_manager = DatabaseManager()

            # Try to initialize connection pool
            if self.db_manager.initialize_sync_pool():
                # Create tables if they don't exist
                self.db_manager.create_tables()

                # Initialize repositories
                self.chat_repo = ChatRepository(self.db_manager)
                self.file_repo = FileRepository(self.db_manager)
                self.host_repo = HostRepository(self.db_manager)
                self.db_enabled = True

                logger.info("Database initialized successfully")
            else:
                logger.warning("Database connection failed - using in-memory storage")

        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            logger.info("Continuing with in-memory storage")

    def _init_file_processor(self):
        """Initialize file processor for uploads"""
        self.file_processor = None

        if not FILE_LOADER_AVAILABLE:
            logger.warning("File loader module not available")
            return

        try:
            upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
            self.file_processor = FileProcessor(
                upload_dir=upload_dir,
                db_manager=self.db_manager if self.db_enabled else None
            )
            logger.info(f"File processor initialized. Upload dir: {upload_dir}")
        except Exception as e:
            logger.error(f"File processor initialization failed: {e}")

    def _init_agents(self):
        """Initialize agents with Anthropic Claude"""
        try:
            import anthropic

            anthropic_config = self.config.get('anthropic', {})
            api_key = anthropic_config.get('api_key', '')
            model = anthropic_config.get('model', 'claude-opus-4-5-20251101')

            if not api_key:
                print("[!] No API key configured. Running in demo mode.")
                self.agent_instances = {}
                return

            self.anthropic_client = anthropic.Anthropic(api_key=api_key)
            self.model = model
            self.agent_histories = {}

            for agent_id, agent_config in DEVOPS_AGENT_CONFIGS.items():
                print(f"  [+] {agent_config['name']}: Claude ({model})")
                self.agent_instances[agent_id] = {
                    "name": agent_config["name"],
                    "system_message": agent_config["prompt"],
                    "model": "Claude"
                }
                self.agent_histories[agent_id] = []

        except ImportError:
            print("[!] Anthropic not installed. Running in demo mode.")
            self.agent_instances = {}

    def get_or_create_conversation(self, session_id: str) -> List[Dict]:
        """Get or create a conversation for a session"""
        if session_id not in self.conversations:
            self.conversations[session_id] = []
            # Load from database if available
            if self.db_enabled and self.chat_repo:
                try:
                    db_history = self.chat_repo.get_session_history(session_id, limit=100)
                    for msg in db_history:
                        self.conversations[session_id].append({
                            "role": msg["role"],
                            "content": msg["message"],
                            "agent_id": msg.get("agent_id"),
                            "timestamp": msg.get("created_at")
                        })
                except Exception as e:
                    logger.error(f"Failed to load conversation from database: {e}")
        return self.conversations[session_id]

    def save_message(self, session_id: str, role: str, content: str,
                     agent_id: Optional[str] = None, tokens: int = 0) -> None:
        """Save a message to database if enabled"""
        if self.db_enabled and self.chat_repo:
            try:
                self.chat_repo.save_message(
                    session_id=session_id,
                    role=role,
                    message=content,
                    agent_id=agent_id,
                    tokens_used=tokens
                )
            except Exception as e:
                logger.error(f"Failed to save message to database: {e}")

    def log_host_action(self, hostname: str, action: str, status: str,
                        ip_address: Optional[str] = None,
                        user_id: Optional[str] = None,
                        details: Optional[Dict] = None) -> None:
        """Log a host action to database if enabled"""
        if self.db_enabled and self.host_repo:
            try:
                self.host_repo.log_action(
                    hostname=hostname,
                    action=action,
                    status=status,
                    ip_address=ip_address,
                    user_id=user_id,
                    details=details
                )
            except Exception as e:
                logger.error(f"Failed to log host action: {e}")


# Initialize state
state = ChatState()


# Pydantic models
class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = "default"
    force_agent: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    agent_id: str
    agent_name: str
    agent_icon: str
    timestamp: str
    session_id: str


class AgentInfo(BaseModel):
    id: str
    name: str
    icon: str
    category: str
    keywords: List[str]


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]

    async def send_message(self, message: dict, session_id: str):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_json(message)

    async def broadcast(self, message: dict):
        for connection in self.active_connections.values():
            await connection.send_json(message)


manager = ConnectionManager()


# API Routes
@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main chat UI"""
    return get_chat_html()


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    model = getattr(state, 'model', state.config.get('anthropic', {}).get('model', 'unknown'))

    health_status = {
        "status": "healthy",
        "version": "1.0.0",
        "agents_loaded": len(state.agent_instances),
        "model": model,
        "database": {
            "enabled": state.db_enabled,
            "status": "connected" if state.db_enabled else "not configured"
        },
        "file_processor": {
            "enabled": state.file_processor is not None,
            "status": "ready" if state.file_processor else "not available"
        }
    }

    # Check database health if enabled
    if state.db_enabled and state.db_manager:
        try:
            db_health = state.db_manager.health_check()
            health_status["database"]["status"] = db_health.get("status", "unknown")
        except Exception:
            health_status["database"]["status"] = "error"

    return health_status


@app.get("/api/agents", response_model=List[AgentInfo])
async def list_agents():
    """List all available agents"""
    agents = []
    for agent_id, config in DEVOPS_AGENT_CONFIGS.items():
        agents.append(AgentInfo(
            id=agent_id,
            name=config["name"],
            icon=config.get("icon", "🔧"),
            category=config.get("category", "General"),
            keywords=config.get("keywords", [])[:10]
        ))
    return agents


@app.get("/api/agents/categories")
async def list_agent_categories():
    """List agents grouped by category"""
    return get_agents_by_category()


@app.get("/api/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get details for a specific agent"""
    config = get_agent_config(agent_id)
    if not config:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {
        "id": agent_id,
        "name": config["name"],
        "icon": config.get("icon", "🔧"),
        "category": config.get("category", "General"),
        "keywords": config.get("keywords", []),
        "prompt": config.get("prompt", "")[:500] + "..."
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """Send a message and get a response"""
    # Determine agent
    if message.force_agent and message.force_agent in DEVOPS_AGENT_CONFIGS:
        agent_id = message.force_agent
    else:
        agent_id = get_agent_for_query(message.message)

    agent_config = get_agent_config(agent_id)

    # Get conversation history
    conversation = state.get_or_create_conversation(message.session_id)

    # Add user message to conversation
    conversation.append({
        "role": "user",
        "content": message.message,
        "timestamp": datetime.now().isoformat()
    })

    # Save user message to database
    state.save_message(message.session_id, "user", message.message, agent_id)

    # Get file context if available
    file_context = ""
    if state.file_processor:
        file_context = state.file_processor.get_context_for_chat(
            message.session_id, max_files=3
        )

    # Generate response
    tokens_used = 0
    if agent_id in state.agent_instances and hasattr(state, 'anthropic_client'):
        try:
            agent_data = state.agent_instances[agent_id]
            history = state.agent_histories.get(agent_id, [])

            # Add user message to history (include file context if available)
            user_content = message.message
            if file_context:
                user_content = f"{file_context}\n\nUser Question: {message.message}"

            history.append({"role": "user", "content": user_content})

            # Call Anthropic API
            response = state.anthropic_client.messages.create(
                model=state.model,
                max_tokens=state.config.get('max_tokens', 4096),
                system=agent_data["system_message"],
                messages=history
            )
            response_text = response.content[0].text

            # Track token usage
            if hasattr(response, 'usage'):
                tokens_used = response.usage.input_tokens + response.usage.output_tokens

            # Add assistant response to history
            history.append({"role": "assistant", "content": response_text})
            state.agent_histories[agent_id] = history

        except Exception as e:
            response_text = f"Error communicating with agent: {str(e)}"
    else:
        # Demo mode response
        response_text = f"**{agent_config['name']}** would help you with: {message.message}\n\n_(Running in demo mode - configure API key for full functionality)_"

    # Add assistant message to conversation
    conversation.append({
        "role": "assistant",
        "agent_id": agent_id,
        "content": response_text,
        "timestamp": datetime.now().isoformat()
    })

    # Save assistant response to database
    state.save_message(message.session_id, "assistant", response_text, agent_id, tokens_used)

    return ChatResponse(
        response=response_text,
        agent_id=agent_id,
        agent_name=agent_config["name"],
        agent_icon=agent_config.get("icon", "🔧"),
        timestamp=datetime.now().isoformat(),
        session_id=message.session_id
    )


@app.get("/api/conversation/{session_id}")
async def get_conversation(session_id: str):
    """Get conversation history for a session"""
    return state.get_or_create_conversation(session_id)


@app.delete("/api/conversation/{session_id}")
async def clear_conversation(session_id: str):
    """Clear conversation history for a session"""
    if session_id in state.conversations:
        state.conversations[session_id] = []
        # Clear agent histories
        if hasattr(state, 'agent_histories'):
            for agent_id in state.agent_histories:
                state.agent_histories[agent_id] = []
    # Also clear from database if enabled
    if state.db_enabled and state.chat_repo:
        state.chat_repo.delete_session(session_id)
    return {"status": "cleared", "session_id": session_id}


# ================================================================================
# FILE UPLOAD ENDPOINTS
# ================================================================================

@app.post("/api/files/upload")
async def upload_file(
    file: UploadFile = File(...),
    session_id: str = Form(default="default")
):
    """
    Upload a file for processing.
    Supports PDF, text files, and images.
    """
    if not state.file_processor:
        raise HTTPException(
            status_code=503,
            detail="File processing is not available. Install required dependencies."
        )

    try:
        # Read file content
        content = await file.read()

        # Process the file
        result = await state.file_processor.process_file(
            file_content=content,
            original_filename=file.filename,
            mime_type=file.content_type,
            session_id=session_id
        )

        if result["success"]:
            return {
                "status": "success",
                "file_id": result.get("file_id"),
                "filename": result["original_filename"],
                "file_type": result["file_type"],
                "extracted_text_preview": (
                    result.get("extracted_text", "")[:500] + "..."
                    if result.get("extracted_text") and len(result.get("extracted_text", "")) > 500
                    else result.get("extracted_text", "")
                ),
                "metadata": result["metadata"]
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Processing failed"))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/files/{file_id}")
async def get_file(file_id: int):
    """Get file details and extracted content by ID."""
    if not state.file_processor:
        raise HTTPException(status_code=503, detail="File processing not available")

    result = state.file_processor.get_file_content(file_id)
    if not result:
        raise HTTPException(status_code=404, detail="File not found")

    return result


@app.get("/api/files/session/{session_id}")
async def get_session_files(
    session_id: str,
    file_type: Optional[str] = Query(None, description="Filter by file type")
):
    """Get all files uploaded for a session."""
    if not state.file_processor:
        return []

    return state.file_processor.get_session_files(session_id, file_type)


@app.get("/api/files/search")
async def search_files(
    q: str = Query(..., description="Search query"),
    file_type: Optional[str] = Query(None, description="Filter by file type"),
    limit: int = Query(50, le=100)
):
    """Search files by content."""
    if not state.file_processor:
        return []

    return state.file_processor.search_files(q, file_type, limit)


@app.delete("/api/files/{file_id}")
async def delete_file(file_id: int):
    """Delete a file record."""
    if not state.file_processor:
        raise HTTPException(status_code=503, detail="File processing not available")

    success = state.file_processor.delete_file(file_id)
    if not success:
        raise HTTPException(status_code=404, detail="File not found or could not be deleted")

    return {"status": "deleted", "file_id": file_id}


@app.get("/api/files/stats")
async def get_file_stats():
    """Get file processing statistics."""
    if not state.file_processor:
        return {"error": "File processing not available"}

    return state.file_processor.get_stats()


# ================================================================================
# HOST HISTORY ENDPOINTS
# ================================================================================

@app.post("/api/hosts/log")
async def log_host_action(
    hostname: str = Form(...),
    action: str = Form(...),
    status: str = Form(...),
    ip_address: Optional[str] = Form(None),
    user_id: Optional[str] = Form(None),
    details: Optional[str] = Form(None)
):
    """Log a host action."""
    if not state.db_enabled or not state.host_repo:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        details_dict = json.loads(details) if details else None
    except json.JSONDecodeError:
        details_dict = {"raw": details}

    record_id = state.host_repo.log_action(
        hostname=hostname,
        action=action,
        status=status,
        ip_address=ip_address,
        user_id=user_id,
        details=details_dict
    )

    if record_id:
        return {"status": "logged", "id": record_id}
    else:
        raise HTTPException(status_code=500, detail="Failed to log action")


@app.get("/api/hosts/{hostname}/history")
async def get_host_history(
    hostname: str,
    limit: int = Query(100, le=500),
    action: Optional[str] = Query(None)
):
    """Get activity history for a specific host."""
    if not state.db_enabled or not state.host_repo:
        return []

    return state.host_repo.get_host_history(hostname, limit=limit, action=action)


@app.get("/api/hosts/{hostname}/stats")
async def get_host_stats(hostname: str):
    """Get statistics for a specific host."""
    if not state.db_enabled or not state.host_repo:
        return {}

    return state.host_repo.get_host_stats(hostname)


@app.get("/api/hosts")
async def get_all_hosts(limit: int = Query(100, le=1000)):
    """Get list of all known hosts."""
    if not state.db_enabled or not state.host_repo:
        return []

    return state.host_repo.get_all_hosts(limit)


@app.get("/api/hosts/activity/recent")
async def get_recent_activity(
    hours: int = Query(24, le=168),
    action: Optional[str] = Query(None)
):
    """Get recent activity across all hosts."""
    if not state.db_enabled or not state.host_repo:
        return []

    return state.host_repo.get_recent_activity(hours=hours, action=action)


@app.get("/api/hosts/activity/summary")
async def get_activity_summary(hours: int = Query(24, le=168)):
    """Get summary of host activity."""
    if not state.db_enabled or not state.host_repo:
        return {}

    return state.host_repo.get_activity_summary(hours)


@app.get("/api/hosts/activity/failed")
async def get_failed_actions(hours: int = Query(24, le=168)):
    """Get recent failed actions."""
    if not state.db_enabled or not state.host_repo:
        return []

    return state.host_repo.get_failed_actions(hours)


# ================================================================================
# DATABASE STATUS ENDPOINTS
# ================================================================================

@app.get("/api/database/health")
async def database_health():
    """Check database connectivity."""
    if not state.db_enabled or not state.db_manager:
        return {
            "status": "unavailable",
            "message": "Database not configured or connection failed"
        }

    return state.db_manager.health_check()


@app.get("/api/database/stats")
async def database_stats():
    """Get database statistics."""
    if not state.db_enabled:
        return {"status": "unavailable"}

    stats = {
        "database_enabled": state.db_enabled,
        "file_processor_enabled": state.file_processor is not None
    }

    if state.chat_repo:
        sessions = state.chat_repo.get_all_sessions(limit=1000)
        stats["chat"] = {
            "total_sessions": len(sessions),
            "total_messages": sum(s.get("message_count", 0) for s in sessions)
        }

    if state.file_repo:
        stats["files"] = state.file_repo.get_file_stats()

    if state.host_repo:
        stats["hosts"] = state.host_repo.get_activity_summary(24)

    return stats


@app.get("/api/sessions")
async def list_sessions(
    limit: int = Query(100, le=500),
    active_hours: Optional[int] = Query(None, description="Only sessions active within hours")
):
    """Get list of all chat sessions."""
    if not state.db_enabled or not state.chat_repo:
        # Return in-memory sessions
        return [
            {"session_id": sid, "message_count": len(msgs)}
            for sid, msgs in state.conversations.items()
        ]

    return state.chat_repo.get_all_sessions(limit, active_hours)


@app.get("/api/sessions/{session_id}/stats")
async def get_session_stats(session_id: str):
    """Get statistics for a specific session."""
    if not state.db_enabled or not state.chat_repo:
        conversation = state.get_or_create_conversation(session_id)
        return {
            "session_id": session_id,
            "total_messages": len(conversation),
            "user_messages": sum(1 for m in conversation if m.get("role") == "user"),
            "assistant_messages": sum(1 for m in conversation if m.get("role") == "assistant")
        }

    return state.chat_repo.get_session_stats(session_id)


# WebSocket endpoint
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time chat"""
    await manager.connect(websocket, session_id)
    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            message = data.get("message", "")
            force_agent = data.get("force_agent")

            # Send typing indicator
            await manager.send_message({
                "type": "typing",
                "agent_id": get_agent_for_query(message) if not force_agent else force_agent
            }, session_id)

            # Process message
            chat_message = ChatMessage(
                message=message,
                session_id=session_id,
                force_agent=force_agent
            )
            response = await chat(chat_message)

            # Send response
            await manager.send_message({
                "type": "message",
                "response": response.response,
                "agent_id": response.agent_id,
                "agent_name": response.agent_name,
                "agent_icon": response.agent_icon,
                "timestamp": response.timestamp
            }, session_id)

    except WebSocketDisconnect:
        manager.disconnect(session_id)


def get_chat_html() -> str:
    """Return the chat UI HTML - Dashboard Style Design"""
    from chatbot.ui_dashboard import get_dashboard_html
    return get_dashboard_html()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
