# SvelteKit Admin Integration Example

This example shows how to integrate the CMS Blog AI module with a SvelteKit admin panel.

## Files Included

```
examples/sveltekit/
├── lib/
│   ├── api.ts              # API client for CMS Blog AI
│   └── types.ts            # TypeScript type definitions
├── routes/
│   └── admin/
│       └── blog/
│           ├── +page.svelte        # Posts list page
│           ├── +page.server.ts     # Posts server load
│           ├── agents/
│           │   └── +page.svelte    # Agents management
│           └── schedules/
│               └── +page.svelte    # Schedules management
└── README.md
```

## Setup

1. Copy the `lib/` files to your SvelteKit project's `src/lib/` directory
2. Copy the `routes/` files to your `src/routes/` directory
3. Configure the API base URL in `lib/api.ts`

## Usage

### API Client

```typescript
import { CMSBlogAPI } from '$lib/api';

const api = new CMSBlogAPI('http://localhost:8000/api/v1');

// List posts
const posts = await api.listPosts({ page: 1, status: 'draft' });

// Generate AI post
const newPost = await api.generatePost({
  agent_id: 'uuid-here',
  topic: 'Understanding GDPR',
  target_keyword: 'data protection'
});

// Create schedule
const schedule = await api.createSchedule({
  agent_id: 'uuid-here',
  interval: 'daily',
  publish_hour: 9,
  timezone: 'Europe/Warsaw'
});
```

### Server-Side Data Loading

```typescript
// +page.server.ts
import { CMSBlogAPI } from '$lib/api';

export async function load({ url }) {
  const api = new CMSBlogAPI(process.env.CMS_API_URL);
  const page = Number(url.searchParams.get('page')) || 1;

  const posts = await api.listPosts({ page });

  return { posts };
}
```
