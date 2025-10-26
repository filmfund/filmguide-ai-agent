from uagents import Agent, Context, Model
import os
import openai 
from dotenv import load_dotenv
import pandas as pd
import requests

load_dotenv() 
openai.api_key = os.getenv("OPENAI_API_KEY")
OPENAI_API_KEY= os.getenv("OPENAI_API_KEY")
AGENT_PORT = os.getenv("AGENT_PORT")  
AGENT_SEED= os.getenv("AGENT_SEED")
SECURITY_KEY= os.getenv("SECURITY_KEY")
ASI_ONE_API_KEY=os.getenv("ASI_ONE_API_KEY")
MOVIE_ENDPOINT=os.getenv("MOVIE_ENDPOINT")

class Message(Model):
    text: str
    user_id: str
    security_key: str

class ChatResponse(Model):
    text: str  
    user_id: str

agent = Agent(
    name="Movie Recommender Agent",
    port=5050,
    seed=AGENT_SEED,
    endpoint = [MOVIE_ENDPOINT+'/submit'],
    #endpoint = ['https://bill-azoted-delia.ngrok-free.dev/submit'],
    mailbox=True,
    publish_agent_details=True
)

movies = pd.read_csv("data/movies.csv")

# Startup handler
@agent.on_event("startup")
async def startup_function(ctx: Context):
    ctx.logger.info(f"Hello, I'm agent {agent.name} and my address is {agent.address}. Wallet: {agent.wallet.address()}")
    ctx.logger.info("Agent is ready to receive messages!")

# Function to get movie recommendations
def get_movie_recommendations(user_input: str) -> str:
    url = "https://api.asi1.ai/v1/chat/completions"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {ASI_ONE_API_KEY}' 
    }

    prompt = f"""
    You are **FilmGuide**, a knowledgeable and friendly AI movie expert who loves cinema.
    You chat naturally with users about movies, actors, genres, and recommendations.
    You can suggest movies, describe plots, mention directors or actors, and give brief opinions.
    Be concise but engaging — answer like a human film buff, not a database.
    Use the provided dataset if relevant, otherwise use your own film knowledge.

    The user says:
    "{user_input}"

    Use the following dataset to guide your answer when possible:
    {movies.to_dict(orient='records')}
    """

    response = requests.post(
        url,
        headers=headers,
        json={
            "model": "asi1-mini",  
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 500
        }
    )
    result = response.json()
    return result['choices'][0]['message']['content']



@agent.on_message(model=Message)
async def handle_message(ctx: Context, sender: str, msg: Message):
    print(f"\nGot message from {sender}")
    ctx.logger.info(f"   User ID: {msg.user_id}")
    print(f"   Message: {msg.text}")

    # Get movie recommendations
    try:
        if msg.security_key != SECURITY_KEY:
            raise Exception("Access denied. Security key not valid.")
        
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
        print(f"Error occurred: {e}")


@agent.on_event("shutdown")
async def shutdown(ctx: Context):
    ctx.logger.info("Movie Recommender Agent shutting down")

if __name__ == "__main__":
    agent.run()