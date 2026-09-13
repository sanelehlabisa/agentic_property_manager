import { createContext, type ReactNode, useContext, useMemo, useState } from "react";

import { authenticateEmail } from "../api/auth";
import {
  clearStoredSession,
  getStoredSession,
  storeSession,
  type DemoSession,
  type SessionUser,
  type UserRole,
} from "./session";

interface SignInResult {
  requiresOnboarding: boolean;
  user?: SessionUser;
}

interface AuthContextValue {
  user: SessionUser | null;
  signIn: (
    email: string,
    details?: { name: string; role: UserRole },
  ) => Promise<SignInResult>;
  signOut: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<DemoSession | null>(getStoredSession);

  const value = useMemo<AuthContextValue>(
    () => ({
      user: session?.user ?? null,
      signIn: async (email, details) => {
        const response = await authenticateEmail({ email, ...details });
        if (response.requires_onboarding || !response.token || !response.user) {
          return { requiresOnboarding: true };
        }
        const nextSession = { token: response.token, user: response.user };
        storeSession(nextSession);
        setSession(nextSession);
        return { requiresOnboarding: false, user: response.user };
      },
      signOut: () => {
        clearStoredSession();
        setSession(null);
      },
    }),
    [session],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// The provider and hook intentionally share this small module.
// eslint-disable-next-line react-refresh/only-export-components
export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}
