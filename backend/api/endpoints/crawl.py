import asyncio
from concurrent.futures import ThreadPoolExecutor
from fastapi import APIRouter, HTTPException
from newspaper import Article, Config
from backend.socket_manager import trigger_crawl_and_wait

router = APIRouter()

def fetch_content(item):
    """Downloads and parses content for a single article."""
    try:
        config = Config()
        config.verify_ssl = False
        article = Article(item['link'], config=config)
        article.download()
        article.parse()
        item['content'] = article.text
    except Exception as e:
        item['content'] = ""
    return item

@router.post("/crawl")
async def crawl_endpoint(keyword: str, get_content: bool = False):
    try:
        result = await trigger_crawl_and_wait(keyword)
        
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=f"Worker error: {result.get('message')}")
        
        data = result.get("data")
        
        if get_content and data:
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor(max_workers=3) as executor:
                # Schedule the fetch_content function to be run in the thread pool
                tasks = [loop.run_in_executor(executor, fetch_content, item) for item in data]
                # Wait for all tasks to complete and gather the results
                updated_data = await asyncio.gather(*tasks)
                return updated_data
        
        return data

    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Request timed out. The worker took too long to respond.")
