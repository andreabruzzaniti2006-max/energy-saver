import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { AlertTriangle, CircleDollarSign, FileSpreadsheet, PlugZap, RefreshCcw, Thermometer, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { KpiCard } from "@/components/KpiCard";
import { ChartsPanel } from "@/components/ChartsPanel";
import { AdviceCard } from "@/components/AdviceCard";
import { api, extractApiError, formatCurrency, formatDateTime, formatNumber } from "@/lib/api";
import { toast } from "@/components/ui/sonner";

export default function DashboardPage() {
  const [overview, setOverview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);

  const loadOverview = async () => {
    try {
      setLoading(true);
      const { data } = await api.get("/dashboard/overview");
      setOverview(data);
    } catch (error) {
      toast.error(extractApiError(error, "Impossibile caricare la dashboard"));
    } finally {
      setLoading(false);
    }
  };

  const runAnalysis = async () => {
    try {
      setRunning(true);
      await api.post("/analytics/run");
      toast.success("Analisi completata con successo");
      await loadOverview();
    } catch (error) {
      toast.error(extractApiError(error, "Analisi non disponibile"));
    } finally {
      setRunning(false);
    }
  };

  useEffect(() => {
    loadOverview();
  }, []);

  const analysis = overview?.latest_analysis?.analysis;

  if (loading) {
    return <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">{Array.from({ length: 4 }).map((_, index) => <div key={index} className="h-40 rounded-2xl bg-secondary" />)}</div>;
  }

  return (
    <div className="space-y-6">
      <section className="grid gap-4 rounded-[28px] border border-border bg-card p-5 shadow-[var(--shadow-md)] lg:grid-cols-[1.1fr_0.9fr] lg:p-7">
        <div>
          <Badge className="rounded-full bg-secondary text-secondary-foreground">Valore economico in primo piano</Badge>
          <h2 className="mt-4 font-['Space_Grotesk'] text-4xl font-semibold tracking-[-0.04em] text-foreground">Visualizza costi, sprechi e azioni con impatto immediato.</h2>
          <p className="mt-4 max-w-2xl text-base leading-7 text-muted-foreground">Ogni analisi combina storico consumi, meteo e prezzo energia per far emergere dove intervenire e quanto puoi recuperare in margine.</p>
          {overview?.counts?.pending_bill_reviews ? (
            <div className="mt-5 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm leading-6 text-amber-800">
              Hai {overview.counts.pending_bill_reviews} bolletta/e da rivedere. Apri Bollette e completa consumo, costo e periodo per includerle nell’analisi.
            </div>
          ) : null}
          <div className="mt-6 flex flex-wrap gap-3">
            <Button data-testid="dashboard-run-analysis-button" className="min-h-11" onClick={runAnalysis} disabled={running}>
              <RefreshCcw className="h-4 w-4" />
              {running ? "Analisi in corso..." : "Lancia analisi"}
            </Button>
            <Button asChild data-testid="dashboard-manual-entry-button" variant="outline" className="min-h-11 bg-card">
              <Link to="/consumption">Inserisci consumi</Link>
            </Button>
          </div>
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          <div className="rounded-2xl bg-secondary p-4">
            <p className="text-sm text-muted-foreground">Meteo</p>
            <div className="mt-3 flex items-center gap-3">
              <Thermometer className="h-5 w-5 text-primary" />
              <span className="font-medium text-foreground">{overview?.integration_status?.weather || "pending"}</span>
            </div>
          </div>
          <div className="rounded-2xl bg-secondary p-4">
            <p className="text-sm text-muted-foreground">Prezzo energia</p>
            <div className="mt-3 flex items-center gap-3">
              <Zap className="h-5 w-5 text-primary" />
              <span className="font-medium text-foreground">{overview?.integration_status?.prices || "pending"}</span>
            </div>
          </div>
          <div className="rounded-2xl bg-secondary p-4">
            <p className="text-sm text-muted-foreground">Email alert</p>
            <div className="mt-3 flex items-center gap-3">
              <PlugZap className="h-5 w-5 text-primary" />
              <span className="font-medium text-foreground">{overview?.integration_status?.email_mode}</span>
            </div>
          </div>
          <div className="rounded-2xl bg-secondary p-4">
            <p className="text-sm text-muted-foreground">Google login</p>
            <div className="mt-3 flex items-center gap-3">
              <FileSpreadsheet className="h-5 w-5 text-primary" />
              <span className="font-medium text-foreground">{overview?.integration_status?.google_oauth_configured ? "attivo" : "non configurato"}</span>
            </div>
          </div>
        </div>
      </section>

      <section className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <KpiCard icon={CircleDollarSign} label="Costo energia" value={formatCurrency(analysis?.kpis?.total_cost_eur)} delta={analysis?.prediction?.expected_variation_pct} tone="warning" dataTestId="kpi-cost-card" />
        <KpiCard icon={Zap} label="Consumo kWh" value={`${formatNumber(analysis?.kpis?.total_consumption_kwh)} kWh`} delta={3.4} tone="neutral" dataTestId="kpi-consumption-card" />
        <KpiCard icon={AlertTriangle} label="Sprechi stimati" value={formatCurrency(analysis?.kpis?.estimated_waste_eur)} delta={-1.2} tone="danger" dataTestId="kpi-waste-card" />
        <KpiCard icon={PlugZap} label="Risparmio potenziale" value={formatCurrency(analysis?.kpis?.potential_monthly_savings_eur)} delta={11.8} tone="success" dataTestId="kpi-savings-card" />
      </section>

      <ChartsPanel analysis={analysis} />

      <section className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
        <Card className="border-border bg-card shadow-[var(--shadow-sm)]">
          <CardHeader className="flex flex-row items-center justify-between gap-4">
            <div>
              <CardTitle className="font-['Space_Grotesk'] text-xl tracking-[-0.02em]">Consigli prioritari</CardTitle>
              <p className="mt-1 text-sm text-muted-foreground">Azioni ordinate per impatto economico e velocità di rientro.</p>
            </div>
            <Button asChild data-testid="see-all-insights-button" variant="outline" className="bg-card">
              <Link to="/insights">Apri insights</Link>
            </Button>
          </CardHeader>
          <CardContent className="grid gap-4">
            {(analysis?.advices || []).length ? (
              analysis.advices.slice(0, 2).map((advice) => <AdviceCard key={advice.title} advice={advice} compact />)
            ) : (
              <div className="rounded-2xl bg-secondary p-5 text-sm leading-6 text-muted-foreground">Esegui la prima analisi per vedere consigli con ROI e payback.</div>
            )}
          </CardContent>
        </Card>

        <div className="grid gap-4">
          <Card className="border-border bg-card shadow-[var(--shadow-sm)]">
            <CardHeader>
              <CardTitle className="font-['Space_Grotesk'] text-xl tracking-[-0.02em]">Ultime anomalie</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {(analysis?.anomalies || []).slice(0, 4).map((anomaly) => (
                <div key={anomaly.timestamp} className="rounded-2xl bg-secondary p-4" data-testid="anomaly-item">
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm font-medium text-foreground">{anomaly.reasons?.[0]}</p>
                    <Badge className="rounded-full bg-card text-foreground">{formatCurrency(anomaly.estimated_loss_eur)}</Badge>
                  </div>
                  <p className="mt-2 text-sm text-muted-foreground">{formatDateTime(anomaly.timestamp)}</p>
                </div>
              ))}
              {!(analysis?.anomalies || []).length ? <div className="rounded-2xl bg-secondary p-4 text-sm text-muted-foreground">Nessuna anomalia disponibile. Aggiungi dati o lancia l’analisi.</div> : null}
            </CardContent>
          </Card>

          <Card className="border-border bg-card shadow-[var(--shadow-sm)]">
            <CardHeader>
              <CardTitle className="font-['Space_Grotesk'] text-xl tracking-[-0.02em]">Ultime bollette</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {(overview?.recent_bills || []).length ? (
                overview.recent_bills.map((bill) => (
                  <div key={bill.id} className="rounded-2xl bg-secondary p-4">
                    <div className="flex items-center justify-between gap-3">
                      <p className="text-sm font-medium text-foreground">{bill.filename}</p>
                      <Badge className="rounded-full bg-card text-foreground">{bill.extraction_status}</Badge>
                    </div>
                    <p className="mt-2 text-xs uppercase tracking-[0.22em] text-muted-foreground">{formatDateTime(bill.uploaded_at)}</p>
                  </div>
                ))
              ) : (
                <div className="rounded-2xl bg-secondary p-4 text-sm text-muted-foreground">Nessuna bolletta caricata. Vai su Bollette per iniziare.</div>
              )}
            </CardContent>
          </Card>
        </div>
      </section>
    </div>
  );
}
