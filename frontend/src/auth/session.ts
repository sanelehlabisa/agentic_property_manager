export type UserRole = "homeowner" | "manager" | "tenant" | "provider";

export interface SessionUser {
  id: string;
  email: string;
  name: string;
  role: UserRole;
}

export interface DemoSession {
  token: string;
  user: SessionUser;
}

const SESSION_KEY = "property_manager_demo_session";

export function getStoredSession(): DemoSession | null {
  const value = window.localStorage.getItem(SESSION_KEY);
  if (!value) return null;
  try {
    return JSON.parse(value) as DemoSession;
  } catch {
    window.localStorage.removeItem(SESSION_KEY);
    return null;
  }
}

export function storeSession(session: DemoSession): void {
  window.localStorage.setItem(SESSION_KEY, JSON.stringify(session));
}

export function clearStoredSession(): void {
  window.localStorage.removeItem(SESSION_KEY);
}

export function roleHome(role: UserRole): string {
  if (role === "tenant") return "/tenant/home";
  if (role === "provider") return "/provider/jobs";
  return "/portfolio";
}
