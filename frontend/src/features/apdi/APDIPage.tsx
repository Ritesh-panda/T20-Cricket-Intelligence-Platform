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

  return (
    <div className="space-y-6">
      {/* Header and Filter Toolbar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 rounded-xl bg-white dark:bg-cricket-navy-900 border border-slate-200 dark:border-cricket-navy-800 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
            <Scale className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              <span>Attention-to-Performance Discrepancy Index (APDI)</span>
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Measuring narrative and media coverage disproportionality against objective cricket metrics.
            </p>
          </div>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-2 w-full sm:w-auto">
          <select
            value={roleCohort}
            onChange={(e) => {
              setRoleCohort(e.target.value);
              setPage(0);
            }}
            className="px-3 py-1.5 rounded-lg text-xs bg-slate-50 dark:bg-cricket-navy-950 border border-slate-200 dark:border-cricket-navy-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-emerald-500"
          >
            <option value="">All Cohorts</option>
            <option value="batter">Batters</option>
            <option value="bowler">Bowlers</option>
            <option value="all_rounder">All-Rounders</option>
            <option value="team">Teams</option>
          </select>

          <select
            value={categoryFilter}
            onChange={(e) => {
              setCategoryFilter(e.target.value);
              setPage(0);
            }}
            className="px-3 py-1.5 rounded-lg text-xs bg-slate-50 dark:bg-cricket-navy-950 border border-slate-200 dark:border-cricket-navy-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-emerald-500"
          >
            <option value="">All Categories</option>
            <option value="OVER_ATTENDED">Over-Attended</option>
            <option value="UNDER_ATTENDED">Under-Attended</option>
            <option value="BALANCED">Balanced</option>
            <option value="INSUFFICIENT_DATA">Insufficient Data</option>
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
              title="Reset filters"
            >
              <X className="w-3.5 h-3.5" />
            </Button>
          )}
        </div>
      </div>

      {/* APDI Methodology Explanation Panel */}
      <Card className="bg-slate-50/70 dark:bg-cricket-navy-900/40 border-slate-200 dark:border-cricket-navy-800">
        <CardContent className="p-4 sm:p-5 space-y-3">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-900 dark:text-slate-100">
            <BookOpen className="w-4 h-4 text-emerald-500" />
            <span>APDI Mathematical Formulation & Cohort Normalization</span>
          </div>
          <div className="text-xs text-slate-600 dark:text-slate-400 space-y-2 leading-relaxed">
            <p>
              The <strong>Attention-to-Performance Discrepancy Index (APDI)</strong> is defined as:{' '}
              <span className="font-mono bg-white dark:bg-cricket-navy-950 px-2 py-0.5 rounded border border-slate-200 dark:border-cricket-navy-800 text-slate-900 dark:text-slate-100 font-semibold">
                APDI = NormAttention − NormPerformance
              </span>
              , where both scores are percentile-normalized within their respective role cohorts
              (e.g., batters vs. other tournament batters).
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-2 pt-1">
              <div className="p-2 rounded bg-white dark:bg-cricket-navy-950 border border-slate-200/80 dark:border-cricket-navy-800">
                <span className="font-semibold text-amber-600 dark:text-amber-400 block text-[11px]">
                  APDI &gt; +0.15
                </span>
                <span className="text-[10px] text-slate-500">
                  Over-Attended: Media coverage significantly exceeds objective performance.
                </span>
              </div>
              <div className="p-2 rounded bg-white dark:bg-cricket-navy-950 border border-slate-200/80 dark:border-cricket-navy-800">
                <span className="font-semibold text-indigo-600 dark:text-indigo-400 block text-[11px]">
                  APDI &lt; -0.15
                </span>
                <span className="text-[10px] text-slate-500">
                  Under-Attended: High objective performance received disproportionately low media.
                </span>
              </div>
              <div className="p-2 rounded bg-white dark:bg-cricket-navy-950 border border-slate-200/80 dark:border-cricket-navy-800">
                <span className="font-semibold text-emerald-600 dark:text-emerald-400 block text-[11px]">
                  -0.15 to +0.15
                </span>
                <span className="text-[10px] text-slate-500">
                  Balanced: Media attention roughly mirrors cricket performance.
                </span>
              </div>
              <div className="p-2 rounded bg-white dark:bg-cricket-navy-950 border border-slate-200/80 dark:border-cricket-navy-800">
                <span className="font-semibold text-slate-500 block text-[11px]">
                  Sample &lt; Threshold
                </span>
                <span className="text-[10px] text-slate-500">
                  Insufficient Data: Score is unavailable (null) to prevent misleading claims.
                </span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Content Area */}
      {error ? (
        <ErrorState
          title="Failed to Load APDI Evaluations"
          message={extractErrorMessage(error)}
          onRetry={() => refetch()}
        />
      ) : isLoading ? (
        <Card className="p-6 space-y-3">
          <Skeleton className="h-6 w-1/4" />
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
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
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* APDI Table */}
          <div className="lg:col-span-2">
            <Card>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Entity</TableHead>
                    <TableHead>Cohort</TableHead>
                    <TableHead>Norm Attention</TableHead>
                    <TableHead>Norm Performance</TableHead>
                    <TableHead>APDI Score</TableHead>
                    <TableHead>Classification</TableHead>
                    <TableHead className="text-right">Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {apdiData?.items.map((r: APDIRecordResponse) => (
                    <TableRow
                      key={r.record_id}
                      className={
                        selectedRecord?.record_id === r.record_id
                          ? 'bg-emerald-500/10 dark:bg-emerald-500/15'
                          : ''
                      }
                    >
                      <TableCell>
                        <div className="font-semibold text-xs text-slate-900 dark:text-slate-100">
                          {r.entity_name}
                        </div>
                        <div className="font-mono text-[10px] text-slate-400">
                          {r.entity_id}
                        </div>
                      </TableCell>
                      <TableCell className="text-xs font-mono capitalize">
                        {r.role_cohort}
                      </TableCell>
                      <TableCell className="font-mono text-xs">
                        {r.normalized_attention_score !== null ? (
                          (r.normalized_attention_score * 100).toFixed(1) + '%'
                        ) : (
                          <span className="text-slate-400 italic">n/a</span>
                        )}
                      </TableCell>
                      <TableCell className="font-mono text-xs">
                        {r.normalized_performance_score !== null ? (
                          (r.normalized_performance_score * 100).toFixed(1) + '%'
                        ) : (
                          <span className="text-slate-400 italic">n/a</span>
                        )}
                      </TableCell>
                      <TableCell className="font-mono text-xs font-bold">
                        {r.apdi_value !== null ? (
                          <span
                            className={
                              r.apdi_value > 0.15
                                ? 'text-amber-500'
                                : r.apdi_value < -0.15
                                ? 'text-indigo-500'
                                : 'text-emerald-500'
                            }
                          >
                            {r.apdi_value > 0 ? `+${r.apdi_value.toFixed(2)}` : r.apdi_value.toFixed(2)}
                          </span>
                        ) : (
                          <span className="text-slate-400 italic font-normal">unavailable</span>
                        )}
                      </TableCell>
                      <TableCell>{getDiscrepancyBadge(r.discrepancy_category)}</TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setSelectedRecord(r)}
                          className="text-xs py-1 px-2.5 h-7"
                        >
                          Lineage
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Card>
          </div>

          {/* Evidence Lineage Inspector */}
          <div>
            <Card className="sticky top-20">
              <CardHeader>
                <div>
                  <CardTitle>Evidence Lineage & Audit</CardTitle>
                  <CardDescription>
                    {selectedRecord ? selectedRecord.entity_name : 'Select a record to audit'}
                  </CardDescription>
                </div>
                {selectedRecord && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setSelectedRecord(null)}
                  >
                    <X className="w-4 h-4" />
                  </Button>
                )}
              </CardHeader>
              <CardContent className="space-y-4">
                {!selectedRecord ? (
                  <div className="py-12 text-center text-xs text-slate-400 dark:text-slate-500">
                    Click "Lineage" on any evaluation to inspect raw attention, cricket facts, and sample size warnings.
                  </div>
                ) : (
                  <div className="space-y-4 text-xs">
                    {/* Score Summary */}
                    <div className="p-3 rounded-lg bg-slate-50 dark:bg-cricket-navy-950 border border-slate-100 dark:border-cricket-navy-800 space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="text-slate-500">Discrepancy Status:</span>
                        {getDiscrepancyBadge(selectedRecord.discrepancy_category)}
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-slate-500">APDI Score:</span>
                        <span className="font-mono font-bold text-sm">
                          {selectedRecord.apdi_value !== null ? selectedRecord.apdi_value.toFixed(3) : 'null'}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-slate-500">Evidence Sufficiency:</span>
                        <span className="font-mono font-medium">{selectedRecord.evidence_sufficiency_status}</span>
                      </div>
                    </div>

                    {/* Quality Warnings */}
                    {selectedRecord.data_quality_warnings && selectedRecord.data_quality_warnings.length > 0 && (
                      <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-800 dark:text-amber-300 space-y-1">
                        <div className="flex items-center gap-1.5 font-semibold text-amber-900 dark:text-amber-200">
                          <AlertCircle className="w-3.5 h-3.5" />
                          <span>Sample Size Warnings:</span>
                        </div>
                        <ul className="list-disc list-inside space-y-0.5 ml-1">
                          {selectedRecord.data_quality_warnings.map((w, i) => (
                            <li key={i}>{w}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Raw Scores & Identifiers */}
                    <div className="space-y-1.5 pt-2 border-t border-slate-100 dark:border-cricket-navy-800 font-mono text-[11px]">
                      <div className="flex justify-between text-slate-500">
                        <span>Raw Attention Composite:</span>
                        <span className="text-slate-800 dark:text-slate-200 font-bold">
                          {selectedRecord.raw_attention_score.toFixed(1)}
                        </span>
                      </div>
                      <div className="flex justify-between text-slate-500">
                        <span>Raw Performance Composite:</span>
                        <span className="text-slate-800 dark:text-slate-200 font-bold">
                          {selectedRecord.raw_performance_score.toFixed(1)}
                        </span>
                      </div>
                      <div className="flex justify-between text-slate-500">
                        <span>Analytics Run ID:</span>
                        <span className="truncate max-w-[140px]">{selectedRecord.run_id}</span>
                      </div>
                      <div className="flex justify-between text-slate-500">
                        <span>Formula Version:</span>
                        <span>{selectedRecord.formula_version}</span>
                      </div>
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
