import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { login as apiLogin, signup as apiSignup } from "@/api/auth";

const AuthContext = createContext(null);
const STORAGE_KEY = "mediassist_session";

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        setUser(JSON.parse(stored));
      } catch {
        localStorage.removeItem(STORAGE_KEY);
      }
    }
    setIsLoading(false);
  }, []);

  function persistSession(result) {
    const session = {
      userId: result.user_id,
      name: result.name,
      email: result.email,
      accessToken: result.access_token,
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
    setUser(session);
    return session;
  }

  const login = useCallback(async ({ email, password }) => {
    const result = await apiLogin({ email, password });
    return persistSession(result);
  }, []);

  const signup = useCallback(async ({ name, email, password }) => {
    const result = await apiSignup({ name, email, password });
    return persistSession(result);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, isLoading, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}