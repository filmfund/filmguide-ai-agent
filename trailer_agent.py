from uagents import Agent, Context, Model
import os
import openai 
from dotenv import load_dotenv
import pandas as pd
import requests

load_dotenv() 
openai.api_key = os.getenv("OPENAI_API_KEY")
OPENAI_API_KEY= os.getenv("OPENAI_API_KEY")
TRAILER_AGENT_PORT = os.getenv("TRAILER_AGENT_PORT")  
TRAILER_AGENT_SEED= os.getenv("TRAILER_AGENT_SEED")
SECURITY_KEY= os.getenv("SECURITY_KEY")
ASI_ONE_API_KEY=os.getenv("ASI_ONE_API_KEY")
TRAILER_ENDPOINT=os.getenv("TRAILER_ENDPOINT")

class Message(Model):
    text: str
    user_id: str
    security_key: str

class ChatResponse(Model):
    text: str  
    user_id: str

trailer_agent = Agent(
    name="Trailer Agent",
    port=TRAILER_AGENT_PORT,
    seed=TRAILER_AGENT_SEED,
    endpoint = [TRAILER_ENDPOINT+'/submit'],
    #endpoint = ['https://bill-azoted-delia.ngrok-free.dev/submit'],
    mailbox=True,
    publish_agent_details=True
)

@trailer_agent.on_event("startup")
async def startup_function(ctx: Context):
    ctx.logger.info(f"Hello, I'm agent {trailer_agent.name} and my address is {trailer_agent.address}. Wallet: {trailer_agent.wallet.address()}")
    ctx.logger.info("Agent is ready to receive messages!")
    global movies, movies_compact, movies_video_dict
    movies = pd.read_csv("data/movies.csv")
    movies_compact = ""
    for _, movie in movies.iterrows():
        movies_compact += f"{movie['Name ']} - {movie['Genre']} - {movie['video']} - {movie['Director']} - {movie['Description short ']}\n"

    #movies_dict=movies.to_dict(orient='records')
    movies_video_dict = movies['video'].to_dict()
    ctx.logger.info(f"Loaded {len(movies)} movies into memory")

def get_trailers(user_input: str) -> str:
    url = "https://api.asi1.ai/v1/chat/completions"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {ASI_ONE_API_KEY}' 
    }

    prompt = f"""
    You are TrailerGuide, a trailer finder assistant.

    Your task:
    - Find the trailer link for the movie the user mentions
    - If no exact match, suggest 2-3 similar movies with their trailers
    - Be concise and helpful
    - Provide insights from the transcript if available.

    Trailers from the dataset : {movies_video_dict}
    
    The user says:
    "{user_input}"

    Use the following dataset to guide your answer when possible:
    {movies_compact}
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



@trailer_agent.on_message(model=Message)
async def handle_message(ctx: Context, sender: str, msg: Message):
    print(f"\nGot message from {sender}")
    ctx.logger.info(f"   User ID: {msg.user_id}")
    print(f"   Message: {msg.text}")

    try:
        if msg.security_key != SECURITY_KEY:
            raise Exception("Access denied. Security key not valid.")
        
        trailers = get_trailers(msg.text)
        print(f"Trailer information: {trailers}")
        
        # Send response back to the sender
        response = ChatResponse(
            text=trailers,
            user_id=msg.user_id
        )
        await ctx.send(sender, response)
        print(f"Response sent back to {sender}")
        
    except Exception as e:
        error_response = ChatResponse(
            text=f"Sorry, I encountered an error: {str(e)}",
            user_id=msg.user_id
        )
        await ctx.send(sender, error_response)
        print(f"Error occurred: {e}")


@trailer_agent.on_event("shutdown")
async def shutdown(ctx: Context):
    ctx.logger.info("Trailer Agent shutting down")

if __name__ == "__main__":
    trailer_agent.run()