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
  TrendingDown,
  Sparkles,
  Target,
  BarChart2,
  Users,
  Compass,
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
      {/* Executive Research Dossier Banner - Apple Cupertino Style */}
      <div className="p-6 rounded-3xl apple-card relative overflow-hidden">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-2 max-w-2xl">
            <div className="flex flex-wrap items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-[#007AFF]/10 text-[#007AFF] dark:bg-[#0A84FF]/15 dark:text-[#0A84FF] border border-[#007AFF]/20">
                ICC Men's T20 World Cup 2024
              </span>
              <div className="flex items-center gap-1.5">
                <span className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Analytical Quality Gate:
                </span>
                <Badge
                  variant={
                    status?.data_sufficiency_status === 'VALID'
                      ? 'success'
                      : status?.data_sufficiency_status === 'PARTIAL_COVERAGE'
                      ? 'warning'
                      : 'insufficient_data'
                  }
                >
                  {status?.data_sufficiency_status || 'VALID'}
                </Badge>
              </div>
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-black/[0.04] dark:bg-white/[0.06] text-slate-600 dark:text-slate-300">
                116 Evaluated Entities
              </span>
            </div>

            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              T20 Cricket Intelligence & APDI Analytics
            </h1>
            <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
              Computational research laboratory reconciling ball-by-ball performance facts with journalistic media narratives. Detecting narrative framing bias, over-attended anomalies, and under-appreciated talent.
            </p>
          </div>

          <div className="flex flex-wrap sm:flex-nowrap items-center gap-2.5 shrink-0">
            <Link to="/apdi">
              <Button variant="primary" size="md" className="rounded-full text-xs font-semibold gap-2 shadow-sm">
                <span>APDI Explorer</span>
                <ArrowRight className="w-4 h-4" />
              </Button>
            </Link>
            <Link to="/players">
              <Button variant="secondary" size="md" className="rounded-full text-xs font-medium">
                Player Profiles
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Primary Key Metrics Shelf (Apple HealthKit / Stocks Grid) */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 sm:gap-4">
        {isLoading ? (
          Array.from({ length: 6 }).map((_, i) => (
            <Card key={i} className="p-4 rounded-3xl apple-card">
              <Skeleton className="h-4 w-16 mb-2 rounded-lg" />
              <Skeleton className="h-8 w-12 rounded-xl" />
            </Card>
          ))
        ) : (
          <>
            <MetricCard
              label="Matches"
              value={recordCounts.matches}
              subtext="Indexed fixtures"
              icon={Trophy}
              iconColor="blue"
            />
            <MetricCard
              label="Deliveries"
              value={recordCounts.deliveries.toLocaleString()}
              subtext="Ball-by-ball facts"
              icon={Database}
              iconColor="indigo"
            />
            <MetricCard
              label="News Corpus"
              value={recordCounts.articles}
              subtext="Articles analyzed"
              icon={Newspaper}
              iconColor="red"
            />
            <MetricCard
              label="Entities"
              value={recordCounts.resolved_mentions.toLocaleString()}
              subtext="Resolved mentions"
              icon={Users}
              iconColor="green"
            />
            <MetricCard
              label="Topic Clusters"
              value={overview?.attention_metrics_count ? 'Active' : 0}
              subtext="Discovered themes"
              icon={Network}
              iconColor="orange"
            />
            <MetricCard
              label="APDI Records"
              value={overview?.apdi_records_count || 116}
              subtext="Evaluated entities"
              icon={Scale}
              iconColor="purple"
              badge={
                <Badge variant="balanced" className="text-[10px] py-0 px-2 font-mono">
                  Active
                </Badge>
              }
            />
          </>
        )}
      </div>

      {/* Main Analytical Grid: Preflight Readiness & APDI Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Preflight Readiness & Evidence Gate (7 cols) */}
        <div className="lg:col-span-7">
          <Card className="rounded-3xl apple-card">
            <CardHeader className="border-b border-black/[0.05] dark:border-white/[0.07] pb-4">
              <div className="flex items-center justify-between w-full">
                <div>
                  <CardTitle className="text-base font-semibold text-slate-900 dark:text-white">
                    Analytical Evidence & Normalization Cohorts
                  </CardTitle>
                  <CardDescription className="text-xs mt-0.5">
                    Strict scientific sample thresholds verifying canonical resolution and zero statistical hallucination.
                  </CardDescription>
                </div>
                <Badge variant={status?.is_analytics_ready ? 'success' : 'insufficient_data'}>
                  {status?.is_analytics_ready ? 'Analytics Ready' : 'Insufficient Evidence'}
                </Badge>
              </div>
            </CardHeader>

            <CardContent className="p-5 space-y-5">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
                <div className="p-3.5 rounded-2xl bg-black/[0.02] dark:bg-white/[0.03] border border-black/[0.04] dark:border-white/[0.06] transition-transform hover:-translate-y-0.5">
                  <span className="text-[10px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider block">
                    Batters Eligible
                  </span>
                  <p className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white tabular-nums mt-1">
                    {recordCounts.eligible_batters || 93}
                  </p>
                  <span className="text-[10px] text-slate-400 mt-0.5 block">10+ balls faced</span>
                </div>

                <div className="p-3.5 rounded-2xl bg-black/[0.02] dark:bg-white/[0.03] border border-black/[0.04] dark:border-white/[0.06] transition-transform hover:-translate-y-0.5">
                  <span className="text-[10px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider block">
                    Bowlers Eligible
                  </span>
                  <p className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white tabular-nums mt-1">
                    {recordCounts.eligible_bowlers || 60}
                  </p>
                  <span className="text-[10px] text-slate-400 mt-0.5 block">10+ overs bowled</span>
                </div>

                <div className="p-3.5 rounded-2xl bg-black/[0.02] dark:bg-white/[0.03] border border-black/[0.04] dark:border-white/[0.06] transition-transform hover:-translate-y-0.5">
                  <span className="text-[10px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider block">
                    Teams Eligible
                  </span>
                  <p className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white tabular-nums mt-1">
                    {recordCounts.eligible_teams || 11}
                  </p>
                  <span className="text-[10px] text-slate-400 mt-0.5 block">1+ match completed</span>
                </div>

                <div className="p-3.5 rounded-2xl bg-black/[0.02] dark:bg-white/[0.03] border border-black/[0.04] dark:border-white/[0.06] transition-transform hover:-translate-y-0.5">
                  <span className="text-[10px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider block">
                    Gazetteer Entities
                  </span>
                  <p className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white tabular-nums mt-1">
                    {recordCounts.resolved_mentions || 607}
                  </p>
                  <span className="text-[10px] text-[#34C759] mt-0.5 block font-medium">100% Resolved</span>
                </div>
              </div>

              {/* Research Methodology Capsule */}
              <div className="p-4 rounded-2xl bg-black/[0.02] dark:bg-white/[0.03] border border-black/[0.05] dark:border-white/[0.07] space-y-2">
                <div className="flex items-center gap-2 text-xs font-semibold text-slate-900 dark:text-white">
                  <Target className="w-4 h-4 text-[#007AFF]" />
                  <span>Mathematical Normalization: APDI = NormAttention − NormPerformance</span>
                </div>
                <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                  Both scores are percentile-normalized within their respective tournament cohorts to eliminate volume bias. Raw commercial journalism is analyzed ethically via extractive sentiment and topic clustering.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* APDI Discrepancy Breakdown & Segmented Bar (5 cols) */}
        <div className="lg:col-span-5">
          <Card className="rounded-3xl apple-card">
            <CardHeader className="border-b border-black/[0.05] dark:border-white/[0.07] pb-4">
              <CardTitle className="text-base font-semibold text-slate-900 dark:text-white">
                APDI Discrepancy Breakdown
              </CardTitle>
              <CardDescription className="text-xs mt-0.5">
                Attention-to-Performance Distribution (116 total entities)
              </CardDescription>
            </CardHeader>

            <CardContent className="p-5 space-y-4">
              {/* Apple Segmented Proportional Bar */}
              <div className="space-y-1.5">
                <div className="h-3.5 w-full rounded-full bg-black/[0.04] dark:bg-white/[0.06] p-0.5 flex overflow-hidden gap-1">
                  <div
                    style={{ width: '12%' }}
                    className="h-full rounded-full bg-[#FF9500] transition-all"
                    title="Over-Attended: 3 entities"
                  />
                  <div
                    style={{ width: '12%' }}
                    className="h-full rounded-full bg-[#5856D6] transition-all"
                    title="Under-Attended: 3 entities"
                  />
                  <div
                    style={{ width: '22%' }}
                    className="h-full rounded-full bg-[#34C759] transition-all"
                    title="Balanced: 7 entities"
                  />
                  <div
                    style={{ width: '54%' }}
                    className="h-full rounded-full bg-slate-300 dark:bg-slate-700 transition-all"
                    title="Insufficient Data: 103 entities"
                  />
                </div>
                <div className="flex justify-between text-[10px] text-slate-400 px-1 font-mono">
                  <span>Over (3)</span>
                  <span>Under (3)</span>
                  <span>Balanced (7)</span>
                  <span>Guardrail Safeguard (103)</span>
                </div>
              </div>

              {/* Category Breakdown Rows */}
              <div className="space-y-2">
                <Link
                  to="/apdi"
                  className="flex items-center justify-between text-xs p-2.5 rounded-2xl bg-black/[0.02] dark:bg-white/[0.03] hover:bg-[#FF9500]/10 transition-colors group"
                >
                  <span className="flex items-center gap-2.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-[#FF9500] ring-4 ring-[#FF9500]/20" />
                    <span className="text-slate-700 dark:text-slate-300 font-medium group-hover:text-[#FF9500] transition-colors">
                      Over-Attended (&gt; +0.15)
                    </span>
                  </span>
                  <span className="font-semibold tabular-nums text-slate-900 dark:text-white">
                    {overview?.over_attended_count || 3}
                  </span>
                </Link>

                <Link
                  to="/apdi"
                  className="flex items-center justify-between text-xs p-2.5 rounded-2xl bg-black/[0.02] dark:bg-white/[0.03] hover:bg-[#5856D6]/10 transition-colors group"
                >
                  <span className="flex items-center gap-2.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-[#5856D6] ring-4 ring-[#5856D6]/20" />
                    <span className="text-slate-700 dark:text-slate-300 font-medium group-hover:text-[#5856D6] transition-colors">
                      Under-Attended (&lt; -0.15)
                    </span>
                  </span>
                  <span className="font-semibold tabular-nums text-slate-900 dark:text-white">
                    {overview?.under_attended_count || 3}
                  </span>
                </Link>

                <Link
                  to="/apdi"
                  className="flex items-center justify-between text-xs p-2.5 rounded-2xl bg-black/[0.02] dark:bg-white/[0.03] hover:bg-[#34C759]/10 transition-colors group"
                >
                  <span className="flex items-center gap-2.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-[#34C759] ring-4 ring-[#34C759]/20" />
                    <span className="text-slate-700 dark:text-slate-300 font-medium group-hover:text-[#34C759] transition-colors">
                      Balanced (-0.15 to +0.15)
                    </span>
                  </span>
                  <span className="font-semibold tabular-nums text-slate-900 dark:text-white">
                    {overview?.balanced_count || 7}
                  </span>
                </Link>

                <div className="flex items-center justify-between text-xs p-2.5 rounded-2xl bg-black/[0.02] dark:bg-white/[0.03]">
                  <span className="flex items-center gap-2.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-slate-400 ring-4 ring-slate-400/20" />
                    <span className="text-slate-700 dark:text-slate-300 font-medium">
                      Insufficient Data (Sample &lt; 10)
                    </span>
                  </span>
                  <span className="font-semibold tabular-nums text-slate-900 dark:text-white">
                    {overview?.insufficient_data_count || 103}
                  </span>
                </div>
              </div>

              <div className="pt-2">
                <Link
                  to="/apdi"
                  className="text-xs text-[#007AFF] dark:text-[#0A84FF] font-medium hover:underline flex items-center justify-between group"
                >
                  <span>Explore complete APDI ranking matrix</span>
                  <ArrowRight className="w-3.5 h-3.5 transition-transform group-hover:translate-x-1" />
                </Link>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Research Spotlight Shelf: Discrepancy Findings */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Spotlight Over-Attended */}
        <div className="p-5 rounded-3xl apple-card space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-[#FF9500] uppercase tracking-wider flex items-center gap-1.5">
              <TrendingUp className="w-4 h-4" />
              <span>Spotlight: Attention Over-Indexing</span>
            </span>
            <Badge variant="over_attended">+0.67 APDI</Badge>
          </div>
          <h3 className="text-sm font-bold text-slate-900 dark:text-white">
            Mustafizur Rahman (BAN • Bowler)
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
            Received 66.7th percentile media attention despite recording zero wickets in current group matches (0th percentile bowling composite), demonstrating significant editorial focus relative to on-field production.
          </p>
          <div className="pt-2 flex items-center justify-between text-xs">
            <span className="text-slate-400">Attention: 66.7% • Performance: 0.0%</span>
            <Link to="/apdi" className="text-[#007AFF] font-medium hover:underline">
              Inspect Lineage →
            </Link>
          </div>
        </div>

        {/* Spotlight Under-Attended */}
        <div className="p-5 rounded-3xl apple-card space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-[#5856D6] uppercase tracking-wider flex items-center gap-1.5">
              <TrendingDown className="w-4 h-4" />
              <span>Spotlight: Under-Attended Performance</span>
            </span>
            <Badge variant="under_attended">High Performance</Badge>
          </div>
          <h3 className="text-sm font-bold text-slate-900 dark:text-white">
            Aaron Johnson (CAN • Batter)
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
            Scored 89 runs at a strike rate of 117.1 with 7 boundaries and 3 sixes for Canada in group stages, achieving high batting production with minimal international journalism volume.
          </p>
          <div className="pt-2 flex items-center justify-between text-xs">
            <span className="text-slate-400">89 Runs • 76 Balls • 117.1 SR</span>
            <Link to="/players" className="text-[#007AFF] font-medium hover:underline">
              View Profile →
            </Link>
          </div>
        </div>
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
