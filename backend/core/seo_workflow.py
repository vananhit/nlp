import asyncio
from typing import List, Dict, TypedDict, Any

from backend.api.endpoints.crawl import crawl_endpoint
from backend.services import gcp_nlp, llm_seo_analyzer

# --- 1. Định nghĩa State của Graph ---
class GraphState(TypedDict):
    keyword: str
    output_fields: List[str]  # Sẽ được sử dụng để xác định output cuối cùng
    num_suggestions: int
    article_type: str | None
    # --- Ngữ cảnh từ người dùng ---
    marketing_goal: str | None
    target_audience: str | None
    brand_voice: str | None
    custom_notes: str | None # Sẽ được thay thế bằng product_info
    product_info: str | None # Trường mới để chứa thông tin sản phẩm
    language: str | None
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
        # gcp_nlp.analyze_text vẫn là sync, llm_seo_analyzer.analyze_competitor bây giờ là async
        gcp_task = asyncio.to_thread(gcp_nlp.analyze_text, article['content'])
        llm_task = llm_seo_analyzer.analyze_competitor(article['content'])
        
        gcp_result, llm_result = await asyncio.gather(gcp_task, llm_task)
        
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
    # Gọi trực tiếp hàm async mới
    brief = await llm_seo_analyzer.synthesize_insights(
        analyses=state['analysis_results'],
        marketing_goal=state.get('marketing_goal'),
        target_audience=state.get('target_audience'),
        brand_voice=state.get('brand_voice'),
        custom_notes=state.get('custom_notes'), # Giữ lại để tương thích, nhưng ưu tiên product_info
        product_info=state.get('product_info'),
        language=state.get('language'),
        article_type=state.get('article_type')
    )
    print(f"Synthesized Brief: {brief[:500]}...")  # In một phần của brief để kiểm tra
    state['content_brief'] = brief
    return state

async def generate_initial_ideas(state: GraphState) -> GraphState:
    """
    Node: Tạo ra N bộ ý tưởng (title, meta description, sapo) ban đầu.
    Sử dụng hàm generate_seo_ideas đã được cập nhật với structured output.
    """
    print(f"--- Node: Generating {state['num_suggestions']} initial ideas ---")
    # Gọi trực tiếp hàm async mới
    ideas = await llm_seo_analyzer.generate_seo_ideas(
        state['content_brief'],
        state['num_suggestions'],
        language=state.get('language')
    )
    state['seo_ideas'] = ideas
    return state

async def generate_outlines(state: GraphState) -> GraphState:
    """
    Node: Tạo dàn ý chi tiết cho từng ý tưởng.
    """
    print(f"--- Node: Generating outlines for {len(state['seo_ideas'])} ideas ---")
    tasks = []
    for idea in state['seo_ideas']:
        # --- BẢO VỆ CHỐNG LỖI KEYERROR ---
        # Sử dụng .get() để truy cập an toàn, cung cấp giá trị mặc định là chuỗi rỗng
        title = idea.get('title', '')
        meta_description = idea.get('meta_description', '')

        # Bỏ qua việc tạo outline nếu không có title
        if not title:
            print(f"--- Warning: Skipping outline generation for an idea with no title. ---")
            continue

        # Gọi trực tiếp hàm async
        tasks.append(
            llm_seo_analyzer.generate_seo_outline(
                brief=state['content_brief'],
                title=title,
                meta_description=meta_description,
                language=state.get('language')
            )
        )
    
    if tasks:
        outlines = await asyncio.gather(*tasks)
        state['outlines'] = outlines
    else:
        state['outlines'] = [] # Đảm bảo outlines là một list trống nếu không có task nào
        
    return state

async def generate_full_articles(state: GraphState) -> GraphState:
    """
    Node: Viết bài viết hoàn chỉnh và phân tích chuyên mục.
    """
    print(f"--- Node: Generating {len(state['outlines'])} full articles ---")
    
    # --- 1. Generate article content ---
    generation_tasks = []
    valid_ideas_for_articles = [idea for idea in state['seo_ideas'] if idea.get('title')]

    for i, outline in enumerate(state['outlines']):
        # Đảm bảo chúng ta không bị lỗi index nếu số lượng outline và idea hợp lệ không khớp
        if i < len(valid_ideas_for_articles):
            # --- BẢO VỆ CHỐNG LỖI KEYERROR ---
            title = valid_ideas_for_articles[i].get('title', 'Untitled')
            # Gọi trực tiếp hàm async
            generation_tasks.append(
                llm_seo_analyzer.generate_article_from_outline(
                    brief=state['content_brief'],
                    title=title,
                    outline=outline,
                    language=state.get('language')
                )
            )

    if not generation_tasks:
        print("--- Warning: No valid outlines to generate articles from. ---")
        state['final_suggestions'] = []
        return state

    articles_content = await asyncio.gather(*generation_tasks)
    
    # --- 2. Analyze categories for each article ---
    analysis_tasks = [
        asyncio.to_thread(gcp_nlp.analyze_text, content)
        for content in articles_content
    ]
    analysis_results = await asyncio.gather(*analysis_tasks)

    # --- 3. Assemble final results ---
    final_suggestions = []
    for i, article_content in enumerate(articles_content):
        idea = state['seo_ideas'][i]
        nlp_result = analysis_results[i]
        
        # Sort categories by confidence and get top 10
        sorted_categories = sorted(
            nlp_result.get('categories', []),
            key=lambda x: x.get('confidence', 0),
            reverse=True
        )
        top_10_categories = [
            {"name": cat['name'], "score": cat['confidence']}
            for cat in sorted_categories[:10]
        ]

        final_suggestions.append({
            "title": idea.get("title"),
            "description": idea.get("meta_description"),
            "h1": idea.get("title"),
            "sapo": idea.get("sapo"),
            "content": article_content,
            "categories": top_10_categories
        })
        
    state['final_suggestions'] = final_suggestions
    return state

# --- 3. Xây dựng Graph (sẽ được thực hiện trong file processing.py) ---
# LangGraph sẽ được khởi tạo và các node sẽ được thêm vào ở endpoint.
