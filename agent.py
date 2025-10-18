from uagents import Agent, Context, Model, Protocol
import os
import openai 
from dotenv import load_dotenv
import pandas as pd

load_dotenv() 
openai.api_key = os.getenv("OPENAI_API_KEY")
AGENT_PORT = os.getenv("AGENT_PORT", "8001")  # Default to 8001 if not set

class ChatMessage(Model):
    text: str
    user_id: str

class ChatResponse(Model):
    text: str  
    user_id: str

# Mailbox agent published on Agentverse
agent = Agent(
    name="Movie Recommender Agent",
    port=AGENT_PORT,
    mailbox=True,
    publish_agent_details=True,
)

# Create a protocol
chat_proto = Protocol("chat")

#Check agent details
print(f"Your agent's address is: {agent.address}")
movies = pd.read_excel("data/movies.xlsx")


# Startup handler
@agent.on_event("startup")
async def startup_function(ctx: Context):
    ctx.logger.info(f"Hello, I'm agent {agent.name} and my address is {agent.address}.")
    ctx.logger.info(f"Agent is running on port: {AGENT_PORT}")
    ctx.logger.info(f"Agent mailbox enabled: {agent.mailbox}")
    ctx.logger.info("Agent is ready to receive messages!")

# Function to get movie recommendations
def get_movie_recommendations(user_input: str) -> str:
    prompt = f"""Recommend me 2 or 3 movies based on the following descriptions:
    {user_input}
    using the following dataset:{movies.head(9).to_dict(orient='records')}
    """
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# This runs when we receive a ChatMessage
@chat_proto.on_message(model=ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    print(f"\n📨 Got message from {sender}")
    print(f"   User: {msg.user_id}")
    print(f"   Message: {msg.text}")
    
    # Get movie recommendations
    try:
        recommendations = get_movie_recommendations(msg.text)
        print(f"🎬 Generated recommendations: {recommendations}")
        
        # Send response back to the sender
        response = ChatResponse(
            text=recommendations,
            user_id=msg.user_id
        )
        await ctx.send(sender, response)
        print(f"✅ Response sent back to {sender}")
        
    except Exception as e:
        error_response = ChatResponse(
            text=f"Sorry, I encountered an error: {str(e)}",
            user_id=msg.user_id
        )
        await ctx.send(sender, error_response)
        print(f"❌ Error occurred: {e}")

agent.include(chat_proto)

@agent.on_event("shutdown")
async def shutdown(ctx: Context):
    ctx.logger.info("Movie Recommender Agent shutting down")

if __name__ == "__main__":
    agent.run()