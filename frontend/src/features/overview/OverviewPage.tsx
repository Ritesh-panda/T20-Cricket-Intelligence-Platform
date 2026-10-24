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
      {/* Platform Status Banner */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 rounded-xl bg-slate-100 dark:bg-cricket-navy-900 border border-slate-200 dark:border-cricket-navy-800">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              <span>Analytical Quality Gate:</span>
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
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Tournament scope:{' '}
              <span className="font-mono text-slate-700 dark:text-slate-300">
                {status?.tournament || 'T20 World Cup 2024'}
              </span>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 self-end sm:self-auto">
          <Link to="/apdi">
            <Button variant="outline" size="sm" className="text-xs gap-1.5">
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
            <Card key={i} className="p-4">
              <Skeleton className="h-4 w-16 mb-2" />
              <Skeleton className="h-8 w-12" />
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
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
              <div className="p-3 rounded-lg bg-slate-50 dark:bg-cricket-navy-950/60 border border-slate-100 dark:border-cricket-navy-800">
                <span className="text-[11px] font-medium text-slate-500 uppercase tracking-wider">
                  Batters Eligible
                </span>
                <p className="text-xl font-bold font-mono text-slate-800 dark:text-slate-100 mt-1">
                  {recordCounts.eligible_batters}
                </p>
              </div>
              <div className="p-3 rounded-lg bg-slate-50 dark:bg-cricket-navy-950/60 border border-slate-100 dark:border-cricket-navy-800">
                <span className="text-[11px] font-medium text-slate-500 uppercase tracking-wider">
                  Bowlers Eligible
                </span>
                <p className="text-xl font-bold font-mono text-slate-800 dark:text-slate-100 mt-1">
                  {recordCounts.eligible_bowlers}
                </p>
              </div>
              <div className="p-3 rounded-lg bg-slate-50 dark:bg-cricket-navy-950/60 border border-slate-100 dark:border-cricket-navy-800">
                <span className="text-[11px] font-medium text-slate-500 uppercase tracking-wider">
                  Teams Eligible
                </span>
                <p className="text-xl font-bold font-mono text-slate-800 dark:text-slate-100 mt-1">
                  {recordCounts.eligible_teams}
                </p>
              </div>
              <div className="p-3 rounded-lg bg-slate-50 dark:bg-cricket-navy-950/60 border border-slate-100 dark:border-cricket-navy-800">
                <span className="text-[11px] font-medium text-slate-500 uppercase tracking-wider">
                  Resolved Entities
                </span>
                <p className="text-xl font-bold font-mono text-slate-800 dark:text-slate-100 mt-1">
                  {recordCounts.resolved_mentions}
                </p>
              </div>
            </div>

            {/* Warnings list if any */}
            {status?.warnings && status.warnings.length > 0 && (
              <div className="p-3.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-xs text-amber-800 dark:text-amber-300 space-y-1">
                <div className="flex items-center gap-1.5 font-semibold text-amber-900 dark:text-amber-200">
                  <AlertCircle className="w-4 h-4 shrink-0 text-amber-500" />
                  <span>Evidence Sufficiency Warnings:</span>
                </div>
                <ul className="list-disc list-inside space-y-0.5 ml-1 text-slate-600 dark:text-amber-300/80">
                  {status.warnings.map((w, i) => (
                    <li key={i}>{w}</li>
                  ))}
                </ul>
              </div>
            )}
          </CardContent>
        </Card>

        {/* APDI Summary Snapshot */}
        <Card>
          <CardHeader>
            <CardTitle>APDI Discrepancy Breakdown</CardTitle>
            <CardDescription>Attention-to-Performance Distribution</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
                  <span className="text-slate-600 dark:text-slate-300">Over-Attended</span>
                </span>
                <span className="font-mono font-semibold">
                  {overview?.over_attended_count || 0}
                </span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-indigo-500" />
                  <span className="text-slate-600 dark:text-slate-300">Under-Attended</span>
                </span>
                <span className="font-mono font-semibold">
                  {overview?.under_attended_count || 0}
                </span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
                  <span className="text-slate-600 dark:text-slate-300">Balanced</span>
                </span>
                <span className="font-mono font-semibold">
                  {overview?.balanced_count || 0}
                </span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-slate-400" />
                  <span className="text-slate-600 dark:text-slate-300">Insufficient Data</span>
                </span>
                <span className="font-mono font-semibold">
                  {overview?.insufficient_data_count || 0}
                </span>
              </div>
            </div>

            <div className="pt-3 border-t border-slate-100 dark:border-cricket-navy-800">
              <Link to="/apdi" className="text-xs text-emerald-600 dark:text-emerald-400 font-medium hover:underline flex items-center gap-1">
                Explore full methodology & cohorts <ArrowRight className="w-3 h-3" />
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
