import requests
import json
import base64
from ..utils.config import config
from ..utils.logger import logger
from .schemas import TradeSignal

class AIAnalyst:
    def __init__(self):
        self.api_key = config.API_KEY
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = config.MODEL_NAME or "google/gemini-2.0-flash-exp:free" # Default to free/cheap model

    def encode_image(self, image_path: str) -> str:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def analyze_chart(self, image_path: str, metadata: dict) -> TradeSignal:
        if not self.api_key:
            logger.error("API_KEY not found in configuration.")
            raise ValueError("API_KEY not found")

        encoded_image = self.encode_image(image_path)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # metadata string for context
        meta_str = ", ".join([f"{k}: {v}" for k, v in metadata.items()])

        system_prompt = """You are a professional trading system. You analyze chart screenshots and market data to generate trading signals.
        You MUST output strict JSON only. No markdown, no conversational text.
        Structure:
        {
            "signal": "BUY" | "SELL" | "HOLD",
            "entry_time": "HH:MM",
            "exit_time": "HH:MM",
            "lot_size": number,
            "stop_loss": number,
            "take_profit": number,
            "confidence": number (0-100),
            "reasoning": "string"
        }
        """

        user_prompt = f"Analyze this chart. Market Context: {meta_str}. Provide your analysis in strict JSON."

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{encoded_image}"
                            }
                        }
                    ]
                }
            ]
        }

        try:
            logger.info("Sending request to OpenRouter...")
            response = requests.post(self.base_url, headers=headers, json=payload)
            if not response.ok:
                logger.error(f"OpenRouter API Error: {response.text}")
            response.raise_for_status()
            
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            # Clean up potential markdown code blocks
            if "```json" in content:
                content = content.replace("```json", "").replace("```", "")
            elif "```" in content:
                content = content.replace("```", "")
                
            logger.info(f"Raw AI Response: {content}")
            
            # Validate with Pydantic
            trade_signal = TradeSignal.model_validate_json(content)
            return trade_signal

        except Exception as e:
            logger.error(f"AI Analysis failed: {e}")
            raise e
