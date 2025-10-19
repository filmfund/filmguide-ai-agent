from uagents import Agent, Context, Model
import asyncio
import os
from dotenv import load_dotenv
load_dotenv() 


class Message(Model):
    text: str
    user_id: str

class ChatResponse(Model):
    text: str
    user_id: str


CLIENT_SEED=os.getenv("CLIENT_SEED")
MOVIE_AGENT_ADDRESS = os.getenv("MOVIE_AGENT_ADDRESS")

client = Agent(
    name="Client",
    seed=CLIENT_SEED,
    port=8001, 
    mailbox=False,
    endpoint=["http://localhost:8001/submit"]
)

print("=" * 60)
print(f"Client Address: {client.address}")
print(f"Sending to: {MOVIE_AGENT_ADDRESS}")
print("=" * 60)

@client.on_event("startup")
async def send_message(ctx: Context):
    ctx.logger.info("📤 Sending message...")
    
    msg = Message(
        text="Recommend me Bitcoin movies",
        user_id="test_client_123"
    )
    
    await ctx.send(MOVIE_AGENT_ADDRESS, msg)
    ctx.logger.info("✅ Message sent! Waiting for response...")

@client.on_message(model=ChatResponse)
async def handle_response(ctx: Context, sender: str, msg: ChatResponse):
    ctx.logger.info("=" * 60)
    ctx.logger.info("📨 GOT RESPONSE!")
    ctx.logger.info(f"   From: {sender}")
    ctx.logger.info(f"   Message: {msg.text}")
    ctx.logger.info("=" * 60)
    
    # Wait then stop
    await asyncio.sleep(2)
    ctx.agent.stop()

if __name__ == "__main__":
    client.run()
