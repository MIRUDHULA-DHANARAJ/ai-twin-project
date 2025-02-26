import streamlit as st
import requests
import sys
import os
import pandas as pd

# Use os.path to make the path more robust
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.append(backend_path)
print(os.getcwd())
import config

st.title("AI-Twin Chatbot")
st.subheader("Weather")

city = st.text_input("Enter City:")

if st.button("Get Weather"):
    try:
        response = requests.post(f"http://{config.API_HOST}:{config.API_PORT}/weather/", json={"city": city})
        response.raise_for_status()
        weather_data = response.json()
        st.write(f"Temperature: {weather_data['temperature']}°C")
        st.write(f"Description: {weather_data['description']}")

        # Add weather icon
        weather_description = weather_data['description'].lower()
        if "clear" in weather_description:
            st.image("https://openweathermap.org/img/wn/01d@2x.png", width=50)  # Clear sky icon
        elif "cloud" in weather_description:
            st.image("https://openweathermap.org/img/wn/03d@2x.png", width=50)  # Cloudy icon
        elif "rain" in weather_description:
            st.image("https://openweathermap.org/img/wn/10d@2x.png", width=50)  # Rain icon
        # ... add more conditions ...

    except requests.exceptions.RequestException as e:
        st.error(f"Error getting weather: {e}")

# Chat section
with st.expander("Chat"):
    context = st.text_area("Enter Context:", "The Eiffel Tower is in Paris.")
    user_input = st.text_input("Enter your message:")

    if user_input:
        st.write(f"User: {user_input}")
        try:
            # Refined Prompt Engineering
            prompt = f"Given the following context: {context}. Answer the question: {user_input}"
            response = requests.post(f"http://{config.API_HOST}:{config.API_PORT}/chat", json={"message": prompt, "context": context})
            response.raise_for_status()
            ai_response = response.json().get("response")
            st.write(f"AI: {ai_response}")
        except requests.exceptions.RequestException as e:
            st.error(f"Error: {e}")

# Reminders section
with st.expander("Reminders"):
    user_id = st.text_input("User ID for Reminders:", "user123")

    if st.button("Get Reminders"):
        try:
            response = requests.get(f"http://{config.API_HOST}:{config.API_PORT}/reminders/{user_id}")
            response.raise_for_status()
            reminders = response.json()
            if reminders and reminders[1]:
                df = pd.DataFrame(reminders[1])
                st.dataframe(df)
            else:
                st.write("No reminders found.")
        except requests.exceptions.RequestException as e:
            if response is not None:
                if response.status_code == 404:
                    st.error("Reminder not found.")
                else:
                    st.error(f"Error: {e}")
            else:
                st.error(f"Error: {e}")

    st.subheader("Create Reminder")

    task = st.text_input("Task:")
    due_date = st.text_input("Due Date (YYYY-MM-DD HH:MM:SS):")

    if st.button("Create Reminder"):
        try:
            response = requests.post(f"http://{config.API_HOST}:{config.API_PORT}/reminders/", json={"user_id": user_id, "task": task, "due_date": due_date})
            response.raise_for_status()
            st.success("Reminder created!")
        except requests.exceptions.RequestException as e:
            st.error(f"Error creating reminder: {e}")

    st.subheader("Update Reminder")
    reminder_id_update = st.number_input("Reminder ID to Update:", min_value=1, step=1, value=1)
    update_task = st.text_input("Updated Task (leave blank to keep current):", "")
    update_due_date = st.text_input("Updated Due Date (leave blank to keep current):", "")
    update_completed = st.checkbox("Completed")

    if st.button("Update Reminder"):
        try:
            update_data = {}
            if update_task:
                update_data["task"] = update_task
            if update_due_date:
                update_data["due_date"] = update_due_date
            update_data["completed"] = update_completed

            response = requests.put(f"http://{config.API_HOST}:{config.API_PORT}/reminders/{reminder_id_update}", json=update_data)
            response.raise_for_status()
            st.success(f"Reminder {reminder_id_update} updated!")
        except requests.exceptions.RequestException as e:
            st.error(f"Error updating reminder: {e}")

    st.subheader("Delete Reminder")
    reminder_id_delete = st.number_input("Reminder ID to Delete:", min_value=1, step=1, value=1)
    if st.button("Delete Reminder"):
        try:
            response = requests.delete(f"http://{config.API_HOST}:{config.API_PORT}/reminders/{reminder_id_delete}")
            response.raise_for_status()
            st.success(f"Reminder {reminder_id_delete} deleted!")
        except requests.exceptions.RequestException as e:
            st.error(f"Error deleting reminder: {e}")