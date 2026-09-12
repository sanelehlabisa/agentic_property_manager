import { Route, Routes } from "react-router-dom";

import { RoleGuard } from "../auth/RoleGuard";
import { AppShell } from "../components/AppShell";
import { HealthPage } from "../pages/HealthPage";
import { RolePreviewPage } from "../pages/RolePreviewPage";
import { SignInPlaceholderPage } from "../pages/SignInPlaceholderPage";

export function AppRouter() {
  return (
    <Routes>
      <Route index element={<HealthPage />} />
      <Route path="sign-in" element={<SignInPlaceholderPage />} />

      <Route element={<AppShell />}>
        <Route element={<RoleGuard allow={["homeowner", "manager"]} />}>
          <Route
            path="portfolio"
            element={<RolePreviewPage title="Property portfolio" />}
          />
        </Route>
        <Route element={<RoleGuard allow={["tenant"]} />}>
          <Route
            path="tenant/home"
            element={<RolePreviewPage title="Tenant home" />}
          />
        </Route>
        <Route element={<RoleGuard allow={["provider"]} />}>
          <Route
            path="provider/jobs"
            element={<RolePreviewPage title="Matched jobs" />}
          />
        </Route>
      </Route>

      <Route path="*" element={<HealthPage />} />
    </Routes>
  );
}
