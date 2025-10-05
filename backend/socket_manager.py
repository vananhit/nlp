import socketio
import asyncio
import uuid
from backend.core.config import settings

# --- Socket.IO Setup ---
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
socket_app = socketio.ASGIApp(sio)

# --- State Management ---
worker_sid = None
crawl_requests = {}
crawl_semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_CRAWLS)

# --- Event Handlers ---
@sio.event
async def connect(sid, environ, auth):
    global worker_sid
    print(f"Socket connection attempt from {sid}")
    client_id = auth.get("clientId")
    secret_id = auth.get("secretId")

    if client_id == settings.WORKER_CLIENT_ID and secret_id == settings.WORKER_SECRET_ID:
        print(f"Worker {sid} connected successfully.")
        worker_sid = sid
    else:
        print(f"Authentication failed for {sid}. Disconnecting.")
        raise socketio.exceptions.ConnectionRefusedError('Authentication failed')

@sio.event
def disconnect(sid):
    global worker_sid
    if sid == worker_sid:
        print(f"Worker {sid} disconnected.")
        worker_sid = None

@sio.on('crawl_result')
async def handle_crawl_result(sid, data):
    if sid != worker_sid:
        return

    request_id = data.get("request_id")
    if request_id and request_id in crawl_requests:
        print(f"Received crawl result for request_id: {request_id}")
        crawl_requests[request_id]["result"] = data
        crawl_requests[request_id]["event"].set()
    else:
        print(f"Received crawl result with no or invalid request_id: {data}")

# --- Helper Function for API Endpoint ---
async def trigger_crawl_and_wait(keyword: str):
    if worker_sid is None:
        raise ConnectionError("Worker is not connected.")

    request_id = str(uuid.uuid4())
    event = asyncio.Event()
    crawl_requests[request_id] = {"event": event, "result": None}

    async with crawl_semaphore:
        try:
            print(f"Sending 'start_crawl' to worker for request_id: {request_id}")
            await sio.emit('start_crawl', {'keyword': keyword, 'request_id': request_id}, to=worker_sid)

            await asyncio.wait_for(event.wait(), timeout=120.0)

            result = crawl_requests[request_id]["result"]
            return result

        finally:
            if request_id in crawl_requests:
                del crawl_requests[request_id]
