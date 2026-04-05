import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { formatDateTime } from "@/lib/api";

const categoryLabels = {
  all: "Tutte",
  anomaly: "Sprechi",
  forecast: "Costi",
  savings: "Risparmio",
};

const NotificationList = ({ items = [] }) => {
  if (!items.length) {
    return <p className="rounded-2xl bg-secondary p-4 text-sm text-muted-foreground">Nessuna notifica disponibile.</p>;
  }

  return (
    <div className="space-y-3">
      {items.map((item) => (
        <div key={item.id} data-testid="notification-item" className="rounded-2xl border border-border bg-card p-4 shadow-[var(--shadow-sm)]">
          <div className="mb-2 flex items-center justify-between gap-3">
            <Badge className="rounded-full bg-secondary text-secondary-foreground">{item.type}</Badge>
            {!item.read ? <Badge className="rounded-full bg-primary text-primary-foreground">Nuovo</Badge> : null}
          </div>
          <p className="font-medium text-foreground">{item.title}</p>
          <p className="mt-2 text-sm leading-6 text-muted-foreground">{item.message}</p>
          <p className="mt-3 text-xs uppercase tracking-[0.18em] text-muted-foreground">{formatDateTime(item.created_at)}</p>
        </div>
      ))}
    </div>
  );
};

export const NotificationsCenter = ({ open, onOpenChange, items, unreadCount, onMarkAllRead }) => {
  const filtered = {
    all: items,
    anomaly: items.filter((item) => item.type === "anomaly"),
    forecast: items.filter((item) => item.type === "forecast"),
    savings: items.filter((item) => item.type === "savings"),
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-full max-w-xl bg-background sm:max-w-xl">
        <SheetHeader className="mb-6">
          <SheetTitle>Centro notifiche</SheetTitle>
          <SheetDescription>Alert, forecast costi e opportunità di risparmio per la tua sede.</SheetDescription>
        </SheetHeader>

        <div className="mb-4 flex items-center justify-between gap-3 rounded-2xl bg-secondary p-4">
          <div>
            <p className="text-sm font-medium text-foreground">{unreadCount} non lette</p>
            <p className="text-sm text-muted-foreground">Aggiornate dopo ogni analisi o report.</p>
          </div>
          <Button data-testid="mark-all-read-button" variant="outline" className="bg-card" onClick={onMarkAllRead}>
            Segna tutte lette
          </Button>
        </div>

        <Tabs defaultValue="all" className="space-y-4">
          <TabsList data-testid="notifications-tabs" className="grid w-full grid-cols-4 bg-secondary">
            {Object.entries(categoryLabels).map(([value, label]) => (
              <TabsTrigger key={value} value={value} className="min-h-11 text-xs sm:text-sm">
                {label}
              </TabsTrigger>
            ))}
          </TabsList>
          {Object.entries(filtered).map(([key, value]) => (
            <TabsContent key={key} value={key} className="focus-visible:outline-none">
              <NotificationList items={value} />
            </TabsContent>
          ))}
        </Tabs>
      </SheetContent>
    </Sheet>
  );
};
