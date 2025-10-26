from uagents import Agent, Model, Context
import os
import asyncio
import json
from typing import Dict
from dotenv import load_dotenv
import uuid

load_dotenv()

BACKEND_SEED = os.getenv("BACKEND_SEED")
AGENTVERSE_KEY = os.getenv("AGENTVERSE_API_KEY")
MOVIE_AGENT_ADDR = os.getenv("MOVIE_AGENT_ADDRESS")
TRAILER_AGENT_ADDR = os.getenv("TRAILER_AGENT_ADDRESS")
SECURITY_KEY = os.getenv("SECURITY_KEY")
BACKEND_ENDPOINT = os.getenv("BACKEND_ENDPOINT")
MEMORY_FILE = "conversation_memory.json"

# -------------------------
# Message Models - MUST MATCH movie_agent.py EXACTLY!
# -------------------------
class Message(Model):
    text: str
    user_id: str
    security_key: str

class ChatResponse(Model):
    text: str  
    user_id: str

backend_agent = Agent(
    name="BackendAgent",
    seed=BACKEND_SEED,
    mailbox=True,
    endpoint=BACKEND_ENDPOINT + '/submit'
)

print("=" * 60)
print("Backend Agent Configuration")
print("=" * 60)
print(f"Agent Address: {backend_agent.address}")
print(f"Port: 8000")
print(f"Movie Agent Address: {MOVIE_AGENT_ADDR}")
print(f"Trailer Agent Address: {TRAILER_AGENT_ADDR}")
print("=" * 60)


pending_requests: Dict[str, dict] = {}

# -------------------------
# Conversation Memory 
# -------------------------
def load_memory():
    """Load conversation memory from JSON"""
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading memory: {e}")
            return {}
    return {}

def save_memory(mem):
    """Save conversation memory to JSON"""
    try:
        with open(MEMORY_FILE, "w") as f:
            json.dump(mem, f, indent=2)
    except Exception as e:
        print(f"Error saving memory: {e}")

def get_conversation_history(user_id: str, last_n: int = 5):
    """Get last N messages for a user"""
    mem = load_memory()
    key = f"movie_{user_id}"
    history = mem.get(key, [])
    return history[-last_n:]

def add_to_memory(user_id: str, role: str, text: str):
    """Add a message to conversation history"""
    mem = load_memory()
    key = f"movie_{user_id}"
    
    if key not in mem:
        mem[key] = []
    
    mem[key].append({
        "role": role,
        "content": text
    })
    
    # Keep only last 20 messages
    if len(mem[key]) > 20:
        mem[key] = mem[key][-20:]
    
    save_memory(mem)

def format_history(user_id: str):
    """Format conversation history as string"""
    history = get_conversation_history(user_id)
    if not history:
        return ""
    
    formatted = "Previous conversation:\n"
    for msg in history:
        formatted += f"{msg['role']}: {msg['content']}\n"
    return formatted


@backend_agent.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info("=" * 60)
    ctx.logger.info("🚀 BACKEND AGENT STARTED")
    ctx.logger.info("=" * 60)
    ctx.logger.info(f"Backend Address: {backend_agent.address}, Wallet: {backend_agent.wallet.address()}")
    ctx.logger.info(f"REST Endpoint: http://localhost:8000/chat")
    ctx.logger.info("=" * 60)

@backend_agent.on_message(model=ChatResponse)
async def handle_movie_response(ctx: Context, sender: str, msg: ChatResponse):
    """
    This handler receives responses from Movie Agent
    """
    ctx.logger.info(f"Received response from Movie Agent")
    ctx.logger.info(f"   Sender: {sender}")
    ctx.logger.info(f"   User: {msg.user_id}")
    
    # Find pending request for this user
    if msg.user_id in pending_requests:
        pending_requests[msg.user_id]["response"] = msg.text
        pending_requests[msg.user_id]["completed"] = True
        add_to_memory(msg.user_id, "assistant", msg.text)
        
        ctx.logger.info(f"Response stored for user {msg.user_id}")
    else:
        ctx.logger.warning(f"No pending request found for {msg.user_id}")

# -------------------------
# REST Endpoint for Web Application
# -------------------------
class RecommendRequest(Model):
    text: str
    user_id: str

class RecommendResponse(Model):
    reply: str
    user_id: str
    session_id: str

def agent_address_router(text: str):
    trailer_keywords = ["trailer", "watch", "show me", "clip", "video"]
    if any(word.lower() in text.lower() for word in trailer_keywords):
        return TRAILER_AGENT_ADDR
    return MOVIE_AGENT_ADDR

@backend_agent.on_rest_post("/chat", RecommendRequest, RecommendResponse)
async def recommend_endpoint(ctx: Context, req: RecommendRequest) -> RecommendResponse:
    """
    REST endpoint that your web app will call
    """
    try:
        ctx.logger.info(f"Request from user: {req.user_id}")
        ctx.logger.info(f"   Message: {req.text}")
        
        # Get conversation history
        history_text = format_history(req.user_id)
        
        # Add user message to memory
        add_to_memory(req.user_id, "user", req.text)
        
        # Enhance prompt with conversation context
        enhanced_text = req.text
        if history_text:
            enhanced_text = f"{history_text}\n\nNew question: {req.text}"
            ctx.logger.info("   Including conversation history")
        
        # Generate unique session ID
        session_id = str(uuid.uuid4())[:8]
        
        # Store as pending request
        pending_requests[req.user_id] = {
            "session_id": session_id,
            "text": req.text,
            "response": None,
            "completed": False
        }
        
        
        # Create message for the Agent
        movie_message = Message(
            text=enhanced_text,
            user_id=req.user_id,
            security_key=SECURITY_KEY
        )
        
        #Determine the agent
        agent_addr = agent_address_router(req.text)
        agent_type = "Trailer" if TRAILER_AGENT_ADDR is not None and agent_addr == TRAILER_AGENT_ADDR else "Movie"
        ctx.logger.info(f" Forwarding to {agent_type} Agent...")
        await ctx.send(agent_addr, movie_message)
        
        # Wait for response with timeout
        max_wait = 30  # seconds
        wait_interval = 0.5
        elapsed = 0
        
        ctx.logger.info("⏳ Waiting for Movie Agent response...")
        
        while elapsed < max_wait:
            if pending_requests[req.user_id]["completed"]:
                # Got response!
                response_text = pending_requests[req.user_id]["response"]
                
                # Clean up
                del pending_requests[req.user_id]
                
                ctx.logger.info("✅ Returning response to web app")
                
                return RecommendResponse(
                    reply=response_text,
                    user_id=req.user_id,
                    session_id=session_id
                )
            
            await asyncio.sleep(wait_interval)
            elapsed += wait_interval
        
        # Timeout
        ctx.logger.error("⏱️  Timeout - Movie Agent didn't respond")
        
        if req.user_id in pending_requests:
            del pending_requests[req.user_id]
        
        return RecommendResponse(
            reply="The movie agent is taking too long. Please try again.",
            user_id=req.user_id,
            session_id=session_id
        )
        
    except Exception as e:
        ctx.logger.error(f"Error: {e}")
    
        if req.user_id in pending_requests:
            del pending_requests[req.user_id]
        
        return RecommendResponse(
            reply=f"Error: {str(e)}",
            user_id=req.user_id,
            session_id="error"
        )

@backend_agent.on_event("shutdown")
async def shutdown(ctx: Context):
    ctx.logger.info("Backend Agent shutting down")


if __name__ == "__main__":
    backend_agent.run()