import speech_recognition as sr
import pyttsx3
from datetime import datetime
import time

def recognize_speech_from_mic(recognizer, microphone):
    """Transcribe speech from recorded from `microphone`."""
    if not isinstance(recognizer, sr.Recognizer):
        raise TypeError("`recognizer` must be `Recognizer` instance")
    if not isinstance(microphone, sr.Microphone):
        raise TypeError("`microphone` must be `Microphone` instance")

    with microphone as source:
        recognizer.adjust_for_ambient_noise(source)
        print("Listening...")
        audio = recognizer.listen(source)

    response = {
        "success": True,
        "error": None,
        "transcription": None
    }

    try:
        response["transcription"] = recognizer.recognize_google(audio, language="en-US")
    except sr.RequestError:
        response["success"] = False
        response["error"] = "API unavailable"
    except sr.UnknownValueError:
        response["error"] = "Unable to recognize speech"

    return response

def text_to_speech(engine, text):
    """Convert text to speech."""
    print(f"Speaking: {text}")  # Debug print
    engine.say(text)
    engine.runAndWait()

def execute_command(engine, command):
    """Execute the action corresponding to the recognized command."""
    if command == "what time is it":
        current_time = datetime.now().strftime("%H:%M:%S")
        print("Current time:", current_time)
        text_to_speech(engine, "The current time is " + current_time)
    elif command == "what day is it":
        current_day = datetime.now().strftime("%A")
        print("Today is:", current_day)
        text_to_speech(engine, "Today is " + current_day)
    elif command == "what date is it":
        current_date = datetime.now().strftime("%B %d, %Y")
        print("Today's date is:", current_date)
        text_to_speech(engine, "Today's date is " + current_date)
    elif command == "thank you":
        response_text = "You are very welcome!"
        print(response_text)
        text_to_speech(engine, response_text)
    elif command == "tell me a lie":
        response_text = "You are quite a handsome chap!"
        print(response_text)
        text_to_speech(engine, response_text)
    else:
        print("Command not recognized.")
        text_to_speech(engine, "Command not recognized.")

def main():
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    print("Initiating text-to-speech engine...")
    start_time = time.time()
    engine = pyttsx3.init()
    rate = engine.getProperty('rate')
    engine.setProperty('rate', rate - 25)  # Slow down the speech rate
    end_time = time.time()
    print(f"Text-to-speech engine initialized. Time Taken: {end_time - start_time:.2f} seconds")

    while True:
        print("Listening for 'Hey Nora' to activate...")
        response = recognize_speech_from_mic(recognizer, microphone)

        if response["success"] and response["transcription"]:
            transcription = response["transcription"].lower()
            print("You said: {}".format(transcription))
            if transcription == "hey nora":
                current_hour = datetime.now().hour
                if 5 <= current_hour < 12:
                    greeting = "Good Morning"
                elif 12 <= current_hour < 18:
                    greeting = "Good Afternoon"
                else:
                    greeting = "Good Evening"
                
                print(f"{greeting}. Activated. How can I help you?")
                text_to_speech(engine, f"{greeting}. How can I help you?")
                while True:
                    print("Listening for commands...")
                    response = recognize_speech_from_mic(recognizer, microphone)

                    if response["success"] and response["transcription"]:
                        transcription = response["transcription"].lower()
                        print("You said: {}".format(transcription))
                        text_to_speech(engine, "You said: {}".format(transcription))
                        if transcription == "sleep":
                            print("Terminating the application.")
                            current_hour = datetime.now().hour
                            if 5 <= current_hour < 18:
                                farewell = "Have a great day!"
                            else:
                                farewell = "Have a good night!"
                            text_to_speech(engine, f"Terminating the application. {farewell}")
                            return
                        execute_command(engine, transcription)
                    else:
                        error_message = "I didn't catch that. What did you say?\nError: {}".format(response["error"])
                        print(error_message)
                        text_to_speech(engine, error_message)
        else:
            print("Didn't catch 'Hey Nora'. Listening again in 0.5 seconds...")
            time.sleep(0.5)

if __name__ == "__main__":
    main()
