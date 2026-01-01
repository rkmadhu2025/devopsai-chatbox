"""
================================================================================
DEVOPS GENAI CHATBOT - FASTAPI WEB SERVER
================================================================================
Multi-Agent AI-powered DevOps Assistant with:
- REST API endpoints
- WebSocket real-time chat
- Web UI
- Tool integrations

Run: uvicorn chatbot.main:app --reload --port 8000
================================================================================
"""

import os
import sys
import json
import asyncio
from datetime import datetime
from typing import Optional, Dict, List, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.devops_agents import (
    DEVOPS_AGENT_CONFIGS,
    get_agent_for_query,
    get_agent_config,
    get_all_agent_names,
    get_agents_by_category
)

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
        return self.conversations[session_id]


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
    return {
        "status": "healthy",
        "version": "1.0.0",
        "agents_loaded": len(state.agent_instances),
        "model": model
    }


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

    # Generate response
    if agent_id in state.agent_instances and hasattr(state, 'anthropic_client'):
        try:
            agent_data = state.agent_instances[agent_id]
            history = state.agent_histories.get(agent_id, [])

            # Add user message to history
            history.append({"role": "user", "content": message.message})

            # Call Anthropic API
            response = state.anthropic_client.messages.create(
                model=state.model,
                max_tokens=state.config.get('max_tokens', 4096),
                system=agent_data["system_message"],
                messages=history
            )
            response_text = response.content[0].text

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
    return {"status": "cleared", "session_id": session_id}


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
