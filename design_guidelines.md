{
  "brand_attributes": {
    "tone": ["minimal", "moderno", "SaaS premium tipo Stripe", "orientato al valore economico", "affidabile"],
    "visual_metaphor": "Energy clarity: sabbia chiara (calma) + teal (azione/risparmio) + slate (precisione dati).",
    "do_not": [
      "No transparent backgrounds (niente glassmorphism).",
      "No layout centrati tipo landing generica: usare griglie, sidebar, contenuto allineato a sinistra.",
      "No gradient scuri/saturi (vedi regole in fondo).",
      "No emoji per icone: usare lucide-react o FontAwesome."
    ]
  },
  "design_tokens": {
    "css_custom_properties": {
      "location": "/app/frontend/src/index.css (sostituire i token :root e .dark)",
      "light": {
        "--background": "36 33% 96%",
        "--foreground": "200 18% 14%",
        "--card": "0 0% 100%",
        "--card-foreground": "200 18% 14%",
        "--popover": "0 0% 100%",
        "--popover-foreground": "200 18% 14%",
        "--primary": "184 55% 28%",
        "--primary-foreground": "0 0% 98%",
        "--secondary": "36 25% 90%",
        "--secondary-foreground": "200 18% 14%",
        "--muted": "36 18% 92%",
        "--muted-foreground": "200 10% 40%",
        "--accent": "164 22% 78%",
        "--accent-foreground": "200 18% 14%",
        "--destructive": "0 72% 52%",
        "--destructive-foreground": "0 0% 98%",
        "--border": "36 14% 84%",
        "--input": "36 14% 84%",
        "--ring": "184 55% 28%",
        "--radius": "0.75rem",
        "--chart-1": "184 55% 28%",
        "--chart-2": "164 35% 34%",
        "--chart-3": "200 18% 22%",
        "--chart-4": "36 55% 55%",
        "--chart-5": "18 70% 55%"
      },
      "dark_optional": {
        "note": "Dark mode opzionale; se abilitato, mantenerlo neutro (slate) con teal come accento. Non usare gradienti scuri.",
        "--background": "200 18% 10%",
        "--foreground": "0 0% 98%",
        "--card": "200 18% 12%",
        "--card-foreground": "0 0% 98%",
        "--primary": "184 55% 45%",
        "--primary-foreground": "200 18% 10%",
        "--secondary": "200 14% 18%",
        "--secondary-foreground": "0 0% 98%",
        "--muted": "200 14% 18%",
        "--muted-foreground": "200 10% 70%",
        "--accent": "164 22% 28%",
        "--accent-foreground": "0 0% 98%",
        "--border": "200 14% 22%",
        "--input": "200 14% 22%",
        "--ring": "184 55% 45%"
      },
      "extra_tokens_add": {
        "--shadow-sm": "0 1px 2px rgba(15, 23, 42, 0.06)",
        "--shadow-md": "0 10px 25px rgba(15, 23, 42, 0.08)",
        "--shadow-lg": "0 18px 45px rgba(15, 23, 42, 0.10)",
        "--surface-1": "hsl(var(--card))",
        "--surface-2": "hsl(var(--secondary))",
        "--focus-outline": "0 0 0 3px hsl(var(--ring) / 0.25)",
        "--grid-max": "72rem"
      }
    },
    "palette_hex_reference": {
      "bg_sand": "#F4EBDD",
      "sand_2": "#E7D7C1",
      "primary_teal": "#2D8A8A",
      "sage": "#9AA79A",
      "slate_text": "#1E2D2D",
      "muted_text": "#5B6B70",
      "danger": "#E5484D",
      "warning": "#C58B2B",
      "success": "#1F8A5B"
    },
    "spacing_system": {
      "rule": "Usare 2–3x più spazio del normale: padding card 16–20px mobile, 20–24px desktop; gap griglie 12–16px.",
      "tailwind": {
        "page_padding": "px-4 sm:px-6 lg:px-8",
        "section_spacing": "py-6 sm:py-8",
        "card_padding": "p-4 sm:p-5",
        "grid_gap": "gap-3 sm:gap-4"
      }
    },
    "radius": {
      "default": "rounded-xl",
      "inputs": "rounded-lg",
      "chips_badges": "rounded-full"
    }
  },
  "typography": {
    "font_pairing": {
      "heading": "Space Grotesk (600/700)",
      "body": "Work Sans (400/500)",
      "mono_optional": "IBM Plex Mono (per valori tecnici, id, timestamp)"
    },
    "implementation": {
      "google_fonts": [
        "https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Work+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap"
      ],
      "tailwind_usage": {
        "app_shell": "font-sans",
        "headings": "font-[\"Space Grotesk\"] tracking-[-0.02em]",
        "body": "font-[\"Work Sans\"]",
        "numbers": "tabular-nums"
      }
    },
    "text_size_hierarchy": {
      "h1": "text-4xl sm:text-5xl lg:text-6xl",
      "h2": "text-base md:text-lg",
      "body": "text-sm sm:text-base",
      "small": "text-xs sm:text-sm",
      "kpi_value": "text-2xl sm:text-3xl font-semibold tracking-[-0.02em]"
    },
    "content_rules": [
      "Numeri e valuta sempre con tabular-nums.",
      "Etichette KPI brevi (max 2 righe).",
      "Usare € e kWh come unità primarie; CO₂ come secondaria (badge)."
    ]
  },
  "layout": {
    "app_shell": {
      "pattern": "Sidebar + topbar + content grid (Stripe-like).",
      "mobile": "Sidebar collassata in Sheet; topbar con selettore sede + notifiche.",
      "desktop": "Sidebar fissa 260px; content max-w-[var(--grid-max)] ma non centrato: allineare a sinistra con padding coerente.",
      "grid": {
        "dashboard": "grid grid-cols-1 lg:grid-cols-12 gap-4",
        "kpi_row": "col-span-12 grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4",
        "main_chart": "col-span-12 lg:col-span-8",
        "side_panel": "col-span-12 lg:col-span-4"
      }
    },
    "page_templates": {
      "auth": "Split layout: sinistra form (card), destra panel informativo con illustrazione/immagine (solo desktop).",
      "onboarding": "Wizard a step con progress + summary laterale (desktop) / accordion (mobile).",
      "data_pages": "Header con filtri (date range, sede), poi contenuto a sezioni: KPI -> grafici -> timeline -> tabella."
    }
  },
  "components": {
    "component_path": {
      "shadcn_primary": "/app/frontend/src/components/ui",
      "use": [
        "button.jsx",
        "card.jsx",
        "tabs.jsx",
        "table.jsx",
        "badge.jsx",
        "select.jsx",
        "calendar.jsx",
        "popover.jsx",
        "sheet.jsx",
        "dialog.jsx",
        "dropdown-menu.jsx",
        "sonner.jsx",
        "skeleton.jsx",
        "progress.jsx",
        "separator.jsx",
        "tooltip.jsx",
        "breadcrumb.jsx"
      ]
    },
    "key_ui_blocks": {
      "topbar": {
        "description": "Ricerca/command (opzionale), selettore sede, date range, pulsante 'Aggiungi bolletta', campanella notifiche.",
        "shadcn": ["dropdown-menu", "select", "popover", "calendar", "button", "badge"],
        "data_testids": [
          "location-switcher",
          "date-range-trigger",
          "upload-bill-button",
          "notifications-open-button"
        ]
      },
      "kpi_cards": {
        "description": "4 KPI principali: Costo mese, Consumo kWh, Sprechi stimati, Risparmio potenziale. Ogni card ha delta vs periodo precedente.",
        "shadcn": ["card", "badge", "tooltip"],
        "visual": "Icona lineare (lucide), valore grande, delta in badge (success/warn/danger).",
        "data_testids": [
          "kpi-cost-card",
          "kpi-consumption-card",
          "kpi-waste-card",
          "kpi-savings-card"
        ]
      },
      "charts": {
        "library": "Recharts",
        "description": "AreaChart per consumo, BarChart per costo, LineChart per previsione. Tooltip custom con unità e confronto.",
        "empty_state": "Skeleton + testo 'In attesa di dati' + CTA 'Carica bolletta' o 'Inserisci manualmente'.",
        "data_testids": ["consumption-chart", "cost-chart", "forecast-chart"]
      },
      "anomaly_timeline": {
        "description": "Timeline verticale con eventi (fuori orario, picchi, standby). Ogni item: severità, impatto € stimato, azione consigliata.",
        "shadcn": ["card", "badge", "accordion", "button"],
        "data_testids": ["anomaly-timeline", "anomaly-item"]
      },
      "smart_advice_cards": {
        "description": "Cards con consiglio concreto + ROI/payback + slider 'priorità' (solo UI) + CTA 'Applica' / 'Ignora'.",
        "shadcn": ["card", "badge", "button", "progress", "tooltip"],
        "data_testids": ["advice-card", "advice-apply-button", "advice-dismiss-button"]
      },
      "bills_upload_review": {
        "description": "Upload PDF con drag&drop + lista bollette + preview (se disponibile) + estrazione campi (POC).",
        "shadcn": ["card", "button", "input", "dialog", "table"],
        "data_testids": [
          "bill-upload-dropzone",
          "bill-upload-input",
          "bills-table",
          "bill-preview-open-button"
        ]
      },
      "manual_entry": {
        "description": "Form per inserimento consumi (giorno/ora, kWh, costo opzionale) + validazione + conferma toast.",
        "shadcn": ["form", "input", "calendar", "button", "select", "textarea", "sonner"],
        "data_testids": [
          "manual-entry-form",
          "manual-entry-submit-button",
          "manual-entry-kwh-input",
          "manual-entry-date-input"
        ]
      },
      "notifications_center": {
        "description": "Inbox notifiche con filtri (tutte/sprechi/prezzi/report) + stato letto/non letto.",
        "shadcn": ["tabs", "badge", "card", "button", "separator"],
        "data_testids": ["notifications-tabs", "notification-item", "mark-all-read-button"]
      },
      "pricing_ui": {
        "description": "Tabella piani Free/Pro (solo UI) con confronto feature + CTA 'Passa a Pro' (mock).",
        "shadcn": ["card", "badge", "button", "table"],
        "data_testids": ["pricing-free-card", "pricing-pro-card", "upgrade-to-pro-button"]
      }
    },
    "buttons": {
      "style": "Professional / Corporate (raggio 8–12px, tonal fill, hover sottile)",
      "variants": {
        "primary": {
          "tailwind": "bg-primary text-primary-foreground shadow-[var(--shadow-sm)] hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
          "motion": "hover: brightness +1–2%, active: scale-95 (solo sul bottone)"
        },
        "secondary": {
          "tailwind": "bg-secondary text-secondary-foreground hover:bg-secondary/80 border border-border",
          "motion": "hover: border più evidente"
        },
        "ghost": {
          "tailwind": "hover:bg-muted text-foreground",
          "motion": "hover: background fade"
        },
        "danger": {
          "tailwind": "bg-destructive text-destructive-foreground hover:bg-destructive/90",
          "motion": "hover: subtle"
        }
      },
      "data_testid_rule": "Ogni Button deve avere data-testid descrittivo (kebab-case)."
    },
    "forms": {
      "inputs": {
        "style": "No trasparenze. Input su bianco con bordo sand, focus ring teal.",
        "tailwind": "bg-card border-border focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
        "data_testids": "Tutti gli input/select/calendar trigger devono avere data-testid."
      },
      "validation": "Errori inline sotto il campo (text-destructive text-sm) + aria-describedby."
    }
  },
  "motion_microinteractions": {
    "library": "framer-motion (consigliato)",
    "install": "npm i framer-motion",
    "principles": [
      "Animazioni brevi: 160–220ms per hover/focus; 240–320ms per entrance.",
      "Usare easing 'easeOut' per entrate, 'easeInOut' per toggle.",
      "No transition: all. Applicare transition solo a background-color, border-color, box-shadow, opacity.",
      "Ridurre motion con prefers-reduced-motion."
    ],
    "patterns": {
      "page_enter": "fade + slight y (8px) su header e cards",
      "kpi_hover": "shadow-md + translateY(-1px) (solo card)",
      "timeline_expand": "accordion con height auto + opacity",
      "toast": "sonner default + messaggi brevi orientati a € risparmiati"
    }
  },
  "data_viz_guidelines": {
    "charts": {
      "colors": {
        "consumption": "hsl(var(--chart-1))",
        "cost": "hsl(var(--chart-4))",
        "forecast": "hsl(var(--chart-2))",
        "anomaly": "hsl(var(--destructive))"
      },
      "rules": [
        "Assi e griglie molto leggere: stroke border/40.",
        "Tooltip su card bianca con shadow-sm, testo slate.",
        "Mostrare sempre unità (kWh, €) e periodo.",
        "Empty state: non lasciare grafici vuoti; usare Skeleton + CTA."
      ]
    }
  },
  "accessibility": {
    "requirements": [
      "WCAG AA: contrasto testo su sand/white sempre verificato.",
      "Focus visibile: ring teal + ring-offset su background chiaro.",
      "Tasti e target touch >= 44px.",
      "Usare aria-label su icone-only buttons (es: notifiche).",
      "Prefer-reduced-motion: disabilitare entrance e ridurre hover lift."
    ]
  },
  "images": {
    "image_urls": [
      {
        "category": "auth_side_panel",
        "description": "Immagine laterale login (solo desktop) per evocare contesto PMI (cucina/caffetteria).",
        "url": "https://images.unsplash.com/photo-1645677020082-721a854c24f2?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Njd8MHwxfHNlYXJjaHwzfHxyZXN0YXVyYW50JTIwa2l0Y2hlbiUyMGVxdWlwbWVudCUyMGVuZXJneSUyMGVmZmljaWVuY3l8ZW58MHx8fGdyZWVufDE3NzUzNDg1OTN8MA&ixlib=rb-4.1.0&q=85"
      },
      {
        "category": "industry_switcher_gym",
        "description": "Immagine per onboarding (selettore settore: palestra) o empty state insights.",
        "url": "https://images.unsplash.com/photo-1596357395328-bb8ef99affbb?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Njl8MHwxfHNlYXJjaHwxfHxneW0lMjBpbnRlcmlvciUyMG1vZGVybiUyMGNsZWFufGVufDB8fHxibHVlfDE3NzUzNDg1OTN8MA&ixlib=rb-4.1.0&q=85"
      }
    ]
  },
  "instructions_to_main_agent": {
    "global": [
      "Aggiornare /app/frontend/src/App.css: rimuovere stile CRA demo (App-header centrato). Tenere App.css minimale o vuoto.",
      "Aggiornare /app/frontend/src/index.css: sostituire token :root con quelli sopra + aggiungere font import (Google Fonts) e font-family base.",
      "Usare shadcn/ui per tutti i componenti interattivi (select, dialog, sheet, calendar, toast/sonner).",
      "Aggiungere data-testid a: bottoni, link, input, select trigger, tab triggers, elementi KPI, grafici wrapper, error messages.",
      "No trasparenze: evitare bg-white/60, backdrop-blur, opacity su superfici di contenuto. Usare solid card backgrounds.",
      "Gradients: solo decorativi e max 20% viewport (vedi regole)."
    ],
    "page_by_page": {
      "login": [
        "Card form con Google login + dev bypass (secondary button).",
        "Aggiungere microcopy: 'Stima risparmio in 7 giorni' sotto H1.",
        "data-testid: google-login-button, dev-bypass-button, login-email-input (se presente)."
      ],
      "onboarding": [
        "Wizard 4 step: 1) Azienda & settore 2) Orari apertura 3) Carica bolletta o inserisci manualmente 4) Conferma & obiettivi risparmio.",
        "Progress in alto (Progress component) + stepper testuale.",
        "CTA sticky bottom su mobile (primary)."
      ],
      "dashboard": [
        "Header con date range + sede.",
        "KPI row (2x2 mobile, 4 in desktop).",
        "Grafico principale + pannello laterale con 'Consigli prioritari' e 'Ultime anomalie'."
      ],
      "bills": [
        "Dropzone sopra + tabella sotto.",
        "Dialog preview bolletta (se POC) o dettagli estratti.",
        "Mostrare stato: 'In elaborazione', 'Estratta', 'Errore'."
      ],
      "insights": [
        "Timeline anomalie con filtri severità.",
        "Ogni item mostra: quando, cosa, impatto € stimato, CTA 'Vedi consiglio'."
      ],
      "reports": [
        "Lista report mensili + CTA 'Genera report' (mock se necessario).",
        "Mostrare highlights: risparmio potenziale, top 3 sprechi."
      ],
      "pricing": [
        "Due card affiancate (stack mobile). Pro evidenziato con border-primary.",
        "No billing reale: CTA apre dialog 'Coming soon' + raccolta email (dev)."
      ]
    }
  }
}

<General UI UX Design Guidelines>  
    - You must **not** apply universal transition. Eg: `transition: all`. This results in breaking transforms. Always add transitions for specific interactive elements like button, input excluding transforms
    - You must **not** center align the app container, ie do not add `.App { text-align: center; }` in the css file. This disrupts the human natural reading flow of text
   - NEVER: use AI assistant Emoji characters like`🤖🧠💭💡🔮🎯📚🎭🎬🎪🎉🎊🎁🎀🎂🍰🎈🎨🎰💰💵💳🏦💎🪙💸🤑📊📈📉💹🔢🏆🥇 etc for icons. Always use **FontAwesome cdn** or **lucid-react** library already installed in the package.json

 **GRADIENT RESTRICTION RULE**
NEVER use dark/saturated gradient combos (e.g., purple/pink) on any UI element.  Prohibited gradients: blue-500 to purple 600, purple 500 to pink-500, green-500 to blue-500, red to pink etc
NEVER use dark gradients for logo, testimonial, footer etc
NEVER let gradients cover more than 20% of the viewport.
NEVER apply gradients to text-heavy content or reading areas.
NEVER use gradients on small UI elements (<100px width).
NEVER stack multiple gradient layers in the same viewport.

**ENFORCEMENT RULE:**
    • Id gradient area exceeds 20% of viewport OR affects readability, **THEN** use solid colors

**How and where to use:**
   • Section backgrounds (not content backgrounds)
   • Hero section header content. Eg: dark to light to dark color
   • Decorative overlays and accent elements only
   • Hero section with 2-3 mild color
   • Gradients creation can be done for any angle say horizontal, vertical or diagonal

- For AI chat, voice application, **do not use purple color. Use color like light green, ocean blue, peach orange etc**

</Font Guidelines>

- Every interaction needs micro-animations - hover states, transitions, parallax effects, and entrance animations. Static = dead. 
   
- Use 2-3x more spacing than feels comfortable. Cramped designs look cheap.

- Subtle grain textures, noise overlays, custom cursors, selection states, and loading animations: separates good from extraordinary.
   
- Before generating UI, infer the visual style from the problem statement (palette, contrast, mood, motion) and immediately instantiate it by setting global design tokens (primary, secondary/accent, background, foreground, ring, state colors), rather than relying on any library defaults. Don't make the background dark as a default step, always understand problem first and define colors accordingly
    Eg: - if it implies playful/energetic, choose a colorful scheme
           - if it implies monochrome/minimal, choose a black–white/neutral scheme

**Component Reuse:**
	- Prioritize using pre-existing components from src/components/ui when applicable
	- Create new components that match the style and conventions of existing components when needed
	- Examine existing components to understand the project's component patterns before creating new ones

**IMPORTANT**: Do not use HTML based component like dropdown, calendar, toast etc. You **MUST** always use `/app/frontend/src/components/ui/ ` only as a primary components as these are modern and stylish component

**Best Practices:**
	- Use Shadcn/UI as the primary component library for consistency and accessibility
	- Import path: ./components/[component-name]

**Export Conventions:**
	- Components MUST use named exports (export const ComponentName = ...)
	- Pages MUST use default exports (export default function PageName() {...})

**Toasts:**
  - Use `sonner` for toasts"
  - Sonner component are located in `/app/src/components/ui/sonner.tsx`

Use 2–4 color gradients, subtle textures/noise overlays, or CSS-based noise to avoid flat visuals.
</General UI UX Design Guidelines>
