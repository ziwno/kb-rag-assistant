import axios from "axios";
import { TOKEN_KEY } from "@/store/authStore";

// 浏览器访问后端的地址。
// - 本地开发: 不设置时默认连 http://localhost:8000
// - Docker 生产(经反代): 构建时传 NEXT_PUBLIC_API_BASE_URL=""，走同源，由 Nginx 转发 /api
const _configured = process.env.NEXT_PUBLIC_API_BASE_URL;
export const API_BASE_URL = _configured === "" ? "" : _configured || "http://localhost:8000";

export const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  timeout: 120000,
  headers: { "Content-Type": "application/json" },
});

// 请求拦截: 自动附加 JWT
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = window.localStorage.getItem(TOKEN_KEY);
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 响应拦截: 401 时清除本地凭证并跳转登录页
api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      window.localStorage.removeItem(TOKEN_KEY);
      if (!window.location.pathname.startsWith("/login")) {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);
