import { CircleDollarSign, Clock3, Leaf, Wallet } from "lucide-react";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { formatCurrency } from "@/lib/api";

const priorityStyles = {
  high: "bg-rose-50 text-rose-700",
  medium: "bg-amber-50 text-amber-700",
  low: "bg-emerald-50 text-emerald-700",
};

export const AdviceCard = ({ advice, compact = false }) => {
  const paybackValue = Math.max(0, Math.min(100, 100 - (Number(advice.payback_months || 0) * 4)));

  return (
    <Card data-testid="advice-card" className="h-full border-border bg-card shadow-[var(--shadow-sm)]">
      <CardHeader className="space-y-4 pb-4">
        <div className="flex items-start justify-between gap-3">
          <div>
            <Badge className={`rounded-full border-0 ${priorityStyles[advice.priority] || priorityStyles.low}`}>{advice.priority}</Badge>
            <CardTitle className="mt-3 font-['Space_Grotesk'] text-xl tracking-[-0.02em]">{advice.title}</CardTitle>
          </div>
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-secondary">
            <Leaf className="h-5 w-5 text-primary" />
          </div>
        </div>
        <p className="text-sm leading-6 text-muted-foreground">{advice.reason}</p>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className={`grid ${compact ? "grid-cols-1" : "grid-cols-1 sm:grid-cols-3"} gap-3`}>
          <div className="rounded-2xl bg-secondary p-4">
            <div className="mb-2 flex items-center gap-2 text-sm text-muted-foreground">
              <Wallet className="h-4 w-4" />
              Risparmio
            </div>
            <p className="text-lg font-semibold tabular-nums text-foreground">{formatCurrency(advice.monthly_savings_eur)}</p>
          </div>
          <div className="rounded-2xl bg-secondary p-4">
            <div className="mb-2 flex items-center gap-2 text-sm text-muted-foreground">
              <CircleDollarSign className="h-4 w-4" />
              ROI 1° anno
            </div>
            <p className="text-lg font-semibold tabular-nums text-foreground">{Number(advice.roi_pct_year_1 || 0).toFixed(1)}%</p>
          </div>
          <div className="rounded-2xl bg-secondary p-4">
            <div className="mb-2 flex items-center gap-2 text-sm text-muted-foreground">
              <Clock3 className="h-4 w-4" />
              Payback
            </div>
            <p className="text-lg font-semibold tabular-nums text-foreground">{Number(advice.payback_months || 0).toFixed(1)} mesi</p>
          </div>
        </div>

        <div>
          <div className="mb-2 flex items-center justify-between text-xs text-muted-foreground">
            <span>Velocità di ritorno</span>
            <span>{Number(advice.payback_months || 0).toFixed(1)} mesi</span>
          </div>
          <Progress value={paybackValue} />
        </div>

        <div className="rounded-2xl border border-border bg-background p-4 text-sm text-foreground">{advice.action}</div>
      </CardContent>
      <CardFooter className="flex flex-col gap-2 sm:flex-row sm:justify-between">
        <Button data-testid="advice-apply-button" className="w-full sm:w-auto">Applica</Button>
        <Button data-testid="advice-dismiss-button" variant="outline" className="w-full bg-card sm:w-auto">
          Ignora
        </Button>
      </CardFooter>
    </Card>
  );
};
