from __future__ import annotations

# ============================ 截图服务路由模块 ============================ #
# 模块功能: 提供截图文件的 HTTP 服务端点
# 模块接口说明: GET /screenshots/{run_id}/{filename} 返回 PNG 文件

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from backend.core.config import get_settings

router = APIRouter(prefix="/screenshots", tags=["screenshots"])


@router.get("/{run_id}/{filename}")
async def serve_screenshot(run_id: str, filename: str) -> FileResponse:
    """返回指定 run 的截图文件。"""
    settings = get_settings()
    file_path = (settings.screenshot_dir / run_id / filename).resolve()

    # 路径遍历防护：确保请求路径不逃离 screenshot_dir（加 / 防止兄弟目录前缀匹配）
    if not str(file_path).startswith(str(settings.screenshot_dir.resolve()) + "/"):
        if file_path != settings.screenshot_dir.resolve():
            raise HTTPException(status_code=403, detail="Access denied")

    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Screenshot not found")

    return FileResponse(str(file_path), media_type="image/png")
