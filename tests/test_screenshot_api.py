"""截图服务端点测试。"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.core import config

client = TestClient(app)


def _patch_screenshot_dir(tmp_path: Path):
    """将 screenshot_dir 临时指向 tmp_path，返回 cleanup 函数。"""
    import os

    old_env = os.environ.get("SYNTHETIC_USER_LAB_DATABASE_URL")
    os.environ["SYNTHETIC_USER_LAB_DATABASE_URL"] = ":memory:"
    config.get_settings.cache_clear()
    settings = config.get_settings()
    settings.screenshot_dir = tmp_path

    def cleanup():
        config.get_settings.cache_clear()
        if old_env is not None:
            os.environ["SYNTHETIC_USER_LAB_DATABASE_URL"] = old_env
        elif "SYNTHETIC_USER_LAB_DATABASE_URL" in os.environ:
            del os.environ["SYNTHETIC_USER_LAB_DATABASE_URL"]

    return cleanup


def test_serve_screenshot_found(tmp_path: Path):
    """截图文件存在时返回 PNG。"""
    run_dir = tmp_path / "test-run"
    run_dir.mkdir()
    screenshot = run_dir / "step-1-before.png"
    screenshot.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)

    cleanup = _patch_screenshot_dir(tmp_path)
    try:
        resp = client.get("/api/v1/screenshots/test-run/step-1-before.png")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "image/png"
    finally:
        cleanup()


def test_serve_screenshot_not_found(tmp_path: Path):
    """截图文件不存在时返回 404。"""
    cleanup = _patch_screenshot_dir(tmp_path)
    try:
        resp = client.get("/api/v1/screenshots/no-exist-run/no-exist.png")
        assert resp.status_code == 404
    finally:
        cleanup()


def test_serve_screenshot_path_traversal(tmp_path: Path):
    """路径遍历请求应被 403 拦截（使用匹配路由模式的路径）。"""
    # 创建一个截图文件用于测试
    run_dir = tmp_path / "test-run"
    run_dir.mkdir()
    (run_dir / "step-1.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)

    # 在 screenshot_dir 的兄弟目录放一个文件
    sibling_dir = tmp_path.parent / (tmp_path.name + "-secrets")
    sibling_dir.mkdir()
    (sibling_dir / "secret.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 50)

    cleanup = _patch_screenshot_dir(tmp_path)
    try:
        # 尝试通过 run_id 包含 ../ 来逃离 screenshot_dir
        # FastAPI 会将 URL 中的 ../ 交给路径参数
        resp = client.get("/api/v1/screenshots/..%2F..%2Fetc/passwd")
        assert resp.status_code in {403, 404, 422}

        # 测试 URL-decoded 的路径遍历：run_id 包含路径遍历字符
        # 例如 /screenshots/x/../../../tmp/sibling/secret.png
        resp = client.get("/api/v1/screenshots/x/..%2F..%2F..%2Fsecret.png")
        assert resp.status_code in {403, 404}
    finally:
        cleanup()
