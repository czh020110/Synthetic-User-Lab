import { QueryCache, QueryClient } from '@tanstack/react-query';
import { message } from 'antd';
import { ApiClientError, getErrorMessage } from './api-error';

const NO_RETRY_STATUSES = new Set([400, 401, 403, 404, 409, 422]);

function shouldRetryRequest(failureCount: number, error: unknown): boolean {
  if (failureCount >= 1) {
    return false;
  }
  if (error instanceof ApiClientError && error.status && NO_RETRY_STATUSES.has(error.status)) {
    return false;
  }
  return true;
}

export const queryClient = new QueryClient({
  queryCache: new QueryCache({
    onError: (error, query) => {
      if (query.state.data !== undefined) {
        return;
      }
      if (query.meta?.silentError === true) {
        return;
      }
      message.error(getErrorMessage(error));
    },
  }),
  defaultOptions: {
    queries: {
      retry: shouldRetryRequest,
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: false,
    },
  },
});
