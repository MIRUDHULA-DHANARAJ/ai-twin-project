from fastapi import FastAPI, HTTPException
from transformers import AutoTokenizer, AutoModelForCausalLM
from pydantic import BaseModel
import logging
import os
import requests
from supabase import create_client, Client
import random
from dotenv import load_dotenv
from transformers import pipeline
import torch
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()

# Environment Variables
WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# Supabase Client Initialization
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Models
poem_generator = pipeline("text-generation", model="gpt2")

# Joke Database
jokes = [
    "Why don't scientists trust atoms? Because they make up everything!",
    "What do you call a lazy kangaroo? A pouch potato.",
    "Why did the scarecrow win an award? Because he was outstanding in his field!"
]

# Models (Moved to the top)
class ChatRequest(BaseModel):
    message: str
    context: str = "This is a default context."

class PoemRequest(BaseModel):
    prompt: str

class WeatherRequest(BaseModel):
    city: str

class ReminderCreate(BaseModel):
    user_id: str
    task: str
    due_date: str

class ReminderUpdate(BaseModel):
    task: str = None
    due_date: str = None
    completed: bool = None

# Supabase Functions
def create_reminder(user_id: str, task: str, due_date: str):
    data, count = supabase.table("reminders").insert({"user_id": user_id, "task": task, "due_date": due_date}).execute()
    return data

def get_reminders(user_id: str):
    data, count = supabase.table("reminders").select("*").eq("user_id", user_id).execute()
    return data

def update_reminder(reminder_id: int, task: str = None, due_date: str = None, completed: bool = None):
    update_data = {}
    if task:
        update_data["task"] = task
    if due_date:
        update_data["due_date"] = due_date
    if completed is not None:
        update_data["completed"] = completed

    data, count = supabase.table("reminders").update(update_data).eq("id", reminder_id).execute()
    return data

def delete_reminder(reminder_id: int):
    data, count = supabase.table("reminders").delete().eq("id", reminder_id).execute()
    return data

# Weather Function
def get_weather(city: str):
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": WEATHER_API_KEY,
        "units": "metric"
    }
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        weather_data = response.json()
        return weather_data
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching weather data: {e}")
        print(e)
        return None

# New Functions
def generate_poem(prompt: str):
    try:
        poem = poem_generator(prompt, max_length=150)[0]['generated_text']
        return poem
    except Exception as e:
        logger.error(f"Error generating poem: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def get_random_joke():
    return random.choice(jokes)

# Intent Detection (Simple)
def detect_intent(message):
    message = message.lower()
    if "weather" in message:
        print("Intent: weather") #add this line
        return "weather"
    elif "reminder" in message:
        return "reminder"
    elif "poem" in message:
        return "poem"
    elif "joke" in message:
        return "joke"
    elif "love" in message or "feelings" in message:
        return "love"
    else:
        print("Intent: general_conversation") #add this line.
        return "general_conversation"

# DialoGPT Model Loading

tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-medium")
model = AutoModelForCausalLM.from_pretrained("microsoft/DialoGPT-medium")

def get_dialo_gpt_response(prompt):
    try:
        inputs = tokenizer.encode(prompt + tokenizer.eos_token, return_tensors="pt")
        attention_mask = torch.ones(inputs.shape, dtype=torch.long) #Add attention mask.
        outputs = model.generate(inputs, attention_mask=attention_mask, max_length=1000, pad_token_id=tokenizer.eos_token_id)
        response = tokenizer.decode(outputs[:, inputs.shape[-1]:][0], skip_special_tokens=True)
        return response.strip()
    except Exception as e:
        logger.error(f"Error generating DialoGPT response: {e}")
        return "Sorry, I encountered an error."
# API Endpoints
@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        intent = detect_intent(request.message)
        print(f"Intent: {intent}")
        if intent == "poem":
            print("Poem intent triggered")
            return {"response": generate_poem(request.message)}
        elif intent == "joke":
            print("joke intent triggered")
            return {"response": get_random_joke()}
        elif intent == "weather":
            print("weather intent triggered")
            # Extract city name from user message
            message = request.message.lower()
            city = None
            if "weather in" in message:
                city = message.split("weather in")[-1].replace("?", "").strip()
            elif "weather of" in message:
                city = message.split("weather of")[-1].replace("?", "").strip()
            else:
                words = message.split()
                for i, word in enumerate(words):
                    if word == "in" or word == "of":
                        if i + 1 < len(words):
                            city = " ".join(words[i + 1:]).replace("?", "").strip()
                            break

            print(f"city: {city}")
            if city:
                weather_data = get_weather(city)
                if weather_data:
                    temperature = weather_data["main"]["temp"]
                    description = weather_data["weather"][0]["description"]
                    return {"response": f"The weather in {city} is {temperature}°C and {description}."}
                else:
                    return {"response": f"Could not retrieve weather for {city}."}
            else:
                return {"response": "Please specify a city."}
        elif intent == "reminder":
            print("reminder intent triggered")
            return {"response": "Reminder functionality not yet implemented via chat, please use reminder section."}
        else:
            print("DialoGPT intent triggered")
            prompt = f"{request.message}"
            answer = get_dialo_gpt_response(prompt)
            return {"response": answer}
    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        raise HTTPException(status_code=500, detail=str(e))
@app.post("/poem/")
async def generate_poem_endpoint(request: PoemRequest):
    return {"poem": generate_poem(request.prompt)}

@app.get("/joke/")
async def get_joke_endpoint():
    return {"joke": get_random_joke()}

@app.post("/reminders/")
async def create_new_reminder(reminder: ReminderCreate):
    try:
        data = create_reminder(reminder.user_id, reminder.task, reminder.due_date)
        return data
    except Exception as e:
        logger.error(f"Error creating reminder: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reminders/{user_id}")
async def get_user_reminders(user_id: str):
    try:
        data = get_reminders(user_id)
        return data
    except Exception as e:
        logger.error(f"Error getting reminders: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/reminders/{reminder_id}")
async def update_user_reminder(reminder_id: int, reminder: ReminderUpdate):
    try:
        data = update_reminder(reminder_id, reminder.task, reminder.due_date, reminder.completed)
        return data
    except Exception as e:
        logger.error(f"Error updating reminder: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/reminders/{reminder_id}")
async def delete_user_reminder(reminder_id: int):
    try:
        data = delete_reminder(reminder_id)
        return data
    except Exception as e:
        logger.error(f"Error deleting reminder: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/weather/")
async def get_city_weather(request: WeatherRequest):
    try:
        weather_data = get_weather(request.city)
        if weather_data:
            temperature = weather_data["main"]["temp"]
            description = weather_data["weather"][0]["description"]
            return {"temperature": temperature, "description": description}
        else:
            raise HTTPException(status_code=404, detail="City not found or weather data unavailable")
    except Exception as e:
        logger.error(f"Error getting weather: {e}")
        print(e)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/")
async def root():
    return {"message": "AI-Twin API is running"}

if __name__ == "__main__":
    import uvicorn
    API_HOST = os.environ.get("API_HOST", "127.0.0.1")
    API_PORT = int(os.environ.get("API_PORT", "8000"))
    uvicorn.run(app, host=API_HOST, port=API_PORT)