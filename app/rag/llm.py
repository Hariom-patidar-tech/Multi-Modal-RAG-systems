from groq import Groq
from app.core.config import settings
from app.core.logger import logger
# Hamare centralized prompts file se SYSTEM_PROMPT import karenge
from app.rag.prompts import SYSTEM_PROMPT 

class LLMEngine:
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.model_name = "llama-3.3-70b-versatile"
        
        if not self.api_key:
            logger.error("GROQ_API_KEY missing in project environment configurations.")
            raise ValueError("Groq API key must be configured in your .env file.")
            
        try:
            self.client = Groq(api_key=self.api_key)
            logger.info(f"Groq LLM Client initialized with model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Groq Client: {str(e)}")
            raise RuntimeError(f"LLM Initialization Error: {str(e)}")

    def generate_answer(self, context: str, question: str) -> str:
        """
        中央 (Centralized) SYSTEM_PROMPT aur runtime user instructions ko alag-alag split karke
        Llama 3.3 se accurate, hallucination-free answer generate karta hai.
        """
        if not context.strip():
            logger.warning("Empty context passed to LLM Engine.")
            return "Mujhe aapke database me is sawaal se related koi relevant context nahi mila."

        # User specific payload format
        user_content = f"Context:\n{context}\n\nQuestion:\n{question}\n\nAnswer:"

        try:
            logger.info(f"Invoking Groq API completion engine ({self.model_name})...")
            
            # Proper separation of concerns: System instructions vs User payload
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": user_content
                    }
                ],
                temperature=0.3, # Low temperature taaki responses deterministic and factual rahein
                max_tokens=1024
            )
            
            answer = response.choices[0].message.content
            logger.info("LLM Response generated successfully!")
            return answer

        except Exception as e:
            logger.error(f"Groq API call execution failed: {str(e)}")
            return f"Sorry, processing error during generation layer: {str(e)}"