from fastapi import APIRouter, Request, Depends, Form, HTTPException, UploadFile, File, Query, Body
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, Response
from fastapi.templating import Jinja2Templates
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.usage_log import UsageLog
from backend.models.admin_login_history import AdminLoginHistory
from backend.services.api_key_manager import api_key_manager
from backend.services.otp_manager import otp_manager
from user_agents import parse
from backend.services.gcp_sa_manager import gcp_sa_manager
from backend.services.client_app_manager import client_app_manager
from backend.security import create_access_token, verify_password, get_password_hash
from backend.core.config import settings
from datetime import timedelta, datetime
from jose import JWTError, jwt
import json
import asyncio

# --- Setup ---
router = APIRouter()
# Point to the root of the templates directory
templates = Jinja2Templates(directory="backend/templates")

# --- Admin User from Settings ---
ADMIN_USERNAME = settings.ADMIN_USERNAME
ADMIN_HASHED_PASSWORD = get_password_hash(settings.ADMIN_PASSWORD) if settings.ADMIN_PASSWORD else ""

# --- Authentication Dependency ---
async def get_current_admin(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return None

    # Token is expected to be in the format "Bearer <token>"
    if not token.startswith("Bearer "):
        return None
    
    token = token.split("Bearer ")[1]

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        # In a real app, you might want to look up the user in a DB here
        if username == settings.ADMIN_USERNAME:
             return username
        return None
    except JWTError:
        return None

# --- Routes ---
@router.get("/admin/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/admin/login")
async def handle_login(request: Request, db: Session = Depends(get_db), username: str = Form(...), password: str = Form(...)):
    # If password is not set, ADMIN_HASHED_PASSWORD will be an empty string,
    # and verify_password will always fail, effectively disabling login.
    if settings.ADMIN_USERNAME and   ADMIN_HASHED_PASSWORD and username == settings.ADMIN_USERNAME  and verify_password(password, ADMIN_HASHED_PASSWORD):
        # --- Log login history ---
        user_agent_string = request.headers.get("user-agent")
        user_agent = parse(user_agent_string)
        
        # --- Get real IP from headers ---
        x_forwarded_for = request.headers.get("x-forwarded-for")
        if x_forwarded_for:
            # The header can contain a comma-separated list of IPs.
            # The client's IP is typically the first one.
            ip_address = x_forwarded_for.split(",")[0].strip()
        else:
            # Fallback to client.host if the header is not present
            ip_address = request.client.host

        login_history = AdminLoginHistory(
            username=username,
            ip_address=ip_address,
            user_agent=user_agent_string,
            os=user_agent.os.family,
            os_version=user_agent.os.version_string,
            browser=user_agent.browser.family,
            browser_version=user_agent.browser.version_string
        )
        db.add(login_history)
        db.commit()
        # --- End log ---

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": username}, expires_delta=access_token_expires
        )
        # Redirect to the new default admin page
        response = RedirectResponse(url="/api/admin/gemini-keys", status_code=303)
        response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
        return response
    
    # If login fails, re-render the login page with an error
    return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid username or password"})

@router.get("/admin/logout")
async def logout(request: Request):
    # Redirect to the login page
    response = RedirectResponse(url="/api/admin/login", status_code=303)
    # Remove the access token cookie
    response.delete_cookie("access_token")
    return response

@router.get("/admin/dashboard", response_class=HTMLResponse)
async def dashboard_redirect(user: str = Depends(get_current_admin)):
    """Redirects the old dashboard URL to the new default page."""
    if not user:
        return RedirectResponse(url="/api/admin/login")
    return RedirectResponse(url="/api/admin/gemini-keys")

def mask_api_key(key: str) -> str:
    """Masks the API key, showing only the first 4 and last 4 characters."""
    if len(key) > 8:
        return f"{key[:4]}{len(key)*'*'}{key[-4:]}"
    return key

@router.get("/admin/gemini-keys", response_class=HTMLResponse)
async def manage_gemini_keys(request: Request, user: str = Depends(get_current_admin)):
    if not user:
        return RedirectResponse(url="/api/admin/login")
    
    keys_data = api_key_manager.get_all_keys()
    # Add a masked version of the key for display
    for key_info in keys_data:
        key_info['masked_key'] = mask_api_key(key_info['key'])
        
    return templates.TemplateResponse("admin/manage_gemini.html", {"request": request, "keys": keys_data})

@router.get("/admin/gcp-accounts", response_class=HTMLResponse)
async def manage_gcp_accounts(request: Request, user: str = Depends(get_current_admin)):
    if not user:
        return RedirectResponse(url="/api/admin/login")
    
    accounts = gcp_sa_manager.get_all_accounts_info()
    return templates.TemplateResponse("admin/manage_gcp.html", {"request": request, "accounts": accounts})

@router.post("/admin/gcp-accounts/upload")
async def upload_gcp_account(request: Request, file: UploadFile = File(...), user: str = Depends(get_current_admin)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a JSON file.")

    result = gcp_sa_manager.add_account(file.file)
    if not result.get("success"):
        # In a real app, you'd pass the error to the template to show the user
        raise HTTPException(status_code=500, detail=f"Could not save file: {result.get('error')}")

    return RedirectResponse(url="/api/admin/gcp-accounts", status_code=303)

@router.post("/admin/gcp-accounts/delete")
async def delete_gcp_account(request: Request, filename: str = Form(...), user: str = Depends(get_current_admin)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    gcp_sa_manager.delete_account(filename)
    return RedirectResponse(url="/api/admin/gcp-accounts", status_code=303)


@router.post("/admin/add-key")
async def add_key(request: Request, new_key: str = Form(...), user: str = Depends(get_current_admin)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Vì key đã được xác thực ở frontend, chúng ta thêm nó với trạng thái "valid"
    api_key_manager.add_key(new_key.strip(), status="valid")
    return RedirectResponse(url="/api/admin/gemini-keys", status_code=303)

@router.post("/admin/add-keys-bulk")
async def add_keys_bulk(request: Request, keys: list[str] = Body(..., embed=True), user: str = Depends(get_current_admin)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    added_count = 0
    for key in keys:
        # The add_key method should ideally prevent duplicates.
        # Assuming it does, or we add a check here.
        api_key_manager.add_key(key.strip(), status="valid")
        added_count += 1
        
    return JSONResponse({"success": True, "message": f"{added_count} keys added successfully."})

@router.post("/admin/delete-key")
async def delete_key(request: Request, key_to_delete: str = Form(...), user: str = Depends(get_current_admin)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    api_key_manager.delete_key(key_to_delete)
    return RedirectResponse(url="/api/admin/gemini-keys", status_code=303)

@router.post("/admin/validate-key")
async def validate_key(request: Request, new_key: str = Form(...), user: str = Depends(get_current_admin)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        # Cấu hình tạm thời với key mới để xác thực
        genai.configure(api_key=new_key.strip())
        # Thử một lệnh gọi API nhẹ nhàng, ví dụ như liệt kê các model
        # Nếu lệnh này thành công, key được coi là hợp lệ
        models = [m for m in genai.list_models()]
        print(f"Key validation successful. Found models.")
        return JSONResponse({"valid": True})
    except (google_exceptions.PermissionDenied, google_exceptions.Unauthenticated) as e:
        # Lỗi cụ thể cho key không hợp lệ hoặc hết hạn
        print(f"Key validation failed: Invalid API Key. Error: {e}")
        return JSONResponse({"valid": False, "error": "API Key không hợp lệ hoặc đã hết hạn. Vui lòng kiểm tra lại."})
    except Exception as e:
        # Bắt các lỗi khác có thể xảy ra (ví dụ: lỗi mạng)
        print(f"An unexpected error occurred during key validation: {e}")
        return JSONResponse({"valid": False, "error": "Đã xảy ra lỗi không mong muốn khi xác thực key."})

# --- Helper function for bulk validation (sync) ---
def _validate_key_sync(key: str):
    """Synchronous function to validate a single API key."""
    try:
        genai.configure(api_key=key)
        # Lightweight API call to validate
        [m for m in genai.list_models()]
        return key, True
    except Exception:
        return key, False

@router.post("/admin/validate-keys-bulk")
async def validate_keys_bulk(request: Request, keys: list[str] = Body(..., embed=True), user: str = Depends(get_current_admin)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Create tasks to run the synchronous validation function in a thread pool
    tasks = [asyncio.to_thread(_validate_key_sync, key.strip()) for key in keys if key.strip()]
    
    # Wait for all validation tasks to complete
    results = await asyncio.gather(*tasks)

    # Process the results
    valid_keys = [key for key, is_valid in results if is_valid]
    invalid_keys = [key for key, is_valid in results if not is_valid]
            
    return JSONResponse({"valid_keys": valid_keys, "invalid_keys": invalid_keys})

@router.post("/admin/export-keys")
async def export_keys(request: Request, otp: str = Form(...), user: str = Depends(get_current_admin)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    if not otp_manager.verify(otp):
        raise HTTPException(status_code=401, detail="Invalid OTP")

    keys = api_key_manager.get_all_keys()
    keys_text = "\n".join([key_info['key'] for key_info in keys])
    
    return Response(
        content=keys_text,
        media_type="text/plain",
        headers={"Content-Disposition": "attachment; filename=gemini_api_keys.txt"}
    )

@router.post("/admin/check-key-status")
async def check_key_status(request: Request, key_to_check: str = Form(...), user: str = Depends(get_current_admin)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    new_status = "invalid"
    try:
        genai.configure(api_key=key_to_check.strip())
        # Lệnh gọi API nhẹ nhàng để kiểm tra
        [m for m in genai.list_models()]
        new_status = "valid"
    except Exception as e:
        print(f"Status check failed for key ending in ...{key_to_check[-4:]}: {e}")
        new_status = "invalid"
    
    # Cập nhật trạng thái trong manager
    api_key_manager.update_key_status(key_to_check, new_status)
    
    return JSONResponse({"status": new_status})

@router.get("/admin/history", response_class=HTMLResponse)
async def view_history(
    request: Request,
    db: Session = Depends(get_db),
    user: str = Depends(get_current_admin),
    email: str = Query(None),
    start_date: str = Query(None),
    end_date: str = Query(None)
):
    if not user:
        return RedirectResponse(url="/api/admin/login")

    query = db.query(UsageLog)

    if email:
        query = query.filter(UsageLog.user_email.ilike(f"%{email}%"))
    if start_date:
        try:
            start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(UsageLog.timestamp >= start_datetime)
        except ValueError:
            pass # Bỏ qua nếu định dạng ngày không hợp lệ
    if end_date:
        try:
            # Add 1 day to the end_date to include all records on that day
            end_datetime = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            # Use '<' to get all records before the start of the next day
            query = query.filter(UsageLog.timestamp < end_datetime)
        except ValueError:
            pass # Ignore if the date format is invalid

    logs = query.order_by(UsageLog.timestamp.desc()).all()

    # Helper function to format JSON with Unicode characters preserved
    def pretty_json_formatter(data):
        return json.dumps(data, indent=2, ensure_ascii=False)

    return templates.TemplateResponse("admin/history.html", {
        "request": request,
        "logs": logs,
        "filters": {"email": email, "start_date": start_date, "end_date": end_date},
        "pretty_json": pretty_json_formatter
    })

@router.get("/admin/clients", response_class=HTMLResponse)
async def manage_clients(request: Request, db: Session = Depends(get_db), user: str = Depends(get_current_admin)):
    if not user:
        return RedirectResponse(url="/api/admin/login")
    
    # Check for newly created client info in session to display it once
    new_client_info = request.session.pop("new_client_info", None)

    clients = client_app_manager.get_client_apps(db)
    
    context = {
        "request": request,
        "clients": clients
    }
    if new_client_info:
        context["new_client"] = new_client_info["client"]
        context["new_client_secret"] = new_client_info["secret"]

    return templates.TemplateResponse("admin/manage_clients.html", context)

@router.post("/admin/clients/add")
async def add_client_app(request: Request, name: str = Form(...), db: Session = Depends(get_db), user: str = Depends(get_current_admin)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    new_client, new_secret = client_app_manager.create_client_app(db, name=name.strip())
    
    # Store the new client info in the session to display after redirect
    request.session["new_client_info"] = {
        "client": {"name": new_client.name, "client_id": new_client.client_id},
        "secret": new_secret
    }
    
    return RedirectResponse(url="/api/admin/clients", status_code=303)

@router.post("/admin/clients/delete")
async def delete_client_app(request: Request, client_id: str = Form(...), db: Session = Depends(get_db), user: str = Depends(get_current_admin)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    client_app_manager.delete_client_app(db, client_id)
    return RedirectResponse(url="/api/admin/clients", status_code=303)

@router.get("/admin/login-history", response_class=HTMLResponse)
async def view_login_history(
    request: Request,
    db: Session = Depends(get_db),
    user: str = Depends(get_current_admin),
    username: str = Query(None),
    start_date: str = Query(None),
    end_date: str = Query(None)
):
    if not user:
        return RedirectResponse(url="/api/admin/login")

    # --- Set default date filters to today if not provided ---
    if start_date is None and end_date is None:
        today = datetime.now().strftime("%Y-%m-%d")
        start_date = today
        end_date = today

    query = db.query(AdminLoginHistory)

    if username:
        query = query.filter(AdminLoginHistory.username.ilike(f"%{username}%"))
    if start_date:
        try:
            start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(AdminLoginHistory.timestamp >= start_datetime)
        except ValueError:
            pass
    if end_date:
        try:
            end_datetime = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            query = query.filter(AdminLoginHistory.timestamp < end_datetime)
        except ValueError:
            pass

    history = query.order_by(AdminLoginHistory.timestamp.desc()).all()

    return templates.TemplateResponse("admin/login_history.html", {
        "request": request,
        "history": history,
        "filters": {"username": username, "start_date": start_date, "end_date": end_date}
    })
