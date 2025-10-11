import google.generativeai as genai
import json
from backend.services.api_key_manager import api_key_manager
import asyncio

async def analyze_context_with_llm(content: str, main_topic: str, search_intent: str) -> list[str]:
    """
    Sử dụng LLM để phân tích ngữ nghĩa và đối chiếu nội dung với chủ đề và ý định.
    Hàm này sẽ tạo ra các "Actionable Insights" dựa trên phân tích của LLM.
    """
    # Nếu không có thông tin đầu vào từ người dùng, không cần phân tích.
    if not main_topic and not search_intent:
        return []

    prompt_parts = [
        "You are an expert SEO analyst. Your task is to analyze the provided article against the user's stated goals. Do not rewrite the article. Only provide your analysis.",
        f"Here is the full article:\n---\n{content}\n---\n",
        "Based on the article, please answer the following questions concisely. For each question, provide a one-sentence 'Actionable Insight' that can be used to instruct a writer.",
        "Your response MUST be a valid JSON array of strings, where each string is an actionable insight. For example: [\"Actionable Insight: The main topic 'X' is not central. The content should emphasize it more.\", \"Actionable Insight: The search intent is 'comparison', but the article only discusses one product. It should compare at least two.\"]"
    ]

    if main_topic:
        prompt_parts.append(
            f"\nQuestion 1: The user's main topic is '{main_topic}'. Does the article cover this topic comprehensively and centrally? Is it the main focus?"
        )
    
    if search_intent:
        prompt_parts.append(
            f"\nQuestion 2: The user's search intent is '{search_intent}'. Does the article's content, tone, and structure effectively fulfill this intent?"
        )

    final_prompt = "\n".join(prompt_parts)

    print("--- CONTEXT ANALYSIS PROMPT SENT TO GEMINI ---")
    print(final_prompt)
    print("----------------------------------------------")

    # --- Sử dụng ApiKeyManager để lấy key và cấu hình ---
    try:
        api_key = await api_key_manager.get_next_key_async()
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-pro')
        response = await model.generate_content_async(final_prompt)
        
        # Cố gắng parse chuỗi JSON từ phản hồi.
        # LLM có thể trả về chuỗi JSON nằm trong ```json ... ```, nên cần làm sạch.
        cleaned_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        insights = json.loads(cleaned_text)
        
        if isinstance(insights, list):
            return insights
        else:
            # Fallback nếu LLM không trả về cấu trúc list như mong đợi.
            return ["Error: LLM analysis did not return a valid list structure."]

    except Exception as e:
        print(f"An error occurred during LLM context analysis: {e}")
        # Fallback nếu có lỗi (ví dụ: JSON không hợp lệ hoặc lỗi API).
        raw_response = response.text if 'response' in locals() else 'N/A'
        return [f"Could not perform LLM context analysis. Raw response: {raw_response}"]


def _generate_syntax_instructions(content: str) -> list[str]:
    """
    Tạo ra các chỉ dẫn biên tập dựa trên phân tích cú pháp đơn giản (độ dài câu).
    Mục tiêu: Cải thiện độ dễ đọc của văn bản.
    Hàm này giờ hoạt động trực tiếp trên nội dung gốc, không cần kết quả từ NLP API.
    """
    instructions = []
    
    # Tách văn bản thành các câu.
    sentences = content.split('.')
    
    # Tìm các câu được coi là "dài" (ví dụ: hơn 25 từ).
    long_sentences = [s for s in sentences if len(s.split()) > 25]
    
    # Nếu có nhiều hơn 2 câu dài, tạo một chỉ dẫn yêu cầu làm cho câu ngắn gọn hơn.
    if len(long_sentences) > 2:
        instructions.append(
            "Readability Improvement: The text contains several long sentences (over 25 words). "
            "Break them down into shorter, clearer sentences to improve readability."
        )
    return instructions

def _generate_entity_instructions(nlp_analysis: dict, main_topic: str = None) -> list[str]:
    """
    Tạo ra các chỉ dẫn biên tập dựa trên phân tích thực thể.
    Mục tiêu: Đảm bảo nội dung tập trung vào đúng chủ đề và có tính toàn diện.
    """
    instructions = []
    entities = nlp_analysis.get("entities", [])
    
    if not entities:
        return instructions

    # Tìm các thực thể xuất hiện thường xuyên nhất để xác định chủ đề chính của bài viết.
    entity_names = [e.get("name", "").lower() for e in entities]
    entity_counts = {name: entity_names.count(name) for name in set(entity_names)}
    sorted_entities = sorted(entity_counts.items(), key=lambda item: item[1], reverse=True)
    
    # Lấy 3 thực thể hàng đầu.
    top_3_entities = [e[0] for e in sorted_entities[:3]]

    instructions.append(
        f"Topical Focus: The main entities detected are: {', '.join(top_3_entities)}. "
        "Ensure the rewritten content maintains a strong focus on these core concepts."
    )
    
    # So sánh với chủ đề chính do người dùng cung cấp.
    if main_topic and main_topic.lower() not in top_3_entities:
        instructions.append(
            f"Topical Gap: The user-defined main topic '{main_topic}' is not among the top entities. "
            "The rewritten content should give it more prominence."
        )
        
    return instructions

def _generate_sentiment_instructions(nlp_analysis: dict) -> list[str]:
    """
    Tạo ra các chỉ dẫn biên tập dựa trên phân tích cảm xúc.
    Mục tiêu: Điều chỉnh giọng văn (tone and voice) cho phù hợp với mục đích bài viết.
    """
    instructions = []
    sentiment = nlp_analysis.get("sentiment", {})
    score = sentiment.get("score", 0) # > 0 là tích cực, < 0 là tiêu cực
    magnitude = sentiment.get("magnitude", 0) # Cường độ cảm xúc

    # Xác định giọng văn dựa trên điểm số.
    tone = "neutral"
    if score > 0.25:
        tone = "positive"
    elif score < -0.25:
        tone = "negative"

    # Xác định cường độ cảm xúc.
    intensity = "low"
    if magnitude > 1.5:
        intensity = "high"
    elif magnitude > 0.7:
        intensity = "moderate"

    instructions.append(
        f"Tone and Voice: The current tone is generally {tone} with {intensity} intensity. "
        "When rewriting, either maintain or adjust this tone based on the article's goal. "
        "For example, for a product review, a more enthusiastic and positive tone is often better."
    )
    return instructions

def _generate_category_instructions(nlp_analysis: dict, search_intent: str = None) -> list[str]:
    """
    Tạo ra các chỉ dẫn biên tập dựa trên phân loại nội dung.
    Mục tiêu: Đảm bảo nội dung phù hợp với đối tượng mục tiêu.
    """
    instructions = []
    categories = nlp_analysis.get("categories", [])
    if not categories:
        return instructions

    # Lấy danh mục chính mà Google NLP phân loại.
    top_category = categories[0].get("name")
    instructions.append(f"Content Angle: The content is classified under '{top_category}'.")

    # Kiểm tra sự không nhất quán giữa danh mục và ý định tìm kiếm.
    if search_intent and "beginner" in search_intent.lower():
        # Nếu nội dung mang tính kỹ thuật nhưng ý định là cho người mới bắt đầu.
        if "/Computers & Electronics" in top_category or "/Science" in top_category:
            instructions.append(
                "Audience Mismatch: The content is technical, but the intent is for beginners. "
                "Simplify complex jargon, provide clear definitions, and use analogies."
            )
    return instructions


async def rewrite_content_with_gemini(enriched_data: dict, content: str) -> str:
    """
    Sử dụng Google Gemini để viết lại nội dung dựa trên dữ liệu phân tích đã được làm giàu.
    Đây là "Động cơ Tái cấu trúc" chính.
    """
    
    # --- 1. Xây dựng Prompt Chi tiết ---
    # "Module Tạo Prompt" sẽ tổng hợp tất cả các phân tích thành một mệnh lệnh lớn cho AI.
    nlp_analysis = enriched_data.get("nlp_analysis", {})
    
    prompt_parts = [
        # Đóng vai: Yêu cầu AI hành động như một chuyên gia biên tập SEO.
        "You are an expert SEO content editor. Your task is to rewrite the following article to significantly improve its quality, readability, and SEO performance.",
        # Cung cấp nội dung gốc.
        f"Original Article:\n---\n{content}\n---\n",
        # Đưa ra yêu cầu chung.
        "Based on a deep NLP analysis, you MUST apply the following strategic improvements:",
    ]

    # Thêm các ghi chú từ logic đối chiếu (quan trọng nhất).
    if enriched_data.get("cross_reference_notes"):
        notes = "\n".join(f"- {note}" for note in enriched_data["cross_reference_notes"])
        prompt_parts.append(f"\n**High-Priority Actionable Insights:**\n{notes}")

    # Tạo và thêm các chỉ dẫn chi tiết từ các hàm phân tích.
    all_instructions = []
    all_instructions.extend(_generate_syntax_instructions(content)) # Sửa đổi: Truyền content trực tiếp
    all_instructions.extend(_generate_entity_instructions(nlp_analysis))
    all_instructions.extend(_generate_sentiment_instructions(nlp_analysis))
    all_instructions.extend(_generate_category_instructions(nlp_analysis))

    if all_instructions:
        instructions_text = "\n".join(f"- {inst}" for inst in all_instructions)
        prompt_parts.append(f"\n**Detailed Editorial Guidelines:**\n{instructions_text}")
    
    # Lời kêu gọi hành động cuối cùng.
    prompt_parts.append("\nRewrite the entire article now, incorporating all of the above instructions. Do not just list the changes; provide the full, rewritten text.")
    
    # Nối tất cả các phần lại thành prompt cuối cùng.
    final_prompt = "\n".join(prompt_parts)
    
    print("--- PROMPT SENT TO GEMINI ---")
    print(final_prompt)
    print("-----------------------------")

    # --- 2. Gọi API của Gemini với key được quản lý ---
    try:
        api_key = await api_key_manager.get_next_key_async()
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-pro')
        response = await model.generate_content_async(final_prompt)
        return response.text
    except Exception as e:
        print(f"An error occurred with the Gemini API: {e}")
        # Trả về thông báo lỗi thay vì làm sập ứng dụng.
        raise e # Re-raise the exception to be handled by the endpoint
