import axios, { AxiosError } from 'axios';
import type {
  AnalyticsOverviewResponse,
  AnalyticsRunResponse,
  AnalyticsValidationResponse,
  APDIRecordResponse,
  ArticleDetailResponse,
  ArticleParagraphResponse,
  ArticleResponse,
  CommentaryResponse,
  CricketPerformanceResponse,
  CrossSourceMatchResponse,
  DeliveryResponse,
  EntityMentionResponse,
  HealthResponse,
  IngestionRunResponse,
  MatchPerformanceScorecard,
  MatchResponse,
  MediaAttentionResponse,
  NarrativeFramingResponse,
  NarrativeTimelineResponse,
  PaginatedResponse,
  PipelineStatsResponse,
  PlayerResponse,
  ReadinessResponse,
  SourceRecordResponse,
  StatusResponse,
  TeamResponse,
} from '../types/api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export function extractErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const axiosErr = error as AxiosError<{ message?: string; error?: string; detail?: any }>;
    if (axiosErr.response?.data?.message) {
      return axiosErr.response.data.message;
    }
    if (axiosErr.response?.status === 404) {
      return 'The requested resource was not found.';
    }
    if (axiosErr.response?.status === 500) {
      return 'An internal database or server error occurred.';
    }
    if (axiosErr.code === 'ECONNABORTED') {
      return 'Request timed out while connecting to the backend.';
    }
    if (axiosErr.message === 'Network Error') {
      return 'Cannot connect to the research API. Ensure the FastAPI backend is running on http://127.0.0.1:8000.';
    }
    return axiosErr.message || 'An unexpected error occurred.';
  }
  return error instanceof Error ? error.message : 'An unexpected error occurred.';
}

export const api = {
  // 1. Health & Readiness
  getHealth: async (): Promise<HealthResponse> => {
    const { data } = await apiClient.get<HealthResponse>('/health');
    return data;
  },
  getReadiness: async (): Promise<ReadinessResponse> => {
    const { data } = await apiClient.get<ReadinessResponse>('/ready');
    return data;
  },
  getStatus: async (tournament?: string): Promise<StatusResponse> => {
    const { data } = await apiClient.get<StatusResponse>('/api/v1/status', {
      params: { tournament },
    });
    return data;
  },

  // 2. Matches & Scorecards
  getMatches: async (params?: {
    tournament?: string;
    season?: string;
    team_id?: string;
    limit?: number;
    offset?: number;
  }): Promise<PaginatedResponse<MatchResponse>> => {
    const { data } = await apiClient.get<PaginatedResponse<MatchResponse>>('/api/v1/matches', {
      params,
    });
    return data;
  },
  getMatch: async (matchId: string): Promise<MatchResponse> => {
    const { data } = await apiClient.get<MatchResponse>(`/api/v1/matches/${matchId}`);
    return data;
  },
  getMatchDeliveries: async (
    matchId: string,
    params?: { innings?: number; over_num?: number; phase?: string; limit?: number; offset?: number }
  ): Promise<PaginatedResponse<DeliveryResponse>> => {
    const { data } = await apiClient.get<PaginatedResponse<DeliveryResponse>>(
      `/api/v1/matches/${matchId}/deliveries`,
      { params }
    );
    return data;
  },
  getMatchPerformance: async (matchId: string): Promise<MatchPerformanceScorecard> => {
    const { data } = await apiClient.get<MatchPerformanceScorecard>(
      `/api/v1/matches/${matchId}/performance`
    );
    return data;
  },

  // 3. Players & Teams
  getPlayers: async (params?: {
    role?: string;
    team_id?: string;
    search?: string;
    limit?: number;
    offset?: number;
  }): Promise<PaginatedResponse<PlayerResponse>> => {
    const { data } = await apiClient.get<PaginatedResponse<PlayerResponse>>('/api/v1/players', {
      params,
    });
    return data;
  },
  getPlayer: async (playerId: string): Promise<PlayerResponse> => {
    const { data } = await apiClient.get<PlayerResponse>(`/api/v1/players/${playerId}`);
    return data;
  },
  getTeams: async (params?: {
    search?: string;
    limit?: number;
    offset?: number;
  }): Promise<PaginatedResponse<TeamResponse>> => {
    const { data } = await apiClient.get<PaginatedResponse<TeamResponse>>('/api/v1/teams', {
      params,
    });
    return data;
  },
  getTeam: async (teamId: string): Promise<TeamResponse> => {
    const { data } = await apiClient.get<TeamResponse>(`/api/v1/teams/${teamId}`);
    return data;
  },

  // 4. Articles & Commentary
  getArticles: async (params?: {
    source_domain?: string;
    language?: string;
    limit?: number;
    offset?: number;
  }): Promise<PaginatedResponse<ArticleResponse>> => {
    const { data } = await apiClient.get<PaginatedResponse<ArticleResponse>>('/api/v1/articles', {
      params,
    });
    return data;
  },
  getArticle: async (articleId: string): Promise<ArticleDetailResponse> => {
    const { data } = await apiClient.get<ArticleDetailResponse>(`/api/v1/articles/${articleId}`);
    return data;
  },
  getArticleParagraphs: async (
    articleId: string,
    params?: { limit?: number; offset?: number }
  ): Promise<PaginatedResponse<ArticleParagraphResponse>> => {
    const { data } = await apiClient.get<PaginatedResponse<ArticleParagraphResponse>>(
      `/api/v1/articles/${articleId}/paragraphs`,
      { params }
    );
    return data;
  },
  getCommentary: async (params?: {
    match_id?: string;
    innings?: number;
    over_num?: number;
    source_domain?: string;
    limit?: number;
    offset?: number;
  }): Promise<PaginatedResponse<CommentaryResponse>> => {
    const { data } = await apiClient.get<PaginatedResponse<CommentaryResponse>>(
      '/api/v1/commentary',
      { params }
    );
    return data;
  },

  // 5. NLP, Topics & Narratives
  getTopics: async (params?: {
    run_id?: string;
    limit?: number;
    offset?: number;
  }): Promise<PaginatedResponse<any>> => {
    const { data } = await apiClient.get<PaginatedResponse<any>>('/api/v1/topics', { params });
    return data;
  },
  getEntities: async (params?: {
    entity_type?: string;
    resolution_status?: string;
    resolved_id?: string;
    source_type?: string;
    limit?: number;
    offset?: number;
  }): Promise<PaginatedResponse<EntityMentionResponse>> => {
    const { data } = await apiClient.get<PaginatedResponse<EntityMentionResponse>>(
      '/api/v1/entities',
      { params }
    );
    return data;
  },
  getNarrativeTimeline: async (params?: {
    limit?: number;
    offset?: number;
  }): Promise<PaginatedResponse<NarrativeTimelineResponse>> => {
    const { data } = await apiClient.get<PaginatedResponse<NarrativeTimelineResponse>>(
      '/api/v1/narratives/timeline',
      { params }
    );
    return data;
  },
  getCrossSourceMatches: async (params?: {
    status?: string;
    match_id?: string;
    limit?: number;
    offset?: number;
  }): Promise<PaginatedResponse<CrossSourceMatchResponse>> => {
    const { data } = await apiClient.get<PaginatedResponse<CrossSourceMatchResponse>>(
      '/api/v1/narratives/matches',
      { params }
    );
    return data;
  },

  // 6. Analytics & APDI
  getAnalyticsOverview: async (tournament?: string): Promise<AnalyticsOverviewResponse> => {
    const { data } = await apiClient.get<AnalyticsOverviewResponse>(
      '/api/v1/analytics/overview',
      { params: { tournament } }
    );
    return data;
  },
  getMediaAttention: async (params?: {
    tournament?: string;
    entity_id?: string;
    limit?: number;
    offset?: number;
  }): Promise<PaginatedResponse<MediaAttentionResponse>> => {
    const { data } = await apiClient.get<PaginatedResponse<MediaAttentionResponse>>(
      '/api/v1/analytics/attention',
      { params }
    );
    return data;
  },
  getPerformanceMetrics: async (params?: {
    tournament?: string;
    entity_id?: string;
    role?: string;
    limit?: number;
    offset?: number;
  }): Promise<PaginatedResponse<CricketPerformanceResponse>> => {
    const { data } = await apiClient.get<PaginatedResponse<CricketPerformanceResponse>>(
      '/api/v1/analytics/performance',
      { params }
    );
    return data;
  },
  getEntityFraming: async (entityId: string): Promise<NarrativeFramingResponse> => {
    const { data } = await apiClient.get<NarrativeFramingResponse>(
      '/api/v1/analytics/framing',
      { params: { entity_id: entityId } }
    );
    return data;
  },
  getAPDIRecords: async (params?: {
    tournament?: string;
    role_cohort?: string;
    discrepancy_category?: string;
    limit?: number;
    offset?: number;
  }): Promise<PaginatedResponse<APDIRecordResponse>> => {
    const { data } = await apiClient.get<PaginatedResponse<APDIRecordResponse>>(
      '/api/v1/analytics/apdi',
      { params }
    );
    return data;
  },
  getEntityAPDI: async (entityId: string): Promise<APDIRecordResponse> => {
    const { data } = await apiClient.get<APDIRecordResponse>(`/api/v1/analytics/apdi/${entityId}`);
    return data;
  },
  validateAnalytics: async (): Promise<AnalyticsValidationResponse> => {
    const { data } = await apiClient.get<AnalyticsValidationResponse>('/api/v1/analytics/validation');
    return data;
  },

  // 7. Observability & Provenance
  getIngestionRuns: async (params?: {
    status?: string;
    limit?: number;
    offset?: number;
  }): Promise<PaginatedResponse<IngestionRunResponse>> => {
    const { data } = await apiClient.get<PaginatedResponse<IngestionRunResponse>>(
      '/api/v1/observability/ingestion-runs',
      { params }
    );
    return data;
  },
  getSourceRecords: async (params?: {
    source_name?: string;
    limit?: number;
    offset?: number;
  }): Promise<PaginatedResponse<SourceRecordResponse>> => {
    const { data } = await apiClient.get<PaginatedResponse<SourceRecordResponse>>(
      '/api/v1/observability/sources',
      { params }
    );
    return data;
  },
  getPipelineStats: async (sourceId?: string): Promise<PipelineStatsResponse> => {
    const { data } = await apiClient.get<PipelineStatsResponse>(
      '/api/v1/observability/pipeline-stats',
      { params: { source_id: sourceId } }
    );
    return data;
  },
  getAnalyticsRuns: async (params?: {
    tournament?: string;
    limit?: number;
    offset?: number;
  }): Promise<PaginatedResponse<AnalyticsRunResponse>> => {
    const { data } = await apiClient.get<PaginatedResponse<AnalyticsRunResponse>>(
      '/api/v1/observability/analytics-runs',
      { params }
    );
    return data;
  },
};
