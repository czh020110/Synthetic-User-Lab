import axios from 'axios';
import { ApiClientError } from '../lib/api-error';

const client = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
});

// FastAPI 校验错误 detail 是 [{loc, msg, type}, ...]；普通错误 detail 是字符串。
// 统一提取为可读 message，避免直接把数组塞进 Error 导致 '[object Object]'。
function extractErrorMessage(detail: unknown, fallback: string): string {
  if (typeof detail === 'string' && detail.trim()) {
    return detail;
  }
  if (Array.isArray(detail)) {
    const parts = detail
      .map((item) => {
        if (typeof item === 'string') return item;
        if (item && typeof item === 'object') {
          const loc = Array.isArray((item as { loc?: unknown }).loc)
            ? (item as { loc: unknown[] }).loc.join('.')
            : '';
          const msg = (item as { msg?: unknown }).msg;
          return loc ? `${loc}: ${msg}` : String(msg ?? '');
        }
        return String(item);
      })
      .filter(Boolean);
    if (parts.length) return parts.join('; ');
  }
  return fallback;
}

// 响应拦截器：自动解包 ApiResponse.data
client.interceptors.response.use(
  (res) => {
    const data = res.data;
    if (data.success === false) {
      return Promise.reject(
        new ApiClientError(data.message || 'API Error', {
          status: res.status,
          detail: data,
        })
      );
    }
    return data.data ?? null;
  },
  (err) => {
    const status = err.response?.status;
    const detail = err.response?.data?.detail;
    const message = extractErrorMessage(detail, err.message);
    return Promise.reject(
      new ApiClientError(message, {
        status,
        detail: err.response?.data,
      })
    );
  }
);

export default client;
