# A/B Testing Module z PostHog

Kompletny moduł do A/B testów z automatycznym zarządzaniem eksperymentami i powiadomieniami email.

## Funkcje

- **PostHog SDK Integration** - Inicjalizacja i śledzenie eksperymentów
- **Auto-Scheduler** - Automatyczne przełączanie testów po osiągnięciu istotności statystycznej
- **Email Notifications** - Powiadomienia o wynikach przez Resend
- **CLI Tools** - Zarządzanie eksperymentami z linii poleceń
- **GitHub Actions** - Automatyczne codzienne sprawdzanie

---

## Wymagania

- Node.js 18+
- Konto PostHog (darmowe: https://posthog.com)
- Konto Resend (darmowe: https://resend.com) - opcjonalne, dla email

---

## Instalacja

### 1. Zainstaluj zależności

```bash
npm install posthog-js resend
npm install -D tsx @types/node
```

### 2. Skopiuj pliki do projektu

```bash
# Struktura docelowa
your-project/
├── src/
│   └── lib/
│       ├── posthog.ts              # <- z src/posthog.ts
│       └── utils/
│           └── analytics.ts        # <- z src/analytics.ts
├── scripts/
│   ├── posthog-cli.ts              # <- z scripts/
│   ├── experiment-scheduler.ts     # <- z scripts/
│   └── setup-experiments.ts        # <- z scripts/
└── .github/
    └── workflows/
        └── experiment-scheduler.yml # <- z .github/workflows/
```

### 3. Skonfiguruj zmienne środowiskowe

```env
# .env
PUBLIC_POSTHOG_KEY=phc_your_project_key
PUBLIC_POSTHOG_HOST=https://eu.posthog.com

# Dla scripts (opcjonalnie w .env lub GitHub Secrets)
POSTHOG_PERSONAL_API_KEY=phx_your_personal_api_key
RESEND_API_KEY=re_your_resend_key
NOTIFICATION_EMAIL=your@email.com
```

---

## Konfiguracja PostHog

### Krok 1: Utwórz konto PostHog

1. Idź na https://posthog.com i załóż konto
2. Wybierz region (EU lub US)
3. Utwórz nowy projekt

### Krok 2: Pobierz klucze API

| Klucz | Gdzie znaleźć | Użycie |
|-------|---------------|--------|
| Project API Key | Settings → Project → Project API Key | SDK (public) |
| Personal API Key | Settings → User → Personal API Keys → Create | API/Scripts (secret) |

### Krok 3: Skonfiguruj host

| Region | Host |
|--------|------|
| EU | `https://eu.posthog.com` |
| US | `https://app.posthog.com` |

---

## Użycie

### Inicjalizacja w aplikacji

#### SvelteKit

```typescript
// src/routes/+layout.svelte
<script>
  import { onMount } from 'svelte';
  import { browser } from '$app/environment';
  import { initPostHog } from '$lib/posthog';

  onMount(() => {
    if (browser) {
      initPostHog();
    }
  });
</script>
```

#### Next.js

```typescript
// app/layout.tsx
'use client';
import { useEffect } from 'react';
import { initPostHog } from '@/lib/posthog';

export default function RootLayout({ children }) {
  useEffect(() => {
    initPostHog();
  }, []);

  return <html><body>{children}</body></html>;
}
```

#### Vanilla JS

```html
<script type="module">
  import { initPostHog } from './lib/posthog.js';
  initPostHog();
</script>
```

---

### Implementacja A/B testu w komponencie

```typescript
// Przykład dla SvelteKit (Svelte 5)
<script lang="ts">
  import { onMount } from 'svelte';
  import posthog from 'posthog-js';

  const EXPERIMENT_KEY = 'hero-headline-test';

  let variant = $state('control');
  let isLoaded = $state(false);

  const variants = {
    control: { headline: 'Oryginalny nagłówek' },
    test: { headline: 'Alternatywny nagłówek' },
  };

  onMount(() => {
    // Timeout fallback
    const timeout = setTimeout(() => {
      if (!isLoaded) isLoaded = true;
    }, 1500);

    posthog.onFeatureFlags(() => {
      clearTimeout(timeout);
      const flag = posthog.getFeatureFlag(EXPERIMENT_KEY);
      variant = (flag as string) || 'control';
      isLoaded = true;

      // Track impression
      posthog.capture('$experiment_started', {
        experiment: EXPERIMENT_KEY,
        variant: variant
      });
    });
  });
</script>

{#if !isLoaded}
  <div class="skeleton">Loading...</div>
{:else}
  <h1>{variants[variant].headline}</h1>
{/if}
```

---

### Tworzenie eksperymentów

#### Opcja A: Przez PostHog UI

1. Idź do Experiments → New Experiment
2. Wybierz Feature Flag key
3. Dodaj warianty
4. Ustaw metryki (np. form_submit event)
5. Uruchom eksperyment

#### Opcja B: Przez CLI

```bash
# Lista eksperymentów
npx tsx scripts/posthog-cli.ts list

# Utwórz nowy
npx tsx scripts/posthog-cli.ts create "Nazwa testu" nazwa-flag-key

# Uruchom
npx tsx scripts/posthog-cli.ts launch 12345

# Zatrzymaj
npx tsx scripts/posthog-cli.ts stop 12345
```

#### Opcja C: Batch script

Edytuj `scripts/setup-experiments.ts` i uruchom:

```bash
npx tsx scripts/setup-experiments.ts
```

---

### Auto-Scheduler

#### Konfiguracja

Edytuj `scripts/experiment-scheduler.ts`:

```typescript
// Parametry istotności statystycznej
const MIN_SAMPLE_SIZE = 100;        // Min. użytkowników per wariant
const MIN_DAYS_RUNNING = 7;         // Min. dni trwania
const SIGNIFICANCE_THRESHOLD = 0.95; // 95% pewności

// Kolejka eksperymentów (priorytet: niższy = wyższy priorytet)
const EXPERIMENT_QUEUE = [
  { id: 12345, name: 'Test 1', priority: 0, flagKey: 'test-1' },
  { id: 12346, name: 'Test 2', priority: 1, flagKey: 'test-2' },
  // ...
];
```

#### Uruchomienie

```bash
# Tylko sprawdzenie statusu
npx tsx scripts/experiment-scheduler.ts

# Automatyczne przełączenie (jeśli warunki spełnione)
npx tsx scripts/experiment-scheduler.ts --auto
```

#### GitHub Actions (automatyczne)

Workflow uruchamia się codziennie o 10:00 CET:

```yaml
# .github/workflows/experiment-scheduler.yml
on:
  schedule:
    - cron: '0 9 * * *'  # 9:00 UTC = 10:00 CET
```

Dodaj secrets w GitHub:
- `POSTHOG_PERSONAL_API_KEY`
- `RESEND_API_KEY`

---

### Email Notifications

Email jest wysyłany automatycznie gdy scheduler przełącza testy.

#### Zawartość emaila:
1. **Wyniki zakończonego testu**
   - Sample size, dni trwania, pewność statystyczna
   - Zwycięzca (jeśli jest)
   - Tabela wariantów z konwersjami

2. **Aktualnie uruchomiony test**
   - Nazwa i ID
   - Przewidywana data zakończenia

3. **Kolejka następnych testów**

4. **Link do PostHog Dashboard**

#### Test wysyłki

```bash
npx tsx scripts/test-email.ts
```

---

## Tracking konwersji

### Automatyczne śledzenie

```typescript
// Przy submit formularza
posthog.capture('form_submit', {
  form_id: 'lead-form',
  // PostHog automatycznie doda experiment variant
});
```

### Z danymi eksperymentu

```typescript
import { trackExperimentConversion } from '$lib/utils/analytics';

function onFormSubmit() {
  trackExperimentConversion({
    experimentId: 'hero-headline-test',
    conversionType: 'form_submit',
    value: 1
  });
}
```

---

## Integracja z CRM (opcjonalne)

### HubSpot

```typescript
// W API route przy tworzeniu leada
const experimentData = getActiveExperiments(); // z analytics.ts

await hubspotClient.crm.contacts.basicApi.create({
  properties: {
    email: data.email,
    ab_test_experiments: JSON.stringify(experimentData)
  }
});
```

---

## API Reference

### posthog.ts

```typescript
// Inicjalizacja
initPostHog(): void

// Sprawdzenie czy zainicjalizowany
isPostHogInitialized(): boolean

// Pobierz instancję (po inicjalizacji)
getPostHog(): PostHog | null
```

### analytics.ts

```typescript
// Śledzenie impression
trackExperimentImpression(data: {
  experimentId: string;
  experimentName: string;
  variantId: string;
  variantName: string;
}): void

// Śledzenie konwersji
trackExperimentConversion(data: {
  experimentId: string;
  conversionType: string;
  value?: number;
}): void

// Zapisz aktywny eksperyment
setActiveExperiment(experimentId: string, variantId: string): void

// Pobierz aktywny wariant
getActiveExperiment(experimentId: string): string | null

// Pobierz wszystkie aktywne
getAllActiveExperiments(): Record<string, string>
```

---

## Troubleshooting

### PostHog nie zbiera eventów

1. Sprawdź czy `PUBLIC_POSTHOG_KEY` jest poprawny
2. Sprawdź czy host to `https://eu.posthog.com` (nie `eu.i.posthog.com`)
3. Otwórz DevTools → Network → szukaj requestów do `eu.posthog.com`
4. Sprawdź Console na błędy

### Warianty nie działają

1. Sprawdź czy Feature Flag jest aktywny w PostHog
2. Sprawdź czy eksperyment jest uruchomiony (ma start_date)
3. Użyj incognito dla czystej sesji (PostHog cachuje warianty)
4. Sprawdź console.log z `[A/B Test]` prefix

### Scheduler nie przełącza

1. Sprawdź czy `--auto` flag jest użyty
2. Sprawdź czy test spełnia warunki (100 users, 7 dni)
3. Sprawdź czy są testy w kolejce (DRAFT status)

### Email nie przychodzi

1. Sprawdź `RESEND_API_KEY`
2. Sprawdź `NOTIFICATION_EMAIL`
3. Uruchom `npx tsx scripts/test-email.ts`
4. Sprawdź folder spam

---

## Przykładowe projekty

- [legitio-landing](https://github.com/zurychhh/legitio-landing) - Landing page z pełną integracją A/B testing

---

## Licencja

MIT License

---

**Autor**: ROC (Rapid Outcome Consulting)
**Wersja**: 1.0.0
**Ostatnia aktualizacja**: Grudzień 2025
