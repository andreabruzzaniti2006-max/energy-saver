import { ArrowDownRight, ArrowUpRight } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export const KpiCard = ({ icon: Icon, label, value, delta, tone = "neutral", dataTestId }) => {
  const deltaIsPositive = Number(delta) >= 0;
  const deltaLabel = delta == null ? "Nessun confronto" : `${deltaIsPositive ? "+" : ""}${Number(delta).toFixed(1)}% vs base`;
  const toneClass =
    tone === "success"
      ? "bg-emerald-50 text-emerald-700"
      : tone === "warning"
        ? "bg-amber-50 text-amber-700"
        : tone === "danger"
          ? "bg-rose-50 text-rose-700"
          : "bg-secondary text-secondary-foreground";

  return (
    <Card data-testid={dataTestId} className="border-border bg-card shadow-[var(--shadow-sm)] transition-shadow duration-200 hover:shadow-[var(--shadow-md)]">
      <CardContent className="p-5">
        <div className="mb-4 flex items-center justify-between gap-4">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-secondary text-foreground">
            <Icon className="h-5 w-5" />
          </div>
          <Badge className={`rounded-full border-0 ${toneClass}`}>{label}</Badge>
        </div>
        <div className="space-y-2">
          <p className="text-sm text-muted-foreground">{label}</p>
          <div className="font-['Space_Grotesk'] text-3xl font-semibold tracking-[-0.03em] tabular-nums text-foreground">{value}</div>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            {deltaIsPositive ? <ArrowUpRight className="h-3.5 w-3.5 text-emerald-600" /> : <ArrowDownRight className="h-3.5 w-3.5 text-rose-600" />}
            <span>{deltaLabel}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
