import google.generativeai as genai
import json
from typing import List, Dict, Any
import asyncio

# --- Langchain Imports for Structured Output ---
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from backend.services.api_key_manager import api_key_manager

async def analyze_competitor(content: str) -> Dict[str, Any]:
    """
    Phân tích nội dung của đối thủ cạnh tranh bằng LLM để trích xuất các insight SEO. (Async version)
    """
    api_key = await api_key_manager.get_next_key_async()
    # No need to check for api_key here, as get_next_key_async will raise an exception if none are available.

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-pro') # Using 1.5 Pro for better JSON handling

    prompt = f"""
    You are an expert SEO analyst. Analyze the following article content and provide a structured analysis in JSON format.

    Article Content:
    ---
    {content[:15000]}
    ---

    Based on the content, provide the following analysis. Your response MUST be a single valid JSON object.

    {{
      "search_intent": "Analyze the primary user intent. Classify as 'Informational', 'Commercial Investigation', 'Transactional', or 'Navigational'. Provide a one-sentence explanation.",
      "content_structure": "Describe the article's structure (e.g., 'Listicle', 'How-to Guide', 'Comparison Review', 'News Article').",
      "key_arguments": [
        "List the top 3-5 main arguments or key points the article makes."
      ],
      "eeat_signals": {{
        "experience": "Does the author demonstrate first-hand experience? Provide a brief assessment.",
        "expertise": "Does the content show deep knowledge? Provide a brief assessment.",
        "authoritativeness": "Does the article establish authority (e.g., citing sources, author bio)? Provide a brief assessment.",
        "trustworthiness": "Is the information presented in a trustworthy manner (e.g., balanced views, clear data)? Provide a brief assessment."
      }},
      "key_entities": [
        "List the top 5-7 most important entities (people, products, concepts) mentioned in the text."
      ]
    }}
    """

    try:
        # Use generate_content_async for non-blocking call
        response = await model.generate_content_async(prompt)
        # Clean the response to ensure it's valid JSON
        cleaned_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned_text)
    except Exception as e:
        print(f"Error during competitor analysis with LLM: {e}")
        # It's better to raise the exception to be handled by the workflow
        raise e

async def synthesize_insights(
    analyses: List[Dict[str, Any]],
    marketing_goal: str | None = None,
    target_audience: str | None = None,
    brand_voice: str | None = None,
    custom_notes: str | None = None,
    product_info: str | None = None, # Thêm tham số mới
    language: str | None = "Vietnamese",
    article_type: str | None = None
) -> str:
    """
    Tổng hợp kết quả phân tích từ nhiều đối thủ và ngữ cảnh tùy chỉnh để tạo ra một 'Content Brief'. (Async version)
    """
    api_key = await api_key_manager.get_next_key_async()

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-pro')

    analyses_str = json.dumps(analyses, indent=2)

    # --- Xây dựng phần prompt tùy chỉnh một cách linh hoạt ---
    custom_directives = []
    if article_type:
        custom_directives.append(f"- **Required Article Type:** {article_type}. The content brief MUST be tailored to this specific format.")
    if marketing_goal:
        custom_directives.append(f"- **Marketing Goal:** {marketing_goal}")
    if target_audience:
        custom_directives.append(f"- **Target Audience:** {target_audience}")
    if brand_voice:
        custom_directives.append(f"- **Brand Voice:** {brand_voice}")
    if custom_notes: # Giữ lại để tương thích ngược nếu cần
        custom_directives.append(f"- **Additional Notes (Legacy):** {custom_notes}")
    if product_info:
        custom_directives.append(f"- **Key Product/Service Information:** {product_info}")

    custom_directives_str = "\n".join(custom_directives)

    # --- Tạo prompt cuối cùng ---
    prompt = f"""
    You are a master SEO strategist and content planner. Your task is to create a single, actionable "Content Brief" for a writer.
    You will base your brief on two sources of information:
    1.  An analysis of the top 10 competing articles.
    2.  A set of custom strategic directives provided by the user.

    **Source 1: Analyses of Top 10 Competitors**
    ---
    {analyses_str}
    ---
    """

    if custom_directives_str:
        prompt += f"""
    **Source 2: Custom Strategic Directives**
    ---
    {custom_directives_str}
    ---
    """

    prompt += f"""
    **Your Task:**
    Based on BOTH the competitor analysis and the custom directives (if provided), create a comprehensive content brief. The brief must be a clear, concise, and actionable set of instructions for a writer to create a new piece of content that is superior to the current top 10 while adhering to the brand's strategy.
    The entire output must be in {language}.

    The brief must include the following sections:

    1.  **Primary Search Intent:** Identify the dominant search intent. Explain what the user is trying to achieve.
    2.  **Winning Content Structure:** Recommend the best content structure, justifying your choice based on competitor data and the marketing goal.
    3.  **Core Topics & Sub-topics:** List essential topics and sub-topics. Synthesize key arguments from competitors and identify content gaps. Crucially, align these topics with the provided marketing goal and target audience.
    4.  **E-E-A-T Enhancement Strategy:** Provide specific advice on demonstrating superior E-E-A-T. Tailor this advice to the specified brand voice and marketing goal.
    5.  **Must-Include Entities:** List critical entities for topical completeness.
    6.  **Headline & Meta Description Angle:** Suggest a compelling angle that aligns with the brand voice and target audience.
    7.  **CTA Prompt (English):** Based on the article’s goal, target audience, and tone of voice, craft 3–5 persuasive and action-driven CTAs that align with the marketing objective — add them only if they naturally fit the content and enhance user engagement or conversion potential.
    Provide the brief as a well-formatted markdown text. Synthesize all information into strategic advice.
    """

    try:
        response = await model.generate_content_async(prompt)
        return response.text
    except Exception as e:
        print(f"Error during insight synthesis with LLM: {e}")
        raise e

# --- Pydantic Models for Structured Output ---
class SeoIdea(BaseModel):
    """Represents a single SEO content idea."""
    title: str = Field(description="The unique and compelling title for the article.")
    meta_description: str = Field(description="The SEO-optimized meta description.")
    sapo: str = Field(description="The engaging opening paragraph (sapo).")

class SeoIdeasResponse(BaseModel):
    """A list of diverse SEO ideas."""
    ideas: List[SeoIdea] = Field(description="A list of diverse SEO ideas.")


async def generate_seo_ideas(brief: str, num_suggestions: int, language: str | None = "Vietnamese") -> List[Dict[str, str]]:
    """
    Từ Content Brief, tạo ra N bộ ý tưởng (Title, Meta Description, Sapo) đa dạng bằng cách sử dụng structured output.
    """
    try:
        api_key = await api_key_manager.get_next_key_async()

        # 1. Khởi tạo model và bind với structured output
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", google_api_key=api_key)
        structured_llm = llm.with_structured_output(SeoIdeasResponse)

        # 2. Tạo prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a creative SEO strategist. Your task is to generate diverse and compelling article ideas based on a content brief. The language for the content must be {language}."),
            ("human", "Please generate {num_suggestions} ideas based on the following Content Brief:\n\n---BEGIN CONTENT BRIEF---\n{brief}\n---END CONTENT BRIEF---")
        ])

        # 3. Tạo chain và thực thi
        chain = prompt | structured_llm
        response_model = await chain.ainvoke({
            "language": language,
            "num_suggestions": num_suggestions,
            "brief": brief
        })

        # 4. Chuyển đổi Pydantic model thành list of dicts để tương thích với workflow hiện tại
        return [idea.dict() for idea in response_model.ideas]

    except Exception as e:
        print(f"Error during structured SEO idea generation with LLM: {e}")
        # Trả về lỗi theo format cũ để workflow có thể xử lý
        return [{"error": f"Failed to generate ideas with structured output. Details: {e}"}]

async def generate_seo_outline(brief: str, title: str, meta_description: str, language: str | None = "Vietnamese") -> str:
    """
    Tạo ra một dàn ý chuẩn SEO (outline) chi tiết cho bài viết dựa trên brief và một ý tưởng cụ thể. (Async version)
    """
    api_key = await api_key_manager.get_next_key_async()

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-pro')

    prompt = f"""
    You are a meticulous content architect and SEO expert. Your task is to create a detailed, SEO-optimized article outline.

    Use the following information:
    1.  **Content Brief:** Provides the overall strategy, topics, and entities.
    2.  **Chosen Title:** The main headline for the article.
    3.  **Meta Description:** A summary of the article's core message.

    Content Brief:
    ---
    {brief}
    ---

    Chosen Title: "{title}"
    Meta Description: "{meta_description}"

    **Your Task:**
    Create a comprehensive and logical article outline based on all the information provided. The outline should be well-structured with clear headings and subheadings (H2, H3, H4). It must cover the core topics from the brief and naturally incorporate the must-include entities. The structure should guide a writer to create an article that is superior to competitors.
    The entire outline must be written in {language}.

    Provide the response as a well-formatted Markdown string.
    """
    try:
        response = await model.generate_content_async(prompt)
        return response.text
    except Exception as e:
        print(f"Error during outline generation with LLM: {e}")
        raise e

async def generate_article_from_outline(brief: str, title: str, outline: str, language: str | None = "Vietnamese") -> str:
    """
    Viết một bài viết hoàn chỉnh dựa trên brief, title, và một dàn ý chi tiết. (Async version)
    """
    api_key = await api_key_manager.get_next_key_async()

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-pro')

    prompt = f"""
    You are an expert SEO copywriter. Your task is to write a complete, high-quality article. You must strictly follow the provided outline and adhere to the strategic goals in the content brief.

    **1. Content Brief (Overall Strategy):**
    ---
    {brief}
    ---

    **2. Article Title:**
    ---
    {title}
    ---

    **3. Detailed Outline (Your Structural Blueprint):**
    ---
    {outline}
    ---

    **Your Task:**
    Write a comprehensive, engaging, and SEO-optimized article in {language}.
    -   **Strictly follow the structure** defined in the Detailed Outline. Use the same headings (H2, H3, etc.).
    -   Ensure the tone, style, and core messages align with the Content Brief.
    -   Naturally weave in the key entities and topics mentioned in the brief.
    -   The final output should be the full article text in Markdown format, ready for publishing. Do not include any extra commentary.
    **STRICT REQUIREMENTS:**
    -  Do **not** add any extra commentary, instructions, or editor’s notes.
    -  Do **not** include explanations, meta comments, or summary outside the article body.
    -  The output must be **the final publish-ready article**, suitable for direct upload to a website.
    """
    try:
        response = await model.generate_content_async(prompt)
        return response.text
    except Exception as e:
        print(f"Error during article generation with LLM: {e}")
        raise e

# --- Pydantic Models for Survey Generation ---
class SurveyQuestionsResponse(BaseModel):
    """A list of survey questions."""
    questions: List[str] = Field(description="A list of insightful survey questions for SEO purposes.")

async def generate_survey_questions(
    keyword: str,
    name: str,
    website: str,
    short_description: str,
    language: str | None = "Vietnamese"
) -> List[str]:
    """
    Generates a structured marketing brief questionnaire based on client info.
    """
    try:
        api_key = await api_key_manager.get_next_key_async()

        # 1. Initialize the model
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", google_api_key=api_key)

        # 2. Create the prompt template
        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """
                You are a professional marketing strategist working at a creative agency.
                Your task is to design a comprehensive **Marketing Brief Questionnaire** 
                in {language}. This questionnaire helps you understand a client's business, 
                products, customers, competitors, brand status, and marketing goals 
                before creating a marketing strategy.
                
                The survey should be organized into **clear sections** (like Product, Customer, Market, Brand, and Goals)
                and each section should include practical, business-oriented questions.
                The tone should be professional, structured, and easy to answer.
                """
            ),
            (
                "human",
                """
                Based on the initial information provided, please generate a structured 
                marketing brief questionnaire (about 30–50 questions total), divided into 
                5–6 main sections. Each section should include a heading and numbered questions.
                
                - **Company/Brand Name:** "{name}"
                - **Primary Keyword/Service:** "{keyword}"
                - **Website:** "{website}"
                - **Brief Description:** "{short_description}"

                The questions should help the agency understand:
                - The company's products or services
                - Target customer insights
                - Market and competitors
                - Pricing and distribution channels
                - Brand and current marketing activities
                - Marketing goals and expected budget

                Format example:
                **BẢNG CÂU HỎI BRIEF MARKETING - [Company/Brand Name]**

                **I. [Section Title]**
                1. [Question 1]
                2. [Question 2]
                ...

                **STRICT INSTRUCTIONS:**
                - The entire output must be in {language}.
                - **DO NOT** add any introductory sentences, greetings, or explanations.
                - The response **MUST** begin directly with the main title `**BẢNG CÂU HỎI BRIEF MARKETING - {name}**`.
                """
            )
        ])

        # 3. Create the chain and invoke it
        chain = prompt | llm
        response = await chain.ainvoke({
            "language": language,
            "name": name,
            "keyword": keyword,
            "website": website,
            "short_description": short_description
        })

        # 4. The output is a single string, which is what we want to return directly.
        return response.content

    except Exception as e:
        print(f"Error during structured survey question generation with LLM: {e}")
        # Raise the exception to be handled by the API endpoint
        raise e
