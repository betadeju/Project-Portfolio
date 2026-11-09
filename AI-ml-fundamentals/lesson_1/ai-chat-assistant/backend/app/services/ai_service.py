import google.generativeai as genai
from config.setting import settings
from app.models.chat import ChatMessage
from typing import List
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model= genai.GenerativeModel('gemini-pro')

    def generate_reponse(self, user_message: str, conversation_history: List[ChatMessage]) -> str:
        """
        Generate a response from the AI model based on the user's message and chat history.

        Args:
            user_message (str): The message from the user.
            chat_history (List[ChatMessage]): The history of chat messages.

        Returns:
            str: The generated response from the AI model.
        """
       

        # Generate a response using the AI model
        try:
             # Prepare the conversation context for the AI model
            context = self._build_context(conversation_history)
            full_prompt = f"{context}\nUser: {user_message}\nAssitant:"
            logger.info (f"Generating response for prompt: {user_message[:50]}...")  # Log the first 50 characters of the prompt
            response = self.model.generate_text(full_prompt)

            if response and response.text:
                return response.text.strip()
            else:
                return "I apologize, but I couldn't generate a response at the moment."
        except Exception as e:
            logger.error(f"Error generating AI response: {str(e)}")
            return f"I'm experiencing technical difficulties: {str(e)}"
    
    def _build_context(self , conversation_history: List[ChatMessage]) -> str:
        """
        Build the context string from the conversation history.

        Args:
            conversation_history (List[ChatMessage]): The history of chat messages.

        Returns:
            str: The formatted context string for the AI model.
        """
        if not conversation_history:
            return "You are a helpful AI assistant. Provide clear, concise, and helpful responses."
        context = "You are a helpful AI assistant. Here's our conversation so far:\n"

        for message in conversation_history[-5]:  # Keep last 5 messages for context
            context += f"{message.role.title()}: {message.content}\n"
        
        return context
     
ai_service = AIService()