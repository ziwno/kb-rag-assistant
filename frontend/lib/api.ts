import axios from "axios";
import { TOKEN_KEY } from "@/store/authStore";

// 浏览器访问后端的地址。Docker 部署时前端容器内通过浏览器直接访问宿主机端口。
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

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
