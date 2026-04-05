import { useEffect, useMemo, useState } from "react";
import { Plus, Trash2, Upload } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Textarea } from "@/components/ui/textarea";
import { api, extractApiError, formatCurrency, formatDateTime } from "@/lib/api";
import { toast } from "@/components/ui/sonner";

const parseBatch = (text) =>
  text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const [timestamp, kwh, cost] = line.split(",").map((item) => item.trim());
      return { timestamp, kwh: Number(kwh), cost_eur: cost ? Number(cost) : null };
    })
    .filter((entry) => entry.timestamp && Number.isFinite(entry.kwh));

export default function ConsumptionPage() {
  const [entries, setEntries] = useState([]);
  const [batchText, setBatchText] = useState("");
  const [form, setForm] = useState({ timestamp: "", kwh: "", cost_eur: "", note: "" });
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const loadEntries = async () => {
    try {
      setLoading(true);
      const { data } = await api.get("/consumption");
      setEntries(data.items || []);
    } catch (error) {
      toast.error(extractApiError(error, "Impossibile caricare i consumi"));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEntries();
  }, []);

  const addEntry = async () => {
    try {
      setSubmitting(true);
      await api.post("/consumption", {
        timestamp: form.timestamp,
        kwh: Number(form.kwh),
        cost_eur: form.cost_eur ? Number(form.cost_eur) : null,
        note: form.note || null,
      });
      setForm({ timestamp: "", kwh: "", cost_eur: "", note: "" });
      toast.success("Voce consumo aggiunta");
      await loadEntries();
    } catch (error) {
      toast.error(extractApiError(error, "Inserimento consumo fallito"));
    } finally {
      setSubmitting(false);
    }
  };

  const importBatch = async () => {
    const parsed = parseBatch(batchText);
    if (!parsed.length) {
      toast.error("Incolla almeno una riga valida");
      return;
    }
    try {
      setSubmitting(true);
      await api.post("/consumption/batch", { entries: parsed });
      setBatchText("");
      toast.success("Batch importato");
      await loadEntries();
    } catch (error) {
      toast.error(extractApiError(error, "Import batch fallito"));
    } finally {
      setSubmitting(false);
    }
  };

  const deleteEntry = async (entryId) => {
    try {
      await api.delete(`/consumption/${entryId}`);
      toast.success("Voce eliminata");
      await loadEntries();
    } catch (error) {
      toast.error(extractApiError(error, "Eliminazione non riuscita"));
    }
  };

  const runAnalysis = async () => {
    try {
      await api.post("/analytics/run");
      toast.success("Analisi aggiornata");
    } catch (error) {
      toast.error(extractApiError(error, "Analisi non disponibile"));
    }
  };

  const totalKwh = useMemo(() => entries.reduce((accumulator, entry) => accumulator + Number(entry.kwh || 0), 0), [entries]);

  return (
    <div className="space-y-6">
      <section className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
        <Card className="border-border bg-card shadow-[var(--shadow-md)]">
          <CardHeader>
            <CardTitle className="font-['Space_Grotesk'] text-2xl tracking-[-0.03em]">Inserimento manuale</CardTitle>
            <p className="text-sm leading-6 text-muted-foreground">Registra letture orarie, giornaliere o mensili per sbloccare KPI e forecast.</p>
          </CardHeader>
          <CardContent className="grid gap-4">
            <Input data-testid="manual-entry-date-input" type="datetime-local" className="min-h-11 bg-card" value={form.timestamp} onChange={(event) => setForm((previous) => ({ ...previous, timestamp: event.target.value }))} />
            <Input data-testid="manual-entry-kwh-input" className="min-h-11 bg-card" value={form.kwh} onChange={(event) => setForm((previous) => ({ ...previous, kwh: event.target.value }))} placeholder="kWh" />
            <Input className="min-h-11 bg-card" value={form.cost_eur} onChange={(event) => setForm((previous) => ({ ...previous, cost_eur: event.target.value }))} placeholder="Costo EUR opzionale" />
            <Input className="min-h-11 bg-card" value={form.note} onChange={(event) => setForm((previous) => ({ ...previous, note: event.target.value }))} placeholder="Nota" />
            <div className="flex flex-col gap-3 sm:flex-row">
              <Button data-testid="manual-entry-submit-button" className="min-h-11 flex-1" onClick={addEntry} disabled={submitting}>
                <Plus className="h-4 w-4" />
                Aggiungi voce
              </Button>
              <Button data-testid="run-analysis-from-consumption-button" variant="outline" className="min-h-11 flex-1 bg-card" onClick={runAnalysis}>
                Esegui analisi
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card className="border-border bg-card shadow-[var(--shadow-md)]">
          <CardHeader>
            <CardTitle className="font-['Space_Grotesk'] text-2xl tracking-[-0.03em]">Import rapido batch</CardTitle>
            <p className="text-sm leading-6 text-muted-foreground">Incolla più righe nel formato <strong>timestamp,kWh,costo</strong>.</p>
          </CardHeader>
          <CardContent className="space-y-4">
            <Textarea
              data-testid="manual-entry-form"
              value={batchText}
              onChange={(event) => setBatchText(event.target.value)}
              className="min-h-[220px] resize-none bg-card"
              placeholder={"2026-04-03T08:00,12.4,3.18\n2026-04-03T09:00,13.1,3.42"}
            />
            <Button data-testid="batch-import-button" className="min-h-11 w-full" onClick={importBatch} disabled={submitting}>
              <Upload className="h-4 w-4" />
              Importa batch
            </Button>
          </CardContent>
        </Card>
      </section>

      <Card className="border-border bg-card shadow-[var(--shadow-sm)]">
        <CardContent className="grid gap-3 p-5 sm:grid-cols-3">
          <div className="rounded-2xl bg-secondary p-4">
            <p className="text-sm text-muted-foreground">Righe archiviate</p>
            <p className="mt-2 font-['Space_Grotesk'] text-3xl font-semibold tracking-[-0.02em] text-foreground">{entries.length}</p>
          </div>
          <div className="rounded-2xl bg-secondary p-4">
            <p className="text-sm text-muted-foreground">Consumo totale</p>
            <p className="mt-2 font-['Space_Grotesk'] text-3xl font-semibold tracking-[-0.02em] text-foreground">{totalKwh.toFixed(1)} kWh</p>
          </div>
          <div className="rounded-2xl bg-secondary p-4">
            <p className="text-sm text-muted-foreground">Costo rilevato</p>
            <p className="mt-2 font-['Space_Grotesk'] text-3xl font-semibold tracking-[-0.02em] text-foreground">{formatCurrency(entries.reduce((accumulator, entry) => accumulator + Number(entry.cost_eur || 0), 0))}</p>
          </div>
        </CardContent>
      </Card>

      <Card className="border-border bg-card shadow-[var(--shadow-sm)]">
        <CardHeader>
          <CardTitle className="font-['Space_Grotesk'] text-xl tracking-[-0.02em]">Storico consumi</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Data</TableHead>
                <TableHead>kWh</TableHead>
                <TableHead>Costo</TableHead>
                <TableHead>Nota</TableHead>
                <TableHead className="text-right">Azioni</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {entries.map((entry) => (
                <TableRow key={entry.id}>
                  <TableCell>{formatDateTime(entry.timestamp)}</TableCell>
                  <TableCell>{entry.kwh}</TableCell>
                  <TableCell>{entry.cost_eur ? formatCurrency(entry.cost_eur) : "—"}</TableCell>
                  <TableCell>{entry.note || "—"}</TableCell>
                  <TableCell className="text-right">
                    <Button data-testid={`delete-consumption-${entry.id}`} variant="outline" className="bg-card" onClick={() => deleteEntry(entry.id)}>
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
              {!loading && !entries.length ? (
                <TableRow>
                  <TableCell colSpan={5} className="py-10 text-center text-muted-foreground">Ancora nessuna lettura inserita.</TableCell>
                </TableRow>
              ) : null}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
