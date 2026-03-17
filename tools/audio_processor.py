import os
from groq import Groq
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def transcribe_audio(file_path: str) -> str:
    """
    Takes an audio file path, sends it to the Whisper model via OpenAI API, 
    and returns the transcribed text.
    """
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found at {file_path}")

        with open(file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-large-v3", 
                file=audio_file,
                response_format="text"
            )
        
        return transcript

    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        return f"Error transcribing audio: {str(e)}"
