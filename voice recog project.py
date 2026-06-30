#say JOJO and ur command jojo can do basic of things so be ready.
import datetime
import json
import re  # Added for math parsing
import urllib.request
import pyjokes
import pyttsx3
import pywhatkit
import requests
import speech_recognition as sr
import wikipedia

# Global variable to store detected city
detected_city = "Delhi"

def talk(text):
    """Make Jojo speak using an Indian English / Hinglish accent on macOS"""
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    
    # Target Indian English voice (Rishi / Isha)
    indian_voice_id = None
    for voice in voices:
        if 'en_in' in voice.id.lower() or 'rishi' in voice.name.lower() or 'isha' in voice.name.lower():
            indian_voice_id = voice.id
            break
            
    if indian_voice_id:
        engine.setProperty('voice', indian_voice_id)
    else:
        # Fallback to default female voice if Indian accent isn't found
        if len(voices) > 1:
            engine.setProperty('voice', voices[1].id) 

    # Adjust speech rate to make Hinglish sentences blend more naturally
    engine.setProperty('rate', 170) 
    
    engine.say(text)
    engine.runAndWait()
    engine.stop()

# --- Auto Geolocation Setup ---
try:
    with urllib.request.urlopen("https://ipapi.co/json/") as response:
        data = json.loads(response.read().decode())
        
    detected_city = data.get("city", "Delhi")
    region = data.get("region")
    country = data.get("country_name")
    print(f"Detected Location: {detected_city}, {region}, {country}")
except Exception as e:
    print(f"Could not automatically detect location: {e}. Defaulting to Delhi.")


def get_weather():
    """Get live weather using wttr.in JSON API to fix the broken weathercom library"""
    try:
        url = f"https://wttr.in/{detected_city}?format=j1"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            weather_data = response.json()
            
            # Extract live values from JSON payload
            current_condition = weather_data['current_condition'][0]
            temp = current_condition['temp_C']
            phrase = current_condition['weatherDesc'][0]['value']
            
            talk(f"The current temperature in {detected_city} is {temp} degrees Celsius with {phrase}.")
            print(f"Weather Success: {temp}°C, {phrase}")
        else:
            talk(f"Sorry, I couldn't connect to the weather service for {detected_city}.")
            
    except Exception as e:
        print(f"Weather API Error: {e}")
        talk("Sorry, I couldn't retrieve the weather details right now.")

def take_command():
    """Listen for a command and return it as text"""
    listener = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            listener.adjust_for_ambient_noise(source, duration=0.5)
            print("Listening...")
            voice = listener.listen(source, timeout=3, phrase_time_limit=5)
            command = listener.recognize_google(voice)
            command = command.lower()
            
            if 'jojo' in command:
                command = command.replace('jojo', '').strip()
                print(f"Command received: {command}")
                return command
    except Exception:
        pass
    return ""

def take_raw_speech():
    """Listens for general speech without requiring the keyword 'jojo' (useful for follow-ups)"""
    listener = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            listener.adjust_for_ambient_noise(source, duration=0.5)
            print("Listening for input...")
            voice = listener.listen(source, timeout=4, phrase_time_limit=6)
            text = listener.recognize_google(voice).lower()
            print(f"User said: {text}")
            return text
    except Exception:
        return ""

def run_calculator():
    """Asks the user what to calculate and processes the expression safely"""
    talk("What do you want me to calculate?")
    expression = take_raw_speech()
    
    if not expression:
        talk("I didn't catch that. Calculator closed.")
        return

    # Normalize spoken arithmetic keywords to mathematical symbols
    expression = expression.replace('plus', '+')
    expression = expression.replace('minus', '-')
    expression = expression.replace('multiply by', '*')
    expression = expression.replace('multiplied by', '*')
    expression = expression.replace('into', '*')
    expression = expression.replace('times', '*')
    expression = expression.replace('divided by', '/')
    expression = expression.replace('divide by', '/')
    expression = expression.replace('x', '*') # Common mistranscription for multiplication
    
    # Clean up any characters that aren't digits or safe math operators
    # This prevents execution of malicious text/code strings via eval()
    clean_expression = re.sub(r'[^0-9+\-*/().\s]', '', expression)
    clean_expression = clean_expression.strip()

    if not clean_expression:
        talk("Sorry, that didn't sound like a valid mathematical expression.")
        return

    try:
        # Evaluate the math string safely
        result = eval(clean_expression)
        
        # Format floating points elegantly if necessary
        if isinstance(result, float) and result.is_integer():
            result = int(result)
        elif isinstance(result, float):
            result = round(result, 2)

        print(f"Math calculation: {clean_expression} = {result}")
        talk(f"The answer is {result}")
    except ZeroDivisionError:
        talk("You cannot divide by zero.")
    except Exception:
        talk("Sorry, I couldn't compute that expression. Please check the values.")

def run_jojo():
    """Process the users command and execute the appropriate action"""
    command = take_command()
    
    # Return False if no valid command was spoken (helps us track inactivity)
    if not command:
        return False
    
    if 'play' in command:
        song = command.replace('play', '')
        talk(f'Playing {song}')
        pywhatkit.playonyt(song)

    elif 'time' in command:
        time = datetime.datetime.now().strftime("%I:%M %p")
        talk(f'Current time is {time}')

    elif 'weather' in command or 'temperature' in command:
        get_weather()

    elif 'calculate' in command or 'calculator' in command:
        run_calculator()

    elif 'who is' in command:
        person = command.replace('who is', '')
        try:
            info = wikipedia.summary(person, sentences=1)
            print(info)
            talk(info)
        except Exception:
            talk("Sorry, I couldn't find the exact person you were looking for.")
    
    elif 'coffee' in command:
        talk("Sure! Ek kaam karo, tum kitchen chalo, mai code handle karti hu.")
        
    elif 'are you single' in command:
        talk("I am in a relationship with wifi.")

    elif 'joke' in command:
        joke = pyjokes.get_joke()
        print(joke)
        talk(joke)
    
    elif 'stop' in command or 'exit' in command or 'quit' in command or 'ruk jao' in command:
        talk("Goodbye! Khush raho aur chill karo.")
        return "break"  # Signal to break out of the main loop cleanly

    else:
        talk("Please say the command again.")
        
    return True # Command successfully executed

# Greet the user on starting
talk("Hello Jeet, I am Jojo. How can I help you today?")

# --- Inactivity Tracking Logic ---
consecutive_silence_count = 0

while True:
    command_executed = run_jojo()
    
    if command_executed == "break":
        break
        
    if not command_executed:
        consecutive_silence_count += 1
        # Checks if silence has hit roughly 10-12 seconds
        if consecutive_silence_count >= 3: 
            talk("I haven't heard anything from you for over 10 seconds. Shutting down. Goodbye!")
            print("System closed due to 10 seconds of inactivity.")
            break
    else:
        # Reset the counter immediately if a valid command is handled
        consecutive_silence_count = 0