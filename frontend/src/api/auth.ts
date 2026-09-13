import { jsonRequest } from "./client";
import type { User } from "./types";
import type { UserRole } from "../auth/session";

interface AuthRequest {
  email: string;
  name?: string;
  role?: UserRole;
}

interface AuthResponse {
  requires_onboarding: boolean;
  token: string | null;
  user: User | null;
}

export function authenticateEmail(data: AuthRequest): Promise<AuthResponse> {
  return jsonRequest<AuthResponse>("/auth/email", "POST", data);
}
