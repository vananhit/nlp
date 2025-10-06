from typing import List, Dict, Any, Optional
import google.generativeai as genai
from backend.services.api_key_manager import api_key_manager
import json

def get_model():
    """
    Configures and returns a new instance of the GenerativeModel.
    This ensures a new API key is used for each set of operations.
    """
    try:
        api_key = api_key_manager.get_next_key()
        if not api_key:
            raise ValueError("Gemini API key not found or no valid keys available.")
        
        # Each call to genai.configure might not be necessary if the key is passed directly,
        # but it's safer to ensure the environment is set for the current key.
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-pro')
        return model
    except (ValueError, FileNotFoundError) as e:
        print(f"Error configuring Generative AI: {e}")
        return None

def generate_basic_info(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates missing basic information using an LLM.
    If address is provided, it also generates the corresponding zipcode.
    """
    model = get_model()
    if not model:
        raise RuntimeError("Generative AI model could not be configured.")

    required_fields = ["username", "name", "address", "hotline", "zipcode"]
    missing_fields = [field for field in required_fields if not state.get(field)]

    if not missing_fields and "address" not in missing_fields:
        return state # No generation needed if all fields are present

    # Special handling for username based on website
    if "username" in missing_fields and state.get("website"):
        try:
            domain = state["website"].split('//')[-1].split('/')[0]
            username = domain.split('.')[0].replace('-', '').replace('.', '')
            state["username"] = username
            missing_fields.remove("username")
        except Exception:
            pass # If parsing fails, let the LLM handle it

    if not missing_fields:
         # If only zipcode was missing but address is present
        if not state.get("zipcode") and state.get("address"):
            pass
        else:
            return state


    prompt_parts = [
        "You are an expert data completion assistant.",
        "Based on the following partial information, please generate the missing fields.",
        f"Keyword: {state.get('keyword', 'N/A')}",
        f"Website: {state.get('website', 'N/A')}",
        f"Short Description: {state.get('short_description', 'N/A')}",
        "Current Information:",
        f"- Name: {state.get('name', 'Missing')}",
        f"- Address: {state.get('address', 'Missing')}",
        f"- Hotline: {state.get('hotline', 'Missing')}",
        f"- Zipcode: {state.get('zipcode', 'Missing')}",
        f"- Username: {state.get('username', 'Missing')}",
        "\nInstructions:",
        "1. Generate plausible information for all 'Missing' fields.",
        "2. If the Address is provided but the Zipcode is missing, find the correct zipcode for that address.",
        "3. If the Address is missing, generate a plausible Vietnamese address.",
        "4. The hotline should be a Vietnamese phone number.",
        "5. The username should be a single word, no spaces, no special characters, derived from the website or name.",
        "6. Return the result as a JSON object with the keys: 'name', 'address', 'hotline', 'zipcode', 'username'."
    ]

    prompt = "\n".join(prompt_parts)

    try:
        response = model.generate_content(prompt)
        generated_data = json.loads(response.text.strip())
        
        # Update state with generated data, only if the original was missing
        for key, value in generated_data.items():
            if not state.get(key):
                state[key] = value

    except Exception as e:
        print(f"Error during LLM call for basic info: {e}")
        # Fallback for critical fields if LLM fails
        if not state.get("name"): state["name"] = state.get("keyword", "Default Name")
        if not state.get("username"): state["username"] = "defaultuser"
        if not state.get("address"): state["address"] = "Not specified"
        if not state.get("zipcode"): state["zipcode"] = "00000"
        if not state.get("hotline"): state["hotline"] = "Not specified"

    return state

def generate_hashtags(state: Dict[str, Any]) -> Dict[str, Any]:
    """Generates a string of relevant hashtags using an LLM."""
    model = get_model()
    if not model:
        raise RuntimeError("Generative AI model could not be configured.")

    prompt_parts = [
        "You are a social media marketing expert.",
        "Based on the following business profile, generate a list of 15 relevant and effective hashtags for social media.",
        f"Main Keyword: {state.get('main_keyword') or state.get('keyword')}",
        f"Name: {state.get('name')}",
        f"Website: {state.get('website')}",
        f"Description: {state.get('short_description', 'N/A')}",
        "\nInstructions:",
        "1. The hashtags should be in Vietnamese but written without accent marks.",
        "2. Each hashtag must follow PascalCase format (e.g., #MonNgonVietNam, #AmThucDuongPho).",
        "3. They should be relevant to the main keyword and business.",
        "4. Create a mix of popular and niche hashtags.",
        "5. Return the result as a single string, with each hashtag starting with '#' and separated by a space."
    ]

    prompt = "\n".join(prompt_parts)

    try:
        response = model.generate_content(prompt)
        state["hashtag"] = response.text.strip()
    except Exception as e:
        print(f"Error during LLM call for hashtags: {e}")
        state["hashtag"] = f"#{state.get('keyword', 'general').replace(' ', '')}"

    return state

def generate_bio_entities(state: Dict[str, Any]) -> Dict[str, Any]:
    """Generates a list of bio entity strings using an LLM."""
    model = get_model()
    if not model:
        raise RuntimeError("Generative AI model could not be configured.")

    num_entities = state.get("num_bio_entities") or 5 # Default to 5 if not specified

    prompt_parts = [
        "You are an expert content writer specializing in creating compelling business biographies optimized for SEO.",
        "Based on the following business profile, write a list of short, engaging paragraphs (bio entities) that include SEO-optimized backlinks.",
        f"Main Keyword: {state.get('main_keyword') or state.get('keyword')}",
        f"Name: {state.get('name')}",
        f"Website: {state.get('website')}",
        f"Address: {state.get('address')}",
        f"Description: {state.get('short_description', 'N/A')}",
        "\nInstructions:",
        f"1. Generate exactly {num_entities} unique paragraphs.",
        "2. Each paragraph must focus on a different strength or aspect of the business.",
        "3. Each paragraph must include at least one backlink to the homepage with a natural SEO-friendly anchor text (e.g., brand name, main keyword, or relevant phrase).",
        "4. The anchor text must fit naturally into the sentence and vary across paragraphs.",
        "5. Each paragraph must be no longer than 200 words.",
        "6. The tone should be professional, trustworthy, and persuasive.",
        "7. The content must be written in Vietnamese.",
        "8. Naturally integrate both the business name and main keyword into the content.",
        "9. Return the result as JSON with key 'bioEntities', e.g. {\"bioEntities\": [\"Paragraph 1\", \"Paragraph 2\"]}."
    ]

    prompt = "\n".join(prompt_parts)

    try:
        response = model.generate_content(prompt)
        # Clean the response text before parsing
        cleaned_text = response.text.strip()
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[7:]
        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-3]
        
        data = json.loads(cleaned_text)
        state["bioEntities"] = data.get("bioEntities", [])
    except Exception as e:
        print(f"Error during LLM call for bio entities: {e}")
        state["bioEntities"] = [f"This is a sample bio for {state.get('name', 'the company')} based on the keyword {state.get('keyword', 'general')}." for _ in range(num_entities)]

    return state
