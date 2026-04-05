import { useEffect, useMemo, useState } from "react";
import { FileSearch, UploadCloud } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { toast } from "@/components/ui/sonner";
import { api, extractApiError, formatCurrency, formatDateTime } from "@/lib/api";

export default function BillsPage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [selectedBill, setSelectedBill] = useState(null);
  const [reviewForm, setReviewForm] = useState({ consumption_kwh: "", total_cost_eur: "", period_start: "", period_end: "", notes: "" });

  const loadBills = async () => {
    try {
      setLoading(true);
      const { data } = await api.get("/bills");
      setItems(data.items || []);
    } catch (error) {
      toast.error(extractApiError(error, "Impossibile caricare le bollette"));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadBills();
  }, []);

  const handleUpload = async () => {
    if (!selectedFile) {
      toast.error("Seleziona un PDF prima di caricare");
      return;
    }
    try {
      setUploading(true);
      const formData = new FormData();
      formData.append("file", selectedFile);
      const { data } = await api.post("/bills/upload", formData, { headers: { "Content-Type": "multipart/form-data" } });
      setSelectedFile(null);
      toast.success("Bolletta caricata con successo");
      if (data.bill?.extraction_status !== "parsed") {
        openReview(data.bill);
        toast.message("Bolletta caricata ma da rivedere: completa consumo, costo e periodo per sbloccare l’analisi.");
      }
      await loadBills();
    } catch (error) {
      toast.error(extractApiError(error, "Upload bolletta fallito"));
    } finally {
      setUploading(false);
    }
  };

  const openReview = (bill) => {
    setSelectedBill(bill);
    setReviewForm({
      consumption_kwh: bill.extracted_fields?.consumption_kwh ?? "",
      total_cost_eur: bill.extracted_fields?.total_cost_eur ?? "",
      period_start: bill.extracted_fields?.period_start ?? "",
      period_end: bill.extracted_fields?.period_end ?? "",
      notes: bill.notes ?? "",
    });
  };

  const saveReview = async () => {
    try {
      await api.patch(`/bills/${selectedBill.id}`, {
        consumption_kwh: reviewForm.consumption_kwh === "" ? null : Number(reviewForm.consumption_kwh),
        total_cost_eur: reviewForm.total_cost_eur === "" ? null : Number(reviewForm.total_cost_eur),
        period_start: reviewForm.period_start || null,
        period_end: reviewForm.period_end || null,
        notes: reviewForm.notes,
      });
      toast.success("Revisione salvata");
      setSelectedBill(null);
      await loadBills();
    } catch (error) {
      toast.error(extractApiError(error, "Salvataggio revisione fallito"));
    }
  };

  const billStats = useMemo(() => ({
    parsed: items.filter((item) => item.extraction_status === "parsed").length,
    pending: items.filter((item) => item.extraction_status !== "parsed").length,
  }), [items]);

  return (
    <div className="space-y-6">
      <section className="grid gap-4 xl:grid-cols-[0.95fr_1.05fr]">
        <Card className="border-border bg-card shadow-[var(--shadow-md)]">
          <CardHeader>
            <CardTitle className="font-['Space_Grotesk'] text-2xl tracking-[-0.03em]">Carica bollette PDF</CardTitle>
            <p className="text-sm leading-6 text-muted-foreground">Upload sicuro in locale/Mongo e parsing best-effort per consumo, costo e periodo.</p>
          </CardHeader>
          <CardContent className="space-y-4">
            <label data-testid="bill-upload-dropzone" className="flex min-h-[260px] cursor-pointer flex-col items-center justify-center rounded-[28px] border border-dashed border-border bg-secondary p-6 text-center">
              <input data-testid="bill-upload-input" type="file" accept="application/pdf" className="hidden" onChange={(event) => setSelectedFile(event.target.files?.[0] || null)} />
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-card">
                <UploadCloud className="h-6 w-6 text-primary" />
              </div>
              <p className="mt-4 font-medium text-foreground">Trascina o seleziona una bolletta</p>
              <p className="mt-2 max-w-sm text-sm leading-6 text-muted-foreground">Il sistema mostra subito lo stato estrazione: Estratta o Needs review.</p>
              {selectedFile ? <span className="mt-4 rounded-full bg-card px-3 py-1 text-xs font-medium text-foreground">{selectedFile.name}</span> : null}
            </label>
            <Button data-testid="bill-upload-submit-button" className="min-h-11 w-full" onClick={handleUpload} disabled={uploading}>
              {uploading ? "Caricamento..." : "Carica PDF"}
            </Button>
          </CardContent>
        </Card>

        <div className="grid gap-4">
          <Card className="border-border bg-card shadow-[var(--shadow-sm)]">
            <CardContent className="grid gap-3 p-5 sm:grid-cols-3">
              <div className="rounded-2xl bg-secondary p-4">
                <p className="text-sm text-muted-foreground">Totale bollette</p>
                <p className="mt-2 font-['Space_Grotesk'] text-3xl font-semibold tracking-[-0.02em] text-foreground">{items.length}</p>
              </div>
              <div className="rounded-2xl bg-secondary p-4">
                <p className="text-sm text-muted-foreground">Estratte</p>
                <p className="mt-2 font-['Space_Grotesk'] text-3xl font-semibold tracking-[-0.02em] text-foreground">{billStats.parsed}</p>
              </div>
              <div className="rounded-2xl bg-secondary p-4">
                <p className="text-sm text-muted-foreground">Da rivedere</p>
                <p className="mt-2 font-['Space_Grotesk'] text-3xl font-semibold tracking-[-0.02em] text-foreground">{billStats.pending}</p>
              </div>
            </CardContent>
          </Card>

          <Card className="border-border bg-card shadow-[var(--shadow-sm)]">
            <CardHeader>
              <CardTitle className="font-['Space_Grotesk'] text-xl tracking-[-0.02em]">Coda revisione</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {items.slice(0, 4).map((bill) => (
                <div key={bill.id} className="flex items-center justify-between gap-3 rounded-2xl bg-secondary p-4">
                  <div>
                    <p className="font-medium text-foreground">{bill.filename}</p>
                    <p className="text-sm text-muted-foreground">{formatDateTime(bill.uploaded_at)}</p>
                  </div>
                  <Badge className="rounded-full bg-card text-foreground">{bill.extraction_status}</Badge>
                </div>
              ))}
              {!items.length ? <div className="rounded-2xl bg-secondary p-4 text-sm text-muted-foreground">Ancora nessuna bolletta caricata.</div> : null}
            </CardContent>
          </Card>
        </div>
      </section>

      <Card className="border-border bg-card shadow-[var(--shadow-sm)]">
        <CardHeader className="flex flex-row items-center justify-between gap-3">
          <div>
            <CardTitle className="font-['Space_Grotesk'] text-xl tracking-[-0.02em]">Archivio bollette</CardTitle>
            <p className="mt-1 text-sm text-muted-foreground">Stato parsing, costi estratti e revisione manuale.</p>
          </div>
          <Badge className="rounded-full bg-secondary text-secondary-foreground">{loading ? "Loading" : `${items.length} file`}</Badge>
        </CardHeader>
        <CardContent>
          <Table data-testid="bills-table">
            <TableHeader>
              <TableRow>
                <TableHead>File</TableHead>
                <TableHead>Upload</TableHead>
                <TableHead>Consumo</TableHead>
                <TableHead>Costo</TableHead>
                <TableHead>Stato</TableHead>
                <TableHead className="text-right">Azioni</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {items.map((bill) => (
                <TableRow key={bill.id}>
                  <TableCell className="font-medium text-foreground">{bill.filename}</TableCell>
                  <TableCell>{formatDateTime(bill.uploaded_at)}</TableCell>
                  <TableCell>{bill.extracted_fields?.consumption_kwh ? `${bill.extracted_fields.consumption_kwh} kWh` : "—"}</TableCell>
                  <TableCell>{bill.extracted_fields?.total_cost_eur ? formatCurrency(bill.extracted_fields.total_cost_eur) : "—"}</TableCell>
                  <TableCell><Badge className="rounded-full bg-secondary text-secondary-foreground">{bill.extraction_status}</Badge></TableCell>
                  <TableCell className="text-right">
                    <Button data-testid="bill-preview-open-button" variant="outline" className="bg-card" onClick={() => openReview(bill)}>
                      <FileSearch className="h-4 w-4" />
                      Rivedi
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Dialog open={Boolean(selectedBill)} onOpenChange={(open) => !open && setSelectedBill(null)}>
        <DialogContent className="max-w-2xl bg-background">
          <DialogHeader>
            <DialogTitle>Revisione bolletta</DialogTitle>
            <DialogDescription>Correggi i campi estratti per migliorare analisi e report.</DialogDescription>
          </DialogHeader>
          {selectedBill ? (
            <div className="grid gap-4 md:grid-cols-2">
              <Input value={reviewForm.consumption_kwh} onChange={(event) => setReviewForm((previous) => ({ ...previous, consumption_kwh: event.target.value }))} placeholder="Consumo kWh" className="min-h-11 bg-card" />
              <Input value={reviewForm.total_cost_eur} onChange={(event) => setReviewForm((previous) => ({ ...previous, total_cost_eur: event.target.value }))} placeholder="Costo totale EUR" className="min-h-11 bg-card" />
              <Input value={reviewForm.period_start} onChange={(event) => setReviewForm((previous) => ({ ...previous, period_start: event.target.value }))} placeholder="Periodo inizio (dd/mm/yyyy)" className="min-h-11 bg-card" />
              <Input value={reviewForm.period_end} onChange={(event) => setReviewForm((previous) => ({ ...previous, period_end: event.target.value }))} placeholder="Periodo fine (dd/mm/yyyy)" className="min-h-11 bg-card" />
              <Input value={reviewForm.notes} onChange={(event) => setReviewForm((previous) => ({ ...previous, notes: event.target.value }))} placeholder="Note revisione" className="min-h-11 bg-card md:col-span-2" />
              <div className="rounded-2xl bg-secondary p-4 md:col-span-2">
                <p className="text-sm text-muted-foreground">Preview parsing</p>
                <p className="mt-2 text-sm leading-6 text-foreground">{selectedBill.extracted_fields?.raw_text_preview || "Anteprima non disponibile"}</p>
              </div>
              <Button data-testid="bill-review-save-button" className="min-h-11 md:col-span-2" onClick={saveReview}>Salva revisione</Button>
            </div>
          ) : null}
        </DialogContent>
      </Dialog>
    </div>
  );
}
