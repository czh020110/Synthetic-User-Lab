export class ApiClientError extends Error {
  status?: number;
  detail?: unknown;

  constructor(message: string, options?: { status?: number; detail?: unknown }) {
    super(message);
    this.name = 'ApiClientError';
    this.status = options?.status;
    this.detail = options?.detail;
    Object.setPrototypeOf(this, ApiClientError.prototype);
  }
}

export function isApiClientError(error: unknown): error is ApiClientError {
  return error instanceof ApiClientError;
}

export function hasStatus(error: unknown, status: number): boolean {
  return isApiClientError(error) && error.status === status;
}

export function getErrorMessage(error: unknown, fallback = '请求失败，请稍后重试'): string {
  if (typeof error === 'string' && error.trim()) {
    return error;
  }
  if (isApiClientError(error) && error.message.trim()) {
    return error.message;
  }
  if (error instanceof Error && error.message.trim()) {
    return error.message;
  }
  return fallback;
}
