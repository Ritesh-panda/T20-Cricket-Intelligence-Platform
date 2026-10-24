import { describe, it, expect, vi } from 'vitest';
import { extractErrorMessage, api, apiClient } from '../lib/api';

describe('API Client & Error Handling', () => {
  it('extracts custom error message from server response', () => {
    const error = {
      isAxiosError: true,
      response: {
        status: 404,
        data: {
          error: 'ResourceNotFound',
          message: "matches with ID 'm_missing' was not found.",
        },
      },
    };
    expect(extractErrorMessage(error)).toBe("matches with ID 'm_missing' was not found.");
  });

  it('handles network error cleanly', () => {
    const error = {
      isAxiosError: true,
      message: 'Network Error',
    };
    expect(extractErrorMessage(error)).toContain('Cannot connect to the research API');
  });

  it('handles request timeout cleanly', () => {
    const error = {
      isAxiosError: true,
      code: 'ECONNABORTED',
    };
    expect(extractErrorMessage(error)).toContain('timed out');
  });

  it('preserves INSUFFICIENT_DATA and null APDI values without converting to zero', async () => {
    const mockApdiResponse = {
      data: {
        items: [
          {
            record_id: 'apdi_test_1',
            entity_id: 'p_unknown',
            entity_name: 'Unknown Player',
            entity_type: 'player',
            role_cohort: 'batter',
            tournament: 'T20 World Cup 2024',
            comparison_window: 'tournament',
            raw_attention_score: 5.0,
            normalized_attention_score: null,
            raw_performance_score: 12.0,
            normalized_performance_score: null,
            apdi_value: null,
            discrepancy_category: 'INSUFFICIENT_DATA',
            evidence_sufficiency_status: 'INSUFFICIENT_DATA',
            sample_size_indicators: {},
            data_quality_warnings: ['Sample size below threshold'],
            framing_breakdown: {},
            evidence_lineage: {},
            formula_version: '6A.1.0',
            created_at_utc: '2026-10-24T12:00:00Z',
          },
        ],
        pagination: { total: 1, limit: 20, offset: 0, has_more: false },
      },
    };

    vi.spyOn(apiClient, 'get').mockResolvedValueOnce(mockApdiResponse);

    const result = await api.getAPDIRecords();
    expect(result.items.length).toBe(1);
    const rec = result.items[0];
    expect(rec.discrepancy_category).toBe('INSUFFICIENT_DATA');
    expect(rec.apdi_value).toBeNull();
    expect(rec.normalized_attention_score).toBeNull();
    expect(rec.normalized_performance_score).toBeNull();
    // Guard against treating null as 0
    expect(rec.apdi_value).not.toBe(0);
  });
});
