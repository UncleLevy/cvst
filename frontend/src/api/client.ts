import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";

const API_URL: string = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000/api";

export const ACCESS_KEY = "access_token";
export const REFRESH_KEY = "refresh_token";

const api = axios.create({ baseURL: API_URL });

export function setTokens(access: string, refresh?: string) {
  localStorage.setItem(ACCESS_KEY, access);
  if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

export function hasToken(): boolean {
  return Boolean(localStorage.getItem(ACCESS_KEY));
}

api.interceptors.request.use((config) => {
  const token = localStorage.getItem(ACCESS_KEY);
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

let refreshPromise: Promise<string> | null = null;

async function refreshAccessToken(): Promise<string> {
  const refresh = localStorage.getItem(REFRESH_KEY);
  if (!refresh) throw new Error("No refresh token");
  const res = await axios.post(`${API_URL}/auth/token/refresh/`, { refresh });
  const access = res.data.access as string;
  localStorage.setItem(ACCESS_KEY, access);
  return access;
}

// On a 401, try once to refresh the access token and replay the request.
// If that fails, clear the session and tell the app to go to the login page.
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as (InternalAxiosRequestConfig & { _retry?: boolean }) | undefined;
    const url = original?.url ?? "";
    const isAuthCall = url.includes("/auth/login") || url.includes("/auth/token/refresh");

    if (error.response?.status === 401 && original && !original._retry && !isAuthCall) {
      original._retry = true;
      try {
        refreshPromise ??= refreshAccessToken().finally(() => {
          refreshPromise = null;
        });
        const access = await refreshPromise;
        original.headers.Authorization = `Bearer ${access}`;
        return api(original);
      } catch {
        clearTokens();
        window.dispatchEvent(new Event("auth:logout"));
      }
    }
    return Promise.reject(error);
  },
);

/** Turn an axios/DRF error into a readable one-line message. */
export function errorMessage(err: unknown, fallback = "Something went wrong."): string {
  if (axios.isAxiosError(err)) {
    if (!err.response) return "Cannot reach the server. Is the backend running?";
    const data = err.response.data;
    if (data && typeof data === "object") {
      const obj = data as Record<string, unknown>;
      if (typeof obj.detail === "string") return obj.detail;
      const parts = Object.entries(obj).map(([key, value]) => {
        const text = Array.isArray(value) ? value.join(" ") : String(value);
        return key === "non_field_errors" ? text : `${key}: ${text}`;
      });
      if (parts.length) return parts.join(" · ");
    }
  }
  return fallback;
}

export default api;
