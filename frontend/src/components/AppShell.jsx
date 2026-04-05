import { useEffect, useMemo, useState } from "react";
import { Link, NavLink, useLocation } from "react-router-dom";
import { Bell, BookOpenText, ChartColumnIncreasing, CircleDollarSign, FileBarChart2, Gauge, Menu, Settings, UploadCloud } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { Separator } from "@/components/ui/separator";
import { api } from "@/lib/api";
import { NotificationsCenter } from "@/components/NotificationsCenter";

const navigation = [
  { to: "/dashboard", label: "Dashboard", icon: Gauge },
  { to: "/bills", label: "Bolletta", icon: UploadCloud },
  { to: "/consumption", label: "Consumi", icon: ChartColumnIncreasing },
  { to: "/insights", label: "Insights", icon: CircleDollarSign },
  { to: "/reports", label: "Report", icon: FileBarChart2 },
  { to: "/pricing", label: "Piani", icon: BookOpenText },
  { to: "/settings", label: "Impostazioni", icon: Settings },
];

const SidebarNav = ({ session, onLogout, onNavigate }) => (
  <div className="flex h-full flex-col justify-between">
    <div>
      <div className="mb-8 rounded-2xl border border-border bg-card p-4 shadow-[var(--shadow-sm)]">
        <div className="mb-3 flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-primary text-primary-foreground">ES</div>
          <div>
            <p className="font-['Space_Grotesk'] text-sm font-semibold tracking-[-0.02em]">Energy Saver</p>
            <p className="text-xs text-muted-foreground">Ottimizzazione consumi</p>
          </div>
        </div>
        <div className="rounded-xl bg-secondary p-3">
          <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Piano</p>
          <div className="mt-2 flex items-center justify-between gap-3">
            <span className="font-medium text-foreground">{session.org?.plan === "free" ? "Free" : session.org?.plan}</span>
            <Badge className="rounded-full bg-accent text-accent-foreground">PMI</Badge>
          </div>
        </div>
      </div>

      <nav className="space-y-1.5">
        {navigation.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              data-testid={`nav-${item.label.toLowerCase()}`}
              onClick={onNavigate}
              className={({ isActive }) =>
                [
                  "flex min-h-11 items-center gap-3 rounded-xl px-3 py-2 text-sm font-medium transition-colors duration-200",
                  isActive ? "bg-primary text-primary-foreground shadow-[var(--shadow-sm)]" : "text-muted-foreground hover:bg-secondary hover:text-foreground",
                ].join(" ")
              }
            >
              <Icon className="h-4 w-4" />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>
    </div>

    <div className="space-y-4 rounded-2xl border border-border bg-card p-4 shadow-[var(--shadow-sm)]">
      <div>
        <p className="text-sm font-semibold text-foreground">{session.user?.name}</p>
        <p className="text-xs text-muted-foreground">{session.user?.email}</p>
      </div>
      <Separator />
      <Button data-testid="logout-button" variant="outline" className="w-full justify-start bg-card" onClick={onLogout}>
        Esci
      </Button>
    </div>
  </div>
);

export const AppShell = ({ session, onLogout, children }) => {
  const location = useLocation();
  const [notificationData, setNotificationData] = useState({ items: [], unread_count: 0 });
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const pageTitle = useMemo(() => navigation.find((item) => item.to === location.pathname)?.label || "Energy Saver", [location.pathname]);

  const fetchNotifications = async () => {
    try {
      const { data } = await api.get("/notifications");
      setNotificationData(data);
    } catch (error) {
      setNotificationData({ items: [], unread_count: 0 });
    }
  };

  useEffect(() => {
    fetchNotifications();
  }, [location.pathname]);

  const markAllRead = async () => {
    await api.post("/notifications/mark-all-read");
    await fetchNotifications();
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="mx-auto flex min-h-screen w-full max-w-[1500px] gap-0">
        <aside className="hidden w-[272px] border-r border-border bg-secondary px-5 py-6 lg:block">
          <SidebarNav session={session} onLogout={onLogout} />
        </aside>

        <div className="flex min-h-screen flex-1 flex-col">
          <header className="sticky top-0 z-20 border-b border-border bg-background px-4 py-4 sm:px-6 lg:px-8">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <Sheet>
                  <SheetTrigger asChild>
                    <Button data-testid="mobile-menu-button" variant="outline" size="icon" className="bg-card lg:hidden">
                      <Menu className="h-4 w-4" />
                    </Button>
                  </SheetTrigger>
                  <SheetContent side="left" className="w-[320px] bg-background">
                    <SheetHeader className="mb-6">
                      <SheetTitle>Navigazione</SheetTitle>
                      <SheetDescription>Accedi rapidamente a dashboard, bollette, consumi e report.</SheetDescription>
                    </SheetHeader>
                    <SidebarNav session={session} onLogout={onLogout} onNavigate={() => {}} />
                  </SheetContent>
                </Sheet>
                <div>
                  <p className="text-xs uppercase tracking-[0.24em] text-muted-foreground">SaaS Energy Ops</p>
                  <h1 className="font-['Space_Grotesk'] text-2xl font-semibold tracking-[-0.03em] text-foreground">{pageTitle}</h1>
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <Button data-testid="date-range-trigger" variant="outline" className="min-h-11 bg-card">
                  Ultimi 30 giorni
                </Button>
                <Button asChild data-testid="upload-bill-button" className="min-h-11">
                  <Link to="/bills">Aggiungi bolletta</Link>
                </Button>
                <Button
                  data-testid="notifications-open-button"
                  variant="outline"
                  className="relative min-h-11 bg-card"
                  onClick={() => setNotificationsOpen(true)}
                  aria-label="Apri notifiche"
                >
                  <Bell className="h-4 w-4" />
                  {notificationData.unread_count > 0 ? (
                    <span className="absolute -right-1 -top-1 flex h-5 min-w-5 items-center justify-center rounded-full bg-primary px-1 text-[10px] font-semibold text-primary-foreground">
                      {notificationData.unread_count}
                    </span>
                  ) : null}
                </Button>
              </div>
            </div>
          </header>

          <main className="flex-1 px-4 py-6 sm:px-6 lg:px-8">{children}</main>
        </div>
      </div>

      <NotificationsCenter
        open={notificationsOpen}
        onOpenChange={setNotificationsOpen}
        items={notificationData.items}
        unreadCount={notificationData.unread_count}
        onMarkAllRead={markAllRead}
      />
    </div>
  );
};
