import { useMemo, useState } from "react";
import { useNavigate, useOutletContext } from "react-router-dom";
import { CalendarClock, ChevronRight, Factory, MapPin, UploadCloud } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { toast } from "@/components/ui/sonner";
import { api, extractApiError } from "@/lib/api";

const parseManualEntries = (text) => {
  return text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const [timestamp, kwh, cost] = line.split(",").map((item) => item.trim());
      return {
        timestamp,
        kwh: Number(kwh),
        cost_eur: cost ? Number(cost) : null,
      };
    })
    .filter((item) => item.timestamp && Number.isFinite(item.kwh));
};

const steps = [
  { title: "Azienda", caption: "Settore e ragione sociale" },
  { title: "Sede", caption: "Posizione e orari operativi" },
  { title: "Primi dati", caption: "Bolletta PDF o righe manuali" },
  { title: "Obiettivi", caption: "Target risparmio e conferma" },
];

export default function OnboardingPage() {
  const navigate = useNavigate();
  const { session, refreshSession } = useOutletContext();
  const [currentStep, setCurrentStep] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [manualText, setManualText] = useState("");
  const [form, setForm] = useState({
    company_name: session.org?.name || "Energy Saver Demo",
    sector: session.site?.sector || "bar",
    site_name: session.site?.name || "Sede principale",
    city: session.site?.city || "Milano",
    latitude: String(session.site?.latitude || 45.4642),
    longitude: String(session.site?.longitude || 9.19),
    business_open_hour: String(session.site?.business_open_hour || 6),
    business_close_hour: String(session.site?.business_close_hour || 18),
    savings_goal_pct: String(session.site?.savings_goal_pct || 12),
  });

  const progressValue = useMemo(() => ((currentStep + 1) / steps.length) * 100, [currentStep]);

  const updateField = (key, value) => setForm((previous) => ({ ...previous, [key]: value }));

  const submitOnboarding = async () => {
    try {
      setSubmitting(true);
      await api.post("/onboarding/complete", {
        company_name: form.company_name,
        sector: form.sector,
        site_name: form.site_name,
        city: form.city,
        latitude: Number(form.latitude),
        longitude: Number(form.longitude),
        business_open_hour: Number(form.business_open_hour),
        business_close_hour: Number(form.business_close_hour),
        savings_goal_pct: Number(form.savings_goal_pct),
      });

      const parsedEntries = parseManualEntries(manualText);
      if (selectedFile) {
        const formData = new FormData();
        formData.append("file", selectedFile);
        await api.post("/bills/upload", formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });
      }
      if (parsedEntries.length) {
        await api.post("/consumption/batch", { entries: parsedEntries });
      }
      if (selectedFile || parsedEntries.length) {
        await api.post("/analytics/run");
      }

      await refreshSession();
      toast.success("Onboarding completato");
      navigate("/dashboard");
    } catch (error) {
      toast.error(extractApiError(error, "Onboarding non completato"));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,0.8fr)_minmax(0,1.2fr)]">
      <Card className="h-fit border-border bg-card shadow-[var(--shadow-md)]">
        <CardHeader className="space-y-5">
          <Badge className="w-fit rounded-full bg-secondary text-secondary-foreground">Onboarding guidato</Badge>
          <div>
            <CardTitle className="font-['Space_Grotesk'] text-3xl tracking-[-0.03em] text-foreground">Attiva la tua cabina di controllo energetica</CardTitle>
            <p className="mt-3 text-sm leading-6 text-muted-foreground">Configura la sede, collega i primi dati e ottieni le prime raccomandazioni con ROI.</p>
          </div>
          <Progress value={progressValue} />
          <div className="grid gap-3">
            {steps.map((step, index) => (
              <div key={step.title} className={`rounded-2xl border p-4 ${index === currentStep ? "border-primary bg-secondary" : "border-border bg-card"}`}>
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-medium text-foreground">{index + 1}. {step.title}</p>
                    <p className="mt-1 text-sm text-muted-foreground">{step.caption}</p>
                  </div>
                  <span className="text-xs uppercase tracking-[0.22em] text-muted-foreground">Step {index + 1}</span>
                </div>
              </div>
            ))}
          </div>
        </CardHeader>
      </Card>

      <Card className="border-border bg-card shadow-[var(--shadow-md)]">
        <CardHeader className="space-y-3">
          <CardTitle className="font-['Space_Grotesk'] text-2xl tracking-[-0.03em] text-foreground">{steps[currentStep].title}</CardTitle>
          <p className="text-sm leading-6 text-muted-foreground">{steps[currentStep].caption}</p>
        </CardHeader>
        <CardContent className="space-y-6">
          {currentStep === 0 ? (
            <div className="grid gap-4 md:grid-cols-2">
              <div className="rounded-2xl bg-secondary p-4">
                <div className="mb-3 flex items-center gap-2 text-sm font-medium text-foreground"><Factory className="h-4 w-4" /> Azienda</div>
                <Input data-testid="company-name-input" className="min-h-11 bg-card" value={form.company_name} onChange={(event) => updateField("company_name", event.target.value)} placeholder="Nome azienda" />
              </div>
              <div className="rounded-2xl bg-secondary p-4">
                <div className="mb-3 text-sm font-medium text-foreground">Settore</div>
                <Select value={form.sector} onValueChange={(value) => updateField("sector", value)}>
                  <SelectTrigger data-testid="sector-select-trigger" className="min-h-11 bg-card">
                    <SelectValue placeholder="Seleziona settore" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="bar">Bar</SelectItem>
                    <SelectItem value="ristorante">Ristorante</SelectItem>
                    <SelectItem value="palestra">Palestra</SelectItem>
                    <SelectItem value="altro">Altro</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          ) : null}

          {currentStep === 1 ? (
            <div className="grid gap-4 md:grid-cols-2">
              <div className="rounded-2xl bg-secondary p-4 md:col-span-2">
                <div className="mb-3 flex items-center gap-2 text-sm font-medium text-foreground"><MapPin className="h-4 w-4" /> Sede</div>
                <Input data-testid="site-name-input" className="min-h-11 bg-card" value={form.site_name} onChange={(event) => updateField("site_name", event.target.value)} placeholder="Nome sede" />
              </div>
              <Input data-testid="city-input" className="min-h-11 bg-card" value={form.city} onChange={(event) => updateField("city", event.target.value)} placeholder="Città" />
              <Input data-testid="latitude-input" className="min-h-11 bg-card" value={form.latitude} onChange={(event) => updateField("latitude", event.target.value)} placeholder="Latitudine" />
              <Input data-testid="longitude-input" className="min-h-11 bg-card" value={form.longitude} onChange={(event) => updateField("longitude", event.target.value)} placeholder="Longitudine" />
              <Input data-testid="business-open-hour-input" className="min-h-11 bg-card" value={form.business_open_hour} onChange={(event) => updateField("business_open_hour", event.target.value)} placeholder="Ora apertura" />
              <Input data-testid="business-close-hour-input" className="min-h-11 bg-card" value={form.business_close_hour} onChange={(event) => updateField("business_close_hour", event.target.value)} placeholder="Ora chiusura" />
            </div>
          ) : null}

          {currentStep === 2 ? (
            <div className="grid gap-4 xl:grid-cols-2">
              <div className="rounded-2xl bg-secondary p-4">
                <div className="mb-3 flex items-center gap-2 text-sm font-medium text-foreground"><UploadCloud className="h-4 w-4" /> Carica bolletta PDF</div>
                <label data-testid="bill-upload-dropzone" className="flex min-h-[220px] cursor-pointer flex-col items-center justify-center rounded-2xl border border-dashed border-border bg-card p-6 text-center">
                  <input
                    data-testid="bill-upload-input"
                    type="file"
                    accept="application/pdf"
                    className="hidden"
                    onChange={(event) => setSelectedFile(event.target.files?.[0] || null)}
                  />
                  <p className="font-medium text-foreground">Seleziona PDF bolletta</p>
                  <p className="mt-2 text-sm leading-6 text-muted-foreground">Parsing best-effort con possibilità di revisione successiva.</p>
                  {selectedFile ? <span className="mt-4 rounded-full bg-secondary px-3 py-1 text-xs font-medium text-foreground">{selectedFile.name}</span> : null}
                </label>
              </div>
              <div className="rounded-2xl bg-secondary p-4">
                <div className="mb-3 flex items-center gap-2 text-sm font-medium text-foreground"><CalendarClock className="h-4 w-4" /> Inserimento manuale</div>
                <Textarea
                  data-testid="manual-entry-textarea"
                  value={manualText}
                  onChange={(event) => setManualText(event.target.value)}
                  className="min-h-[220px] resize-none bg-card"
                  placeholder={"Formato: 2026-04-01T08:00,12.4,3.18\n2026-04-01T09:00,13.1,3.42"}
                />
                <p className="mt-3 text-xs leading-5 text-muted-foreground">Timestamp ISO, kWh, costo opzionale separati da virgola.</p>
              </div>
            </div>
          ) : null}

          {currentStep === 3 ? (
            <div className="grid gap-4 lg:grid-cols-[1fr_0.8fr]">
              <div className="rounded-2xl bg-secondary p-5">
                <p className="text-sm font-medium text-foreground">Target economico</p>
                <Input
                  data-testid="savings-goal-input"
                  className="mt-3 min-h-11 bg-card"
                  value={form.savings_goal_pct}
                  onChange={(event) => updateField("savings_goal_pct", event.target.value)}
                  placeholder="12"
                />
                <p className="mt-3 text-sm leading-6 text-muted-foreground">Definisci una soglia iniziale di miglioramento per prioritizzare raccomandazioni e notifiche.</p>
              </div>
              <div className="rounded-2xl border border-border bg-card p-5">
                <p className="text-sm uppercase tracking-[0.22em] text-muted-foreground">Riepilogo</p>
                <div className="mt-4 space-y-3 text-sm text-foreground">
                  <p><strong>Azienda:</strong> {form.company_name}</p>
                  <p><strong>Sede:</strong> {form.site_name} · {form.city}</p>
                  <p><strong>Settore:</strong> {form.sector}</p>
                  <p><strong>Dati iniziali:</strong> {selectedFile ? "PDF pronto" : "nessun PDF"} · {parseManualEntries(manualText).length} righe manuali</p>
                  <p><strong>Obiettivo risparmio:</strong> {form.savings_goal_pct}%</p>
                </div>
              </div>
            </div>
          ) : null}

          <div className="flex flex-col gap-3 border-t border-border pt-6 sm:flex-row sm:items-center sm:justify-between">
            <Button
              data-testid="onboarding-back-button"
              variant="outline"
              className="min-h-11 bg-card"
              onClick={() => setCurrentStep((step) => Math.max(0, step - 1))}
              disabled={currentStep === 0 || submitting}
            >
              Indietro
            </Button>
            {currentStep < steps.length - 1 ? (
              <Button data-testid="onboarding-next-button" className="min-h-11" onClick={() => setCurrentStep((step) => Math.min(steps.length - 1, step + 1))}>
                Continua
                <ChevronRight className="h-4 w-4" />
              </Button>
            ) : (
              <Button data-testid="onboarding-submit-button" className="min-h-11" onClick={submitOnboarding} disabled={submitting}>
                Completa configurazione
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
