/**
 * 将后端返回的截图绝对路径转为前端可访问的 API URL。
 *
 * 后端路径格式: /absolute/path/screenshots/{run_id}/step-N-before.png
 * 转换为: /api/v1/screenshots/{run_id}/step-N.png
 */
export function screenshotPathToUrl(path: string | null | undefined): string | null {
  if (!path) return null;
  const match = path.match(/screenshots\/([^/]+)\/(.+\.png)$/);
  if (!match) return null;
  return `/api/v1/screenshots/${match[1]}/${match[2]}`;
}
