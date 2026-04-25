import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]  # 计算根项目绝对路径(0当前父目录,1往上.2再往上)
# 等价于:BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# /backend/core/config.py

def load_dotenv(dotenv_path: Path = BASE_DIR / ".env") -> None:
    """从项目根目录 .env 加载环境变量。"""

    if not dotenv_path.exists():
        return

    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


load_dotenv()

class ModelRouter:
    def __init__(self):
        self.model_provider = os.getenv("MODEL_PROVIDER", "openai")
        self.base_url = ""
        self.api_key = ""
        self.model_name = ""

    def allocate_model(self):
        if self.model_provider == "openai":
            self.model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-4o")
            self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
            self.api_key = os.getenv("OPENAI_API_KEY", "")
        elif self.model_provider == "dashscope":
            self.model_name = os.getenv("DASHSCOPE_MODEL_NAME", "qwen3.5-flash")
            self.api_key = os.getenv("DASHSCOPE_API_KEY", "")
            self.base_url = os.getenv("DASHSCOPE_BASE_URL", "")


def get_model_router():
    router = ModelRouter()
    router.allocate_model()
    return router

