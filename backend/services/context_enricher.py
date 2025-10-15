import os
import io
import random
import re
from typing import List, Dict, Any, TypedDict, Optional

# --- Core Imports ---
from fastapi import HTTPException, status
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI

# --- Google Drive Imports ---
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload

# --- Text Extraction Imports ---
import pypdf
import docx
import httpx
import trafilatura

# --- Constants ---
GDRIVE_URL_PATTERN = r"https://drive\.google\.com/file/d/([a-zA-Z0-9_-]+)"
WEB_URL_PATTERN = r"https?://[^\s/$.?#].[^\s]*"
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
CREDENTIALS_DIR = "backend/credentials/service_accounts"
GOOGLE_DRIVE_SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

# --- Service Account Management ---
def _get_random_gdrive_credentials():
    """Loads a random service account credential from the specified directory."""
    try:
        files = [f for f in os.listdir(CREDENTIALS_DIR) if f.endswith('.json')]
        if not files:
            raise FileNotFoundError("No service account files found in credentials directory.")
        
        random_credential_file = random.choice(files)
        credential_path = os.path.join(CREDENTIALS_DIR, random_credential_file)
        
        creds = service_account.Credentials.from_service_account_file(
            credential_path, scopes=GOOGLE_DRIVE_SCOPES
        )
        return creds
    except Exception as e:
        print(f"ERROR: Could not load Google Drive credentials: {e}")
        # In a real app, you might want a more robust fallback or error reporting
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not configure Google Drive service."
        )

# --- Tool Implementations ---

def gdrive_file_extractor(gdrive_url: str) -> str:
    """
    Extracts text from a Google Drive file (PDF, DOCX, Google Docs).
    This is a synchronous function designed to be called with asyncio.to_thread.
    """
    print(f"TOOL CALLED: gdrive_file_extractor with URL: {gdrive_url}")
    try:
        creds = _get_random_gdrive_credentials()
        drive_service = build('drive', 'v3', credentials=creds)
        
        match = re.search(GDRIVE_URL_PATTERN, gdrive_url)
        if not match:
            return "Error: Invalid Google Drive URL format."
        file_id = match.group(1)

        metadata = drive_service.files().get(fileId=file_id, fields='size, mimeType, name').execute()
        
        if int(metadata.get('size', 0)) > MAX_FILE_SIZE_BYTES:
            return f"Error: File '{metadata['name']}' exceeds the 5MB size limit."

        mime_type = metadata.get('mimeType')
        request = None
        
        if mime_type == 'application/vnd.google-apps.document':
            request = drive_service.files().export_media(fileId=file_id, mimeType='text/plain')
        elif mime_type == 'application/pdf' or mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            request = drive_service.files().get_media(fileId=file_id)
        else:
            return f"Error: Unsupported file type '{mime_type}' for file '{metadata['name']}'."

        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            _, done = downloader.next_chunk()
        
        fh.seek(0)
        
        if mime_type == 'application/vnd.google-apps.document':
            return fh.read().decode('utf-8')
        elif mime_type == 'application/pdf':
            reader = pypdf.PdfReader(fh)
            return "\n".join(page.extract_text() for page in reader.pages)
        elif mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            doc = docx.Document(fh)
            return "\n".join(para.text for para in doc.paragraphs)

    except HttpError as e:
        if e.resp.status == 404:
            return "Error: Google Drive file not found or access denied. Please ensure the file is shared with the service account."
        return f"Error: An API error occurred: {e}"
    except Exception as e:
        return f"Error: An unexpected error occurred while processing Google Drive file: {e}"

async def web_page_extractor(web_url: str) -> str:
    """
    Extracts main content from a web page using httpx and trafilatura.
    """
    print(f"TOOL CALLED: web_page_extractor with URL: {web_url}")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(web_url, follow_redirects=True, timeout=15.0)
            response.raise_for_status()
        
        # trafilatura is synchronous, so we run it in a thread
        extracted_text = await asyncio.to_thread(trafilatura.extract, response.text)
        return extracted_text or "Could not extract main content from the webpage."
    except httpx.HTTPStatusError as e:
        return f"Error: Could not fetch webpage. Status code: {e.response.status_code}"
    except Exception as e:
        return f"Error: An unexpected error occurred while processing web page: {e}"

# --- LangGraph Agent for Context Enrichment ---

class EnrichmentState(TypedDict):
    original_text: str
    found_urls: List[str]
    urls_to_process: List[Dict[str, str]]
    extracted_contents: Dict[str, str]
    final_text: str

class UrlDecision(BaseModel):
    """A decision on whether to process a specific URL."""
    url: str = Field(description="The URL to be processed.")
    should_process: bool = Field(description="True if the URL is relevant and should be processed, False otherwise.")
    reason: str = Field(description="A brief reason for the decision.")

class UrlProcessingList(BaseModel):
    """A list of decisions for all found URLs."""
    decisions: List[UrlDecision]

async def find_urls(state: EnrichmentState) -> EnrichmentState:
    """Finds all unique URLs in the original text."""
    all_urls = re.findall(f"({GDRIVE_URL_PATTERN}|{WEB_URL_PATTERN})", state['original_text'])
    unique_urls = sorted(list(set([url[0] for url in all_urls])), key=len, reverse=True)
    state['found_urls'] = unique_urls
    return state

async def url_processing_router(state: EnrichmentState) -> str:
    """The 'brain' of the agent. Decides which URLs to process."""
    if not state['found_urls']:
        return "end"

    llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0)
    structured_llm = llm.with_structured_output(UrlProcessingList)
    
    prompt = f"""You are an intelligent context analysis agent. Your task is to decide which URLs found in a user's text are worth extracting for additional context. The primary goal is to gather detailed information to deeply understand a product, service, or specific task mentioned in the text.

    **User's Text:**
    ---
    {state['original_text']}
    ---

    **Rules for Decision Making:**
    1.  **Goal-Oriented Extraction:** Only process URLs that provide specific, in-depth information directly related to the main subject of the user's text. Ask yourself: "Will the content of this URL help me understand the core product/task better?"
    2.  **Prioritize Documents:** **ALWAYS** process Google Drive URLs (drive.google.com). They are explicitly provided documents and are considered high-value context.
    3.  **Avoid General References:** **DO NOT** process generic homepage URLs (e.g., 'google.com', 'facebook.com', 'abc.com'). These are often mentioned for reference but do not contain the specific, detailed brief or documentation needed.
    4.  **Context is Key:** Analyze how the URL is mentioned. For example, in the phrase "This is the brief for abc.com (link_to_document)", you should process "link_to_document" but ignore "abc.com" because it's just identifying the subject, not providing the brief itself.
    5.  **Ignore Irrelevant Links:** Do not process social media links or other links that seem irrelevant to the main topic.

    **Analyze the following URLs based on the text and rules above. For each one, decide if it should be processed:**
    {state['found_urls']}
    """
    
    response = await structured_llm.ainvoke(prompt)
    
    urls_to_process = []
    for decision in response.decisions:
        if decision.should_process:
            url_type = "gdrive" if "drive.google.com" in decision.url else "web"
            urls_to_process.append({"url": decision.url, "type": url_type})
            
    state['urls_to_process'] = urls_to_process
    
    return "process_urls" if urls_to_process else "aggregate"

async def process_urls(state: EnrichmentState) -> EnrichmentState:
    """Processes the URLs selected by the router using the appropriate tools."""
    import asyncio
    tasks = []
    for item in state['urls_to_process']:
        if item['type'] == 'gdrive':
            tasks.append(asyncio.to_thread(gdrive_file_extractor, item['url']))
        else:
            tasks.append(web_page_extractor(item['url']))
            
    results = await asyncio.gather(*tasks)
    
    extracted_contents = {item['url']: result for item, result in zip(state['urls_to_process'], results)}
    state['extracted_contents'] = extracted_contents
    return state

def aggregate_results(state: EnrichmentState) -> EnrichmentState:
    """Aggregates the extracted content back into the original text."""
    final_text = state['original_text']
    if state.get('extracted_contents'):
        for url, content in state['extracted_contents'].items():
            replacement = f"\n--- Content extracted from {url} ---\n{content}\n--- End of content ---\n"
            final_text = final_text.replace(url, replacement)
    state['final_text'] = final_text
    return state

# --- Workflow Compilation ---
def get_enrichment_workflow():
    workflow = StateGraph(EnrichmentState)
    workflow.add_node("find_urls", find_urls)
    workflow.add_node("process_urls", process_urls)
    workflow.add_node("aggregate", aggregate_results)
    
    workflow.set_entry_point("find_urls")
    workflow.add_conditional_edges(
        "find_urls",
        url_processing_router,
        {"process_urls": "process_urls", "aggregate": "aggregate", "end": END}
    )
    workflow.add_edge("process_urls", "aggregate")
    workflow.add_edge("aggregate", END)
    
    return workflow.compile()

# Main function to be called by the API
async def enrich_context(text: str) -> str:
    if not text or not isinstance(text, str):
        return ""
        
    app = get_enrichment_workflow()
    initial_state = {"original_text": text}
    final_state = await app.ainvoke(initial_state)
    return final_state.get('final_text', text)
