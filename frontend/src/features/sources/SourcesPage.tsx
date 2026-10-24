import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Database,
  History,
  Shield,
  Layers,
  CheckCircle,
  XCircle,
  AlertCircle,
  Info,
} from 'lucide-react';
import { api, extractErrorMessage } from '../../lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/Card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/Table';
import { Badge } from '../../components/ui/Badge';
import { EmptyState } from '../../components/ui/EmptyState';
import { ErrorState } from '../../components/ui/ErrorState';
import { Skeleton } from '../../components/ui/Skeleton';
import type { IngestionRunResponse, SourceRecordResponse, AnalyticsRunResponse } from '../../types/api';

export const SourcesPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'provenance' | 'ingestion_runs' | 'analytics_runs'>('provenance');

  // Provenance Sources
  const { data: sourcesData, isLoading: isSourcesLoading, error: sourcesError } = useQuery({
    queryKey: ['sourceRecords'],
    queryFn: () => api.getSourceRecords({ limit: 20 }),
    enabled: activeTab === 'provenance',
  });

  // Ingestion Runs
  const { data: ingestionData, isLoading: isIngestionLoading, error: ingestionError } = useQuery({
    queryKey: ['ingestionRuns'],
    queryFn: () => api.getIngestionRuns({ limit: 20 }),
    enabled: activeTab === 'ingestion_runs',
  });

  // Analytics Runs
  const { data: analyticsRunsData, isLoading: isAnalyticsRunsLoading, error: analyticsRunsError } = useQuery({
    queryKey: ['analyticsRuns'],
    queryFn: () => api.getAnalyticsRuns({ limit: 20 }),
    enabled: activeTab === 'analytics_runs',
  });

  // Pipeline Stats
  const { data: pipelineStats } = useQuery({
    queryKey: ['pipelineStatsOverview'],
    queryFn: () => api.getPipelineStats(),
  });

  return (
    <div className="space-y-6">
      {/* Header and Tab Selector */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 rounded-xl bg-white dark:bg-cricket-navy-900 border border-slate-200 dark:border-cricket-navy-800 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
            <Database className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">
              Data Sources & Pipeline Observability
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Immutable provenance records, crawler harvest statistics, and ingestion audit runs.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1 border border-slate-200 dark:border-cricket-navy-800 p-1 rounded-lg bg-slate-50 dark:bg-cricket-navy-950">
          <button
            onClick={() => setActiveTab('provenance')}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
              activeTab === 'provenance'
                ? 'bg-white dark:bg-cricket-navy-800 text-emerald-600 dark:text-emerald-400 shadow-sm font-semibold'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
            }`}
          >
            Source Provenance
          </button>
          <button
            onClick={() => setActiveTab('ingestion_runs')}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
              activeTab === 'ingestion_runs'
                ? 'bg-white dark:bg-cricket-navy-800 text-emerald-600 dark:text-emerald-400 shadow-sm font-semibold'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
            }`}
          >
            Ingestion Runs
          </button>
          <button
            onClick={() => setActiveTab('analytics_runs')}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
              activeTab === 'analytics_runs'
                ? 'bg-white dark:bg-cricket-navy-800 text-emerald-600 dark:text-emerald-400 shadow-sm font-semibold'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
            }`}
          >
            Analytics Batches
          </button>
        </div>
      </div>

      {/* Pipeline State Distribution Cards */}
      {pipelineStats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
          <Card className="p-4">
            <span className="text-[11px] font-medium text-slate-500 uppercase tracking-wider">
              Discovered URLs
            </span>
            <p className="text-2xl font-bold font-mono text-slate-900 dark:text-slate-100 mt-1">
              {pipelineStats.total_discovered}
            </p>
          </Card>
          <Card className="p-4">
            <span className="text-[11px] font-medium text-slate-500 uppercase tracking-wider">
              Crawler Attempts
            </span>
            <p className="text-2xl font-bold font-mono text-slate-900 dark:text-slate-100 mt-1">
              {pipelineStats.total_attempts}
            </p>
          </Card>
          <Card className="p-4">
            <span className="text-[11px] font-medium text-slate-500 uppercase tracking-wider">
              HTTP Errors
            </span>
            <p className="text-2xl font-bold font-mono text-rose-600 mt-1">
              {pipelineStats.http_errors}
            </p>
          </Card>
          <Card className="p-4">
            <span className="text-[11px] font-medium text-slate-500 uppercase tracking-wider">
              Stored Entities
            </span>
            <p className="text-2xl font-bold font-mono text-emerald-600 mt-1">
              {Object.values(pipelineStats.entity_counts || {}).reduce((a, b) => a + b, 0)}
            </p>
          </Card>
        </div>
      )}

      {/* Provenance Tab */}
      {activeTab === 'provenance' && (
        <>
          {sourcesError ? (
            <ErrorState title="Failed to Load Sources" message={extractErrorMessage(sourcesError)} />
          ) : isSourcesLoading ? (
            <Skeleton className="h-48 w-full" />
          ) : sourcesData?.items.length === 0 ? (
            <EmptyState
              title="No Harvest Provenance Records"
              description="Harvested files, JSONL payloads, and raw HTML provenance records will be audited here."
              icon="database"
            />
          ) : (
            <Card>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Source Name</TableHead>
                    <TableHead>Identifier</TableHead>
                    <TableHead>License Tag</TableHead>
                    <TableHead>Redistributable</TableHead>
                    <TableHead>Harvest Timestamp</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sourcesData?.items.map((s: SourceRecordResponse) => (
                    <TableRow key={s.provenance_id}>
                      <TableCell className="font-semibold text-xs text-slate-900 dark:text-slate-100 font-mono">
                        {s.source_name}
                      </TableCell>
                      <TableCell className="font-mono text-xs text-slate-600 dark:text-slate-400">
                        {s.source_identifier}
                      </TableCell>
                      <TableCell>
                        <Badge variant="neutral">{s.license_tag}</Badge>
                      </TableCell>
                      <TableCell>
                        {s.redistributable ? (
                          <Badge variant="success">Yes</Badge>
                        ) : (
                          <Badge variant="warning">No (Internal Only)</Badge>
                        )}
                      </TableCell>
                      <TableCell className="font-mono text-xs text-slate-500">
                        {s.harvest_timestamp_utc}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Card>
          )}
        </>
      )}

      {/* Ingestion Runs Tab */}
      {activeTab === 'ingestion_runs' && (
        <>
          {ingestionError ? (
            <ErrorState title="Failed to Load Ingestion Runs" message={extractErrorMessage(ingestionError)} />
          ) : isIngestionLoading ? (
            <Skeleton className="h-48 w-full" />
          ) : ingestionData?.items.length === 0 ? (
            <EmptyState
              title="No Ingestion Runs Executed"
              description="Pipeline execution audits tracking extracted, ingested, and skipped records will appear here."
              icon="database"
            />
          ) : (
            <Card>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Run ID</TableHead>
                    <TableHead>Source</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Extracted</TableHead>
                    <TableHead>Ingested</TableHead>
                    <TableHead>Skipped</TableHead>
                    <TableHead>Started UTC</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {ingestionData?.items.map((r: IngestionRunResponse) => (
                    <TableRow key={r.run_id}>
                      <TableCell className="font-mono text-xs font-semibold">
                        {r.run_id}
                      </TableCell>
                      <TableCell className="text-xs capitalize">{r.source_name}</TableCell>
                      <TableCell>
                        {r.status === 'COMPLETED' ? (
                          <Badge variant="success">COMPLETED</Badge>
                        ) : r.status === 'FAILED' ? (
                          <Badge variant="danger">FAILED</Badge>
                        ) : (
                          <Badge variant="warning">{r.status}</Badge>
                        )}
                      </TableCell>
                      <TableCell className="font-mono text-xs">{r.records_extracted}</TableCell>
                      <TableCell className="font-mono text-xs text-emerald-600 font-bold">
                        {r.records_ingested}
                      </TableCell>
                      <TableCell className="font-mono text-xs text-slate-400">
                        {r.records_skipped}
                      </TableCell>
                      <TableCell className="font-mono text-xs text-slate-500">
                        {r.started_at_utc}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Card>
          )}
        </>
      )}

      {/* Analytics Runs Tab */}
      {activeTab === 'analytics_runs' && (
        <>
          {analyticsRunsError ? (
            <ErrorState title="Failed to Load Analytics Runs" message={extractErrorMessage(analyticsRunsError)} />
          ) : isAnalyticsRunsLoading ? (
            <Skeleton className="h-48 w-full" />
          ) : analyticsRunsData?.items.length === 0 ? (
            <EmptyState
              title="No Analytics Batches Executed"
              description="Batch executions evaluating media attention, performance composites, and APDI will be logged here."
              icon="database"
            />
          ) : (
            <Card>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Run ID</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Tournament</TableHead>
                    <TableHead>Processed</TableHead>
                    <TableHead>Valid APDI</TableHead>
                    <TableHead>Insufficient Data</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {analyticsRunsData?.items.map((ar: AnalyticsRunResponse) => (
                    <TableRow key={ar.run_id}>
                      <TableCell className="font-mono text-xs font-semibold">{ar.run_id}</TableCell>
                      <TableCell>
                        <Badge variant="success">{ar.status}</Badge>
                      </TableCell>
                      <TableCell className="text-xs">{ar.tournament}</TableCell>
                      <TableCell className="font-mono text-xs">{ar.entities_processed}</TableCell>
                      <TableCell className="font-mono text-xs text-emerald-600 font-bold">
                        {ar.valid_apdi_count}
                      </TableCell>
                      <TableCell className="font-mono text-xs text-slate-400">
                        {ar.insufficient_data_count}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Card>
          )}
        </>
      )}
    </div>
  );
};
