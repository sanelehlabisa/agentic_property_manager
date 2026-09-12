export type UserRole = "homeowner" | "manager" | "tenant" | "provider";

const SESSION_ROLE_KEY = "property_manager_demo_role";
const roles: UserRole[] = ["homeowner", "manager", "tenant", "provider"];

export function getSessionRole(): UserRole | null {
  const value = window.localStorage.getItem(SESSION_ROLE_KEY);
  return roles.includes(value as UserRole) ? (value as UserRole) : null;
}

export function setSessionRole(role: UserRole): void {
  window.localStorage.setItem(SESSION_ROLE_KEY, role);
}

export function clearSessionRole(): void {
  window.localStorage.removeItem(SESSION_ROLE_KEY);
}

export function roleHome(role: UserRole): string {
  if (role === "tenant") return "/tenant/home";
  if (role === "provider") return "/provider/jobs";
  return "/portfolio";
}
