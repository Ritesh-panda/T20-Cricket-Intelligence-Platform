import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import App from '../App';
import { apiClient } from '../lib/api';

describe('App & Shell Integration', () => {
  it('renders application navigation shell with all required sections', async () => {
    // Mock health & readiness API responses
    vi.spyOn(apiClient, 'get').mockImplementation((url) => {
      if (url === '/health') {
        return Promise.resolve({
          data: { status: 'healthy', version: '1.0.0', timestamp_utc: new Date().toISOString() },
        });
      }
      if (url === '/ready') {
        return Promise.resolve({
          data: {
            status: 'ready',
            database_accessible: true,
            schema_version: 5,
            database_tables_count: 28,
            timestamp_utc: new Date().toISOString(),
          },
        });
      }
      if (url === '/api/v1/status') {
        return Promise.resolve({
          data: {
            pipeline_status: 'empty',
            tournament: 'T20 World Cup 2024',
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
            supported_capabilities: ['canonical_schemas', 'rest_api_serving'],
            warnings: ['No structured matches found'],
            checked_at_utc: new Date().toISOString(),
          },
        });
      }
      if (url === '/api/v1/analytics/overview') {
        return Promise.resolve({
          data: {
            tournament: 'T20 World Cup 2024',
            attention_metrics_count: 0,
            performance_metrics_count: 0,
            apdi_records_count: 0,
            over_attended_count: 0,
            under_attended_count: 0,
            balanced_count: 0,
            insufficient_data_count: 0,
            analytics_runs_count: 0,
            preflight_status: 'INSUFFICIENT_DATA',
            is_eligible: false,
            warnings: [],
          },
        });
      }
      return Promise.resolve({
        data: { items: [], pagination: { total: 0, limit: 20, offset: 0, has_more: false } },
      });
    });

    render(<App />);

    // Check brand presence
    expect(screen.getAllByText(/Cricket Intel/i).length).toBeGreaterThan(0);

    // Check navigation items
    expect(screen.getAllByText('Overview').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Matches').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Players').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Media Intelligence').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Topics & Narratives').length).toBeGreaterThan(0);
    expect(screen.getAllByText('APDI Explorer').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Data Sources').length).toBeGreaterThan(0);
    expect(screen.getAllByText('System Health').length).toBeGreaterThan(0);
  });
});
