# logic.py
import roll
from google import genai
from google.genai import types
from models import WORKING_MODELS

# Global memory for chat histories
chat_histories = {}

def get_client():
    return genai.Client(api_key=roll.get_key(), http_options={'api_version': 'v1alpha'})

def get_gemini_response_stream(model_name, prompt, chat_id='default', memory_size=15, language='English'):
    """
    Generates a streaming response from Gemini.
    Yields chunks of text as they arrive.
    """
    global chat_histories
    
    if chat_id not in chat_histories:
        chat_histories[chat_id] = []

    max_retries = len(roll.API_KEYS)
    
    current_message = {"role": "user", "parts": [{"text": prompt}]}
    full_contents = chat_histories[chat_id] + [current_message]

    config = types.GenerateContentConfig(
        system_instruction=f"You are a helpful AI. ALWAYS respond strictly in the following language: {language}. Always output code inside markdown blocks."
    )

    for _ in range(max_retries):
        try:
            client = get_client()
            # USE STREAMING HERE
            response_stream = client.models.generate_content_stream(
                model=model_name, 
                contents=full_contents,
                config=config
            )
            
            full_response_text = ""
            
            # Yield chunks one by one to the frontend
            for chunk in response_stream:
                full_response_text += chunk.text
                yield chunk.text
            
            # Once the stream is fully complete, save to memory
            chat_histories[chat_id].append(current_message)
            chat_histories[chat_id].append({"role": "model", "parts": [{"text": full_response_text}]})
            
            try:
                keep_amount = int(memory_size) * 2
            except ValueError:
                keep_amount = 30
                
            if len(chat_histories[chat_id]) > keep_amount:
                chat_histories[chat_id] = chat_histories[chat_id][-keep_amount:]
                
            return # Successfully finished
            
        except Exception as e:
            if "429" in str(e):
                roll.next_key()
                continue
            # Yield error if it fails
            yield f"\n\n[System Error: {str(e)}]"
            return
            
    yield "\n\n[System Error: Limit reached. All API keys exhausted.]"