import { AlertTriangle, BarChart3, LineChart, TrendingUp } from "lucide-react";
import { Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Line, LineChart as RechartsLineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { formatCurrency, formatNumber } from "@/lib/api";

const EmptyChart = ({ title, buttonLabel }) => (
  <Card className="border-dashed border-border bg-card shadow-[var(--shadow-sm)]">
    <CardHeader>
      <CardTitle className="font-['Space_Grotesk'] text-lg tracking-[-0.02em]">{title}</CardTitle>
    </CardHeader>
    <CardContent className="flex min-h-[260px] flex-col items-center justify-center gap-4 text-center">
      <div className="h-16 w-16 rounded-full bg-secondary" />
      <div>
        <p className="font-medium text-foreground">In attesa di dati</p>
        <p className="max-w-sm text-sm leading-6 text-muted-foreground">Carica una bolletta o inserisci consumi manualmente per sbloccare grafici, anomaly detection e forecast.</p>
      </div>
      <Button data-testid="empty-chart-cta" variant="outline" className="bg-card">
        {buttonLabel}
      </Button>
    </CardContent>
  </Card>
);

const chartBoxClass = "border-border bg-card shadow-[var(--shadow-sm)]";

export const ChartsPanel = ({ analysis }) => {
  if (!analysis?.daily_series?.length) {
    return <EmptyChart title="Trend consumi e costi" buttonLabel="Aggiungi dati" />;
  }

  const forecastData = [
    ...analysis.daily_series.slice(-7).map((item) => ({ name: item.date.slice(5), value: item.cost_eur, type: "storico" })),
    { name: "+30g", value: analysis.prediction?.next_30_days_cost_eur || 0, type: "forecast" },
  ];

  return (
    <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
      <Card data-testid="consumption-chart" className={`${chartBoxClass} xl:col-span-2`}>
        <CardHeader className="flex flex-row items-start justify-between gap-4">
          <div>
            <CardTitle className="font-['Space_Grotesk'] text-lg tracking-[-0.02em]">Consumi giornalieri</CardTitle>
            <p className="mt-1 text-sm text-muted-foreground">Profilo energetico e variazioni nel periodo selezionato.</p>
          </div>
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-secondary">
            <BarChart3 className="h-5 w-5 text-primary" />
          </div>
        </CardHeader>
        <CardContent className="h-[320px]">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={analysis.daily_series}>
              <defs>
                <linearGradient id="consumptionFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="hsl(var(--chart-1))" stopOpacity={0.24} />
                  <stop offset="95%" stopColor="hsl(var(--chart-1))" stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="hsl(var(--border) / 0.5)" vertical={false} />
              <XAxis dataKey="date" tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }} tickFormatter={(value) => value.slice(5)} />
              <YAxis tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }} />
              <Tooltip formatter={(value) => [`${formatNumber(value)} kWh`, "Consumo"]} />
              <Area type="monotone" dataKey="kwh" stroke="hsl(var(--chart-1))" fill="url(#consumptionFill)" strokeWidth={2.5} />
            </AreaChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card data-testid="cost-chart" className={chartBoxClass}>
        <CardHeader className="flex flex-row items-start justify-between gap-4">
          <div>
            <CardTitle className="font-['Space_Grotesk'] text-lg tracking-[-0.02em]">Costo giornaliero</CardTitle>
            <p className="mt-1 text-sm text-muted-foreground">Lettura economica del carico energetico.</p>
          </div>
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-secondary">
            <TrendingUp className="h-5 w-5 text-primary" />
          </div>
        </CardHeader>
        <CardContent className="h-[320px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={analysis.daily_series}>
              <CartesianGrid stroke="hsl(var(--border) / 0.5)" vertical={false} />
              <XAxis dataKey="date" tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }} tickFormatter={(value) => value.slice(5)} />
              <YAxis tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }} />
              <Tooltip formatter={(value) => [formatCurrency(value), "Costo"]} />
              <Bar dataKey="cost_eur" radius={[8, 8, 0, 0]}>
                {analysis.daily_series.map((entry) => (
                  <Cell key={entry.date} fill="hsl(var(--chart-4))" />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card data-testid="forecast-chart" className={`${chartBoxClass} xl:col-span-3`}>
        <CardHeader className="flex flex-row items-start justify-between gap-4">
          <div>
            <CardTitle className="font-['Space_Grotesk'] text-lg tracking-[-0.02em]">Forecast costi</CardTitle>
            <p className="mt-1 text-sm text-muted-foreground">Previsione basata su storico, prezzi energia e meteo.</p>
          </div>
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-secondary">
            <LineChart className="h-5 w-5 text-primary" />
          </div>
        </CardHeader>
        <CardContent className="grid gap-4 xl:grid-cols-[1.3fr_0.7fr]">
          <div className="h-[280px]">
            <ResponsiveContainer width="100%" height="100%">
              <RechartsLineChart data={forecastData}>
                <CartesianGrid stroke="hsl(var(--border) / 0.5)" vertical={false} />
                <XAxis dataKey="name" tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }} />
                <YAxis tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 12 }} />
                <Tooltip formatter={(value) => [formatCurrency(value), "Costo"]} />
                <Line type="monotone" dataKey="value" stroke="hsl(var(--chart-2))" strokeWidth={3} dot={{ r: 4 }} />
              </RechartsLineChart>
            </ResponsiveContainer>
          </div>
          <div className="grid gap-3">
            <div className="rounded-2xl bg-secondary p-4">
              <div className="mb-2 flex items-center gap-2 text-sm text-muted-foreground">
                <AlertTriangle className="h-4 w-4" />
                Alert forecast
              </div>
              <p className="font-['Space_Grotesk'] text-2xl font-semibold tracking-[-0.02em] text-foreground">
                {analysis.prediction?.alert ? "Attivo" : "Stabile"}
              </p>
              <p className="mt-2 text-sm text-muted-foreground">Variazione attesa: {Number(analysis.prediction?.expected_variation_pct || 0).toFixed(1)}%</p>
            </div>
            <div className="rounded-2xl bg-secondary p-4">
              <p className="text-sm text-muted-foreground">Driver rilevati</p>
              <ul className="mt-3 space-y-2 text-sm text-foreground">
                {(analysis.prediction?.drivers || []).map((driver) => (
                  <li key={driver} className="rounded-xl bg-background px-3 py-2">
                    {driver}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
