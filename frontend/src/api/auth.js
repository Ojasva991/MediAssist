import { apiClient } from "./client";

/**
 * Wraps the backend's real auth endpoints (app/routes/auth.py).
 * Both return: { access_token, token_type, user_id, name, email }
 */

/** POST /auth/signup */
export async function signup({ name, email, password }) {
  const { data } = await apiClient.post("/auth/signup", { name, email, password });
  return data;
}

/** POST /auth/login */
export async function login({ email, password }) {
  const { data } = await apiClient.post("/auth/login", { email, password });
  return data;
}
