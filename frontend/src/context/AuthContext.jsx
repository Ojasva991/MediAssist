import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { login as apiLogin, signup as apiSignup } from "@/api/auth";

const AuthContext = createContext(null);
const STORAGE_KEY = "mediassist_session";

/**
 * TEMPORARY MINIMAL PATCH - real backend auth, placeholder UI.
 *
 * The backend now requires a real account + JWT (see app/routes/auth.py
 * and app/auth/dependencies.py) - the old local-only session no longer
 * works, since /passport/* calls without a valid token get rejected
 * with 401.
 *
 * This keeps the EXISTING single-form login UX (name + email, now also
 * + password) working by trying login first, then falling back to
 * signup if no account exists yet - so today's one-page flow still
 * "just works" without a separate signup screen.
 *
 * This is explicitly a stopgap. When the premium UI pass happens, this
 * should become real separate Login / Signup screens with their own
 * validation and error states, per the plan already agreed on.
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

  const login = useCallback(async ({ name, email, password }) => {
    let result;
    try {
      result = await apiLogin({ email, password });
    } catch (loginError) {
      // No account yet for this email -> try creating one, so the
      // existing single-form UX doesn't need a separate signup step.
      try {
        result = await apiSignup({ name, email, password });
      } catch (signupError) {
        // If signup failed because the account already exists, the
        // real problem was an incorrect password on login - surface
        // that message, it's more useful than "email already exists".
        if (signupError.status === 409) {
          throw loginError;
        }
        throw signupError;
      }
    }

    const session = {
      userId: result.user_id,
      name: result.name,
      email: result.email,
      accessToken: result.access_token,
    };
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
