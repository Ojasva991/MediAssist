import { createContext, useContext, useEffect, useState, useCallback } from "react";

const AuthContext = createContext(null);
const STORAGE_KEY = "mediassist_session";

/**
 * The backend spec exposes /passport/{user_id} but no dedicated auth
 * endpoint. This context provides a lightweight local session: the person
 * signs in with a name + email, we derive a stable user_id from the email,
 * and persist it so refreshes keep them logged in. Swap the `login`
 * implementation here if/when a real auth endpoint is added.
 */
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

  const login = useCallback(({ name, email }) => {
    const userId = email.trim().toLowerCase().replace(/[^a-z0-9]/g, "_");
    const session = { userId, name: name.trim(), email: email.trim() };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
    setUser(session);
    return session;
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
