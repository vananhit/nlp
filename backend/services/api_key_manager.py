import json
import threading
import os

# --- API Key Manager ---
class ApiKeyManager:
    def __init__(self, keys_file_path):
        self.keys_file_path = keys_file_path
        self.keys = self._load_keys()
        self.current_index = 0
        self.lock = threading.Lock()

    def _load_keys(self):
        """
        Tải các key từ file JSON.
        Tự động chuyển đổi cấu trúc dữ liệu cũ (list of strings) sang mới (list of dicts).
        """
        try:
            if not os.path.exists(self.keys_file_path):
                with open(self.keys_file_path, "w") as f:
                    json.dump({"keys": []}, f)
                return []

            with open(self.keys_file_path, "r") as f:
                data = json.load(f)
                keys_data = data.get("keys", [])

            # Kiểm tra và chuyển đổi cấu trúc dữ liệu nếu cần
            if keys_data and isinstance(keys_data[0], str):
                print("Old key format detected. Converting to new format.")
                new_keys_data = [{"key": key, "status": "unchecked"} for key in keys_data]
                self.keys = new_keys_data
                self._save_keys() # Lưu lại ngay sau khi chuyển đổi
                return new_keys_data
            
            return keys_data
        except Exception as e:
            print(f"Error loading API keys: {e}.")
            return []

    def get_next_key(self):
        """
        Lấy key hợp lệ tiếp theo trong danh sách (xoay vòng và thread-safe).
        Chỉ xoay vòng qua các key có trạng thái là 'valid'.
        """
        with self.lock:
            valid_keys = [k for k in self.keys if k.get("status") == "valid"]
            if not valid_keys:
                print("Error: No valid API keys available.")
                return None
            
            # Logic xoay vòng chỉ trên các key hợp lệ
            # Điều này phức tạp hơn một chút so với trước đây
            # Một cách tiếp cận đơn giản là chọn một key ngẫu nhiên từ các key hợp lệ
            # Hoặc duy trì một index riêng cho các key hợp lệ.
            # Để đơn giản, chúng ta sẽ dùng xoay vòng trên danh sách đã lọc.
            if self.current_index >= len(valid_keys):
                self.current_index = 0
            
            key_info = valid_keys[self.current_index]
            self.current_index = (self.current_index + 1) % len(valid_keys)
            return key_info["key"]

    def get_all_keys(self):
        """Lấy tất cả các đối tượng key hiện tại."""
        return self.keys

    def add_key(self, new_key, status="unchecked"):
        """Thêm một key mới và lưu vào file."""
        with self.lock:
            # Kiểm tra xem key đã tồn tại chưa
            if any(k.get("key") == new_key for k in self.keys):
                return False
            
            self.keys.append({"key": new_key, "status": status})
            self._save_keys()
            return True

    def delete_key(self, key_to_delete):
        """Xóa một key và lưu vào file."""
        with self.lock:
            original_length = len(self.keys)
            self.keys = [k for k in self.keys if k.get("key") != key_to_delete]
            if len(self.keys) < original_length:
                self._save_keys()
                return True
        return False

    def update_key_status(self, key_to_update, new_status):
        """Cập nhật trạng thái của một key cụ thể."""
        with self.lock:
            key_found = False
            for key_info in self.keys:
                if key_info.get("key") == key_to_update:
                    key_info["status"] = new_status
                    key_found = True
                    break
            if key_found:
                self._save_keys()
            return key_found

    def _save_keys(self):
        """Lưu danh sách key hiện tại vào file JSON."""
        with open(self.keys_file_path, "w") as f:
            json.dump({"keys": self.keys}, f, indent=2)

# Tạo một instance duy nhất (singleton) của manager để toàn bộ ứng dụng sử dụng
# Xác định đường dẫn tuyệt đối đến thư mục chứa file này (services)
current_dir = os.path.dirname(os.path.abspath(__file__))
# Xây dựng đường dẫn tuyệt đối đến file api_keys.json, nằm ngay trong thư mục backend
keys_file_path = os.path.join(current_dir, "..", "api_keys.json")

api_key_manager = ApiKeyManager(keys_file_path=keys_file_path)
