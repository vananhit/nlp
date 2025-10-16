import json
import os
import threading

class AppConfigManager:
    def __init__(self, config_path=os.path.join("backend", "app_config.json")):
        self.config_path = config_path
        self.lock = threading.Lock()
        self.config = self._load_config()

    def _load_config(self):
        """Tải cấu hình từ file JSON."""
        with self.lock:
            try:
                if not os.path.exists(self.config_path):
                    # Nếu file không tồn tại, tạo file với giá trị mặc định
                    default_config = {"rate_limit_seconds": 0.1}
                    with open(self.config_path, "w") as f:
                        json.dump(default_config, f, indent=2)
                    return default_config
                
                with open(self.config_path, "r") as f:
                    return json.load(f)
            except (IOError, json.JSONDecodeError) as e:
                print(f"Error loading config file: {e}. Using default config.")
                return {"rate_limit_seconds": 0.1}

    def get_config(self, key, default=None):
        """Lấy một giá trị cấu hình cụ thể."""
        return self.config.get(key, default)

    def update_config(self, key, value):
        """Cập nhật một giá trị cấu hình và lưu vào file."""
        with self.lock:
            self.config[key] = value
            try:
                with open(self.config_path, "w") as f:
                    json.dump(self.config, f, indent=2)
                return True
            except IOError as e:
                print(f"Error saving config file: {e}")
                return False

# Tạo một instance duy nhất (singleton) để toàn bộ ứng dụng sử dụng
app_config_manager = AppConfigManager()
