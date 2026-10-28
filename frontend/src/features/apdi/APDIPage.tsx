import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Scale,
  TrendingUp,
  AlertCircle,
  HelpCircle,
  Filter,
  CheckCircle,
  X,
  BookOpen,
  Info,
  Shield,
  ArrowRight,
  Database,
  Award,
  Flame,
  Activity,
} from 'lucide-react';
import { api, extractErrorMessage } from '../../lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/Card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/Table';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { EmptyState } from '../../components/ui/EmptyState';
import { ErrorState } from '../../components/ui/ErrorState';
import { Skeleton } from '../../components/ui/Skeleton';
import type { APDIRecordResponse, DiscrepancyCategory } from '../../types/api';

const FEATURED_AUDITS = [
  { id: 'player_mustafizur_rahman', name: 'Mustafizur Rahman', category: 'OVER_ATTENDED', apdi: '+0.67', cohort: 'Bowler' },
  { id: 'team_pak', name: 'Pakistan Team', category: 'OVER_ATTENDED', apdi: '+0.50', cohort: 'Team' },
  { id: 'team_ban', name: 'Bangladesh Team', category: 'OVER_ATTENDED', apdi: '+0.33', cohort: 'Team' },
];

export const APDIPage: React.FC = () => {
  const [roleCohort, setRoleCohort] = useState<string>('');
  const [categoryFilter, setCategoryFilter] = useState<string>('');
  const [selectedRecord, setSelectedRecord] = useState<APDIRecordResponse | null>(null);
  const [page, setPage] = useState<number>(0);
  const limit = 15;

  const {
    data: apdiData,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['apdiRecords', roleCohort, categoryFilter, page],
    queryFn: () =>
      api.getAPDIRecords({
        role_cohort: roleCohort || undefined,
        discrepancy_category: categoryFilter || undefined,
        limit,
        offset: page * limit,
      }),
  });

  const getDiscrepancyBadge = (category: DiscrepancyCategory) => {
    switch (category) {
      case 'OVER_ATTENDED':
        return <Badge variant="over_attended">OVER-ATTENDED</Badge>;
      case 'UNDER_ATTENDED':
        return <Badge variant="under_attended">UNDER-ATTENDED</Badge>;
      case 'BALANCED':
        return <Badge variant="balanced">BALANCED</Badge>;
      case 'INSUFFICIENT_DATA':
        return <Badge variant="insufficient_data">INSUFFICIENT DATA</Badge>;
      default:
        return <Badge variant="neutral">{category}</Badge>;
    }
  };

  const handleSelectAudit = (entityId: string) => {
    const found = apdiData?.items.find((r) => r.entity_id.toLowerCase().includes(entityId.toLowerCase()));
    if (found) setSelectedRecord(found);
  };

  return (
    <div className="space-y-6">
      {/* Header and Filter Toolbar - Apple Frosted Capsule */}
      <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4 p-4 sm:p-5 rounded-3xl apple-glass-card">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-[#AF52DE] to-[#5856D6] text-white flex items-center justify-center shadow-sm shadow-[#AF52DE]/20 shrink-0">
            <Scale className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-slate-900 dark:text-white tracking-tight">
              Attention-to-Performance Discrepancy Index (APDI)
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Measuring narrative and media coverage disproportionality against objective cricket metrics.
            </p>
          </div>
        </div>

        {/* Filters - Apple Pill Selects */}
        <div className="flex items-center gap-2">
          <select
            value={roleCohort}
            onChange={(e) => {
              setRoleCohort(e.target.value);
              setPage(0);
            }}
            className="px-3.5 py-1.5 rounded-full text-xs bg-black/[0.03] dark:bg-white/[0.05] border border-black/[0.06] dark:border-white/[0.08] text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-[#007AFF]/30 transition-all font-medium cursor-pointer"
          >
            <option value="" className="dark:bg-[#1a1d24]">All Cohorts</option>
            <option value="batter" className="dark:bg-[#1a1d24]">Batters</option>
            <option value="bowler" className="dark:bg-[#1a1d24]">Bowlers</option>
            <option value="all_rounder" className="dark:bg-[#1a1d24]">All-Rounders</option>
            <option value="team" className="dark:bg-[#1a1d24]">Teams</option>
          </select>

          <select
            value={categoryFilter}
            onChange={(e) => {
              setCategoryFilter(e.target.value);
              setPage(0);
            }}
            className="px-3.5 py-1.5 rounded-full text-xs bg-black/[0.03] dark:bg-white/[0.05] border border-black/[0.06] dark:border-white/[0.08] text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-[#007AFF]/30 transition-all font-medium cursor-pointer"
          >
            <option value="" className="dark:bg-[#1a1d24]">All Categories</option>
            <option value="OVER_ATTENDED" className="dark:bg-[#1a1d24]">Over-Attended</option>
            <option value="UNDER_ATTENDED" className="dark:bg-[#1a1d24]">Under-Attended</option>
            <option value="BALANCED" className="dark:bg-[#1a1d24]">Balanced</option>
            <option value="INSUFFICIENT_DATA" className="dark:bg-[#1a1d24]">Insufficient Data</option>
          </select>

          {(roleCohort || categoryFilter) && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setRoleCohort('');
                setCategoryFilter('');
                setPage(0);
              }}
              className="rounded-full w-8 h-8 p-0"
              title="Reset filters"
            >
              <X className="w-3.5 h-3.5" />
            </Button>
          )}
        </div>
      </div>

      {/* APDI Methodology Explanation Panel - Apple Vision Style */}
      <Card className="rounded-3xl apple-card">
        <CardContent className="p-5 space-y-4">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-900 dark:text-white">
            <BookOpen className="w-4 h-4 text-[#007AFF]" />
            <span>APDI Mathematical Formulation & Cohort Normalization</span>
          </div>
          <div className="text-xs text-slate-600 dark:text-slate-400 space-y-3 leading-relaxed">
            <div className="flex flex-wrap items-center gap-2">
              <span>The Attention-to-Performance Discrepancy Index (APDI) is defined as:</span>
              <span className="font-mono bg-[#007AFF]/10 text-[#007AFF] px-3 py-1 rounded-full border border-[#007AFF]/20 font-semibold tracking-tight">
                APDI = NormAttention − NormPerformance
              </span>
              <span>where both scores are percentile-normalized within their respective tournament cohorts.</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-4 gap-2.5 pt-1">
              <div className="p-3 rounded-2xl bg-[#FF9500]/10 border border-[#FF9500]/20 transition-transform hover:-translate-y-0.5">
                <span className="font-bold text-[#FF9500] block text-xs">
                  APDI &gt; +0.15
                </span>
                <span className="text-[11px] text-slate-700 dark:text-slate-300 font-medium block mt-1">
                  Over-Attended
                </span>
                <span className="text-[10px] text-slate-500 dark:text-slate-400 mt-0.5 block">
                  Media visibility significantly exceeds objective performance.
                </span>
              </div>

              <div className="p-3 rounded-2xl bg-[#5856D6]/10 border border-[#5856D6]/20 transition-transform hover:-translate-y-0.5">
                <span className="font-bold text-[#5856D6] block text-xs">
                  APDI &lt; -0.15
                </span>
                <span className="text-[11px] text-slate-700 dark:text-slate-300 font-medium block mt-1">
                  Under-Attended
                </span>
                <span className="text-[10px] text-slate-500 dark:text-slate-400 mt-0.5 block">
                  High cricket performance received disproportionately low media.
                </span>
              </div>

              <div className="p-3 rounded-2xl bg-[#34C759]/10 border border-[#34C759]/20 transition-transform hover:-translate-y-0.5">
                <span className="font-bold text-[#34C759] block text-xs">
                  -0.15 to +0.15
                </span>
                <span className="text-[11px] text-slate-700 dark:text-slate-300 font-medium block mt-1">
                  Balanced
                </span>
                <span className="text-[10px] text-slate-500 dark:text-slate-400 mt-0.5 block">
                  Media attention roughly mirrors objective cricket performance.
                </span>
              </div>

              <div className="p-3 rounded-2xl bg-black/[0.02] dark:bg-white/[0.03] border border-black/[0.06] dark:border-white/[0.08] transition-transform hover:-translate-y-0.5">
                <span className="font-bold text-slate-400 block text-xs">
                  Sample &lt; Threshold
                </span>
                <span className="text-[11px] text-slate-700 dark:text-slate-300 font-medium block mt-1">
                  Insufficient Data
                </span>
                <span className="text-[10px] text-slate-500 dark:text-slate-400 mt-0.5 block">
                  Score is unavailable (null) to prevent statistically misleading claims.
                </span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Grid: APDI Matrix & Evidence Lineage */}
      {error ? (
        <ErrorState
          title="Failed to Load APDI Evaluations"
          message={extractErrorMessage(error)}
          onRetry={() => refetch()}
        />
      ) : isLoading ? (
        <Card className="p-6 space-y-3 rounded-3xl apple-card">
          <Skeleton className="h-6 w-1/4 rounded-lg" />
          <Skeleton className="h-12 w-full rounded-2xl" />
          <Skeleton className="h-12 w-full rounded-2xl" />
          <Skeleton className="h-12 w-full rounded-2xl" />
        </Card>
      ) : apdiData?.items.length === 0 ? (
        <EmptyState
          title="No APDI Evaluations Stored"
          description={
            roleCohort || categoryFilter
              ? 'No APDI records match the current filter selection.'
              : 'The analytics engine has not generated APDI records yet because the minimum corpus threshold has not been met. When data is ingested, APDI evaluates attention vs. performance discrepancies.'
          }
          icon="alert"
          secondaryInfo="Execute analytics batch: python -m src.pipeline compute-apdi"
        />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* APDI Table (7 cols) */}
          <div className="lg:col-span-7">
            <Card className="rounded-3xl apple-card overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow className="border-b border-black/[0.05] dark:border-white/[0.07]">
                    <TableHead className="text-xs font-semibold uppercase tracking-wider text-slate-400">Entity</TableHead>
                    <TableHead className="text-xs font-semibold uppercase tracking-wider text-slate-400">Cohort</TableHead>
                    <TableHead className="text-xs font-semibold uppercase tracking-wider text-slate-400">Attention</TableHead>
                    <TableHead className="text-xs font-semibold uppercase tracking-wider text-slate-400">Performance</TableHead>
                    <TableHead className="text-xs font-semibold uppercase tracking-wider text-slate-400">APDI</TableHead>
                    <TableHead className="text-xs font-semibold uppercase tracking-wider text-slate-400">Classification</TableHead>
                    <TableHead className="text-right text-xs font-semibold uppercase tracking-wider text-slate-400">Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {apdiData?.items.map((r) => {
                    const isSelected = selectedRecord?.record_id === r.record_id;
                    return (
                      <TableRow
                        key={r.record_id}
                        onClick={() => setSelectedRecord(r)}
                        className={`cursor-pointer transition-all duration-150 border-b border-black/[0.03] dark:border-white/[0.04] ${
                          isSelected
                            ? 'bg-[#007AFF]/10 dark:bg-[#007AFF]/15 font-medium'
                            : 'hover:bg-black/[0.02] dark:hover:bg-white/[0.03]'
                        }`}
                      >
                        <TableCell className="py-3">
                          <div className="font-semibold text-xs text-slate-900 dark:text-white flex items-center gap-1.5">
                            {isSelected && (
                              <span className="w-1.5 h-1.5 rounded-full bg-[#007AFF]" />
                            )}
                            <span>{r.entity_name}</span>
                          </div>
                          <div className="font-mono text-[10px] text-slate-400 truncate max-w-[130px]">
                            {r.entity_id}
                          </div>
                        </TableCell>

                        <TableCell className="py-3 text-xs capitalize text-slate-600 dark:text-slate-400">
                          {r.role_cohort}
                        </TableCell>

                        <TableCell className="py-3 font-mono text-xs tabular-nums">
                          {r.normalized_attention_score !== null
                            ? `${(r.normalized_attention_score * 100).toFixed(1)}%`
                            : '—'}
                        </TableCell>

                        <TableCell className="py-3 font-mono text-xs tabular-nums">
                          {r.normalized_performance_score !== null
                            ? `${(r.normalized_performance_score * 100).toFixed(1)}%`
                            : '—'}
                        </TableCell>

                        <TableCell className="py-3 font-mono text-xs font-bold tabular-nums">
                          {r.apdi_value !== null ? (
                            <span
                              className={
                                r.apdi_value > 0.15
                                  ? 'text-[#FF9500]'
                                  : r.apdi_value < -0.15
                                  ? 'text-[#5856D6]'
                                  : 'text-[#34C759]'
                              }
                            >
                              {r.apdi_value > 0 ? '+' : ''}
                              {r.apdi_value.toFixed(2)}
                            </span>
                          ) : (
                            <span className="text-slate-400 font-normal">unavailable</span>
                          )}
                        </TableCell>

                        <TableCell className="py-3">
                          {getDiscrepancyBadge(r.discrepancy_category)}
                        </TableCell>

                        <TableCell className="py-3 text-right">
                          <Button
                            variant={isSelected ? 'primary' : 'outline'}
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedRecord(r);
                            }}
                            className={`text-xs py-1 px-3 h-7 rounded-full shadow-xs ${
                              isSelected ? 'bg-[#007AFF] text-white' : ''
                            }`}
                          >
                            Lineage
                          </Button>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>

              {/* Pagination */}
              {apdiData && apdiData.pagination.total > limit && (
                <div className="p-3.5 border-t border-black/[0.05] dark:border-white/[0.07] flex items-center justify-between text-xs text-slate-500">
                  <span className="tabular-nums">
                    Showing {page * limit + 1}–
                    {Math.min((page + 1) * limit, apdiData.pagination.total)} of{' '}
                    {apdiData.pagination.total} records
                  </span>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={page === 0}
                      onClick={() => setPage((p) => Math.max(0, p - 1))}
                      className="rounded-full text-xs"
                    >
                      Previous
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={!apdiData.pagination.has_more}
                      onClick={() => setPage((p) => p + 1)}
                      className="rounded-full text-xs"
                    >
                      Next
                    </Button>
                  </div>
                </div>
              )}
            </Card>
          </div>

          {/* Evidence Lineage Inspector (5 cols) */}
          <div className="lg:col-span-5 sticky top-20">
            <Card className="rounded-3xl apple-card overflow-hidden">
              <CardHeader className="pb-3 border-b border-black/[0.05] dark:border-white/[0.07]">
                <div className="flex items-center justify-between w-full">
                  <div className="flex items-center gap-2">
                    <Shield className="w-4 h-4 text-[#007AFF]" />
                    <div>
                      <CardTitle className="text-sm font-semibold">
                        Evidence Lineage & Audit
                      </CardTitle>
                      <CardDescription className="text-xs">
                        {selectedRecord ? selectedRecord.entity_name : 'Provenance Audit Inspector'}
                      </CardDescription>
                    </div>
                  </div>
                  {selectedRecord && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setSelectedRecord(null)}
                      className="h-7 w-7 p-0 rounded-full hover:bg-black/[0.05] dark:hover:bg-white/[0.08]"
                    >
                      <X className="w-4 h-4" />
                    </Button>
                  )}
                </div>
              </CardHeader>

              <CardContent className="p-5">
                {selectedRecord ? (
                  <div className="space-y-4 text-xs">
                    {/* Score Summary Box */}
                    <div className="p-4 rounded-2xl bg-black/[0.02] dark:bg-white/[0.03] border border-black/[0.05] dark:border-white/[0.07] space-y-2.5">
                      <div className="flex justify-between items-center">
                        <span className="text-slate-500">Discrepancy Status:</span>
                        {getDiscrepancyBadge(selectedRecord.discrepancy_category)}
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-slate-500">APDI Score:</span>
                        <span className="font-mono font-bold text-base text-slate-900 dark:text-white tabular-nums">
                          {selectedRecord.apdi_value !== null ? selectedRecord.apdi_value.toFixed(3) : 'null'}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-slate-500">Evidence Sufficiency:</span>
                        <span className="font-mono font-medium text-slate-800 dark:text-slate-200">
                          {selectedRecord.evidence_sufficiency_status}
                        </span>
                      </div>
                    </div>

                    {/* Quality Warnings */}
                    {selectedRecord.data_quality_warnings && selectedRecord.data_quality_warnings.length > 0 && (
                      <div className="p-3.5 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-amber-800 dark:text-amber-300 space-y-1">
                        <div className="flex items-center gap-1.5 font-semibold text-amber-900 dark:text-amber-200">
                          <AlertCircle className="w-3.5 h-3.5" />
                          <span>Sample Size Warnings:</span>
                        </div>
                        <ul className="list-disc list-inside space-y-0.5 ml-1 text-[11px]">
                          {selectedRecord.data_quality_warnings.map((w, i) => (
                            <li key={i}>{w}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Raw Scores & Identifiers */}
                    <div className="p-3.5 rounded-2xl bg-black/[0.02] dark:bg-white/[0.03] border border-black/[0.05] dark:border-white/[0.07] space-y-2 font-mono text-[11px]">
                      <div className="flex justify-between text-slate-500">
                        <span>Raw Attention Composite:</span>
                        <span className="text-slate-800 dark:text-slate-200 font-bold tabular-nums">
                          {selectedRecord.raw_attention_score.toFixed(1)}
                        </span>
                      </div>
                      <div className="flex justify-between text-slate-500">
                        <span>Raw Performance Composite:</span>
                        <span className="text-slate-800 dark:text-slate-200 font-bold tabular-nums">
                          {selectedRecord.raw_performance_score.toFixed(1)}
                        </span>
                      </div>
                      <div className="flex justify-between text-slate-500">
                        <span>Analytics Run ID:</span>
                        <span className="truncate max-w-[130px]">{selectedRecord.run_id}</span>
                      </div>
                      <div className="flex justify-between text-slate-500">
                        <span>Formula Version:</span>
                        <span>{selectedRecord.formula_version}</span>
                      </div>
                    </div>
                  </div>
                ) : (
                  /* Interactive Lineage Selector */
                  <div className="space-y-4">
                    <div className="p-4 rounded-2xl bg-black/[0.02] dark:bg-white/[0.03] border border-black/[0.05] dark:border-white/[0.07]">
                      <div className="flex items-center gap-2 text-xs font-semibold text-slate-900 dark:text-white mb-1">
                        <Activity className="w-4 h-4 text-[#007AFF]" />
                        <span>Featured Discrepancy Audits</span>
                      </div>
                      <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                        Click any of the highlighted case studies below to inspect their full raw attention and cricket fact lineage:
                      </p>
                    </div>

                    <div className="space-y-2">
                      {FEATURED_AUDITS.map((fa) => (
                        <button
                          key={fa.id}
                          onClick={() => handleSelectAudit(fa.id)}
                          className="w-full p-3 rounded-2xl bg-white dark:bg-white/[0.04] border border-black/[0.05] dark:border-white/[0.07] hover:border-[#007AFF]/40 dark:hover:border-[#007AFF]/40 hover:shadow-sm flex items-center justify-between text-left transition-all duration-150 group"
                        >
                          <div>
                            <div className="text-xs font-semibold text-slate-900 dark:text-white group-hover:text-[#007AFF] transition-colors">
                              {fa.name}
                            </div>
                            <div className="text-[10px] text-slate-400">
                              {fa.cohort} • {fa.category.replace('_', ' ')}
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-xs font-bold text-[#FF9500]">
                              {fa.apdi}
                            </span>
                            <ArrowRight className="w-4 h-4 text-slate-300 group-hover:text-[#007AFF] group-hover:translate-x-0.5 transition-all" />
                          </div>
                        </button>
                      ))}
                    </div>

                    <div className="p-3.5 rounded-2xl bg-[#007AFF]/5 border border-[#007AFF]/15 text-[11px] text-slate-600 dark:text-slate-400 space-y-1">
                      <div className="font-semibold text-[#007AFF] flex items-center gap-1.5">
                        <Shield className="w-3.5 h-3.5" />
                        <span>Audit Proof:</span>
                      </div>
                      <p>
                        Every record preserves SHA-256 provenance hashes across match events and editorial articles for academic reproducibility.
                      </p>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
};
