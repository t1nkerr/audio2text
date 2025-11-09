from google import genai
from keys.creds import GEMINI_API_KEY

client = genai.Client(api_key=GEMINI_API_KEY)
model_info = client.models.get(model="gemini-2.5-flash-001")
print(f"{model_info.input_token_limit=}")
print(f"{model_info.output_token_limit=}")