import { useEffect, useState } from "react";
import { LogOut, Mail, ShieldCheck, Sparkles } from "lucide-react";
import { useOutletContext } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { api, extractApiError } from "@/lib/api";
import { toast } from "@/components/ui/sonner";

export default function SettingsPage() {
  const { logout } = useOutletContext();
  const [summary, setSummary] = useState(null);
  const [saving, setSaving] = useState(false);

  const loadSummary = async () => {
    try {
      const { data } = await api.get("/settings/summary");
      setSummary(data);
    } catch (error) {
      toast.error(extractApiError(error, "Impossibile caricare le impostazioni"));
    }
  };

  useEffect(() => {
    loadSummary();
  }, []);

  const updatePreference = async (key, value) => {
    if (!summary) return;
    const nextPreferences = { ...summary.preferences, [key]: value };
    try {
      setSaving(true);
      const { data } = await api.post("/notifications/preferences", {
        email_enabled: Boolean(nextPreferences.email_enabled),
        anomaly_alerts: Boolean(nextPreferences.anomaly_alerts),
        price_alerts: Boolean(nextPreferences.price_alerts),
        report_alerts: Boolean(nextPreferences.report_alerts),
      });
      setSummary((previous) => ({ ...previous, preferences: data.preferences }));
      toast.success("Preferenze aggiornate");
    } catch (error) {
      toast.error(extractApiError(error, "Aggiornamento preferenze fallito"));
    } finally {
      setSaving(false);
    }
  };

  const sendTestEmail = async () => {
    try {
      const { data } = await api.post("/notifications/test-email");
      toast.success(data.message);
    } catch (error) {
      toast.error(extractApiError(error, "Invio test non riuscito"));
    }
  };

  return (
    <div className="space-y-6">
      <section className="rounded-[28px] border border-border bg-card p-6 shadow-[var(--shadow-md)] lg:p-8">
        <Badge className="rounded-full bg-secondary text-secondary-foreground">Configurazione SaaS</Badge>
        <h2 className="mt-4 font-['Space_Grotesk'] text-4xl font-semibold tracking-[-0.04em] text-foreground">Preferenze notifiche, integrazioni e sicurezza.</h2>
        <p className="mt-4 max-w-3xl text-base leading-7 text-muted-foreground">Questa sezione riassume stato integrazioni, modalità email sviluppo e controllo operativo della sede.</p>
      </section>

      <div className="grid gap-4 xl:grid-cols-[1fr_1fr]">
        <Card className="border-border bg-card shadow-[var(--shadow-sm)]">
          <CardHeader>
            <CardTitle className="font-['Space_Grotesk'] text-xl tracking-[-0.02em]">Preferenze alert</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {[
              { key: "email_enabled", label: "Email alert sviluppo", description: "Registra l’invio nel sistema interno/dev." },
              { key: "anomaly_alerts", label: "Alert anomalie", description: "Picchi, fuori orario e sprechi stimati." },
              { key: "price_alerts", label: "Alert forecast costi", description: "Aumenti previsti nei prossimi 30 giorni." },
              { key: "report_alerts", label: "Alert report", description: "Avviso quando un nuovo report è pronto." },
            ].map((item) => (
              <div key={item.key} className="flex items-center justify-between gap-4 rounded-2xl bg-secondary p-4">
                <div>
                  <p className="font-medium text-foreground">{item.label}</p>
                  <p className="text-sm leading-6 text-muted-foreground">{item.description}</p>
                </div>
                <Switch
                  data-testid={`${item.key}-switch`}
                  checked={Boolean(summary?.preferences?.[item.key])}
                  onCheckedChange={(checked) => updatePreference(item.key, checked)}
                  disabled={saving}
                />
              </div>
            ))}
            <Button data-testid="test-email-button" className="min-h-11 w-full" onClick={sendTestEmail}>
              <Mail className="h-4 w-4" />
              Invia test email
            </Button>
          </CardContent>
        </Card>

        <Card className="border-border bg-card shadow-[var(--shadow-sm)]">
          <CardHeader>
            <CardTitle className="font-['Space_Grotesk'] text-xl tracking-[-0.02em]">Stato integrazioni</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3">
            {summary?.integrations
              ? Object.entries(summary.integrations).map(([key, value]) => (
                  <div key={key} className="flex items-center justify-between gap-3 rounded-2xl bg-secondary p-4">
                    <div className="flex items-center gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-card">
                        <ShieldCheck className="h-4 w-4 text-primary" />
                      </div>
                      <div>
                        <p className="font-medium text-foreground">{key.replace(/_/g, " ")}</p>
                        <p className="text-sm text-muted-foreground">Integrazione disponibile per V1</p>
                      </div>
                    </div>
                    <Badge className="rounded-full bg-card text-foreground">{String(value)}</Badge>
                  </div>
                ))
              : null}
            <div className="rounded-2xl border border-border bg-card p-4">
              <div className="mb-3 flex items-center gap-3 text-foreground">
                <Sparkles className="h-5 w-5 text-primary" />
                <span className="font-medium">Sicurezza applicata</span>
              </div>
              <p className="text-sm leading-6 text-muted-foreground">Sessioni JWT in cookie HTTP-only, validazione file upload e scope tenant per org/sede.</p>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="border-border bg-card shadow-[var(--shadow-sm)]">
        <CardHeader>
          <CardTitle className="font-['Space_Grotesk'] text-xl tracking-[-0.02em]">Esci dal workspace</CardTitle>
        </CardHeader>
        <CardContent>
          <Button data-testid="settings-logout-button" variant="outline" className="min-h-11 bg-card" onClick={logout}>
            <LogOut className="h-4 w-4" />
            Logout
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
