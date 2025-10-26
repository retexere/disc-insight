import google.generativeai as genai
from PIL import Image
from .database_manager import DatabaseManager
import json

class GeminiClient:
    _instance = None

    @staticmethod
    def get_instance():
        if GeminiClient._instance is None:
            GeminiClient()
        return GeminiClient._instance

    def __init__(self):
        if GeminiClient._instance is not None:
            raise Exception("This class is a singleton!")
        else:
            self.db_manager = DatabaseManager.get_instance()
            self.text_model = None
            self.vision_model = None
            self.is_configured = False
            self.configure_client()
            GeminiClient._instance = self

    def configure_client(self):
        api_key = self.db_manager.get_setting('gemini_api_key')
        if api_key:
            try:
                genai.configure(api_key=api_key)
                self.text_model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')
                self.vision_model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')
                self.is_configured = True
                print("Gemini client configured successfully.")
            except Exception as e:
                print(f"Failed to configure Gemini client: {e}")
                self.is_configured = False
        else:
            print("Gemini API key not found in settings.")
            self.is_configured = False

    def _get_analysis_prompt(self, context_text: str) -> str:
        return f"""
        Analyze the following content to infer a DISC personality profile.
        The content is: "{context_text}"

        Based on the content, provide:
        1. A brief interpretive personality analysis.
        2. Key signals or phrases that justify the analysis.
        3. An initial proposal of the DISC vector in percentages [D, I, S, C], where the sum is 100.

        Respond ONLY with a valid JSON object with the following structure:
        {{
          "analysis": "...",
          "signals": "...",
          "disc_vector": {{ "d": <value>, "i": <value>, "s": <value>, "c": <value> }}
        }}
        """

    def suggest_strategy_improvement(self, context: str):
        if not self.is_configured:
            return None, "Gemini client is not configured."

        prompt = f"""
        Actúa como un experto coach de comunicación especializado en el modelo DISC.
        A continuación, te proporciono el contexto de una persona y una estrategia que se está aplicando.

        CONTEXTO:
        ---
        {context}
        ---

        TAREA:
        Basado en el perfil DISC, el objetivo de la estrategia y los resultados recientes, proporciona una
        sugerencia concisa y accionable para mejorar la estrategia. Enfócate en el "siguiente paso".
        No repitas la información que te he dado. Ve directamente a la recomendación.
        """
        try:
            response = self.text_model.generate_content(prompt)
            return response.text, None
        except Exception as e:
            return None, f"Error calling Gemini API for suggestion: {e}"

    def analyze_text_or_html(self, text: str):
        if not self.is_configured:
            return None, "Gemini client is not configured."
        
        prompt = self._get_analysis_prompt(text)
        try:
            response = self.text_model.generate_content(prompt)
            cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
            json.loads(cleaned_response) # Test if it's valid JSON
            return cleaned_response, None
        except Exception as e:
            return None, f"Error calling Gemini API or parsing response: {e}"

    def analyze_image(self, image_path: str):
        if not self.is_configured:
            return None, "Gemini client is not configured."
        
        try:
            img = Image.open(image_path)
            prompt = self._get_analysis_prompt("Describe the person in this image (facial expression, posture, environment) and infer their DISC profile from these visual cues.")
            response = self.vision_model.generate_content([prompt, img])
            cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
            json.loads(cleaned_response) # Test if it's valid JSON
            return cleaned_response, None
        except FileNotFoundError:
            return None, f"Image file not found at path: {image_path}"
        except Exception as e:
            return None, f"Error calling Gemini Vision API or parsing response: {e}"
