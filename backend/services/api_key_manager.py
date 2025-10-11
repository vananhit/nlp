import json
import threading
import os
import time
import asyncio
from collections import deque

# --- Rate-Limited API Key Manager (NEW) ---
class RateLimitedApiKeyManager:
    def __init__(self, keys_file_path=os.path.join("backend", "api_keys.json"), rate_limit_seconds=6):
        """
        Khởi tạo manager với cơ chế điều tiết.
        :param keys_file_path: Đường dẫn đến file JSON chứa API keys.
        :param rate_limit_seconds: Thời gian tối thiểu (giây) giữa các lần sử dụng của cùng một key.
                                  (Mặc định là 6 giây cho 10 requests/phút).
        """
        self.keys_file_path = keys_file_path
        self.rate_limit_seconds = rate_limit_seconds
        self.lock = asyncio.Lock()  # Sử dụng asyncio.Lock cho môi trường bất đồng bộ

        # Hàng đợi (deque) để lưu trữ (key, last_used_time)
        # Sử dụng deque vì nó hiệu quả cho việc thêm/xóa ở cả hai đầu
        self._keys_queue = deque()
        self._load_keys() # Tải và khởi tạo hàng đợi

    def _load_keys(self):
        """
        Tải các key từ file JSON và khởi tạo hàng đợi.
        Mỗi key được lưu dưới dạng một tuple (key_string, last_used_time).
        Ban đầu, last_used_time là 0 để key có thể được sử dụng ngay lập tức.
        """
        try:
            if not os.path.exists(self.keys_file_path):
                with open(self.keys_file_path, "w") as f:
                    json.dump({"keys": []}, f)
                self.keys_config = []
                self._keys_queue.clear()
                return

            with open(self.keys_file_path, "r") as f:
                data = json.load(f)
                self.keys_config = data.get("keys", [])

            # Chuyển đổi cấu trúc dữ liệu cũ nếu cần
            if self.keys_config and isinstance(self.keys_config[0], str):
                print("Old key format detected. Converting to new format.")
                self.keys_config = [{"key": key, "status": "unchecked"} for key in self.keys_config]
                self._save_keys()

            # Chỉ tải các key hợp lệ vào hàng đợi
            valid_keys = [k_info["key"] for k_info in self.keys_config if k_info.get("status") == "valid"]
            self._keys_queue = deque((key, 0) for key in valid_keys)
            print(f"Loaded {len(self._keys_queue)} valid API keys into the rate-limited manager.")

        except Exception as e:
            print(f"Error loading API keys: {e}.")
            self.keys_config = []
            self._keys_queue.clear()

    async def get_next_key_async(self):
        """
        Lấy key hợp lệ tiếp theo một cách bất đồng bộ với cơ chế điều tiết.
        """
        async with self.lock:
            if not self._keys_queue:
                print("Error: No valid API keys available in the queue.")
                # Có thể raise Exception ở đây để xử lý ở nơi gọi
                raise ValueError("No valid API keys available.")

            while True:
                # Lấy key ở đầu hàng đợi (key đã nghỉ lâu nhất)
                key, last_used_time = self._keys_queue[0]
                current_time = time.monotonic()
                elapsed_time = current_time - last_used_time

                if elapsed_time >= self.rate_limit_seconds:
                    # Key này đã "nguội", sẵn sàng để sử dụng
                    # Xoay vòng: lấy key ra khỏi đầu và đưa xuống cuối
                    self._keys_queue.popleft()
                    self._keys_queue.append((key, current_time)) # Cập nhật thời gian sử dụng
                    return key

                # Nếu key vẫn còn "nóng", tính thời gian phải chờ
                wait_time = self.rate_limit_seconds - elapsed_time
                # print(f"Rate limit hit. Waiting for {wait_time:.2f} seconds...")
                await asyncio.sleep(wait_time)
                # Vòng lặp sẽ thử lại với chính key này, lúc này chắc chắn đã hợp lệ

    def get_all_keys(self):
        """Lấy tất cả các đối tượng key hiện tại từ file config."""
        return self.keys_config

    def add_key(self, new_key, status="unchecked"):
        """Thêm một key mới và lưu vào file, sau đó reload lại hàng đợi."""
        # Sử dụng threading.Lock ở đây vì các thao tác file là đồng bộ
        with threading.Lock():
            if any(k.get("key") == new_key for k in self.keys_config):
                return False
            self.keys_config.append({"key": new_key, "status": status})
            self._save_keys()
            self._load_keys() # Tải lại để cập nhật hàng đợi
            return True

    def delete_key(self, key_to_delete):
        """Xóa một key, lưu file và reload lại hàng đợi."""
        with threading.Lock():
            original_length = len(self.keys_config)
            self.keys_config = [k for k in self.keys_config if k.get("key") != key_to_delete]
            if len(self.keys_config) < original_length:
                self._save_keys()
                self._load_keys() # Tải lại
                return True
        return False

    def update_key_status(self, key_to_update, new_status):
        """Cập nhật trạng thái của một key và reload lại hàng đợi."""
        with threading.Lock():
            key_found = False
            for key_info in self.keys_config:
                if key_info.get("key") == key_to_update:
                    key_info["status"] = new_status
                    key_found = True
                    break
            if key_found:
                self._save_keys()
                self._load_keys() # Tải lại
            return key_found

    def _save_keys(self):
        """Lưu danh sách key hiện tại vào file JSON."""
        with open(self.keys_file_path, "w") as f:
            json.dump({"keys": self.keys_config}, f, indent=2)


# --- API Key Manager (OLD - for reference, will be replaced) ---
class ApiKeyManager:
    def __init__(self, keys_file_path = os.path.join("backend", "api_keys.json")):
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
# api_key_manager = ApiKeyManager() # Thay thế bằng manager mới
api_key_manager = RateLimitedApiKeyManager()
