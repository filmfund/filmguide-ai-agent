from uagents import Agent, Context, Model, Protocol
import os
import openai 
from dotenv import load_dotenv
import pandas as pd
import requests
import json

load_dotenv() 
openai.api_key = os.getenv("OPENAI_API_KEY")
OPENAI_API_KEY= os.getenv("OPENAI_API_KEY")
AGENT_PORT = os.getenv("AGENT_PORT")  
AGENT_SEED= os.getenv("AGENT_SEED")
SECURITY_KEY= os.getenv("SECURITY_KEY")
ASI_ONE_API_KEY=os.getenv("ASI_ONE_API_KEY")

class Message(Model):
    text: str
    user_id: str
    security_key: str

class ChatResponse(Model):
    text: str  
    user_id: str

# Mailbox agent published on Agentverse
agent = Agent(
    name="Movie Recommender Agent",
    port=5050,
    seed=AGENT_SEED,
    endpoint = 'http://localhost:5050/submit',
    #endpoint = ['https://bill-azoted-delia.ngrok-free.dev/submit'],
    mailbox=True,
    publish_agent_details=True
)

movies = pd.read_csv("data/movies.csv")

# Startup handler
@agent.on_event("startup")
async def startup_function(ctx: Context):
    ctx.logger.info(f"Hello, I'm agent {agent.name} and my address is {agent.address}.")
    ctx.logger.info(f"Agent is running on port: {AGENT_PORT}")
    ctx.logger.info("Agent is ready to receive messages!")

# Function to get movie recommendations
def get_movie_recommendations(user_input: str) -> str:
    url = "https://api.asi1.ai/v1/chat/completions"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {ASI_ONE_API_KEY}'  # Replace with your API Key
    }

    prompt = f"""Recommend me 2 or 3 movies based on the following descriptions:
    {user_input}
    using the following dataset:{movies.head(9).to_dict(orient='records')}
    """
#TODO : use asi1-mini model
    response = requests.post(
        url,
        headers=headers,
        json={
            "model": "asi1-mini",  # Correct ASI:One model
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 500
        }
    )
    """
    response = openai.ChatCompletion.create(
        model="asi1-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    """
    return response.choices[0].message.content



# This runs when we receive a ChatMessage
#TODO : join this with the on_rest_post method
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

@agent.on_rest_post("/search", Message, ChatResponse)
async def search_products(ctx: Context, req: Message) -> ChatResponse:

    try:
        if req.security_key != SECURITY_KEY:
            raise Exception("Access denied. Security key not valid.")
        
        results = get_movie_recommendations(req.text)
        
        return ChatResponse(
            text=results,
            user_id=req.user_id
        )

    except Exception as e:
        return ChatResponse(
            text=f"Sorry, I encountered an error: {str(e)}",
            user_id=req.user_id
        )

@agent.on_event("shutdown")
async def shutdown(ctx: Context):
    ctx.logger.info("Movie Recommender Agent shutting down")

if __name__ == "__main__":
    agent.run()