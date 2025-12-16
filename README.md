# ROC Reusable Modules

Kolekcja reużywalnych modułów do szybkiego budowania projektów.

## Dostępne moduły

| Moduł | Opis | Status |
|-------|------|--------|
| [ab-testing-posthog](./ab-testing-posthog/) | A/B Testing z PostHog + Auto-scheduler + Email notifications | ✅ Ready |

---

## Szybki start

### A/B Testing z PostHog

```bash
# Skopiuj moduł do projektu
cp -r ab-testing-posthog/src/* your-project/src/lib/
cp -r ab-testing-posthog/scripts/* your-project/scripts/
cp ab-testing-posthog/.github/workflows/* your-project/.github/workflows/

# Zainstaluj zależności
npm install posthog-js resend

# Skonfiguruj zmienne środowiskowe
# Zobacz: ab-testing-posthog/README.md
```

---

## Struktura

```
roc-reusable-modules/
├── ab-testing-posthog/     # A/B Testing module
│   ├── src/                # Source files (TypeScript)
│   ├── scripts/            # CLI i automation scripts
│   ├── templates/          # Email templates
│   ├── examples/           # Example implementations
│   └── .github/workflows/  # GitHub Actions
│
└── README.md               # Ten plik
```

---

## Licencja

MIT License - użyj jak chcesz.

---

**Autor**: ROC (Rapid Outcome Consulting)
**Kontakt**: legitioplprod@gmail.com
