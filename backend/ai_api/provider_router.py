import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]


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
        if key:
            os.environ[key] = value


class ModelRouter:
    def __init__(self) -> None:
        self.model_provider = (os.getenv("MODEL_PROVIDER", "openai") or "openai").lower()
        self.model_name = ""
        self.base_url = ""
        self.api_key = ""
        self.fast_model_name = ""

    # 如果没有配置 fast model 则退回使用主模型,而不是一个意义不明的默认值
    def allocate_model(self) -> None:
        if self.model_provider == "openai":
            self.model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-4o") or "gpt-4o"
            self.fast_model_name = os.getenv("OPENAI_FAST_MODEL_NAME", self.model_name) or self.model_name
            self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
            self.api_key = os.getenv("OPENAI_API_KEY", "")
            return

        if self.model_provider == "dashscope":
            self.model_name = os.getenv("DASHSCOPE_MODEL_NAME", "qwen3.5-flash") or "qwen3.5-flash"
            self.fast_model_name = os.getenv("DASHSCOPE_FAST_MODEL_NAME", self.model_name) or self.model_name
            self.api_key = os.getenv("DASHSCOPE_API_KEY", "")
            self.base_url = os.getenv("DASHSCOPE_BASE_URL", "")


def get_model_router() -> ModelRouter:
    load_dotenv()
    router = ModelRouter()
    router.allocate_model()
    return router
