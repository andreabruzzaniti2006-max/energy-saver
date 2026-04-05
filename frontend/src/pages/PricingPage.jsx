import { Check, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { useState } from "react";

const plans = [
  {
    name: "Free",
    testId: "pricing-free-card",
    price: "0€",
    description: "Per iniziare a visualizzare sprechi e KPI di base.",
    features: ["1 sede", "Dashboard KPI", "Upload bolletta", "Analisi base"],
  },
  {
    name: "Pro",
    testId: "pricing-pro-card",
    price: "49€/mese",
    description: "Per chi vuole forecast avanzati, report completi e più controllo.",
    features: ["Predizioni avanzate", "Report PDF completi", "Alert email", "Scalabilità multi-sede"],
  },
];

export default function PricingPage() {
  const [open, setOpen] = useState(false);

  return (
    <div className="space-y-6">
      <section className="rounded-[28px] border border-border bg-card p-6 shadow-[var(--shadow-md)] lg:p-8">
        <Badge className="rounded-full bg-secondary text-secondary-foreground">Monetizzazione V1</Badge>
        <h2 className="mt-4 font-['Space_Grotesk'] text-4xl font-semibold tracking-[-0.04em] text-foreground">Scegli il piano giusto per crescere dal controllo base all’ottimizzazione continua.</h2>
        <p className="mt-4 max-w-3xl text-base leading-7 text-muted-foreground">In questa release il billing reale non è attivo, ma l’interfaccia è pronta per differenziare chiaramente il valore di Free e Pro.</p>
      </section>

      <div className="grid gap-4 lg:grid-cols-2">
        {plans.map((plan) => (
          <Card key={plan.name} data-testid={plan.testId} className={`border-border bg-card shadow-[var(--shadow-md)] ${plan.name === "Pro" ? "border-primary" : ""}`}>
            <CardHeader className="space-y-4">
              <div className="flex items-center justify-between gap-3">
                <CardTitle className="font-['Space_Grotesk'] text-3xl tracking-[-0.03em] text-foreground">{plan.name}</CardTitle>
                {plan.name === "Pro" ? <Badge className="rounded-full bg-primary text-primary-foreground">Consigliato</Badge> : null}
              </div>
              <p className="font-['Space_Grotesk'] text-5xl font-semibold tracking-[-0.04em] text-foreground">{plan.price}</p>
              <p className="text-sm leading-6 text-muted-foreground">{plan.description}</p>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                {plan.features.map((feature) => (
                  <div key={feature} className="flex items-center gap-3 rounded-2xl bg-secondary p-4">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-card">
                      <Check className="h-4 w-4 text-primary" />
                    </div>
                    <span className="text-sm font-medium text-foreground">{feature}</span>
                  </div>
                ))}
              </div>
              <Button data-testid={plan.name === "Pro" ? "upgrade-to-pro-button" : "start-free-button"} className="min-h-11 w-full" variant={plan.name === "Pro" ? "default" : "outline"} onClick={() => setOpen(true)}>
                {plan.name === "Pro" ? "Passa a Pro" : "Resta su Free"}
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="bg-background">
          <DialogHeader>
            <DialogTitle>Billing in arrivo</DialogTitle>
            <DialogDescription>La monetizzazione reale non è ancora attiva in questa V1, ma la struttura UI è pronta per collegare il checkout.</DialogDescription>
          </DialogHeader>
          <div className="rounded-2xl bg-secondary p-5">
            <div className="mb-3 flex items-center gap-3 text-foreground">
              <Sparkles className="h-5 w-5 text-primary" />
              <span className="font-medium">Coming soon</span>
            </div>
            <p className="text-sm leading-6 text-muted-foreground">Possiamo collegare il piano Pro a un provider pagamenti nella prossima iterazione senza rifare la UX.</p>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
