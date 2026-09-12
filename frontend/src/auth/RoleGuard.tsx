import { Navigate, Outlet, useLocation } from "react-router-dom";

import { getSessionRole, type UserRole } from "./session";

interface RoleGuardProps {
  allow: UserRole[];
}

export function RoleGuard({ allow }: RoleGuardProps) {
  const location = useLocation();
  const role = getSessionRole();

  if (!role) {
    return <Navigate to="/sign-in" replace state={{ from: location.pathname }} />;
  }

  if (!allow.includes(role)) {
    return <Navigate to="/" replace />;
  }

  return <Outlet />;
}
