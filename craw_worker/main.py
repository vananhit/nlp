import socketio
import time
import os
from bs4 import BeautifulSoup
from seleniumbase import SB
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
# It's recommended to load these from environment variables or a config file
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8083")
CLIENT_ID = os.getenv("CLIENT_ID")
SECRET_ID = os.getenv("SECRET_ID")

# --- Socket.IO Client Setup ---
sio = socketio.Client()

@sio.event
def connect():
    print("Successfully connected to the backend.")

@sio.event
def connect_error(data):
    print(f"Connection failed: {data}")

@sio.event
def disconnect():
    print("Disconnected from the backend.")

@sio.on('start_crawl')
def on_start_crawl(data):
    keyword = data.get('keyword')
    request_id = data.get('request_id')
    if not keyword or not request_id:
        print(f"Invalid crawl command received: {data}")
        return

    print(f"Received crawl command for keyword: '{keyword}' (request_id: {request_id})")
    results = []
    try:
        extension_path = '0.1.0_0'
        with SB(uc=True, headless=False, extension_dir=extension_path) as sb:
            sb.open("https://www.google.com/search?q=" + keyword)
            sb.wait_for_element_present(".MjjYud", timeout=5)
            page_source = sb.get_page_source()
            soup = BeautifulSoup(page_source, 'lxml')
            # Use a more robust selector to find search result containers
            # Google often changes class names, so we check for multiple common ones.
            search_results = soup.select('.MjjYud')
            count = 0
            for result in search_results:
                if count >= 10:
                    break

                title_tag = result.find('h3')
                title = title_tag.get_text(strip=True) if title_tag else ""

                link_tag = result.find('a')
                url = link_tag['href'] if link_tag and link_tag.has_attr('href') else ""

                # Description can be in different tags, this is a common one
                desc_tag = result.find(class_='VwiC3b')
                description = desc_tag.get_text(strip=True) if desc_tag else ""

                # Basic validation to ensure it's a likely search result
                if title and url and url.startswith('http'):
                    results.append({
                        "title": title,
                        "link": url,
                        "description": description
                    })
                    count += 1
        print(f"Successfully crawled {len(results)} results.")
        payload = {'status': 'success', 'data': results, 'request_id': request_id}
        print(f"Emitting crawl_result with payload: {payload}")
        sio.emit('crawl_result', payload)

    except Exception as e:
        print(f"An error occurred during crawling: {e}")
        payload = {'status': 'error', 'message': str(e), 'request_id': request_id}
        print(f"Emitting crawl_result with error payload: {payload}")
        sio.emit('crawl_result', payload)


def main():
    while True:
        try:
            print("Attempting to connect to the backend...")
            sio.connect(
                BACKEND_URL,
                auth={'clientId': CLIENT_ID, 'secretId': SECRET_ID},
                socketio_path='/socket.io'
            )
            sio.wait()
        except socketio.exceptions.ConnectionError as e:
            print(f"Failed to connect to backend: {e}. Retrying in 5 seconds...")
            time.sleep(5)
        except Exception as e:
            print(f"An unexpected error occurred: {e}. Retrying in 5 seconds...")
            time.sleep(5)

if __name__ == '__main__':
    main()
