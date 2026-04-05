import { useEffect, useState } from "react";
import { Download, FilePlus2, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api, extractApiError, formatCurrency, formatDateTime } from "@/lib/api";
import { toast } from "@/components/ui/sonner";

export default function ReportsPage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  const loadReports = async () => {
    try {
      setLoading(true);
      const { data } = await api.get("/reports");
      setItems(data.items || []);
    } catch (error) {
      toast.error(extractApiError(error, "Impossibile caricare i report"));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReports();
  }, []);

  const generateReport = async () => {
    try {
      setGenerating(true);
      const { data } = await api.post("/reports/generate");
      toast.success("Report generato con successo");
      await loadReports();
      window.open(`${process.env.REACT_APP_BACKEND_URL}${data.report.download_path}`, "_blank");
    } catch (error) {
      toast.error(extractApiError(error, "Generazione report fallita"));
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="space-y-6">
      <section className="grid gap-4 rounded-[28px] border border-border bg-card p-5 shadow-[var(--shadow-md)] lg:grid-cols-[1.1fr_0.9fr] lg:p-7">
        <div>
          <Badge className="rounded-full bg-secondary text-secondary-foreground">Report automatici</Badge>
          <h2 className="mt-4 font-['Space_Grotesk'] text-4xl font-semibold tracking-[-0.04em] text-foreground">Genera un PDF pronto da condividere con titolare, CFO o consulente.</h2>
          <p className="mt-4 max-w-2xl text-base leading-7 text-muted-foreground">Il report mensile riassume consumo, sprechi, forecast e top azioni ordinate per valore economico.</p>
        </div>
        <Card className="border-border bg-secondary shadow-none">
          <CardContent className="flex h-full flex-col justify-between gap-4 p-5">
            <div>
              <p className="text-sm text-muted-foreground">Report disponibili</p>
              <p className="mt-2 font-['Space_Grotesk'] text-4xl font-semibold tracking-[-0.03em] text-foreground">{items.length}</p>
            </div>
            <Button data-testid="generate-report-button" className="min-h-11 w-full" onClick={generateReport} disabled={generating}>
              <FilePlus2 className="h-4 w-4" />
              {generating ? "Generazione..." : "Genera report"}
            </Button>
          </CardContent>
        </Card>
      </section>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {items.map((report) => (
          <Card key={report.id} className="border-border bg-card shadow-[var(--shadow-sm)]">
            <CardHeader className="flex flex-row items-start justify-between gap-3">
              <div>
                <CardTitle className="font-['Space_Grotesk'] text-xl tracking-[-0.02em]">Report mensile</CardTitle>
                <p className="mt-1 text-sm text-muted-foreground">{formatDateTime(report.created_at)}</p>
              </div>
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-secondary">
                <FileText className="h-5 w-5 text-primary" />
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="rounded-2xl bg-secondary p-4">
                <p className="text-sm text-muted-foreground">Risparmio potenziale</p>
                <p className="mt-2 font-semibold text-foreground">{formatCurrency(report.summary?.potential_monthly_savings_eur)}</p>
              </div>
              <div className="rounded-2xl bg-secondary p-4">
                <p className="text-sm text-muted-foreground">Sprechi stimati</p>
                <p className="mt-2 font-semibold text-foreground">{formatCurrency(report.summary?.estimated_waste_eur)}</p>
              </div>
              <Button asChild data-testid={`download-report-${report.id}`} variant="outline" className="min-h-11 w-full bg-card">
                <a href={`${process.env.REACT_APP_BACKEND_URL}${report.download_url}`} target="_blank" rel="noreferrer">
                  <Download className="h-4 w-4" />
                  Scarica PDF
                </a>
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      {!loading && !items.length ? (
        <Card className="border-dashed border-border bg-card shadow-[var(--shadow-sm)]">
          <CardContent className="flex min-h-[220px] flex-col items-center justify-center gap-4 p-8 text-center">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-secondary">
              <FileText className="h-6 w-6 text-primary" />
            </div>
            <div>
              <p className="font-medium text-foreground">Nessun report ancora generato</p>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">Lancia un’analisi e genera il primo PDF mensile per iniziare a condividere valore con il team.</p>
            </div>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
