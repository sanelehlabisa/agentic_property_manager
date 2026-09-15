import { Route, Routes } from "react-router-dom";

import { RoleGuard } from "../auth/RoleGuard";
import { AppShell } from "../components/AppShell";
import { HealthPage } from "../pages/HealthPage";
import { PortfolioPage } from "../pages/PortfolioPage";
import { PropertyDetailPage } from "../pages/PropertyDetailPage";
import { ProviderMarketplacePage } from "../pages/ProviderMarketplacePage";
import { ProviderProfilePage } from "../pages/ProviderProfilePage";
import { SignInPage } from "../pages/SignInPage";
import { TenantHomePage } from "../pages/TenantHomePage";

export function AppRouter() {
  return (
    <Routes>
      <Route index element={<HealthPage />} />
      <Route path="sign-in" element={<SignInPage />} />

      <Route element={<AppShell />}>
        <Route element={<RoleGuard allow={["homeowner", "manager"]} />}>
          <Route
            path="portfolio"
            element={<PortfolioPage />}
          />
          <Route path="properties/:propertyId" element={<PropertyDetailPage />} />
        </Route>
        <Route element={<RoleGuard allow={["tenant"]} />}>
          <Route path="tenant/home" element={<TenantHomePage />} />
        </Route>
        <Route element={<RoleGuard allow={["provider"]} />}>
          <Route path="provider/jobs" element={<ProviderMarketplacePage />} />
          <Route path="provider/profile" element={<ProviderProfilePage />} />
        </Route>
      </Route>

      <Route path="*" element={<HealthPage />} />
    </Routes>
  );
}
