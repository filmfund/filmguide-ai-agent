from uagents import Agent, Context, Protocol
import asyncio
from agent import ChatMessage, chat_proto

test_agent = Agent(
    name="test_user",
    seed="test_user_seed_12345",
    port=8003,
    mailbox=True
)
test_agent.include(chat_proto)

MOVIE_AGENT_ADDRESS = "agent1q0qvgq2myct3m8xq7vs8fafgh3umd3kwl9kmz2yp3j6p40v3246cucghmv7"

@test_agent.on_event("startup")
async def send_message(ctx: Context):
    print(f"📤 Sending to address: {MOVIE_AGENT_ADDRESS}")
    
    msg = ChatMessage(
        text="Recommend me a Bitcoin documentary",
        user_id="test_user_001"
    )
    
    try:
        await ctx.send(MOVIE_AGENT_ADDRESS, msg)
        print("✅ Message sent successfully!")
    except Exception as e:
        print(f"❌ Failed to send message: {e}")
    
    await asyncio.sleep(5)
    ctx.agent.stop()


if __name__ == "__main__":
    test_agent.run()