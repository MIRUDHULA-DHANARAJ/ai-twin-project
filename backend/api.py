# backend/api.py
from fastapi import FastAPI, HTTPException, Depends
from transformers import pipeline
from pydantic import BaseModel
import logging
import os
import requests
from supabase import create_client, Client

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()

# Environment Variables
WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# Supabase Client Initialization
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Chat Request Model
class ChatRequest(BaseModel):
    message: str
    context: str = "This is a default context."

# Reminder Models
class ReminderCreate(BaseModel):
    user_id: str
    task: str
    due_date: str

class ReminderUpdate(BaseModel):
    task: str = None
    due_date: str = None
    completed: bool = None

# Weather Model
class WeatherRequest(BaseModel):
    city: str

# AI Pipeline
qa_pipeline = pipeline("question-answering", model="distilbert-base-cased-distilled-squad")

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
        print(e) #print the error.
        return None

# API Endpoints
@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        logger.info(f"Received chat request: {request.message}, context: {request.context}")
        result = qa_pipeline(question=request.message, context=request.context)
        answer = result['answer']
        logger.info(f"Sending chat response: {answer}")
        return {"response": answer}
    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
    API_HOST = os.environ.get("API_HOST", "127.0.0.1") #get api host from env, or use default.
    API_PORT = int(os.environ.get("API_PORT", "8000")) #get api port from env, or use default.
    uvicorn.run(app, host=API_HOST, port=API_PORT)