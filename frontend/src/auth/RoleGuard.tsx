import { Navigate, Outlet, useLocation } from "react-router-dom";

import { useAuth } from "./AuthContext";
import type { UserRole } from "./session";

interface RoleGuardProps {
  allow: UserRole[];
}

export function RoleGuard({ allow }: RoleGuardProps) {
  const location = useLocation();
  const { user } = useAuth();

  if (!user) {
    return <Navigate to="/sign-in" replace state={{ from: location.pathname }} />;
  }

  if (!allow.includes(user.role)) {
    return <Navigate to={roleHome(user.role)} replace />;
  }

  return <Outlet />;
}

function roleHome(role: UserRole): string {
  if (role === "tenant") return "/tenant/home";
  if (role === "provider") return "/provider/jobs";
  return "/portfolio";
}
