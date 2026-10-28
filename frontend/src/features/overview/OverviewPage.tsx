import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Trophy,
  Newspaper,
  MessageSquare,
  Network,
  Scale,
  ShieldCheck,
  AlertCircle,
  Database,
  ArrowRight,
  TrendingUp,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { api, extractErrorMessage } from '../../lib/api';
import { MetricCard } from '../../components/ui/MetricCard';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { EmptyState } from '../../components/ui/EmptyState';
import { ErrorState } from '../../components/ui/ErrorState';
import { Skeleton } from '../../components/ui/Skeleton';

export const OverviewPage: React.FC = () => {
  const {
    data: status,
    isLoading: isStatusLoading,
    error: statusError,
    refetch: refetchStatus,
  } = useQuery({
    queryKey: ['systemStatus'],
    queryFn: () => api.getStatus(),
  });

  const {
    data: overview,
    isLoading: isOverviewLoading,
    error: overviewError,
  } = useQuery({
    queryKey: ['analyticsOverview'],
    queryFn: () => api.getAnalyticsOverview(),
  });

  const {
    data: pipelineStats,
    isLoading: isStatsLoading,
  } = useQuery({
    queryKey: ['pipelineStats'],
    queryFn: () => api.getPipelineStats(),
  });

  const isLoading = isStatusLoading || isOverviewLoading;

  if (statusError) {
    return (
      <ErrorState
        title="Failed to Load Research Overview"
        message={extractErrorMessage(statusError)}
        onRetry={() => refetchStatus()}
      />
    );
  }

  const recordCounts = status?.record_counts || {
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
  };

  const isCorpusEmpty =
    recordCounts.matches === 0 &&
    recordCounts.articles === 0 &&
    recordCounts.commentary_entries === 0;

  return (
    <div className="space-y-6">
      {/* Platform Status Banner - Apple Sequoia Glass Capsule */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-5 rounded-2xl apple-glass-card shadow-apple-card dark:shadow-apple-card-dark">
        <div className="flex items-center gap-3.5">
          <div className="w-11 h-11 rounded-2xl bg-[#34C759]/15 text-[#34C759] flex items-center justify-center shadow-inner">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-semibold text-slate-900 dark:text-white tracking-tight">
                Analytical Quality Gate:
              </h2>
              <Badge
                variant={
                  status?.data_sufficiency_status === 'VALID'
                    ? 'success'
                    : status?.data_sufficiency_status === 'PARTIAL_COVERAGE'
                    ? 'warning'
                    : 'insufficient_data'
                }
              >
                {status?.data_sufficiency_status || 'UNKNOWN'}
              </Badge>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 flex items-center gap-1.5">
              <span>Tournament scope:</span>
              <span className="font-medium text-slate-800 dark:text-slate-200">
                {status?.tournament || 'T20 World Cup 2024'}
              </span>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2.5 self-end sm:self-auto">
          <Link to="/apdi">
            <Button variant="primary" size="sm" className="text-xs gap-1.5 shadow-sm">
              <span>APDI Explorer</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Button>
          </Link>
          <Link to="/health">
            <Button variant="secondary" size="sm" className="text-xs">
              Diagnostics
            </Button>
          </Link>
        </div>
      </div>

      {/* Primary Research Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 sm:gap-4">
        {isLoading ? (
          Array.from({ length: 6 }).map((_, i) => (
            <Card key={i} className="p-4 rounded-2xl">
              <Skeleton className="h-4 w-16 mb-2 rounded-lg" />
              <Skeleton className="h-8 w-12 rounded-lg" />
            </Card>
          ))
        ) : (
          <>
            <MetricCard
              label="Matches"
              value={recordCounts.matches}
              subtext="Cricsheet matches"
              icon={Trophy}
            />
            <MetricCard
              label="Deliveries"
              value={recordCounts.deliveries.toLocaleString()}
              subtext="Ball-by-ball facts"
              icon={Database}
            />
            <MetricCard
              label="Articles"
              value={recordCounts.articles}
              subtext="News journalism"
              icon={Newspaper}
            />
            <MetricCard
              label="Commentary"
              value={recordCounts.commentary_entries}
              subtext="Overs indexed"
              icon={MessageSquare}
            />
            <MetricCard
              label="Topics"
              value={overview?.attention_metrics_count ? 'Active' : 0}
              subtext="Discovered clusters"
              icon={Network}
            />
            <MetricCard
              label="APDI Records"
              value={overview?.apdi_records_count || 0}
              subtext="Evaluated entities"
              icon={Scale}
              badge={
                overview && overview.apdi_records_count > 0 ? (
                  <Badge variant="balanced">Computed</Badge>
                ) : (
                  <Badge variant="insufficient_data">0 Valid</Badge>
                )
              }
            />
          </>
        )}
      </div>

      {/* Main Grid: Analytical Readiness & APDI Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Analytical Readiness Assessment */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <div>
              <CardTitle>Analytical Evidence & Preflight Readiness</CardTitle>
              <CardDescription>
                Quality gate verifying canonical entities, delivery reconciliation, and sample size
                thresholds.
              </CardDescription>
            </div>
            <Badge
              variant={status?.is_analytics_ready ? 'success' : 'insufficient_data'}
            >
              {status?.is_analytics_ready ? 'Analytics Ready' : 'Insufficient Evidence'}
            </Badge>
          </CardHeader>
          <CardContent className="space-y-5">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
              <div className="p-4 rounded-2xl bg-black/[0.02] dark:bg-white/[0.03] border border-black/[0.04] dark:border-white/[0.06] transition-transform hover:-translate-y-0.5">
                <span className="text-[11px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
                  Batters Eligible
                </span>
                <p className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white tabular-nums mt-1">
                  {recordCounts.eligible_batters}
                </p>
              </div>
              <div className="p-4 rounded-2xl bg-black/[0.02] dark:bg-white/[0.03] border border-black/[0.04] dark:border-white/[0.06] transition-transform hover:-translate-y-0.5">
                <span className="text-[11px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
                  Bowlers Eligible
                </span>
                <p className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white tabular-nums mt-1">
                  {recordCounts.eligible_bowlers}
                </p>
              </div>
              <div className="p-4 rounded-2xl bg-black/[0.02] dark:bg-white/[0.03] border border-black/[0.04] dark:border-white/[0.06] transition-transform hover:-translate-y-0.5">
                <span className="text-[11px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
                  Teams Eligible
                </span>
                <p className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white tabular-nums mt-1">
                  {recordCounts.eligible_teams}
                </p>
              </div>
              <div className="p-4 rounded-2xl bg-black/[0.02] dark:bg-white/[0.03] border border-black/[0.04] dark:border-white/[0.06] transition-transform hover:-translate-y-0.5">
                <span className="text-[11px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
                  Resolved Entities
                </span>
                <p className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white tabular-nums mt-1">
                  {recordCounts.resolved_mentions}
                </p>
              </div>
            </div>

            {/* Warnings list if any */}
            {status?.warnings && status.warnings.length > 0 && (
              <div className="p-4 rounded-2xl bg-[#FF9500]/10 border border-[#FF9500]/20 text-xs text-amber-900 dark:text-amber-300 space-y-1.5">
                <div className="flex items-center gap-2 font-semibold text-[#FF9500]">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>Evidence Sufficiency Warnings:</span>
                </div>
                <ul className="list-disc list-inside space-y-1 ml-1 text-slate-700 dark:text-amber-200/90">
                  {status.warnings.map((w, i) => (
                    <li key={i}>{w}</li>
                  ))}
                </ul>
              </div>
            )}
          </CardContent>
        </Card>

        {/* APDI Summary Snapshot - Apple Vision Style with Segmented Bar */}
        <Card>
          <CardHeader>
            <CardTitle>APDI Discrepancy Breakdown</CardTitle>
            <CardDescription>Attention-to-Performance Distribution</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Apple Storage / Distribution Segmented Bar */}
            {overview && overview.apdi_records_count > 0 ? (
              <div className="space-y-2">
                <div className="h-3 w-full rounded-full bg-black/[0.04] dark:bg-white/[0.06] p-0.5 flex overflow-hidden gap-0.5">
                  <div
                    style={{
                      width: `${Math.max(
                        5,
                        ((overview.over_attended_count || 0) / overview.apdi_records_count) * 100
                      )}%`,
                    }}
                    className="h-full rounded-full bg-[#FF9500] transition-all"
                    title={`Over-Attended: ${overview.over_attended_count || 0}`}
                  />
                  <div
                    style={{
                      width: `${Math.max(
                        5,
                        ((overview.under_attended_count || 0) / overview.apdi_records_count) * 100
                      )}%`,
                    }}
                    className="h-full rounded-full bg-[#5856D6] transition-all"
                    title={`Under-Attended: ${overview.under_attended_count || 0}`}
                  />
                  <div
                    style={{
                      width: `${Math.max(
                        5,
                        ((overview.balanced_count || 0) / overview.apdi_records_count) * 100
                      )}%`,
                    }}
                    className="h-full rounded-full bg-[#34C759] transition-all"
                    title={`Balanced: ${overview.balanced_count || 0}`}
                  />
                  {(overview.insufficient_data_count || 0) > 0 && (
                    <div
                      style={{
                        width: `${Math.max(
                          5,
                          ((overview.insufficient_data_count || 0) / overview.apdi_records_count) * 100
                        )}%`,
                      }}
                      className="h-full rounded-full bg-slate-400 dark:bg-slate-600 transition-all"
                      title={`Insufficient Data: ${overview.insufficient_data_count || 0}`}
                    />
                  )}
                </div>
              </div>
            ) : null}

            <div className="space-y-2.5">
              <div className="flex items-center justify-between text-xs p-2 rounded-xl bg-black/[0.02] dark:bg-white/[0.03]">
                <span className="flex items-center gap-2.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-[#FF9500] ring-4 ring-[#FF9500]/20" />
                  <span className="text-slate-700 dark:text-slate-300 font-medium">Over-Attended</span>
                </span>
                <span className="font-semibold tabular-nums text-slate-900 dark:text-white">
                  {overview?.over_attended_count || 0}
                </span>
              </div>
              <div className="flex items-center justify-between text-xs p-2 rounded-xl bg-black/[0.02] dark:bg-white/[0.03]">
                <span className="flex items-center gap-2.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-[#5856D6] ring-4 ring-[#5856D6]/20" />
                  <span className="text-slate-700 dark:text-slate-300 font-medium">Under-Attended</span>
                </span>
                <span className="font-semibold tabular-nums text-slate-900 dark:text-white">
                  {overview?.under_attended_count || 0}
                </span>
              </div>
              <div className="flex items-center justify-between text-xs p-2 rounded-xl bg-black/[0.02] dark:bg-white/[0.03]">
                <span className="flex items-center gap-2.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-[#34C759] ring-4 ring-[#34C759]/20" />
                  <span className="text-slate-700 dark:text-slate-300 font-medium">Balanced</span>
                </span>
                <span className="font-semibold tabular-nums text-slate-900 dark:text-white">
                  {overview?.balanced_count || 0}
                </span>
              </div>
              <div className="flex items-center justify-between text-xs p-2 rounded-xl bg-black/[0.02] dark:bg-white/[0.03]">
                <span className="flex items-center gap-2.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-slate-400 ring-4 ring-slate-400/20" />
                  <span className="text-slate-700 dark:text-slate-300 font-medium">Insufficient Data</span>
                </span>
                <span className="font-semibold tabular-nums text-slate-900 dark:text-white">
                  {overview?.insufficient_data_count || 0}
                </span>
              </div>
            </div>

            <div className="pt-3 border-t border-black/[0.06] dark:border-white/[0.08]">
              <Link
                to="/apdi"
                className="text-xs text-[#007AFF] dark:text-[#0A84FF] font-medium hover:underline flex items-center justify-between group"
              >
                <span>Explore full methodology & cohorts</span>
                <ArrowRight className="w-3.5 h-3.5 transition-transform group-hover:translate-x-1" />
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Empty State Banner when Database has 0 records */}
      {isCorpusEmpty && (
        <EmptyState
          title="Analytical Platform Initialized (Zero Records Ingested)"
          description="The FastAPI backend and all research algorithms (NER, embeddings, sentiment, clustering, APDI) are operational. However, the SQLite database currently contains zero tournament records."
          secondaryInfo="To acquire tournament data: python -m src.pipeline run --source cricsheet"
          icon="database"
        />
      )}
    </div>
  );
};
