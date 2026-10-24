import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from '../context/ThemeContext';
import { APDIPage } from '../features/apdi/APDIPage';
import { MatchesPage } from '../features/matches/MatchesPage';
import { HealthPage } from '../features/health/HealthPage';
import { OverviewPage } from '../features/overview/OverviewPage';
import { api } from '../lib/api';

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <BrowserRouter>{children}</BrowserRouter>
      </ThemeProvider>
    </QueryClientProvider>
  );
};

describe('APDI Explorer Safeguards & Integrity', () => {
  it('correctly handles INSUFFICIENT_DATA and preserves null apdi_value without fabrication', async () => {
    vi.spyOn(api, 'getAPDIRecords').mockResolvedValueOnce({
      items: [
        {
          record_id: 'apdi_rec_001',
          run_id: 'run_test_01',
          entity_id: 'player_001',
          entity_name: 'Test Bowler',
          entity_type: 'PLAYER',
          role_cohort: 'bowler',
          tournament: 'ipl_2024',
          comparison_window: 'full_tournament',
          raw_attention_score: 1.0,
          normalized_attention_score: null,
          raw_performance_score: 1.0,
          normalized_performance_score: null,
          apdi_value: null,
          discrepancy_category: 'INSUFFICIENT_DATA',
          evidence_sufficiency_status: 'INSUFFICIENT_DATA',
          sample_size_indicators: { total_paragraphs: 1 },
          data_quality_warnings: ['Sample size below threshold'],
          framing_breakdown: {},
          evidence_lineage: {},
          formula_version: 'v1.0',
          created_at_utc: '2026-10-24T12:00:00Z',
        },
      ],
      pagination: {
        total: 1,
        limit: 15,
        offset: 0,
        has_more: false,
      },
    });

    render(<APDIPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('Test Bowler')).toBeInTheDocument();
    });

    // Verify category badge
    expect(screen.getByText('INSUFFICIENT DATA')).toBeInTheDocument();

    // Verify that the APDI value is displayed as unavailable, NOT fabricated 0 or 0.00
    expect(screen.getByText('unavailable')).toBeInTheDocument();

    // Verify methodology explanation header is present
    expect(
      screen.getByText('APDI Mathematical Formulation & Cohort Normalization')
    ).toBeInTheDocument();
  });
});

describe('Matches Explorer Empty States', () => {
  it('displays honest empty state when no matches have been ingested', async () => {
    vi.spyOn(api, 'getMatches').mockResolvedValueOnce({
      items: [],
      pagination: {
        total: 0,
        limit: 20,
        offset: 0,
        has_more: false,
      },
    });

    render(<MatchesPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('No Match Records Found')).toBeInTheDocument();
      expect(
        screen.getByText(/The database currently contains 0 structured match records/i)
      ).toBeInTheDocument();
    });
  });
});

describe('System Health Diagnostic Rigor', () => {
  it('displays distinct health tiers: Process, Persistence, Inventory, and Quality Gate', async () => {
    vi.spyOn(api, 'getHealth').mockResolvedValueOnce({
      status: 'healthy',
      version: '1.0.0',
      timestamp_utc: '2026-10-24T12:00:00Z',
    });

    vi.spyOn(api, 'getReadiness').mockResolvedValueOnce({
      status: 'ready',
      database_accessible: true,
      schema_version: 1,
      database_tables_count: 14,
      timestamp_utc: '2026-10-24T12:00:00Z',
    });

    vi.spyOn(api, 'getStatus').mockResolvedValueOnce({
      pipeline_status: 'empty',
      tournament: 'all',
      record_counts: {
        matches: 0,
        deliveries: 0,
        articles: 0,
        paragraphs: 0,
        commentary_entries: 0,
        entity_mentions: 0,
        resolved_mentions: 0,
        sentiment_baselines: 0,
        eligible_batters: 0,
        eligible_bowlers: 0,
        eligible_teams: 0,
      },
      data_sufficiency_status: 'INSUFFICIENT_DATA',
      is_analytics_ready: false,
      supported_capabilities: ['storage', 'nlp'],
      warnings: ['No match data loaded'],
      checked_at_utc: '2026-10-24T12:00:00Z',
    });

    vi.spyOn(api, 'validateAnalytics').mockResolvedValueOnce({
      is_valid: true,
      issues: [],
      checked_at_utc: '2026-10-24T12:00:00Z',
    });

    render(<HealthPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('1. API Liveness')).toBeInTheDocument();
      expect(screen.getByText('2. SQLite Persistence')).toBeInTheDocument();
      expect(screen.getByText('3. Data Availability')).toBeInTheDocument();
      expect(screen.getByText('4. Analytics Quality Gate')).toBeInTheDocument();
    });
  });
});

describe('Overview Research Readiness & Ingestion Notice', () => {
  it('shows unpopulated notice and action required when corpus is empty', async () => {
    vi.spyOn(api, 'getStatus').mockResolvedValueOnce({
      pipeline_status: 'empty',
      tournament: 'all',
      record_counts: {
        matches: 0,
        deliveries: 0,
        articles: 0,
        paragraphs: 0,
        commentary_entries: 0,
        entity_mentions: 0,
        resolved_mentions: 0,
        sentiment_baselines: 0,
        eligible_batters: 0,
        eligible_bowlers: 0,
        eligible_teams: 0,
      },
      data_sufficiency_status: 'INSUFFICIENT_DATA',
      is_analytics_ready: false,
      supported_capabilities: ['storage'],
      warnings: [],
      checked_at_utc: '2026-10-24T12:00:00Z',
    });

    vi.spyOn(api, 'getAnalyticsOverview').mockResolvedValueOnce({
      tournament: 'all',
      attention_metrics_count: 0,
      performance_metrics_count: 0,
      apdi_records_count: 0,
      over_attended_count: 0,
      under_attended_count: 0,
      balanced_count: 0,
      insufficient_data_count: 0,
      analytics_runs_count: 0,
      preflight_status: 'empty',
      is_eligible: false,
      warnings: ['Empty corpus'],
    });

    vi.spyOn(api, 'getPipelineStats').mockResolvedValueOnce({
      source_id: 'all',
      total_discovered: 0,
      total_attempts: 0,
      http_errors: 0,
      total_errors: 0,
      state_distribution: {},
      entity_counts: {},
    });

    render(<OverviewPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('Analytical Quality Gate:')).toBeInTheDocument();
      expect(
        screen.getByText('Analytical Platform Initialized (Zero Records Ingested)')
      ).toBeInTheDocument();
      expect(screen.getByText('APDI Discrepancy Breakdown')).toBeInTheDocument();
    });
  });
});
