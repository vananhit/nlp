import os
import json
import uuid
import threading
from google.cloud import language_v2
from google.oauth2 import service_account

class GcpServiceAccountManager:
    def __init__(self, creds_dir="backend/credentials/service_accounts"):
        self.creds_dir = creds_dir
        os.makedirs(self.creds_dir, exist_ok=True)
        self.accounts = self._load_accounts()
        self.current_index = 0
        self.lock = threading.Lock()

    def _load_accounts(self):
        """Quét thư mục và tải thông tin từ các tệp service account hợp lệ."""
        account_list = []
        for filename in os.listdir(self.creds_dir):
            if filename.endswith(".json"):
                file_path = os.path.join(self.creds_dir, filename)
                try:
                    with open(file_path, "r") as f:
                        data = json.load(f)
                    # Kiểm tra các trường cơ bản để xác nhận đây là tệp service account
                    if "project_id" in data and "client_email" in data:
                        account_list.append({
                            "filename": filename,
                            "project_id": data.get("project_id"),
                            "client_email": data.get("client_email"),
                            "file_path": file_path
                        })
                except (json.JSONDecodeError, KeyError) as e:
                    print(f"Could not load or parse {filename}: {e}")
        return account_list

    def get_all_accounts_info(self):
        """Lấy danh sách thông tin an toàn của tất cả các account."""
        with self.lock:
            # Chỉ trả về thông tin cần thiết cho UI, không bao gồm file_path
            return [{"filename": acc["filename"], "project_id": acc["project_id"], "client_email": acc["client_email"]} for acc in self.accounts]

    def add_account(self, file_stream):
        """Lưu một tệp service account mới và tải lại danh sách."""
        try:
            # Đọc nội dung tệp upload
            content = file_stream.read().decode("utf-8")
            data = json.loads(content)

            # Xác thực cấu trúc cơ bản
            if "project_id" not in data or "client_email" not in data:
                raise ValueError("Invalid service account file format.")

            # Tạo tên tệp duy nhất để tránh ghi đè
            filename = f"{uuid.uuid4()}.json"
            file_path = os.path.join(self.creds_dir, filename)

            with open(file_path, "w") as f:
                f.write(content)

            # Tải lại danh sách account sau khi thêm
            with self.lock:
                self.accounts = self._load_accounts()
            return {"success": True, "filename": filename}
        except Exception as e:
            print(f"Error adding service account: {e}")
            return {"success": False, "error": str(e)}

    def delete_account(self, filename: str):
        """Xóa một tệp service account và tải lại danh sách."""
        with self.lock:
            file_path = os.path.join(self.creds_dir, filename)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    # Tải lại danh sách sau khi xóa
                    self.accounts = self._load_accounts()
                    return True
                except OSError as e:
                    print(f"Error deleting file {filename}: {e}")
                    return False
            return False

    def get_next_client(self) -> language_v2.LanguageServiceClient:
        """
        Lấy client đã xác thực bằng service account tiếp theo (xoay vòng).
        """
        with self.lock:
            if not self.accounts:
                raise Exception("No valid GCP service accounts configured.")
            
            if self.current_index >= len(self.accounts):
                self.current_index = 0
            
            account_to_use = self.accounts[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.accounts)
            
            print(f"Using GCP Service Account: {account_to_use['client_email']}")
            
            # Khởi tạo client một cách tường minh từ tệp
            credentials = service_account.Credentials.from_service_account_file(account_to_use['file_path'])
            client = language_v2.LanguageServiceClient(credentials=credentials)
            return client

# Tạo một instance duy nhất (singleton) để toàn bộ ứng dụng sử dụng
gcp_sa_manager = GcpServiceAccountManager()
