import streamlit as st
from streamlit.runtime.scriptrunner import add_script_run_ctx
# Call set_page_config first, before any other Streamlit commands
st.set_page_config(
    page_title="Futuristic Personal Assistant",
    layout="wide",
    initial_sidebar_state="expanded"
)
import datetime
import json
import os
from pathlib import Path
import requests
import pandas as pd
import plotly.express as px
from datetime import timedelta
import time
import base64
import hashlib
import pytz
import random
import speech_recognition as sr
import pyttsx3
import webbrowser
import openai
import subprocess
import sys
import pygame
from gtts import gTTS
import threading
import keyboard
import pyautogui

# Initialize OpenAI
openai.api_key = ""

class VoiceAssistant:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.recognizer = sr.Recognizer()
        self.is_listening = False
        self.wake_word = "assistant"
        
        # Set voice properties
        voices = self.engine.getProperty('voices')
        self.engine.setProperty('voice', voices[1].id)  # Female voice
        self.engine.setProperty('rate', 150)  # Speed of speech
        
    def speak(self, text):
        try:
            # Create a temporary audio file
            tts = gTTS(text=text, lang='en')
            temp_file = "temp_speech.mp3"
            tts.save(temp_file)
            
            # Initialize pygame mixer
            pygame.mixer.init()
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()
            
            # Wait for the audio to finish
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
                
            # Cleanup
            pygame.mixer.quit()
            os.remove(temp_file)
        except Exception as e:
            print(f"Error in speak function: {e}")
            # Fallback to pyttsx3 if gTTS fails
            self.engine.say(text)
            self.engine.runAndWait()

    def listen(self):
        with sr.Microphone() as source:
            print("Listening...")
            self.recognizer.adjust_for_ambient_noise(source)
            audio = self.recognizer.listen(source)
            try:
                command = self.recognizer.recognize_google(audio).lower()
                return command
            except sr.UnknownValueError:
                return ""
            except sr.RequestError:
                self.speak("Sorry, there was an error with the speech recognition service.")
                return ""

    def process_command(self, command):
        try:
            # Basic commands
            if "open" in command:
                if "google" in command:
                    webbrowser.open("https://www.google.com")
                    return "Opening Google"
                elif "youtube" in command:
                    webbrowser.open("https://www.youtube.com")
                    return "Opening YouTube"
                elif "spotify" in command:
                    webbrowser.open("https://www.spotify.com")
                    return "Opening Spotify"
                elif "gmail" in command:
                    webbrowser.open("https://mail.google.com")
                    return "Opening Gmail"
                
            # Add note command
            elif "add note" in command:
                return "Please use the Notes section to add a note."
                
            # Add task command
            elif "add task" in command:
                return "Please use the Tasks section to add a task."
                
            # Weather command
            elif "weather" in command:
                return "Please enter your city in the Dashboard to check the weather."
                
            # Help command
            elif "help" in command:
                return """
                I can help you with:
                - Opening websites (Google, YouTube, Spotify, Gmail)
                - Adding notes and tasks
                - Checking weather
                - Answering questions
                """
                
            # AI conversation using OpenAI
            try:
                response = openai.chat.completions.create(
                   model="gpt-4",
                   messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": command}
                   ]
                )
                return response.choices[0].message.content
            except Exception as e:
                return f"Error with OpenAI API: {str(e)}"
            
        except Exception as e:
            return f"Sorry, I encountered an error: {str(e)}"

class PersonalAssistant:
    def __init__(self):
        self.notes_file = "notes.json"
        self.tasks_file = "tasks.json"
        self.expenses_file = "expenses.json"
        self.habits_file = "habits.json"
        self.load_data()
        
    def load_data(self):
        # Load or create all data files
        self.data_files = {
            'notes': (self.notes_file, []),
            'tasks': (self.tasks_file, []),
            'expenses': (self.expenses_file, []),
            'habits': (self.habits_file, {})
        }
        
        for key, (file, default) in self.data_files.items():
            if os.path.exists(file):
                with open(file, 'r') as f:
                    setattr(self, key, json.load(f))
            else:
                setattr(self, key, default)

    def save_data(self):
        for key, (file, _) in self.data_files.items():
            with open(file, 'w') as f:
                json.dump(getattr(self, key), f)

    def add_note(self, title, content, category="Uncategorized", attachments=None):
        note = {
            "title": title,
            "content": content,
            "category": category,
            "attachments": attachments or [],
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "tags": []
        }
        self.notes.append(note)
        self.save_data()

    def add_task(self, task, due_date, priority="Medium", category="General"):
        self.tasks.append({
            "task": task,
            "due_date": due_date,
            "priority": priority,
            "category": category,
            "completed": False,
            "created_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        self.save_data()

    def add_expense(self, amount, category, description, date):
        self.expenses.append({
            "amount": float(amount),
            "category": category,
            "description": description,
            "date": date,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        self.save_data()

    def update_habit(self, habit_name, completed=True):
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        if habit_name not in self.habits:
            self.habits[habit_name] = {"streak": 0, "history": {}}
        
        self.habits[habit_name]["history"][today] = completed
        
        streak = 0
        current_date = datetime.datetime.now()
        while True:
            date_str = current_date.strftime("%Y-%m-%d")
            if date_str in self.habits[habit_name]["history"] and self.habits[habit_name]["history"][date_str]:
                streak += 1
                current_date -= datetime.timedelta(days=1)
            else:
                break
        self.habits[habit_name]["streak"] = streak
        self.save_data()

class EnhancedPersonalAssistant(PersonalAssistant):
    def __init__(self):
        super().__init__()
        self.voice_assistant = VoiceAssistant()
        self.initialize_greeting()

    def initialize_greeting(self):
        current_hour = datetime.datetime.now().hour
        if 5 <= current_hour < 12:
            greeting = "Good morning"
        elif 12 <= current_hour < 18:
            greeting = "Good afternoon"
        else:
            greeting = "Good evening"
        
        self.voice_assistant.speak(f"{greeting}! I am your personal assistant. How can I help you today?")
def get_weather(api_key, city):
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        response = requests.get(url)
        data = response.json()
        return {
            "temperature": data["main"]["temp"],
            "humidity": data["main"]["humidity"],
            "description": data["weather"][0]["description"]
        }
    except:
        return None

def main():
    def voice_control_loop():
                add_script_run_ctx()
                while True:
                    try:
                        if "assistant" in st.session_state:
                           command = st.session_state.assistant.voice_assistant.listen()
                           if command:
                               response = st.session_state.assistant.voice_assistant.process_command(command)
                               st.session_state.assistant.voice_assistant.speak(response)
                        else:
                            time.sleep(1)  # Wait for assistant to be initialized
                    except Exception as e:
                       print(f"Error in voice control loop: {e}")
                       time.sleep(1)
   
    # Initialize assistant
    if 'assistant' not in st.session_state:
        st.session_state.assistant = EnhancedPersonalAssistant()

    if 'voice_active' not in st.session_state:
        st.session_state.voice_active = False
        
    if 'last_command' not in st.session_state:
        st.session_state.last_command = None
    
    # Authentication
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.title("🤖 Welcome to Your Futuristic Assistant")
        password = st.text_input("Enter password:", type="password")
        if st.button("Login"):
            if hashlib.sha256(password.encode()).hexdigest() == "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8":
                st.session_state.authenticated = True
                st.rerun()
        return

    # Main interface
    st.sidebar.title("🤖 Navigation")
    page = st.sidebar.radio("Go to:", 
        ["Dashboard", "Voice Assistant", "Notes", "Tasks", "Calendar", "Expenses", "Habits"])

    # Voice Assistant Control
    voice_control = st.sidebar.checkbox("Enable Voice Control")
    
    if voice_control:
        if 'listening_thread' not in st.session_state:
            add_script_run_ctx()
            thread = threading.Thread(target=voice_control_loop, daemon=True)
            thread.start()
            st.session_state.listening_thread = thread

    if page == "Voice Assistant":
        st.title("🎙️ Voice Assistant")
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Voice Controls")
            
            # Toggle button for voice activation
            if st.button("🎤 Listen" if not st.session_state.voice_active else "⏹️ Stop Listening"):
                st.session_state.voice_active = not st.session_state.voice_active
                st.rerun()
            
            # Show status
            if st.session_state.voice_active:
                st.info("Listening... Say something!")
                try:
                    command = st.session_state.assistant.voice_assistant.listen()
                    if command:
                        st.session_state.last_command = command
                        response = st.session_state.assistant.voice_assistant.process_command(command)
                        st.session_state.assistant.voice_assistant.speak(response)
                        st.success(f"Command processed: {command}")
                        st.write(f"Response: {response}")
                except Exception as e:
                    st.error(f"Error processing voice: {str(e)}")
            
            # Command history
            st.subheader("Command History")
            if st.session_state.last_command:
                st.write(f"Last command: {st.session_state.last_command}")
        
        with col2:
            st.subheader("Text Input")
            text_command = st.text_input("Type your command:")
            if text_command:
                response = st.session_state.assistant.voice_assistant.process_command(text_command)
                st.write(f"Response: {response}")
                
            st.subheader("Available Commands")
            st.write("""
            Try these commands:
            - "Open Google"
            - "Open YouTube"
            - "Open Spotify"
            - "Open Gmail"
            - Ask any question
            """)
            
    elif page == "Dashboard":
        st.title("📊 Dashboard")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("Quick Stats")
            total_tasks = len(st.session_state.assistant.tasks)
            completed_tasks = len([t for t in st.session_state.assistant.tasks if t.get('completed', False)])
            st.metric("Tasks Progress", f"{completed_tasks}/{total_tasks}")
            
            st.subheader("Weather")
            city = st.text_input("Enter city:")
            if city:
                weather = get_weather("YOUR_OPENWEATHER_API_KEY", city)
                if weather:
                    st.write(f"Temperature: {weather['temperature']}°C")
                    st.write(f"Humidity: {weather['humidity']}%")
                    st.write(f"Description: {weather['description']}")

        with col2:
            st.subheader("Recent Notes")
            recent_notes = sorted(st.session_state.assistant.notes, 
                                key=lambda x: x['date'], reverse=True)[:3]
            for note in recent_notes:
                st.write(f"📝 {note.get('title', 'Untitled')}")

        with col3:
            st.subheader("Upcoming Tasks")
            upcoming_tasks = sorted(
                [t for t in st.session_state.assistant.tasks if not t.get('completed', False)], 
                key=lambda x: x['due_date'])[:3]
            for task in upcoming_tasks:
                st.write(f"⏰ {task.get('task', 'Untitled')} (Due: {task.get('due_date', 'No date')})")

    elif page == "Notes":
        st.title("📝 Notes")
        
        with st.form("new_note"):
            col1, col2 = st.columns(2)
            with col1:
                note_title = st.text_input("Title")
                note_category = st.selectbox("Category", 
                    ["Personal", "Work", "Study", "Other"])
            with col2:
                note_content = st.text_area("Content")
                uploaded_file = st.file_uploader("Attach File")
            
            if st.form_submit_button("Add Note"):
                if note_title and note_content:
                    attachments = []
                    if uploaded_file:
                        file_contents = uploaded_file.read()
                        encoded_file = base64.b64encode(file_contents).decode()
                        attachments.append({
                            "filename": uploaded_file.name,
                            "content": encoded_file
                        })
                    st.session_state.assistant.add_note(
                        note_title, note_content, note_category, attachments)
                    st.success("Note added successfully!")
                    st.rerun()

        st.subheader("Your Notes")
        search_term = st.text_input("Search notes:")
        category_filter = st.multiselect(
            "Filter by category:",
            ["Personal", "Work", "Study", "Other", "Uncategorized"]
        )

        filtered_notes = st.session_state.assistant.notes
        if search_term:
            filtered_notes = [
                n for n in filtered_notes 
                if search_term.lower() in n.get('title', '').lower() 
                or search_term.lower() in n.get('content', '').lower()
            ]
        if category_filter:
            filtered_notes = [
                n for n in filtered_notes 
                if n.get('category', 'Uncategorized') in category_filter
            ]

        for note in reversed(filtered_notes):
            with st.expander(f"{note.get('title', 'Untitled')} - {note.get('date', 'No date')} ({note.get('category', 'Uncategorized')})"):
                st.write(note.get('content', 'No content'))
                attachments = note.get('attachments', [])
                if attachments:
                    st.write("Attachments:")
                    for attachment in attachments:
                        st.download_button(
                            f"Download {attachment['filename']}", 
                            base64.b64decode(attachment['content']),
                            file_name=attachment['filename']
                        )

    elif page == "Tasks":
        st.title("✓ Tasks")
        
        with st.form("new_task"):
            task = st.text_input("New Task")
            col1, col2 = st.columns(2)
            with col1:
                due_date = st.date_input("Due Date")
                priority = st.selectbox("Priority", ["High", "Medium", "Low"])
            with col2:
                category = st.selectbox("Category", ["Work", "Personal", "Shopping", "Other"])
            
            if st.form_submit_button("Add Task"):
                if task:
                    st.session_state.assistant.add_task(
                        task, due_date.strftime("%Y-%m-%d"), priority, category)
                    st.success("Task added successfully!")
                    st.rerun()

        st.subheader("Your Tasks")
        for idx, task in enumerate(st.session_state.assistant.tasks):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                completed = st.checkbox(
                    f"{task.get('task', 'Untitled')} ({task.get('priority', 'Medium')} priority)",
                    value=task.get('completed', False),
                    key=f"task_{idx}"
                )
                if completed != task.get('completed', False):
                    task['completed'] = completed
                    st.session_state.assistant.save_data()
                    st.rerun()
            with col2:
                st.write(task.get('due_date', 'No date'))
            with col3:
                st.write(task.get('category', 'General'))

    elif page == "Expenses":
        st.title("💰 Expense Tracker")
        
        with st.form("new_expense"):
            col1, col2 = st.columns(2)
            with col1:
                amount = st.number_input("Amount", min_value=0.0)
                category = st.selectbox("Category", 
                    ["Food", "Transport", "Housing", "Entertainment", "Other"])
            with col2:
                description = st.text_input("Description")
                date = st.date_input("Date")
            
            if st.form_submit_button("Add Expense"):
                if amount and description:
                    st.session_state.assistant.add_expense(
                        amount, category, description, date.strftime("%Y-%m-%d"))
                    st.success("Expense added successfully!")
                    st.rerun()

        st.subheader("Expense Analysis")
        if st.session_state.assistant.expenses:
            df_expenses = pd.DataFrame(st.session_state.assistant.expenses)
            df_expenses['date'] = pd.to_datetime(df_expenses['date'])
            
            time_period = st.selectbox(
                "Select time period",
                ["Last 7 days", "Last 30 days", "Last 3 months", "All time"]
            )
            
            if time_period != "All time":
                days = {
                    "Last 7 days": 7,
                    "Last 30 days": 30,
                    "Last 3 months": 90
                }[time_period]
                df_expenses = df_expenses[
                    df_expenses['date'] >= datetime.datetime.now() - timedelta(days=days)
                ]

            total_expenses = df_expenses['amount'].sum()
            st.metric("Total Expenses", f"${total_expenses:.2f}")

            col1, col2 = st.columns(2)
            with col1:
                fig_category = px.pie(
                    df_expenses, 
                    values='amount', 
                    names='category',
                    title='Expenses by Category'
                )
                st.plotly_chart(fig_category)

            with col2:
                daily_expenses = df_expenses.groupby('date')['amount'].sum().reset_index()
                fig_trend = px.line(
                    daily_expenses, 
                    x='date', 
                    y='amount',
                    title='Daily Expenses Trend'
                )
                st.plotly_chart(fig_trend)
        else:
            st.info("No expenses recorded yet. Add some expenses to see the analysis.")

    elif page == "Calendar":
        st.title("📅 Calendar")
        selected_date = st.date_input("Select date")
        
        st.subheader("Tasks due today")
        tasks_due = [
            task for task in st.session_state.assistant.tasks 
            if task.get('due_date') == selected_date.strftime("%Y-%m-%d")
        ]
        
        if tasks_due:
            for task in tasks_due:
                st.write(f"• {task.get('task', 'Untitled')} ({task.get('priority', 'Medium')} priority)")
        else:
            st.info("No tasks due on this date")

        # Monthly view
        st.subheader("Monthly Overview")
        first_day = selected_date.replace(day=1)
        last_day = (first_day + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        # Create calendar grid
        weeks = []
        current_week = []
        week_day = first_day.weekday()
        
        # Add padding for first week
        for _ in range(week_day):
            current_week.append(None)
        
        # Fill in the days
        for day in range(1, last_day.day + 1):
            current_week.append(day)
            if len(current_week) == 7:
                weeks.append(current_week)
                current_week = []
        
        # Add padding for last week
        if current_week:
            current_week.extend([None] * (7 - len(current_week)))
            weeks.append(current_week)
        
        # Display calendar
        days_of_week = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        st.write("  ".join(days_of_week))
        
        for week in weeks:
            cols = st.columns(7)
            for i, day in enumerate(week):
                with cols[i]:
                    if day:
                        date = selected_date.replace(day=day)
                        tasks_count = len([t for t in st.session_state.assistant.tasks 
                                        if t.get('due_date') == date.strftime("%Y-%m-%d")])
                        if tasks_count:
                            st.markdown(f"**{day}** ({tasks_count})")
                        else:
                            st.write(day)

    elif page == "Habits":
        st.title("🎯 Habit Tracker")
        
        new_habit = st.text_input("Add new habit:")
        if st.button("Add Habit") and new_habit:
            if new_habit not in st.session_state.assistant.habits:
                st.session_state.assistant.habits[new_habit] = {
                    "streak": 0,
                    "history": {}
                }
                st.session_state.assistant.save_data()
                st.rerun()

        st.subheader("Your Habits")
        for habit in st.session_state.assistant.habits:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"**{habit}**")
            with col2:
                st.write(f"Streak: {st.session_state.assistant.habits[habit]['streak']} days")
            with col3:
                if st.button("Complete", key=f"habit_{habit}"):
                    st.session_state.assistant.update_habit(habit)
                    st.rerun()

        # Display habit history
        if st.session_state.assistant.habits:
            st.subheader("Habit History")
            history_days = 30  # Show last 30 days
            today = datetime.datetime.now()
            dates = [(today - timedelta(days=i)).strftime("%Y-%m-%d") 
                    for i in range(history_days)]
            dates.reverse()

            # Create habit history table
            habit_data = []
            for habit in st.session_state.assistant.habits:
                row = {"Habit": habit}
                for date in dates:
                    row[date] = "✅" if st.session_state.assistant.habits[habit]["history"].get(date, False) else "❌"
                habit_data.append(row)

            if habit_data:
                df = pd.DataFrame(habit_data)
                st.dataframe(df, use_container_width=True)

        # Habit statistics
        if st.session_state.assistant.habits:
            st.subheader("Habit Statistics")
            col1, col2 = st.columns(2)
            
            with col1:
                # Longest streak
                longest_streak = max(
                    (habit_data["streak"] for habit_data in st.session_state.assistant.habits.values()),
                    default=0
                )
                st.metric("Longest Streak", f"{longest_streak} days")

            with col2:
                # Total habits completed today
                today = datetime.datetime.now().strftime("%Y-%m-%d")
                completed_today = sum(
                    1 for habit_data in st.session_state.assistant.habits.values()
                    if habit_data["history"].get(today, False)
                )
                st.metric("Completed Today", f"{completed_today}/{len(st.session_state.assistant.habits)}")

        else:
            st.info("No habits added yet. Add some habits to start tracking!")

def init_session_state():
    """Initialize session state variables"""
    if 'page' not in st.session_state:
        st.session_state.page = "Dashboard"
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'voice_command_history' not in st.session_state:
        st.session_state.voice_command_history = []
    if 'dark_mode' not in st.session_state:
        st.session_state.dark_mode = False
    if 'notifications_enabled' not in st.session_state:
        st.session_state.notifications_enabled = True
    if 'last_weather_check' not in st.session_state:
        st.session_state.last_weather_check = None
    if 'weather_data' not in st.session_state:
        st.session_state.weather_data = None

def apply_custom_css():
    """Apply custom CSS styling"""
    st.markdown("""
        <style>
        .stApp {
            max-width: 1200px;
            margin: 0 auto;
        }
        .main {
            padding: 2rem;
        }
        .stButton>button {
            border-radius: 20px;
        }
        .stTextInput>div>div>input {
            border-radius: 10px;
        }
        .stSelectbox>div>div>select {
            border-radius: 10px;
        }
        </style>
    """, unsafe_allow_html=True)

def handle_errors(func):
    """Decorator for error handling"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            return None
    return wrapper

if __name__ == "__main__":
    try:
        # Initialize the application
        init_session_state()
        
        # Apply custom styling
        apply_custom_css()
        
        # Run the main application
        main()
        
    except Exception as e:
        st.error(f"Application Error: {str(e)}")
        st.write("Please refresh the page and try again.")