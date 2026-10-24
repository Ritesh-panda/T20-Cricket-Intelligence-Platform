/**
 * Typed API interfaces for T20 Cricket Intelligence Platform.
 * Mirrors the canonical Pydantic models from FastAPI backend.
 */

export interface PaginationMeta {
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export interface PaginatedResponse<T> {
  items: T[];
  pagination: PaginationMeta;
}

export interface HealthResponse {
  status: string;
  version: string;
  timestamp_utc: string;
}

export interface ReadinessResponse {
  status: 'ready' | 'not_ready';
  database_accessible: boolean;
  schema_version: number | null;
  database_tables_count: number;
  timestamp_utc: string;
}

export interface StatusResponse {
  pipeline_status: 'empty' | 'operational' | 'insufficient_data';
  tournament: string;
  record_counts: {
    matches: number;
    deliveries: number;
    articles: number;
    paragraphs: number;
    commentary_entries: number;
    entity_mentions: number;
    resolved_mentions: number;
    sentiment_baselines: number;
    eligible_batters: number;
    eligible_bowlers: number;
    eligible_teams: number;
  };
  data_sufficiency_status: 'VALID' | 'PARTIAL_COVERAGE' | 'INSUFFICIENT_DATA';
  is_analytics_ready: boolean;
  supported_capabilities: string[];
  warnings: string[];
  checked_at_utc: string;
}

export interface MatchResponse {
  match_id: string;
  tournament: string;
  season: string;
  match_date: string;
  venue: string;
  city: string | null;
  team1_id: string;
  team2_id: string;
  toss_winner_id: string | null;
  toss_decision: string | null;
  winner_id: string | null;
  win_by_runs: number | null;
  win_by_wickets: number | null;
  player_of_match_id: string | null;
  target_runs: number | null;
  metadata: Record<string, any>;
  provenance_id: string | null;
}

export interface DeliveryResponse {
  delivery_id: string;
  match_id: string;
  innings: number;
  over_num: number;
  ball_num: number;
  batter_id: string;
  bowler_id: string;
  non_striker_id: string | null;
  batter_runs: number;
  extra_runs: number;
  extra_type: string | null;
  total_runs: number;
  is_legal: boolean;
  is_wicket: boolean;
  wicket_kind: string | null;
  player_dismissed_id: string | null;
  phase: string;
}

export interface MatchBatterScore {
  player_id: string;
  runs: number;
  balls: number;
  fours: number;
  sixes: number;
  strike_rate: number | null;
  is_out: boolean;
  dismissal_kind: string | null;
}

export interface MatchBowlerScore {
  player_id: string;
  overs: number;
  legal_balls: number;
  runs_conceded: number;
  wickets: number;
  economy: number | null;
}

export interface MatchTeamScore {
  team_id: string;
  innings: number;
  total_runs: number;
  total_wickets: number;
  legal_overs: number;
}

export interface MatchPerformanceScorecard {
  match_id: string;
  tournament: string;
  match_date: string;
  venue: string;
  winner_id: string | null;
  team_scores: MatchTeamScore[];
  batters: MatchBatterScore[];
  bowlers: MatchBowlerScore[];
}

export interface PlayerResponse {
  player_id: string;
  full_name: string;
  cricsheet_id: string | null;
  primary_team_id: string | null;
  batting_style: string | null;
  bowling_style: string | null;
  aliases: string[];
}

export interface TeamResponse {
  team_id: string;
  name: string;
  aliases: string[];
}

export interface ArticleResponse {
  article_id: string;
  canonical_url: string;
  headline: string;
  author: string | null;
  published_at_utc: string | null;
  source_domain: string;
  summary: string | null;
  language: string;
  raw_content_hash: string;
  provenance_id: string | null;
}

export interface ArticleDetailResponse extends ArticleResponse {
  full_text: string;
}

export interface ArticleParagraphResponse {
  paragraph_id: string;
  article_id: string;
  paragraph_index: number;
  text: string;
  char_count: number;
}

export interface CommentaryResponse {
  commentary_id: string;
  match_id: string;
  innings: number;
  over_num: number;
  ball_num: number;
  bowler_raw: string;
  batter_raw: string;
  text: string;
  event_tags: string[];
  source_domain: string;
  harvest_timestamp_utc: string;
  provenance_id: string | null;
}

export interface TopicClusterResponse {
  cluster_id: string;
  run_id: string;
  cluster_index: number;
  topic_label: string;
  keywords: string[];
  doc_count: number;
  representative_doc_ids: string[];
  intra_cluster_similarity: number | null;
  is_noise: boolean;
}

export interface EntityMentionResponse {
  mention_id: string;
  source_type: string;
  source_id: string;
  entity_type: string;
  surface_text: string;
  start_char: number;
  end_char: number;
  detection_method: string;
  confidence: number;
  resolved_id: string | null;
  resolution_status: 'RESOLVED' | 'UNRESOLVED' | 'AMBIGUOUS' | string;
  evidence: Record<string, any>;
  pipeline_version: string;
  created_at_utc: string;
}

export interface NarrativeTimelineResponse {
  snapshot_id: string;
  bucket_label: string;
  doc_count: number;
  mean_sentiment: number;
  sentiment_distribution: Record<string, number>;
  top_topics: any[];
  top_entities: any[];
  match_events_count: number;
  observed_timestamps_count: number;
  inferred_timestamps_count: number;
  created_at_utc: string;
}

export interface CrossSourceMatchResponse {
  match_link_id: string;
  editorial_norm_id: string;
  editorial_source_id: string;
  commentary_norm_id: string;
  commentary_source_id: string;
  match_id: string | null;
  similarity_score: number;
  status: string;
  confidence: number;
  matching_method: string;
  evidence: Record<string, any>;
  created_at_utc: string;
}

export interface AnalyticsOverviewResponse {
  tournament: string;
  attention_metrics_count: number;
  performance_metrics_count: number;
  apdi_records_count: number;
  over_attended_count: number;
  under_attended_count: number;
  balanced_count: number;
  insufficient_data_count: number;
  analytics_runs_count: number;
  preflight_status: string;
  is_eligible: boolean;
  warnings: string[];
}

export interface MediaAttentionResponse {
  metric_id: string;
  entity_id: string;
  entity_name: string;
  entity_type: string;
  tournament: string;
  window_start: string | null;
  window_end: string | null;
  paragraph_count: number;
  raw_mention_count: number;
  article_reach: number;
  source_diversity_count: number;
  sources: string[];
  prominence_score: number;
  headline_mentions: number;
  lead_paragraph_mentions: number;
  body_paragraph_mentions: number;
  event_linked_mentions: number;
  temporal_distribution: Record<string, number>;
  article_ids: string[];
  paragraph_ids: string[];
  raw_attention_composite: number;
  formula_version: string;
  created_at_utc: string;
}

export interface CricketPerformanceResponse {
  metric_id: string;
  entity_id: string;
  entity_name: string;
  entity_type: string;
  role: 'batter' | 'bowler' | 'all_rounder' | 'team' | string;
  tournament: string;
  window_start: string | null;
  window_end: string | null;
  matches_played: number;
  innings_count: number;
  runs_scored: number;
  balls_faced: number;
  strike_rate: number | null;
  fours: number;
  sixes: number;
  dismissals: number;
  batting_average: number | null;
  legal_balls_bowled: number;
  overs_bowled: number;
  runs_conceded: number;
  wickets_taken: number;
  bowling_economy: number | null;
  bowling_average: number | null;
  bowling_strike_rate: number | null;
  wides_conceded: number;
  noballs_conceded: number;
  powerplay_runs: number;
  powerplay_balls: number;
  powerplay_wickets: number;
  death_runs: number;
  death_balls: number;
  death_wickets: number;
  team_wins: number;
  team_matches: number;
  win_percentage: number | null;
  raw_performance_composite: number;
  match_ids: string[];
  raw_stats: Record<string, any>;
  formula_version: string;
  created_at_utc: string;
}

export interface NarrativeFramingResponse {
  entity_id: string;
  positive_count: number;
  neutral_count: number;
  negative_count: number;
  total_framed_passages: number;
  net_framing_score: number;
  source_framing_breakdown: Record<string, { positive: number; neutral: number; negative: number }>;
  topic_distribution: Record<string, number>;
  supporting_samples: Array<{
    paragraph_id?: string;
    sentiment?: string;
    framing_score?: number;
    source_domain?: string;
    text_snippet?: string;
  }>;
}

export type DiscrepancyCategory = 'OVER_ATTENDED' | 'UNDER_ATTENDED' | 'BALANCED' | 'INSUFFICIENT_DATA';

export interface APDIRecordResponse {
  record_id: string;
  run_id: string;
  entity_id: string;
  entity_name: string;
  entity_type: string;
  role_cohort: string;
  tournament: string;
  comparison_window: string;
  raw_attention_score: number;
  normalized_attention_score: number | null;
  raw_performance_score: number;
  normalized_performance_score: number | null;
  apdi_value: number | null;
  discrepancy_category: DiscrepancyCategory;
  evidence_sufficiency_status: 'VALID' | 'PARTIAL_COVERAGE' | 'INSUFFICIENT_DATA' | string;
  sample_size_indicators: Record<string, any>;
  data_quality_warnings: string[];
  framing_breakdown: Record<string, any>;
  evidence_lineage: Record<string, any>;
  formula_version: string;
  created_at_utc: string;
}

export interface AnalyticsValidationResponse {
  is_valid: boolean;
  issues: string[];
  checked_at_utc: string;
}

export interface IngestionRunResponse {
  run_id: string;
  source_name: string;
  status: string;
  started_at_utc: string;
  completed_at_utc: string | null;
  records_extracted: number;
  records_ingested: number;
  records_skipped: number;
  error_message: string | null;
}

export interface SourceRecordResponse {
  provenance_id: string;
  source_name: string;
  source_identifier: string;
  source_url: string | null;
  harvest_timestamp_utc: string;
  http_status: number | null;
  content_hash_sha256: string;
  pipeline_version: string;
  license_tag: string;
  redistributable: boolean;
}

export interface PipelineStatsResponse {
  source_id: string;
  total_discovered: number;
  total_attempts: number;
  http_errors: number;
  total_errors: number;
  state_distribution: Record<string, number>;
  entity_counts: Record<string, number>;
}

export interface AnalyticsRunResponse {
  run_id: string;
  status: string;
  tournament: string;
  entity_type: string | null;
  cohorts_analyzed: string[];
  entities_processed: number;
  valid_apdi_count: number;
  insufficient_data_count: number;
  warnings: string[];
  started_at_utc: string;
  completed_at_utc: string | null;
}

export interface ErrorResponse {
  error: string;
  message: string;
  detail?: any;
  timestamp_utc: string;
}
