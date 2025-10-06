import asyncio
from typing import List, Dict, TypedDict, Any

from backend.api.endpoints.crawl import crawl_endpoint
from backend.services import gcp_nlp, llm_seo_analyzer

# --- 1. Định nghĩa State của Graph ---
class GraphState(TypedDict):
    keyword: str
    output_fields: List[str]  # Sẽ được sử dụng để xác định output cuối cùng
    num_suggestions: int
    # --- Ngữ cảnh từ người dùng ---
    marketing_goal: str | None
    target_audience: str | None
    brand_voice: str | None
    custom_notes: str | None
    # --- Dữ liệu xử lý trong workflow ---
    top_articles: List[Dict]
    analysis_results: List[Dict]
    content_brief: str
    # --- Dữ liệu cho workflow mới ---
    seo_ideas: List[Dict]
    outlines: List[str]
    final_suggestions: List[Dict] # Giữ tên này để tương thích output

# --- 2. Định nghĩa các Node của Graph ---

async def fetch_top_articles(state: GraphState) -> GraphState:
    """
    Node: Lấy top 10 bài viết từ Google cho từ khóa.
    """
    print(f"--- Node: Fetching top articles for keyword: {state['keyword']} ---")
    # Gọi hàm crawl đã có và lấy nội dung
    articles = await crawl_endpoint(keyword=state['keyword'], get_content=True)
    state['top_articles'] = articles
    return state

async def analyze_articles(state: GraphState) -> GraphState:
    """
    Node: Phân tích từng bài viết bằng GCP NLP và LLM.
    """
    print(f"--- Node: Analyzing {len(state['top_articles'])} articles ---")
    analysis_results = []
    for article in state['top_articles']:
        if not article.get('content'):
            continue
        
        # Chạy song song GCP NLP và LLM Analyzer
        gcp_result, llm_result = await asyncio.gather(
            asyncio.to_thread(gcp_nlp.analyze_text, article['content']),
            asyncio.to_thread(llm_seo_analyzer.analyze_competitor, article['content'])
        )
        
        combined_analysis = {
            "link": article['link'],
            "gcp_analysis": gcp_result,
            "llm_seo_analysis": llm_result
        }
        analysis_results.append(combined_analysis)
        
    state['analysis_results'] = analysis_results
    return state

async def synthesize_analysis(state: GraphState) -> GraphState:
    """
    Node: Tổng hợp các phân tích thành một Content Brief duy nhất.
    """
    print("--- Node: Synthesizing analysis into a content brief ---")
    # Truyền thêm ngữ cảnh vào hàm tổng hợp
    brief = await asyncio.to_thread(
        llm_seo_analyzer.synthesize_insights,
        state['analysis_results'],
        marketing_goal=state.get('marketing_goal'),
        target_audience=state.get('target_audience'),
        brand_voice=state.get('brand_voice'),
        custom_notes=state.get('custom_notes')
    )
    print(f"Synthesized Brief: {brief[:500]}...")  # In một phần của brief để kiểm tra
    state['content_brief'] = brief
    return state

async def generate_initial_ideas(state: GraphState) -> GraphState:
    """
    Node: Tạo ra N bộ ý tưởng (title, meta description, sapo) ban đầu.
    """
    print(f"--- Node: Generating {state['num_suggestions']} initial ideas ---")
    ideas = await asyncio.to_thread(
        llm_seo_analyzer.generate_seo_ideas,
        state['content_brief'],
        state['num_suggestions']
    )
    state['seo_ideas'] = ideas
    return state

async def generate_outlines(state: GraphState) -> GraphState:
    """
    Node: Tạo dàn ý chi tiết cho từng ý tưởng.
    """
    print(f"--- Node: Generating outlines for {len(state['seo_ideas'])} ideas ---")
    tasks = [
        asyncio.to_thread(
            llm_seo_analyzer.generate_seo_outline,
            state['content_brief'],
            idea['title'],
            idea['meta_description']
        )
        for idea in state['seo_ideas']
    ]
    outlines = await asyncio.gather(*tasks)
    state['outlines'] = outlines
    return state

async def generate_full_articles(state: GraphState) -> GraphState:
    """
    Node: Viết bài viết hoàn chỉnh từ mỗi bộ (ý tưởng + dàn ý).
    """
    print(f"--- Node: Generating {len(state['outlines'])} full articles ---")
    tasks = [
        asyncio.to_thread(
            llm_seo_analyzer.generate_article_from_outline,
            state['content_brief'],
            state['seo_ideas'][i]['title'],
            outline
        )
        for i, outline in enumerate(state['outlines'])
    ]
    articles = await asyncio.gather(*tasks)
    
    # Tập hợp kết quả cuối cùng theo cấu trúc của Pydantic model SeoSuggestion
    final_suggestions = []
    for i, article_content in enumerate(articles):
        idea = state['seo_ideas'][i]
        final_suggestions.append({
            "title": idea.get("title"),
            "description": idea.get("meta_description"), # Ánh xạ meta_description -> description
            "h1": idea.get("title"), # Sử dụng title cho h1
            "sapo": idea.get("sapo"),
            "content": article_content
            # "outline" không có trong schema nên không đưa vào
        })
        
    state['final_suggestions'] = final_suggestions
    return state

# --- 3. Xây dựng Graph (sẽ được thực hiện trong file processing.py) ---
# LangGraph sẽ được khởi tạo và các node sẽ được thêm vào ở endpoint.
