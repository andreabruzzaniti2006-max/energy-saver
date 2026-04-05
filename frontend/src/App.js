import { useEffect, useMemo, useState } from "react";
import "@/App.css";
import { BrowserRouter, Navigate, Outlet, Route, Routes, useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { ThemeProvider } from "next-themes";
import { Toaster } from "@/components/ui/sonner";
import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";
import LoginPage from "@/pages/LoginPage";
import OnboardingPage from "@/pages/OnboardingPage";
import DashboardPage from "@/pages/DashboardPage";
import BillsPage from "@/pages/BillsPage";
import ConsumptionPage from "@/pages/ConsumptionPage";
import InsightsPage from "@/pages/InsightsPage";
import ReportsPage from "@/pages/ReportsPage";
import PricingPage from "@/pages/PricingPage";
import SettingsPage from "@/pages/SettingsPage";

const LoadingScreen = () => (
  <div className="flex min-h-screen items-center justify-center bg-background px-6">
    <div className="w-full max-w-md rounded-2xl border border-border bg-card p-8 shadow-[var(--shadow-md)]">
      <div className="mb-4 h-3 w-32 rounded-full bg-muted" />
      <div className="mb-3 h-10 w-3/4 rounded-full bg-muted" />
      <div className="h-24 rounded-2xl bg-secondary" />
    </div>
  </div>
);

const AuthCallbackPage = ({ refreshSession }) => {
  const navigate = useNavigate();
  const [params] = useSearchParams();

  useEffect(() => {
    const complete = async () => {
      await refreshSession();
      const nextPath = params.get("next") || "/dashboard";
      navigate(nextPath, { replace: true });
    };
    complete();
  }, [navigate, params, refreshSession]);

  return <LoadingScreen />;
};

const ProtectedLayout = ({ session, loading, refreshSession, logout }) => {
  const location = useLocation();

  if (loading) {
    return <LoadingScreen />;
  }

  if (!session) {
    return <Navigate to="/login" replace />;
  }

  if (!session.site?.onboarding_completed && location.pathname !== "/onboarding") {
    return <Navigate to="/onboarding" replace />;
  }

  return (
    <AppShell session={session} onLogout={logout}>
      <Outlet context={{ session, refreshSession, logout }} />
    </AppShell>
  );
};

const PublicLayout = ({ session, loading, refreshSession }) => {
  if (loading) {
    return <LoadingScreen />;
  }

  if (session) {
    return <Navigate to={session.site?.onboarding_completed ? "/dashboard" : "/onboarding"} replace />;
  }

  return <Outlet context={{ refreshSession }} />;
};

const AppRoutes = () => {
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);

  const refreshSession = useMemo(
    () => async () => {
      try {
        const { data } = await api.get("/auth/me");
        setSession(data.session);
        return data.session;
      } catch (error) {
        setSession(null);
        return null;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const logout = async () => {
    await api.post("/auth/logout");
    setSession(null);
  };

  useEffect(() => {
    refreshSession();
  }, [refreshSession]);

  return (
    <Routes>
      <Route element={<PublicLayout session={session} loading={loading} refreshSession={refreshSession} />}>
        <Route path="/login" element={<LoginPage refreshSession={refreshSession} />} />
      </Route>

      <Route path="/auth/callback" element={<AuthCallbackPage refreshSession={refreshSession} />} />

      <Route element={<ProtectedLayout session={session} loading={loading} refreshSession={refreshSession} logout={logout} />}>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/onboarding" element={<OnboardingPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/bills" element={<BillsPage />} />
        <Route path="/consumption" element={<ConsumptionPage />} />
        <Route path="/insights" element={<InsightsPage />} />
        <Route path="/reports" element={<ReportsPage />} />
        <Route path="/pricing" element={<PricingPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Route>
    </Routes>
  );
};

function App() {
  return (
    <ThemeProvider attribute="class" defaultTheme="light" enableSystem={false}>
      <div className="min-h-screen bg-background text-foreground antialiased">
        <BrowserRouter>
          <AppRoutes />
        </BrowserRouter>
        <Toaster richColors position="top-right" />
      </div>
    </ThemeProvider>
  );
}

export default App;
