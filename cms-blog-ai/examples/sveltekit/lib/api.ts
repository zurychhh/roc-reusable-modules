/**
 * CMS Blog AI - SvelteKit API Client
 *
 * Provides a typed interface to the CMS Blog AI REST API.
 * Copy to your SvelteKit project's src/lib/ directory.
 */

import type {
  Post,
  PostCreate,
  PostUpdate,
  PostGenerateRequest,
  PostScheduleRequest,
  Agent,
  AgentCreate,
  AgentUpdate,
  Schedule,
  ScheduleCreate,
  ScheduleUpdate,
  PaginatedResponse,
  TaskResponse,
  PostStatus
} from './types';

export class CMSBlogAPI {
  private baseUrl: string;

  constructor(baseUrl: string = '/api/v1') {
    this.baseUrl = baseUrl.replace(/\/$/, '');
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;

    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      }
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `API Error: ${response.status}`);
    }

    if (response.status === 204) {
      return null as T;
    }

    return response.json();
  }

  // ============================================
  // Posts API
  // ============================================

  async listPosts(params?: {
    page?: number;
    page_size?: number;
    status?: PostStatus;
    agent_id?: string;
  }): Promise<PaginatedResponse<Post>> {
    const query = new URLSearchParams();
    if (params?.page) query.set('page', String(params.page));
    if (params?.page_size) query.set('page_size', String(params.page_size));
    if (params?.status) query.set('status', params.status);
    if (params?.agent_id) query.set('agent_id', params.agent_id);

    const queryStr = query.toString();
    return this.request<PaginatedResponse<Post>>(
      `/posts${queryStr ? `?${queryStr}` : ''}`
    );
  }

  async getPost(postId: string): Promise<Post> {
    return this.request<Post>(`/posts/${postId}`);
  }

  async createPost(data: PostCreate): Promise<Post> {
    return this.request<Post>('/posts', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  async updatePost(postId: string, data: PostUpdate): Promise<Post> {
    return this.request<Post>(`/posts/${postId}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  }

  async deletePost(postId: string): Promise<void> {
    await this.request<void>(`/posts/${postId}`, {
      method: 'DELETE'
    });
  }

  async generatePost(data: PostGenerateRequest): Promise<Post> {
    return this.request<Post>('/posts/generate', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  async schedulePost(
    postId: string,
    data: PostScheduleRequest
  ): Promise<TaskResponse> {
    return this.request<TaskResponse>(`/posts/${postId}/schedule`, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  async publishPost(postId: string): Promise<TaskResponse> {
    return this.request<TaskResponse>(`/posts/${postId}/publish`, {
      method: 'POST'
    });
  }

  // ============================================
  // Agents API
  // ============================================

  async listAgents(params?: {
    page?: number;
    page_size?: number;
    is_active?: boolean;
  }): Promise<PaginatedResponse<Agent>> {
    const query = new URLSearchParams();
    if (params?.page) query.set('page', String(params.page));
    if (params?.page_size) query.set('page_size', String(params.page_size));
    if (params?.is_active !== undefined)
      query.set('is_active', String(params.is_active));

    const queryStr = query.toString();
    return this.request<PaginatedResponse<Agent>>(
      `/agents${queryStr ? `?${queryStr}` : ''}`
    );
  }

  async getAgent(agentId: string): Promise<Agent> {
    return this.request<Agent>(`/agents/${agentId}`);
  }

  async createAgent(data: AgentCreate): Promise<Agent> {
    return this.request<Agent>('/agents', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  async updateAgent(agentId: string, data: AgentUpdate): Promise<Agent> {
    return this.request<Agent>(`/agents/${agentId}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  }

  async deleteAgent(agentId: string): Promise<void> {
    await this.request<void>(`/agents/${agentId}`, {
      method: 'DELETE'
    });
  }

  async triggerGeneration(
    agentId: string,
    params?: { topic?: string; keyword?: string }
  ): Promise<TaskResponse> {
    const query = new URLSearchParams();
    if (params?.topic) query.set('topic', params.topic);
    if (params?.keyword) query.set('keyword', params.keyword);

    const queryStr = query.toString();
    return this.request<TaskResponse>(
      `/agents/${agentId}/generate${queryStr ? `?${queryStr}` : ''}`,
      { method: 'POST' }
    );
  }

  // ============================================
  // Schedules API (The Key Feature!)
  // ============================================

  async listSchedules(params?: {
    page?: number;
    page_size?: number;
    is_active?: boolean;
  }): Promise<PaginatedResponse<Schedule>> {
    const query = new URLSearchParams();
    if (params?.page) query.set('page', String(params.page));
    if (params?.page_size) query.set('page_size', String(params.page_size));
    if (params?.is_active !== undefined)
      query.set('is_active', String(params.is_active));

    const queryStr = query.toString();
    return this.request<PaginatedResponse<Schedule>>(
      `/schedules${queryStr ? `?${queryStr}` : ''}`
    );
  }

  async getSchedule(scheduleId: string): Promise<Schedule> {
    return this.request<Schedule>(`/schedules/${scheduleId}`);
  }

  async createSchedule(data: ScheduleCreate): Promise<Schedule> {
    return this.request<Schedule>('/schedules', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  async updateSchedule(
    scheduleId: string,
    data: ScheduleUpdate
  ): Promise<Schedule> {
    return this.request<Schedule>(`/schedules/${scheduleId}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  }

  async deleteSchedule(scheduleId: string): Promise<void> {
    await this.request<void>(`/schedules/${scheduleId}`, {
      method: 'DELETE'
    });
  }

  async activateSchedule(scheduleId: string): Promise<TaskResponse> {
    return this.request<TaskResponse>(`/schedules/${scheduleId}/activate`, {
      method: 'POST'
    });
  }

  async deactivateSchedule(scheduleId: string): Promise<TaskResponse> {
    return this.request<TaskResponse>(`/schedules/${scheduleId}/deactivate`, {
      method: 'POST'
    });
  }
}

// Default export for convenience
export default CMSBlogAPI;
