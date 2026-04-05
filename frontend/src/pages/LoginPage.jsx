import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowRight, Building2, ChartSpline } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { toast } from "@/components/ui/sonner";
import { api, extractApiError } from "@/lib/api";

const AUTH_IMAGE = "https://images.unsplash.com/photo-1645677020082-721a854c24f2?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Njd8MHwxfHNlYXJjaHwzfHxyZXN0YXVyYW50JTIwa2l0Y2hlbiUyMGVxdWlwbWVudCUyMGVuZXJneSUyMGVmZmljaWVuY3l8ZW58MHx8fGdyZWVufDE3NzUzNDg1OTN8MA&ixlib=rb-4.1.0&q=85";

export default function LoginPage({ refreshSession }) {
  const navigate = useNavigate();
  const [devEmail, setDevEmail] = useState("demo@energysaver.app");
  const [loading, setLoading] = useState(false);

  const handleDevLogin = async () => {
    try {
      setLoading(true);
      await api.post("/auth/dev-login", {
        email: devEmail,
        name: "Energy Saver Demo",
        company_name: "Energy Saver Demo",
      });
      await refreshSession();
      toast.success("Accesso demo completato");
      navigate("/dashboard");
    } catch (error) {
      toast.error(extractApiError(error, "Accesso demo non riuscito"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background px-4 py-8 sm:px-6 lg:px-8">
      <div className="mx-auto grid min-h-[calc(100vh-4rem)] w-full max-w-7xl gap-6 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
        <div className="flex items-center justify-center">
          <Card className="w-full max-w-xl border-border bg-card shadow-[var(--shadow-lg)]">
            <CardHeader className="space-y-5">
              <Badge className="w-fit rounded-full bg-secondary text-secondary-foreground">Stima risparmio in 7 giorni</Badge>
              <div className="space-y-3">
                <CardTitle className="font-['Space_Grotesk'] text-4xl tracking-[-0.04em] text-foreground sm:text-5xl">
                  Trasforma consumi dispersi in margine operativo.
                </CardTitle>
                <CardDescription className="text-base leading-7 text-muted-foreground">
                  Dashboard real-time, consigli con ROI e forecast bolletta per bar, ristoranti e palestre.
                </CardDescription>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="rounded-2xl border border-border bg-secondary p-4">
                <div className="mb-3 flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-primary text-primary-foreground">
                    <Building2 className="h-4 w-4" />
                  </div>
                  <div>
                    <p className="font-medium text-foreground">Login rapido sviluppo</p>
                    <p className="text-sm text-muted-foreground">Usa il bypass sicuro per test e onboarding.</p>
                  </div>
                </div>
                <Input
                  data-testid="login-email-input"
                  value={devEmail}
                  onChange={(event) => setDevEmail(event.target.value)}
                  className="min-h-11 bg-card"
                  placeholder="demo@energysaver.app"
                />
                <Button data-testid="dev-bypass-button" className="mt-3 w-full min-h-11" onClick={handleDevLogin} disabled={loading}>
                  Entra in modalità demo
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </div>

              <Button asChild data-testid="google-login-button" variant="outline" className="min-h-11 w-full justify-center bg-card">
                <a href={`${process.env.REACT_APP_BACKEND_URL}/api/auth/google/start?next_path=/dashboard`}>
                  Continua con Google
                </a>
              </Button>

              <div className="grid gap-3 rounded-2xl bg-secondary p-4 sm:grid-cols-3">
                {[
                  { label: "Sprechi stimati", value: "3.2k€" },
                  { label: "Azioni con ROI", value: "5" },
                  { label: "Forecast costi", value: "+12%" },
                ].map((item) => (
                  <div key={item.label} className="rounded-2xl bg-card p-4 shadow-[var(--shadow-sm)]">
                    <p className="text-sm text-muted-foreground">{item.label}</p>
                    <p className="mt-2 font-['Space_Grotesk'] text-2xl font-semibold tracking-[-0.02em] text-foreground">{item.value}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="hidden overflow-hidden rounded-[32px] border border-border bg-card shadow-[var(--shadow-lg)] lg:block">
          <div className="grid h-full grid-rows-[1.25fr_0.75fr]">
            <div className="relative overflow-hidden">
              <img src={AUTH_IMAGE} alt="Contesto PMI energy management" className="h-full w-full object-cover" />
              <div className="absolute inset-0 bg-[linear-gradient(180deg,rgba(30,45,45,0.04),rgba(30,45,45,0.24))]" />
            </div>
            <div className="grid gap-4 bg-secondary p-8">
              <div className="flex items-center gap-3 rounded-2xl bg-card p-4 shadow-[var(--shadow-sm)]">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary text-primary-foreground">
                  <ChartSpline className="h-5 w-5" />
                </div>
                <div>
                  <p className="font-medium text-foreground">Insight immediato</p>
                  <p className="text-sm leading-6 text-muted-foreground">Capisci quali carichi spegnere, quando e con quale ROI.</p>
                </div>
              </div>
              <div className="rounded-2xl bg-card p-5 shadow-[var(--shadow-sm)]">
                <p className="text-sm uppercase tracking-[0.22em] text-muted-foreground">Perché funziona</p>
                <ul className="mt-4 space-y-3 text-sm leading-6 text-foreground">
                  <li>• Combina meteo reale, prezzi energia e storico consumi.</li>
                  <li>• Genera alert leggibili dal titolare, non solo dal tecnico.</li>
                  <li>• Prioritizza le azioni con impatto economico immediato.</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
