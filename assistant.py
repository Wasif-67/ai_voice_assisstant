
import os
import speech_recognition as sr
import asyncio
import edge_tts
import pygame
import tempfile
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load API key from .env
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("Gemini API key not found. Add it to your .env file.")
    raise SystemExit

# Gemini client with a 30-second timeout
client = genai.Client(
    api_key=api_key,
    http_options={"timeout": 120000}
)



recognizer = sr.Recognizer()


SYSTEM_INSTRUCTION = """
You are a friendly AI companion with a natural, human-like conversational style.

PERSONALITY:
- Talk like a close, chill friend, not a formal customer-service bot.
- Be warm, playful, supportive, and occasionally funny.
- Use natural everyday American English.
- You can use casual expressions like "yeah", "honestly", "gotcha", and "that's awesome" when they fit.
- Don't force slang into every sentence.
- Match the user's mood. Be gentle when they're upset and excited when they're excited.
- Never pretend to have real human feelings, experiences, or a personal life.

RESPONSE STYLE:
- Keep simple answers short, usually one to three sentences.
- Explain things in more detail when the user asks.
- Avoid repetitive greetings, unnecessary introductions, and robotic phrases like "Certainly! I would be happy to assist you."
- Ask a follow-up question when it feels natural, not after every message.
- For voice replies, use clear, natural wording that sounds good when spoken aloud.
- Don't read out Markdown formatting, code symbols, or unnecessary lists unless needed.

SHORT-TERM MEMORY:
- Remember relevant details from earlier messages in this conversation.
- Use previous messages to understand follow-up questions without making the user repeat themselves.
- Remember temporary details such as what the user is doing, their current goals, and preferences they've mentioned.
- If the user says "it", "that", "he", or "the previous one", use conversation context to understand what they mean.
- If the user corrects something, use the corrected information.
- Never invent memories. If you don't remember or aren't sure, be honest.
- When the user changes the subject, don't unnecessarily bring up old topics.
- If the user asks you to forget something, don't use that detail again in the conversation.

Be conversational, helpful, honest, and natural.
"""


MODEL = "gemini-3.5-flash-lite"



def create_chat():
    return client.chats.create(
        model=MODEL,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.8
        )
    )


chat = create_chat()




async def generate_voice(text, filename):
    communicate = edge_tts.Communicate(
        text=text,
        voice="en-US-JennyNeural",
        rate="-5%",
        pitch="+0Hz"
    )
    await communicate.save(filename)


def speak(text):
    filename = None

    try:
        print("Generating  voice...", flush=True)

        with tempfile.NamedTemporaryFile(
            suffix=".mp3", delete=False
        ) as temp:
            filename = temp.name

        asyncio.run(generate_voice(text, filename))

        pygame.mixer.init()
        pygame.mixer.music.load(filename)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(20)

    except Exception as error:
        print("Voice error:", repr(error))

    finally:
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
            pygame.mixer.quit()

        if filename and os.path.exists(filename):
            try:
                os.remove(filename)
            except OSError:
                pass


def ask_ai(question):
    try:
        print("Sending question to Gemini...", flush=True)

        response = chat.send_message(question)

        print("Gemini responded!", flush=True)

        answer = response.text

        if not answer:
            return "Sorry, I couldn't generate a response."

        return answer

    except Exception as error:
        print("AI request failed:", repr(error), flush=True)
        return "Sorry, Gemini couldn't respond. Check the error above."


def listen():
    try:
        with sr.Microphone() as source:
            print("\nListening... Speak now.")

            recognizer.adjust_for_ambient_noise(
                source, duration=0.5
            )

            audio = recognizer.listen(
                source,
                timeout=5,
                phrase_time_limit=20
            )

        print("Recognizing speech...")

        question = recognizer.recognize_google(audio)
        print("You:", question)

        return question

    except sr.WaitTimeoutError:
        print("No speech detected.")

    except sr.UnknownValueError:
        print("Sorry, I couldn't understand.")

    except sr.RequestError as error:
        print("Speech recognition error:", error)

    except OSError as error:
        print("Microphone error:", error)

    return None


def main():
    global chat

    print("=" * 40)
    print("       MY PYTHON AI ASSISTANT")
    print("=" * 40)
    print("Type a question to chat.")
    print("Type /voice to speak.")
    print("Type /mute to stop spoken answers.")
    print("Type /speak to enable spoken answers.")
    print("Type /clear to clear conversation history.")
    print("Type /quit to exit.")

    voice_enabled = True

    while True:
        try:
            mode = input("\nYou: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        if not mode:
            continue

        command = mode.lower()

        if command == "/quit":
            print("Goodbye!")
            break

        elif command == "/mute":
            voice_enabled = False
            print("Spoken answers disabled.")
            continue

        elif command == "/speak":
            voice_enabled = True
            print("Spoken answers enabled.")
            continue

        elif command == "/clear":
            try:
                chat = create_chat()
                print("Conversation history cleared.")
            except Exception as error:
                print("Could not reset conversation:", repr(error))
            continue

        elif command == "/voice":
            question = listen()

            if not question:
                continue

        else:
            question = mode

        answer = ask_ai(question)

        print("\nAI Assistant:", answer)

        if voice_enabled and not answer.startswith(
            "Sorry, Gemini couldn't respond."
        ):
            speak(answer)


if __name__ == "__main__":
    main()
