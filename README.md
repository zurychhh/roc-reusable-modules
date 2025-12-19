# ROC Reusable Modules

Kolekcja reużywalnych modułów do szybkiego budowania projektów.

## Dostępne moduły

| Moduł | Opis | Status |
|-------|------|--------|
| [ab-testing-posthog](./ab-testing-posthog/) | A/B Testing z PostHog + Auto-scheduler + Email notifications | ✅ Ready |
| [cms-blog-ai](./cms-blog-ai/) | AI-powered Blog CMS z Claude API + Scheduler automatycznej publikacji | ✅ Ready |

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

### CMS Blog AI

```bash
# Skopiuj moduł do projektu Python
cp -r cms-blog-ai/src/* your-project/

# Zainstaluj zależności
pip install -r cms-blog-ai/requirements.txt

# Skonfiguruj zmienne środowiskowe
cp cms-blog-ai/.env.example your-project/.env
# Edytuj .env i dodaj ANTHROPIC_API_KEY

# Uruchom z Docker Compose (postgres + redis + api + celery)
cd cms-blog-ai && docker-compose up -d

# Lub uruchom ręcznie
uvicorn main:app --reload                                    # API
celery -A src.tasks.celery_app worker --loglevel=info       # Worker
celery -A src.tasks.celery_app beat --loglevel=info         # Scheduler

# Zobacz: cms-blog-ai/README.md
```

---

## Struktura

```
roc-reusable-modules/
├── ab-testing-posthog/     # A/B Testing module (TypeScript/SvelteKit)
│   ├── src/                # Source files
│   ├── scripts/            # CLI i automation scripts
│   ├── templates/          # Email templates
│   ├── examples/           # Example implementations
│   └── .github/workflows/  # GitHub Actions
│
├── cms-blog-ai/            # CMS Blog AI module (Python/FastAPI)
│   ├── src/                # Python source files
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── ai/             # Claude API integration
│   │   ├── tasks/          # Celery scheduler tasks
│   │   ├── services/       # SEO utilities
│   │   └── api/            # FastAPI endpoints
│   ├── examples/           # SvelteKit integration examples
│   ├── requirements.txt    # Python dependencies
│   ├── docker-compose.yml  # Local development setup
│   └── README.md           # Detailed documentation
│
└── README.md               # Ten plik
```

---

## Licencja

MIT License - użyj jak chcesz.

---

**Autor**: ROC (Rapid Outcome Consulting)
**Kontakt**: legitioplprod@gmail.com
