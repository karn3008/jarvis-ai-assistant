import speech_recognition as sr
import sounddevice as sd
import pyttsx3
import subprocess
import sys
import webbrowser
from datetime import datetime
import re
import platform
import shutil
import os
import json
import requests
from urllib.parse import quote_plus


# =========================
# SETTINGS
# =========================

MEMORY_FILE = "memory.json"


# =========================
# MEMORY SYSTEM
# =========================

def load_memory():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as file:
                return json.load(file)
        except Exception:
            return {}

    return {}


def save_memory(memory):
    with open(MEMORY_FILE, "w", encoding="utf-8") as file:
        json.dump(memory, file, indent=4)


memory = load_memory()


def remember(key, value):
    memory[key] = value
    save_memory(memory)


def recall_memory(key):
    return memory.get(key)


# =========================
# SPEAK
# =========================

def speak(text):
    print("JARVIS:", text)

    try:
        subprocess.run(
            [
                sys.executable,
                "-c",
                "import pyttsx3,sys; e=pyttsx3.init(); e.say(sys.argv[1]); e.runAndWait()",
                str(text)
            ],
            check=False
        )

    except Exception as error:
        print("TTS Error:", error)


# =========================
# AUDIO RECORDING
# =========================

def record_audio(seconds=5):
    sample_rate = 16000

    print(f"Listening for {seconds} seconds...")

    try:
        audio_data = sd.rec(
            int(seconds * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype="int16"
        )

        sd.wait()

        return audio_data, sample_rate

    except Exception as error:
        print("Microphone Error:", error)
        return None, sample_rate


# =========================
# SPEECH RECOGNITION
# =========================

def recognize_audio(audio_data, sample_rate):

    if audio_data is None:
        return ""

    recognizer = sr.Recognizer()

    try:

        audio = sr.AudioData(
            audio_data.tobytes(),
            sample_rate,
            2
        )

        text = recognizer.recognize_google(audio)

        print("You:", text)

        return text.lower().strip()

    except sr.UnknownValueError:

        print("Could not understand.")

        return ""

    except sr.RequestError as error:

        print("Speech recognition error:", error)

        return ""

    except Exception as error:

        print("Recognition Error:", error)

        return ""


# =========================
# WAKE WORD
# =========================

def listen_for_wake_word():

    audio_data, sample_rate = record_audio(3)

    text = recognize_audio(
        audio_data,
        sample_rate
    )

    if not text:
        return ""

    stop_words = [
        "stop",
        "exit",
        "quit",
        "shutdown jarvis",
        "close jarvis",
        "stop jarvis"
    ]

    if text in stop_words:
        return "stop"

    if "jarvis" in text:
        return "jarvis"

    return ""


# =========================
# COMMAND LISTENER
# =========================

def listen():

    audio_data, sample_rate = record_audio(5)

    return recognize_audio(
        audio_data,
        sample_rate
    )


# =========================
# WEATHER
# =========================

def get_weather(command):

    city = "Pune"

    try:

        url = (
            f"https://wttr.in/"
            f"{quote_plus(city)}"
            f"?format=j1"
        )

        response = requests.get(
            url,
            timeout=10
        )

        if response.status_code != 200:

            speak(
                "Sorry sir, I could not get the weather."
            )

            return True

        data = response.json()

        current = data["current_condition"][0]

        temperature = current["temp_C"]

        feels_like = current["FeelsLikeC"]

        humidity = current["humidity"]

        description = current["weatherDesc"][0]["value"]

        speak(
            f"The weather in {city} is {description}. "
            f"The temperature is {temperature} degrees Celsius. "
            f"It feels like {feels_like} degrees. "
            f"Humidity is {humidity} percent."
        )

    except Exception as error:

        print("Weather Error:", error)

        speak(
            "Sorry sir, I could not get the weather information."
        )

    return True


# =========================
# CALCULATOR
# =========================

def looks_like_calculation(command):

    calculation_phrases = [
        "calculate",
        "plus",
        "minus",
        "times",
        "multiply",
        "multiplied",
        "divided by"
    ]

    if any(
        phrase in command
        for phrase in calculation_phrases
    ):
        return True

    if re.search(r"\d+\s*x\s*\d+", command):
        return True

    if re.search(r"\d+\s*[\+\-\*/]\s*\d+", command):
        return True

    return False


def calculate(command):

    expression = command.lower()

    expression = expression.replace(
        "divided by",
        "/"
    )

    expression = expression.replace(
        "multiply by",
        "*"
    )

    expression = expression.replace(
        "multiplied by",
        "*"
    )

    expression = expression.replace(
        "times",
        "*"
    )

    expression = expression.replace(
        " x ",
        "*"
    )

    expression = expression.replace(
        "plus",
        "+"
    )

    expression = expression.replace(
        "minus",
        "-"
    )

    expression = expression.replace(
        "calculate",
        ""
    )

    expression = re.sub(
        r"[^0-9+\-*/().]",
        "",
        expression
    )

    if not expression:
        return None

    try:

        result = eval(
            expression,
            {"__builtins__": None},
            {}
        )

        return result

    except Exception:

        return None


# =========================
# GOOGLE SEARCH
# =========================

def google_search(command):

    query = command

    phrases = [
        "search google for",
        "search google",
        "search for",
        "google search",
        "search"
    ]

    for phrase in phrases:
        query = query.replace(
            phrase,
            ""
        )

    query = query.strip()

    if query:

        speak("Searching Google.")

        webbrowser.open(
            "https://www.google.com/search?q="
            + quote_plus(query)
        )

    else:

        speak(
            "What should I search for?"
        )


# =========================
# YOUTUBE SEARCH
# =========================

def youtube_search(command):

    query = command

    phrases = [
        "search youtube for",
        "search youtube",
        "youtube search",
        "search"
    ]

    for phrase in phrases:

        query = query.replace(
            phrase,
            ""
        )

    query = query.strip()

    if query:

        speak("Searching YouTube.")

        webbrowser.open(
            "https://www.youtube.com/results?search_query="
            + quote_plus(query)
        )

    else:

        speak(
            "What should I search on YouTube?"
        )


# =========================
# OPEN CHROME
# =========================

def open_chrome():

    paths = [

        os.path.expandvars(
            r"%PROGRAMFILES%\Google\Chrome\Application\chrome.exe"
        ),

        os.path.expandvars(
            r"%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe"
        ),

        os.path.expandvars(
            r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
        )
    ]

    for path in paths:

        if os.path.exists(path):

            subprocess.Popen([path])

            speak("Opening Chrome.")

            return True

    speak(
        "Sorry sir, Chrome was not found."
    )

    return False


# =========================
# OPEN VS CODE
# =========================

def open_vscode():

    paths = [

        os.path.expandvars(
            r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"
        ),

        os.path.expandvars(
            r"%PROGRAMFILES%\Microsoft VS Code\Code.exe"
        ),

        os.path.expandvars(
            r"%PROGRAMFILES(X86)%\Microsoft VS Code\Code.exe"
        )
    ]

    for path in paths:

        if os.path.exists(path):

            subprocess.Popen([path])

            speak(
                "Opening Visual Studio Code."
            )

            return True

    speak(
        "Sorry sir, Visual Studio Code was not found."
    )

    return False


# =========================
# APPLICATION CONTROL
# =========================

def open_app(command):

    # NOTEPAD
    if "notepad" in command:

        subprocess.Popen(
            ["notepad.exe"]
        )

        speak(
            "Opening Notepad."
        )

        return True


    # FILE EXPLORER
    if (
        "file explorer" in command
        or "explorer" in command
        or "files" in command
    ):

        subprocess.Popen(
            ["explorer.exe"]
        )

        speak(
            "Opening File Explorer."
        )

        return True


    # CALCULATOR
    if (
        "calculator" in command
        or command == "calc"
        or "open calc" in command
    ):

        subprocess.Popen(
            ["calc.exe"]
        )

        speak(
            "Opening Calculator."
        )

        return True


    # VS CODE
    if (
        "visual studio code" in command
        or "vs code" in command
        or "vscode" in command
        or command == "open code"
    ):

        open_vscode()

        return True


    # CHROME
    if (
        "chrome" in command
        or "google chrome" in command
    ):

        open_chrome()

        return True


    # WHATSAPP
    if "whatsapp" in command:

        try:

            subprocess.Popen(
                [
                    "explorer.exe",
                    r"shell:AppsFolder\5319275A.WhatsAppDesktop_cv1g1gvanyjgm!App"
                ]
            )

            speak(
                "Opening WhatsApp."
            )

        except Exception as error:

            print(
                "WhatsApp Error:",
                error
            )

            speak(
                "Sorry sir, I could not open WhatsApp."
            )

        return True


    # SETTINGS
    if (
        "settings" in command
        or "open settings" in command
    ):

        subprocess.Popen(
            [
                "explorer.exe",
                "ms-settings:"
            ]
        )

        speak(
            "Opening Settings."
        )

        return True


    # TASK MANAGER
    if (
        "task manager" in command
        or "taskmanager" in command
    ):

        subprocess.Popen(
            ["taskmgr.exe"]
        )

        speak(
            "Opening Task Manager."
        )

        return True


    # CONTROL PANEL
    if "control panel" in command:

        subprocess.Popen(
            ["control.exe"]
        )

        speak(
            "Opening Control Panel."
        )

        return True


    return False


# =========================
# SYSTEM INFORMATION
# =========================

def system_info(command):

    # COMPUTER NAME
    if (
        "computer name" in command
        or "pc name" in command
        or "device name" in command
    ):

        name = platform.node()

        speak(
            "Your computer name is "
            + name
        )

        return True


    # RAM
    if (
        "ram" in command
        or "memory" in command
    ):

        try:

            import psutil

            ram_gb = round(
                psutil.virtual_memory().total
                / (1024 ** 3),
                1
            )

            speak(
                f"You have {ram_gb} GB RAM."
            )

        except Exception:

            speak(
                "I could not read the RAM information."
            )

        return True


    # STORAGE
    if (
        "storage" in command
        or "disk space" in command
    ):

        try:

            total, used, free = shutil.disk_usage(
                "C:\\"
            )

            total_gb = round(
                total / (1024 ** 3),
                1
            )

            free_gb = round(
                free / (1024 ** 3),
                1
            )

            speak(
                f"Your C drive has "
                f"{total_gb} GB total "
                f"and {free_gb} GB free space."
            )

        except Exception:

            speak(
                "I could not read the storage information."
            )

        return True


    # PYTHON VERSION
    if "python version" in command:

        speak(
            "Your Python version is "
            + platform.python_version()
        )

        return True


    # WINDOWS VERSION
    if (
        "windows version" in command
        or "what windows am i using" in command
        or "which windows am i using" in command
    ):

        speak(
            "You are using "
            + platform.platform()
        )

        return True


    return False


# =========================
# BATTERY
# =========================

def battery_status():

    try:

        import psutil

        battery = psutil.sensors_battery()

        if battery is None:

            speak(
                "Battery information is not available."
            )

            return True

        percent = battery.percent

        if battery.power_plugged:

            speak(
                f"Battery is at {percent} percent and charging."
            )

        else:

            speak(
                f"Battery is at {percent} percent."
            )

    except Exception as error:

        print(
            "Battery Error:",
            error
        )

        speak(
            "I could not read the battery status."
        )

    return True


# =========================
# VOLUME CONTROL
# =========================

def media_key(key_code):

    try:

        import ctypes

        ctypes.windll.user32.keybd_event(
            key_code,
            0,
            0,
            0
        )

        ctypes.windll.user32.keybd_event(
            key_code,
            0,
            2,
            0
        )

    except Exception as error:

        print(
            "Media Key Error:",
            error
        )


def volume_control(command):

    if (
        "volume up" in command
        or "increase volume" in command
        or "volume increase" in command
    ):

        media_key(0xAF)

        speak(
            "Volume increased."
        )

        return True


    if (
        "volume down" in command
        or "decrease volume" in command
        or "volume decrease" in command
    ):

        media_key(0xAE)

        speak(
            "Volume decreased."
        )

        return True


    if (
        "mute" in command
        or "mute volume" in command
    ):

        media_key(0xAD)

        speak(
            "Volume muted."
        )

        return True


    if (
        "unmute" in command
        or "unmute volume" in command
    ):

        media_key(0xAD)

        speak(
            "Volume unmuted."
        )

        return True


    return False


# =========================
# MEDIA CONTROL
# =========================

def media_control(command):

    if (
        "next song" in command
        or "next track" in command
        or command == "next"
        or "play next" in command
    ):

        media_key(0xB0)

        speak(
            "Next track."
        )

        return True


    if (
        "previous song" in command
        or "previous track" in command
        or command == "previous"
        or "play previous" in command
    ):

        media_key(0xB1)

        speak(
            "Previous track."
        )

        return True


    if (
        "play music" in command
        or "pause music" in command
        or "play pause" in command
        or "pause" in command
        or "resume" in command
    ):

        media_key(0xB3)

        speak(
            "Done."
        )

        return True


    return False


# =========================
# SCREENSHOT
# =========================

def take_screenshot():

    try:

        from PIL import ImageGrab

        folder = os.path.join(
            os.path.expanduser("~"),
            "Pictures",
            "JARVIS Screenshots"
        )

        os.makedirs(
            folder,
            exist_ok=True
        )

        timestamp = datetime.now().strftime(
            "%Y-%m-%d_%H-%M-%S"
        )

        filename = os.path.join(
            folder,
            f"screenshot_{timestamp}.png"
        )

        image = ImageGrab.grab()

        image.save(filename)

        speak(
            "Screenshot captured successfully."
        )

        print(
            "Screenshot saved:",
            filename
        )

    except Exception as error:

        print(
            "Screenshot Error:",
            error
        )

        speak(
            "Sorry sir, I could not take the screenshot."
        )

    return True


# =========================
# OPENROUTER AI BRAIN
# =========================

def ask_ai(question):

    try:

        api_key = os.getenv(
            "OPENROUTER_API_KEY"
        )

        if not api_key:

            speak(
                "AI brain is not connected."
            )

            return True


        headers = {

            "Authorization":
                "Bearer " + api_key,

            "Content-Type":
                "application/json"
        }


        data = {

            "model":
                "openrouter/free",

            "messages": [

                {
                    "role": "system",

                    "content":
                        (
                            "You are JARVIS, "
                            "a helpful voice assistant. "
                            "Give short, clear answers "
                            "suitable for voice. "
                            "Do not use unnecessary "
                            "formatting."
                        )
                },

                {
                    "role": "user",

                    "content": question
                }
            ]
        }


        response = requests.post(

            "https://openrouter.ai/api/v1/chat/completions",

            headers=headers,

            json=data,

            timeout=30
        )


        if response.status_code != 200:

            print(
                "AI Error:",
                response.status_code
            )

            print(
                response.text
            )

            speak(
                "Sorry sir, my AI brain is unavailable right now."
            )

            return True


        result = response.json()

        answer = (
            result["choices"][0]
            ["message"]["content"]
        )


        print(
            "JARVIS AI:",
            answer
        )

        speak(answer)

        return True


    except Exception as error:

        print(
            "AI Error:",
            error
        )

        speak(
            "Sorry sir, I could not connect to my AI brain."
        )

        return True


# =========================
# COMMAND PROCESSOR
# =========================

def process_command(command):

    if not command:

        speak(
            "Sorry sir, I didn't understand."
        )

        return True


    command = command.lower().strip()


    # =========================
    # STOP / EXIT
    # =========================

    stop_commands = [

        "stop",
        "exit",
        "quit",
        "bye",
        "goodbye",
        "stop jarvis",
        "close jarvis",
        "shutdown jarvis"
    ]


    if command in stop_commands:

        speak(
            "Goodbye sir."
        )

        return False


    # =========================
    # MEMORY
    # =========================

    if "remember my name is" in command:

        name = command.split(
            "remember my name is",
            1
        )[1].strip()

        if name:

            remember(
                "name",
                name
            )

            speak(
                f"I will remember your name is {name}."
            )

        return True


    if (
        "what is my name" in command
        or "what's my name" in command
        or "who am i" in command
    ):

        name = recall_memory(
            "name"
        )

        if name:

            speak(
                f"Your name is {name}."
            )

        else:

            speak(
                "You haven't told me your name yet."
            )

        return True


    if "remember my favorite color is" in command:

        color = command.split(
            "remember my favorite color is",
            1
        )[1].strip()

        if color:

            remember(
                "favorite_color",
                color
            )

            speak(
                "I will remember that your "
                f"favorite color is {color}."
            )

        return True


    if (
        "what is my favorite color" in command
        or "what's my favorite color" in command
    ):

        color = recall_memory(
            "favorite_color"
        )

        if color:

            speak(
                f"Your favorite color is {color}."
            )

        else:

            speak(
                "You haven't told me your favorite color yet."
            )

        return True


    # =========================
    # WEATHER
    # =========================

    if (
        "weather" in command
        or "temperature" in command
        or "how hot is it" in command
        or "how cold is it" in command
    ):

        return get_weather(
            command
        )


    # =========================
    # SYSTEM INFORMATION
    # =========================

    if system_info(command):

        return True


    # =========================
    # BATTERY
    # =========================

    if (
        "battery" in command
        or "battery status" in command
        or "battery percentage" in command
    ):

        return battery_status()


    # =========================
    # VOLUME
    # =========================

    if volume_control(command):

        return True


    # =========================
    # MEDIA
    # =========================

    if media_control(command):

        return True


    # =========================
    # SCREENSHOT
    # =========================

    if (
        "take screenshot" in command
        or "capture screenshot" in command
        or "screenshot" in command
        or "screen shot" in command
    ):

        return take_screenshot()


    # =========================
    # CALCULATOR
    # =========================

    if looks_like_calculation(command):

        result = calculate(
            command
        )

        if result is not None:

            speak(
                f"The answer is {result}"
            )

        else:

            speak(
                "Sorry sir, I couldn't calculate that."
            )

        return True


    # =========================
    # APPLICATIONS
    # =========================

    if open_app(command):

        return True


    # =========================
    # YOUTUBE SEARCH
    # =========================

    if (
        "youtube" in command
        and "search" in command
    ):

        youtube_search(
            command
        )

        return True


    # =========================
    # GOOGLE SEARCH
    # =========================

    if (
        "search google" in command
        or "google search" in command
        or command.startswith("search ")
    ):

        google_search(
            command
        )

        return True


    # =========================
    # OPEN GOOGLE
    # =========================

    if "open google" in command:

        speak(
            "Opening Google."
        )

        webbrowser.open(
            "https://www.google.com"
        )

        return True


    # =========================
    # OPEN YOUTUBE
    # =========================

    if "open youtube" in command:

        speak(
            "Opening YouTube."
        )

        webbrowser.open(
            "https://www.youtube.com"
        )

        return True


    # =========================
    # TIME
    # =========================

    if (
        "what time" in command
        or "current time" in command
        or command == "time"
        or "tell me the time" in command
    ):

        current_time = datetime.now().strftime(
            "%I:%M %p"
        )

        speak(
            "The current time is "
            + current_time
        )

        return True


    # =========================
    # DATE
    # =========================

    if (
        "what is today's date" in command
        or "what is the date" in command
        or "today's date" in command
        or "today date" in command
        or command == "date"
    ):

        current_date = datetime.now().strftime(
            "%d %B %Y"
        )

        speak(
            "Today is "
            + current_date
        )

        return True


    # =========================
    # HELLO
    # =========================

    if (
        command == "hello"
        or command == "hi"
        or "hello jarvis" in command
        or "hi jarvis" in command
        or "hey jarvis" in command
    ):

        speak(
            "Hello sir. How can I help you?"
        )

        return True


    # =========================
    # AI BRAIN FALLBACK
    # =========================

    return ask_ai(
        command
    )


# =========================
# CONVERSATION MODE
# =========================

def conversation_mode():

    speak(
        "Yes sir?"
    )


    while True:

        command = listen()


        if not command:

            speak(
                "I didn't hear anything."
            )

            print(
                "Returning to wake-word mode..."
            )

            return True


        running = process_command(
            command
        )


        if not running:

            return False


        print(
            "\nWaiting for your next command..."
        )


# =========================
# MAIN PROGRAM
# =========================

speak(
    "Jarvis is online. "
    "Say Jarvis to activate me."
)


running = True


while running:

    print(
        "\nWaiting for wake word..."
    )


    wake = listen_for_wake_word()


    if wake == "stop":

        speak(
            "Goodbye sir."
        )

        break


    if wake == "jarvis":

        running = conversation_mode()