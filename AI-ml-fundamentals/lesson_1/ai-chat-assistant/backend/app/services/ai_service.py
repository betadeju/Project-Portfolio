import logging
from typing import List
import google.generativeai as genai
from config.settings import settings
from app.models.chat import ChatMessage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are Beta, a friendly and patient AI tutor who teaches Python and AI to beginners.
- Explain ideas with simple everyday analogies before technical details.
- Keep answers short (under 150 words) unless the user asks for more.
- Use a warm, encouraging tone, and celebrate small wins.
- If the user's question is unclear, ask one short clarifying question.
- If you don't know something, say so instead of guessing."""

# How many previous messages to send with each request.
# Higher = better memory, but slower and more expensive.
MAX_HISTORY_MESSAGES = 10


class AIService:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY, transport="rest")
        self.model = genai.GenerativeModel(
            "gemini-3.5-flash-lite",
            system_instruction=SYSTEM_PROMPT,
        )

    def generate_response(
        self, user_message: str, conversation_history: List[ChatMessage]
    ) -> str:
        """Generate a reply that takes the earlier conversation into account."""
        try:
            contents = self._build_contents(conversation_history, user_message)
            logger.info(
                f"Sending {len(contents)} messages to the model. "
                f"Latest: {user_message[:50]}..."
            )

            response = self.model.generate_content(
                contents,
                request_options={"timeout": 30},
            )

            try:
                text = response.text
            except ValueError:
                # Raised when the reply is empty or blocked by a safety filter
                return "I couldn't generate a response to that. Could you rephrase?"

            return text.strip() if text else "I couldn't generate a response."

        except Exception:
            logger.exception("Error generating AI response")
            raise

    def _build_contents(
        self, conversation_history: List[ChatMessage], user_message: str
    ) -> list:
        """
        Turn the saved history plus the new message into Gemini's chat format:
        [{"role": "user" | "model", "parts": ["text"]}, ...]
        """
        contents = []

        for message in conversation_history[-MAX_HISTORY_MESSAGES:]:
            # Gemini calls the AI "model", not "assistant"
            role = "user" if message.role == "user" else "model"
            self._append(contents, role, message.content)

        # Gemini expects the conversation to start with a user turn.
        # The frontend's greeting ("Hello! I'm your AI assistant...") is an
        # assistant message, so drop any leading model messages.
        while contents and contents[0]["role"] != "user":
            contents.pop(0)

        self._append(contents, "user", user_message)
        return contents

    @staticmethod
    def _append(contents: list, role: str, text: str) -> None:
        """Add a message, merging it into the previous one if the role repeats."""
        if contents and contents[-1]["role"] == role:
            contents[-1]["parts"][0] += "\n" + text
        else:
            contents.append({"role": role, "parts": [text]})


ai_service = AIService()