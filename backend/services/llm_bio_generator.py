from typing import List, Dict, Any, Optional
import google.generativeai as genai
from backend.services.api_key_manager import api_key_manager
from backend.services.telegram_notifier import notify_exception
import json
import asyncio

# --- Langchain Imports for Structured Output ---
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

async def get_model():
    """
    Configures and returns a new instance of the GenerativeModel asynchronously.
    """
    try:
        api_key = await api_key_manager.get_next_key_async()
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-pro')
        return model
    except (ValueError, FileNotFoundError) as e:
        print(f"Error configuring Generative AI: {e}")
        return None

# --- Pydantic Schema for Structured Output ---
class BasicInfo(BaseModel):
    """Pydantic model for basic entity information."""
    name: str = Field(description="The full name of the business or entity.")
    address: str = Field(description="The complete physical address.")
    hotline: str = Field(description="The contact phone number or hotline.")
    zipcode: str = Field(description="The postal code or zipcode for the address.")
    username: str = Field(description="A single-word username, no spaces or special characters.")

async def generate_basic_info(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates missing basic information using an LLM with structured output. (Async version)
    If address is provided, it also generates the corresponding zipcode.
    """
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

    language = state.get("language", "Vietnamese")
    
    try:
        api_key = await api_key_manager.get_next_key_async()
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", google_api_key=api_key)
        structured_llm = llm.with_structured_output(BasicInfo)

        prompt = ChatPromptTemplate.from_messages([
            ("system", 
             "You are an expert data completion assistant. Based on the provided partial information, "
             "your task is to generate the missing fields. Return the result as a perfectly formatted JSON object "
             "that adheres to the provided schema. Ensure all fields are populated."
            ),
            ("human", 
             """
             Please generate the missing information based on the following data.

             **Context:**
             - Language for generated content: {language}
             - Keyword: {keyword}
             - Website: {website}
             - Short Description: {short_description}

             **Current Information (with 'Missing' for fields to be generated):**
             - Name: {name}
             - Address: {address}
             - Hotline: {hotline}
             - Zipcode: {zipcode}
             - Username: {username}

             **Instructions:**
             1. Generate plausible information for all fields marked as 'Missing'.
             2. If the Address is provided but the Zipcode is 'Missing', find the correct zipcode for that address.
             3. If the Address is 'Missing', generate a plausible address suitable for the specified language and context.
             4. The hotline should be a valid phone number format appropriate for the language.
             5. The username should be a single word, without spaces or special characters, derived logically from the website or name.
             """
            )
        ])

        chain = prompt | structured_llm
        
        generated_data = await chain.ainvoke({
            "language": language,
            "keyword": state.get('keyword', 'N/A'),
            "website": state.get('website', 'N/A'),
            "short_description": state.get('short_description', 'N/A'),
            "name": state.get('name') or "Missing",
            "address": state.get('address') or "Missing",
            "hotline": state.get('hotline') or "Missing",
            "zipcode": state.get('zipcode') or "Missing",
            "username": state.get('username') or "Missing",
        })

        # Update state with generated data, only if the original was missing
        # Pydantic model ensures generated_data is an object with attributes
        if not state.get("name"): state["name"] = generated_data.name
        if not state.get("address"): state["address"] = generated_data.address
        if not state.get("hotline"): state["hotline"] = generated_data.hotline
        if not state.get("zipcode"): state["zipcode"] = generated_data.zipcode
        if not state.get("username"): state["username"] = generated_data.username

    except Exception as e:
        error_context = f"Lỗi LLM khi tạo basic info cho state: {state}"
        print(f"{error_context}. Chi tiết: {e}")
        await notify_exception(e, context=error_context)
        # Fallback for critical fields if LLM fails
        if not state.get("name"): state["name"] = state.get("keyword", "Default Name")
        if not state.get("username"): state["username"] = "defaultuser"
        if not state.get("address"): state["address"] = "Not specified"
        if not state.get("zipcode"): state["zipcode"] = "00000"
        if not state.get("hotline"): state["hotline"] = "Not specified"

    return state

async def generate_hashtags(state: Dict[str, Any]) -> Dict[str, Any]:
    """Generates a string of relevant hashtags using an LLM. (Async version)"""
    model = await get_model()
    if not model:
        raise RuntimeError("Generative AI model could not be configured.")

    language = state.get("language", "Vietnamese")
    prompt_parts = [
        "You are a social media marketing expert.",
        "Based on the following business profile, generate a list of 15 relevant and effective hashtags for social media.",
        f"Main Keyword: {state.get('main_keyword') or state.get('keyword')}",
        f"Name: {state.get('name')}",
        f"Website: {state.get('website')}",
        f"Description: {state.get('short_description', 'N/A')}",
        "\nInstructions:",
        f"1. The hashtags should be in {language} but written without accent marks (if applicable).",
        "2. Each hashtag must follow PascalCase format (e.g., #MonNgonVietNam, #AmThucDuongPho).",
        "3. They should be relevant to the main keyword and business.",
        "4. Create a mix of popular and niche hashtags.",
        "5. Return the result as a single string, with each hashtag starting with '#' and separated by a space."
    ]

    prompt = "\n".join(prompt_parts)

    try:
        response = await model.generate_content_async(prompt)
        state["hashtag"] = response.text.strip()
    except Exception as e:
        error_context = f"Lỗi LLM khi tạo hashtags cho state: {state}"
        print(f"{error_context}. Chi tiết: {e}")
        await notify_exception(e, context=error_context)
        state["hashtag"] = f"#{state.get('keyword', 'general').replace(' ', '')}"

    return state

async def generate_bio_entities(state: Dict[str, Any]) -> Dict[str, Any]:
    """Generates a list of bio entity strings using an LLM. (Async version)"""
    model = await get_model()
    if not model:
        raise RuntimeError("Generative AI model could not be configured.")

    num_entities = state.get("num_bio_entities") or 5 # Default to 5 if not specified

    language = state.get("language", "Vietnamese")
    num_entities = state.get("num_bio_entities") or 5 # Default to 5 if not specified

    prompt_parts = [
        "You are an expert content writer specializing in creating compelling business biographies optimized for SEO.",
        "Based on the following business profile, write a list of short, engaging paragraphs (bio entities) that include SEO-optimized backlinks.",
        f"Current Date for Context: {state.get('current_date')}. Please ensure the content is timely and relevant to this date.",
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
        f"7. The content must be written in {language}.",
        "8. Naturally integrate both the business name and main keyword into the content.",
        "9. Return the result as JSON with key 'bioEntities', e.g. {\"bioEntities\": [\"Paragraph 1\", \"Paragraph 2\"]}."
    ]

    prompt = "\n".join(prompt_parts)

    try:
        response = await model.generate_content_async(prompt)
        # Clean the response text before parsing
        cleaned_text = response.text.strip()
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[7:]
        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-3]
        
        data = json.loads(cleaned_text)
        state["bioEntities"] = data.get("bioEntities", [])
    except Exception as e:
        error_context = f"Lỗi LLM khi tạo bio entities cho state: {state}"
        print(f"{error_context}. Chi tiết: {e}")
        await notify_exception(e, context=error_context)

    return state


async def generate_survey_questions(
    keyword: str,
    website: Optional[str],
    name: Optional[str],
    short_description: Optional[str],
    language: str | None = "Vietnamese"
) -> List[str]:
    """
    Generates a Brand Discovery Questionnaire to gather in-depth information for a compelling bio.
    """
    try:
        api_key = await api_key_manager.get_next_key_async()

        # 1. Initialize the model
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", google_api_key=api_key)

        # 2. Create the new, improved prompt template
        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """
                You are a professional brand strategist and copywriter. Your task is to create a **Brand Discovery Questionnaire** in {language}. 
                This questionnaire is designed to extract the core essence, story, and unique value proposition of a business or individual to write a compelling, authentic, and SEO-friendly bio.
                The questions should be organized into logical sections, be open-ended, and encourage detailed, story-driven responses.
                """
            ),
            (
                "human",
                """
                Based on the initial information, please generate a comprehensive Brand Discovery Questionnaire. The questionnaire should be divided into 4-5 sections with clear headings and numbered questions.

                - **Subject/Brand Name:** "{name}"
                - **Primary Service/Keyword:** "{keyword}"
                - **Website:** "{website}"
                - **Initial Description:** "{short_description}"

                The questionnaire should explore the following areas:
                1.  **Brand Story & Mission:** The "why" behind the brand.
                2.  **Target Audience & Brand Voice:** Who they serve and how they sound.
                3.  **Products/Services & Uniqueness:** What they offer and what makes them different.
                4.  **Achievements & Vision:** Their successes and future goals.

                Format the output clearly in {language}. For example:

                **BẢNG CÂU HỎI KHÁM PHÁ THƯƠNG HIỆU - [Subject/Brand Name]**

                **I. Câu chuyện & Sứ mệnh Thương hiệu**
                1.  Câu chuyện đằng sau sự ra đời của [Tên Thương hiệu] là gì?
                2.  Sứ mệnh cốt lõi mà bạn muốn thực hiện cho khách hàng của mình là gì?
                ...

                **STRICT INSTRUCTIONS:**
                - The entire output must be in {language}.
                - **DO NOT** add any introductory sentences, greetings, or explanations.
                - The response **MUST** begin directly with the main title `**BẢNG CÂU HỎI KHÁM PHÁ THƯƠNG HIỆU - {name}**`.
                """
            )
        ])

        # 3. Create and invoke the chain
        chain = prompt | llm
        response = await chain.ainvoke({
            "language": language,
            "name": name or "Your Brand",
            "keyword": keyword,
            "website": website or "N/A",
            "short_description": short_description or "N/A"
        })

        # 4. The output is a single string, which is what we want to return directly.
        return response.content

    except Exception as e:
        error_context = f"Lỗi LLM khi tạo survey questions cho keyword: '{keyword}'"
        print(f"{error_context}. Chi tiết: {e}")
        await notify_exception(e, context=error_context)
        raise e
