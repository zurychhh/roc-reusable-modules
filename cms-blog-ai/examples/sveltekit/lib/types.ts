/**
 * CMS Blog AI - TypeScript Type Definitions
 *
 * These types match the API responses from the CMS Blog AI module.
 * Copy to your SvelteKit project's src/lib/ directory.
 */

// ============================================
// Post Types
// ============================================

export type PostStatus = 'draft' | 'scheduled' | 'published' | 'failed';

export interface Post {
  id: string;
  agent_id: string;
  title: string;
  slug: string;
  content: string;
  excerpt?: string;
  meta_title?: string;
  meta_description?: string;
  keywords: string[];
  status: PostStatus;
  scheduled_at?: string;
  published_at?: string;
  tokens_used: number;
  word_count: number;
  readability_score?: number;
  keyword_density?: Record<string, number>;
  created_at: string;
  updated_at: string;
}

export interface PostCreate {
  agent_id: string;
  title: string;
  content: string;
  excerpt?: string;
  slug?: string;
  meta_title?: string;
  meta_description?: string;
  keywords?: string[];
  status?: PostStatus;
}

export interface PostUpdate {
  title?: string;
  content?: string;
  excerpt?: string;
  slug?: string;
  meta_title?: string;
  meta_description?: string;
  keywords?: string[];
  status?: PostStatus;
}

export interface PostGenerateRequest {
  agent_id: string;
  topic: string;
  target_keyword?: string;
}

export interface PostScheduleRequest {
  scheduled_at: string; // ISO datetime
}

// ============================================
// Agent Types
// ============================================

export type AgentTone = 'professional' | 'friendly' | 'casual' | 'formal';
export type PostLength = 'short' | 'medium' | 'long' | 'very_long';
export type AgentWorkflow = 'draft' | 'auto' | 'scheduled';

export interface Agent {
  id: string;
  name: string;
  expertise: string;
  persona: string;
  tone: AgentTone;
  post_length: PostLength;
  schedule_cron?: string;
  workflow: AgentWorkflow;
  settings: Record<string, unknown>;
  is_active: boolean;
  total_posts: number;
  created_at: string;
  updated_at: string;
}

export interface AgentCreate {
  name: string;
  expertise: string;
  persona: string;
  tone?: AgentTone;
  post_length?: PostLength;
  schedule_cron?: string;
  workflow?: AgentWorkflow;
  settings?: Record<string, unknown>;
}

export interface AgentUpdate {
  name?: string;
  expertise?: string;
  persona?: string;
  tone?: AgentTone;
  post_length?: PostLength;
  schedule_cron?: string;
  workflow?: AgentWorkflow;
  settings?: Record<string, unknown>;
  is_active?: boolean;
}

// ============================================
// Schedule Types
// ============================================

export type ScheduleInterval = 'daily' | 'every_3_days' | 'weekly' | 'biweekly';

export interface Schedule {
  id: string;
  agent_id: string;
  interval: ScheduleInterval;
  interval_display: string;
  publish_hour: number;
  timezone: string;
  is_active: boolean;
  auto_publish: boolean;
  target_keywords: string[];
  exclude_keywords: string[];
  post_length?: string;
  cron_expression: string;
  total_posts_generated: number;
  successful_posts: number;
  failed_posts: number;
  last_run_at?: string;
  next_run_at?: string;
  created_at: string;
  updated_at: string;
}

export interface ScheduleCreate {
  agent_id: string;
  interval: ScheduleInterval;
  publish_hour?: number;
  timezone?: string;
  auto_publish?: boolean;
  target_keywords?: string[];
  exclude_keywords?: string[];
  post_length?: PostLength;
}

export interface ScheduleUpdate {
  interval?: ScheduleInterval;
  publish_hour?: number;
  timezone?: string;
  is_active?: boolean;
  auto_publish?: boolean;
  target_keywords?: string[];
  exclude_keywords?: string[];
  post_length?: PostLength;
}

// ============================================
// API Response Types
// ============================================

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface TaskResponse {
  message: string;
  task_id?: string;
  agent_id?: string;
  post_id?: string;
  schedule_id?: string;
}
