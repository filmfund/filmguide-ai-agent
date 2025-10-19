from uagents import Agent, Context, Model, Protocol
import os
import openai 
from dotenv import load_dotenv
import pandas as pd

load_dotenv() 
openai.api_key = os.getenv("OPENAI_API_KEY")
AGENT_PORT = os.getenv("AGENT_PORT")  
AGENT_SEED= os.getenv("AGENT_SEED")

class Message(Model):
    text: str
    user_id: str

class ChatResponse(Model):
    text: str  
    user_id: str

# Mailbox agent published on Agentverse
agent = Agent(
    name="Movie Recommender Agent",
    port=5050,
    seed=AGENT_SEED,
    endpoint = ['http://localhost:5050/submit'],
    mailbox=False
    #publish_agent_details=True
)


movies = pd.read_excel("data/movies.xlsx")

# Startup handler
@agent.on_event("startup")
async def startup_function(ctx: Context):
    ctx.logger.info(f"Hello, I'm agent {agent.name} and my address is {agent.address}.")
    ctx.logger.info(f"Agent is running on port: {AGENT_PORT}")
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
@agent.on_message(model=Message)
async def handle_message(ctx: Context, sender: str, msg: Message):
    print(f"\n📨 Got message from {sender}")
    ctx.logger.info(f"   User ID: {msg.user_id}")
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
        

@agent.on_event("shutdown")
async def shutdown(ctx: Context):
    ctx.logger.info("Movie Recommender Agent shutting down")

if __name__ == "__main__":
    agent.run()