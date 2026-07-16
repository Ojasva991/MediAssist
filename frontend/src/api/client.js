import axios from "axios";

/**
 * Base URL for the MediAssist FastAPI backend.
 * Override via .env -> VITE_API_BASE_URL to point at a local backend during dev.
 */
export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "https://mediassist-3jpl.onrender.com";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // Render free-tier instances can cold-start slowly
  headers: {
    "Content-Type": "application/json",
  },
});

// Attach a request id / timestamp hook point (auth tokens would go here later)
apiClient.interceptors.request.use((config) => {
  return config;
});

// Normalize errors into a predictable shape the UI can render directly.
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const isTimeout = error.code === "ECONNABORTED";
    const status = error.response?.status;
    const backendMessage =
      error.response?.data?.detail || error.response?.data?.message;

    let message = "Something went wrong. Please try again.";
    if (isTimeout) {
      message =
        "The server is taking longer than usual to respond (it may be waking up from sleep). Please try again in a moment.";
    } else if (!error.response) {
      message = "Can't reach the MediAssist server. Check your connection and try again.";
    } else if (backendMessage) {
      message = backendMessage;
    } else if (status === 404) {
      message = "We couldn't find that record.";
    } else if (status >= 500) {
      message = "The server ran into a problem. Please try again shortly.";
    }

    return Promise.reject({
      status: status ?? null,
      message,
      raw: error,
    });
  }
);
