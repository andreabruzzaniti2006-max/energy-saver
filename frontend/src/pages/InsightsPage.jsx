import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, Filter, TrendingUp } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { AdviceCard } from "@/components/AdviceCard";
import { api, extractApiError, formatCurrency, formatDateTime } from "@/lib/api";
import { toast } from "@/components/ui/sonner";

export default function InsightsPage() {
  const [analysisRun, setAnalysisRun] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadAnalysis = async () => {
    try {
      setLoading(true);
      const { data } = await api.get("/analytics/latest");
      setAnalysisRun(data.analysis_run);
    } catch (error) {
      toast.error(extractApiError(error, "Impossibile caricare gli insights"));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAnalysis();
  }, []);

  const analysis = analysisRun?.analysis;
  const anomalyGroups = useMemo(() => ({
    all: analysis?.anomalies || [],
    high: (analysis?.anomalies || []).filter((item) => Number(item.estimated_loss_eur || 0) >= 0.5),
    medium: (analysis?.anomalies || []).filter((item) => Number(item.estimated_loss_eur || 0) < 0.5),
  }), [analysis]);

  return (
    <div className="space-y-6">
      <section className="grid gap-4 rounded-[28px] border border-border bg-card p-5 shadow-[var(--shadow-md)] lg:grid-cols-[1.05fr_0.95fr] lg:p-7">
        <div>
          <Badge className="rounded-full bg-secondary text-secondary-foreground">Core del prodotto</Badge>
          <h2 className="mt-4 font-['Space_Grotesk'] text-4xl font-semibold tracking-[-0.04em] text-foreground">Traduci le anomalie in azioni con ROI comprensibile.</h2>
          <p className="mt-4 max-w-2xl text-base leading-7 text-muted-foreground">Qui il sistema evidenzia cosa sta accadendo, quanto costa e quale decisione operativa conviene prendere per prima.</p>
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          <div className="rounded-2xl bg-secondary p-4">
            <p className="text-sm text-muted-foreground">Consigli attivi</p>
            <p className="mt-2 font-['Space_Grotesk'] text-3xl font-semibold tracking-[-0.02em] text-foreground">{analysis?.advices?.length || 0}</p>
          </div>
          <div className="rounded-2xl bg-secondary p-4">
            <p className="text-sm text-muted-foreground">Anomalie rilevate</p>
            <p className="mt-2 font-['Space_Grotesk'] text-3xl font-semibold tracking-[-0.02em] text-foreground">{analysis?.anomalies?.length || 0}</p>
          </div>
        </div>
      </section>

      <section className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
        <Card className="border-border bg-card shadow-[var(--shadow-sm)]">
          <CardHeader className="flex flex-row items-center justify-between gap-3">
            <div>
              <CardTitle className="font-['Space_Grotesk'] text-xl tracking-[-0.02em]">Timeline anomalie</CardTitle>
              <p className="mt-1 text-sm text-muted-foreground">Fuori orario, weekend e picchi fuori baseline.</p>
            </div>
            <Button data-testid="insights-refresh-button" variant="outline" className="bg-card" onClick={loadAnalysis}>
              <Filter className="h-4 w-4" />
              Aggiorna
            </Button>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="all" className="space-y-4">
              <TabsList className="grid w-full grid-cols-3 bg-secondary">
                <TabsTrigger value="all">Tutte</TabsTrigger>
                <TabsTrigger value="high">High</TabsTrigger>
                <TabsTrigger value="medium">Medium</TabsTrigger>
              </TabsList>
              {Object.entries(anomalyGroups).map(([key, anomalies]) => (
                <TabsContent key={key} value={key}>
                  <div data-testid="anomaly-timeline" className="space-y-3">
                    {anomalies.map((anomaly) => (
                      <div key={`${anomaly.timestamp}-${anomaly.cost_eur}`} className="rounded-2xl border border-border bg-secondary p-4">
                        <div className="flex items-center justify-between gap-3">
                          <Badge className="rounded-full bg-card text-foreground">{formatCurrency(anomaly.estimated_loss_eur)}</Badge>
                          <span className="text-xs uppercase tracking-[0.22em] text-muted-foreground">{formatDateTime(anomaly.timestamp)}</span>
                        </div>
                        <p className="mt-3 font-medium text-foreground">{anomaly.reasons.join(" · ")}</p>
                        <p className="mt-2 text-sm text-muted-foreground">Consumo osservato: {anomaly.kwh} kWh</p>
                      </div>
                    ))}
                    {!loading && !anomalies.length ? <div className="rounded-2xl bg-secondary p-4 text-sm text-muted-foreground">Nessuna anomalia per questo filtro.</div> : null}
                  </div>
                </TabsContent>
              ))}
            </Tabs>
          </CardContent>
        </Card>

        <div className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Card className="border-border bg-card shadow-[var(--shadow-sm)]">
              <CardContent className="p-5">
                <div className="flex items-center gap-3 text-sm text-muted-foreground"><TrendingUp className="h-4 w-4" /> Forecast 30 giorni</div>
                <p className="mt-3 font-['Space_Grotesk'] text-3xl font-semibold tracking-[-0.02em] text-foreground">{formatCurrency(analysis?.prediction?.next_30_days_cost_eur)}</p>
                <p className="mt-2 text-sm text-muted-foreground">Variazione attesa: {Number(analysis?.prediction?.expected_variation_pct || 0).toFixed(1)}%</p>
              </CardContent>
            </Card>
            <Card className="border-border bg-card shadow-[var(--shadow-sm)]">
              <CardContent className="p-5">
                <div className="flex items-center gap-3 text-sm text-muted-foreground"><AlertTriangle className="h-4 w-4" /> Spreco rilevato</div>
                <p className="mt-3 font-['Space_Grotesk'] text-3xl font-semibold tracking-[-0.02em] text-foreground">{formatCurrency(analysis?.kpis?.estimated_waste_eur)}</p>
                <p className="mt-2 text-sm text-muted-foreground">Basato sui picchi fuori baseline e fuori orario.</p>
              </CardContent>
            </Card>
          </div>
          {(analysis?.advices || []).length ? analysis.advices.map((advice) => <AdviceCard key={advice.title} advice={advice} />) : <div className="rounded-2xl bg-secondary p-5 text-sm text-muted-foreground">Lancia un’analisi per popolare gli insights.</div>}
        </div>
      </section>
    </div>
  );
}
