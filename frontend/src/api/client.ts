import axios from 'axios';

const client = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
});

// 响应拦截器：自动解包 ApiResponse.data
client.interceptors.response.use(
  (res) => {
    const data = res.data;
    if (data.success === false) {
      return Promise.reject(new Error(data.message || 'API Error'));
    }
    return data.data ?? null
  },
  (err) => {
    const message = err.response?.data?.detail || err.message;
    return Promise.reject(new Error(message));
  }
);

export default client;
