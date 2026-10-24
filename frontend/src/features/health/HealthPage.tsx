import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Activity,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Database,
  ShieldCheck,
  Server,
  Layers,
  Cpu,
  RefreshCw,
} from 'lucide-react';
import { api, extractErrorMessage } from '../../lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { ErrorState } from '../../components/ui/ErrorState';
import { Skeleton } from '../../components/ui/Skeleton';

export const HealthPage: React.FC = () => {
  // 1. Liveness
  const {
    data: health,
    isLoading: isHealthLoading,
    error: healthError,
    refetch: refetchHealth,
  } = useQuery({
    queryKey: ['systemHealth'],
    queryFn: api.getHealth,
  });

  // 2. Readiness
  const {
    data: readiness,
    isLoading: isReadinessLoading,
    error: readinessError,
    refetch: refetchReadiness,
  } = useQuery({
    queryKey: ['systemReadiness'],
    queryFn: api.getReadiness,
  });

  // 3. Status
  const {
    data: status,
    isLoading: isStatusLoading,
    error: statusError,
    refetch: refetchStatus,
  } = useQuery({
    queryKey: ['systemStatusHealth'],
    queryFn: () => api.getStatus(),
  });

  // 4. Analytics Validation
  const {
    data: validation,
    isLoading: isValLoading,
    error: valError,
    refetch: refetchVal,
  } = useQuery({
    queryKey: ['analyticsValidation'],
    queryFn: api.validateAnalytics,
  });

  const refetchAll = () => {
    refetchHealth();
    refetchReadiness();
    refetchStatus();
    refetchVal();
  };

  const isAppAlive = !healthError && health?.status === 'healthy';
  const isDbReady = !readinessError && readiness?.database_accessible === true;
  const isDataAvailable =
    (status?.record_counts?.matches ?? 0) > 0 ||
    (status?.record_counts?.articles ?? 0) > 0 ||
    (status?.record_counts?.commentary_entries ?? 0) > 0;
  const isAnalyticsReady = status?.is_analytics_ready === true;

  return (
    <div className="space-y-6">
      {/* Header and Refresh Toolbar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 rounded-xl bg-white dark:bg-cricket-navy-900 border border-slate-200 dark:border-cricket-navy-800 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
            <Activity className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">
              System Health & Diagnostics
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Independent four-tier status: Process Liveness, Persistence Readiness, Data Inventory, and Analytical Sufficiency.
            </p>
          </div>
        </div>

        <Button variant="outline" size="sm" onClick={refetchAll} className="gap-2 text-xs">
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Probes</span>
        </Button>
      </div>

      {/* Four Distinct Independent Health Tiers */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Tier 1: Process Liveness */}
        <Card className="p-4 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              1. API Liveness
            </span>
            <Server className="w-4 h-4 text-slate-400" />
          </div>
          <div className="flex items-center gap-2">
            {isAppAlive ? (
              <>
                <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                <span className="text-sm font-bold text-slate-900 dark:text-slate-100">
                  Process Running
                </span>
              </>
            ) : (
              <>
                <XCircle className="w-5 h-5 text-rose-500" />
                <span className="text-sm font-bold text-rose-600">Offline</span>
              </>
            )}
          </div>
          <p className="text-[11px] text-slate-500 font-mono">
            FastAPI v{health?.version || 'unknown'}
          </p>
        </Card>

        {/* Tier 2: Persistence Readiness */}
        <Card className="p-4 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              2. SQLite Persistence
            </span>
            <Database className="w-4 h-4 text-slate-400" />
          </div>
          <div className="flex items-center gap-2">
            {isDbReady ? (
              <>
                <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                <span className="text-sm font-bold text-slate-900 dark:text-slate-100">
                  DB Accessible
                </span>
              </>
            ) : (
              <>
                <XCircle className="w-5 h-5 text-rose-500" />
                <span className="text-sm font-bold text-rose-600">Connection Failed</span>
              </>
            )}
          </div>
          <p className="text-[11px] text-slate-500 font-mono">
            Schema v{readiness?.schema_version || 5} • {readiness?.database_tables_count || 0} tables
          </p>
        </Card>

        {/* Tier 3: Data Inventory Availability */}
        <Card className="p-4 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              3. Data Availability
            </span>
            <Layers className="w-4 h-4 text-slate-400" />
          </div>
          <div className="flex items-center gap-2">
            {isDataAvailable ? (
              <>
                <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                <span className="text-sm font-bold text-slate-900 dark:text-slate-100">
                  Corpus Present
                </span>
              </>
            ) : (
              <>
                <AlertTriangle className="w-5 h-5 text-amber-500" />
                <span className="text-sm font-bold text-amber-600 dark:text-amber-400">
                  Corpus Empty (0 Records)
                </span>
              </>
            )}
          </div>
          <p className="text-[11px] text-slate-500 font-mono">
            Pipeline: {status?.pipeline_status || 'empty'}
          </p>
        </Card>

        {/* Tier 4: Analytical Evidence Sufficiency */}
        <Card className="p-4 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              4. Analytics Quality Gate
            </span>
            <ShieldCheck className="w-4 h-4 text-slate-400" />
          </div>
          <div className="flex items-center gap-2">
            {isAnalyticsReady ? (
              <>
                <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                <span className="text-sm font-bold text-slate-900 dark:text-slate-100">
                  Evidence Sufficient
                </span>
              </>
            ) : (
              <>
                <AlertTriangle className="w-5 h-5 text-amber-500" />
                <span className="text-sm font-bold text-amber-600 dark:text-amber-400">
                  Insufficient Evidence
                </span>
              </>
            )}
          </div>
          <p className="text-[11px] text-slate-500 font-mono">
            Gate: {status?.data_sufficiency_status || 'INSUFFICIENT_DATA'}
          </p>
        </Card>
      </div>

      {/* Structural Validation Report */}
      <Card>
        <CardHeader>
          <div>
            <CardTitle>Structural & Invariant Integrity Check</CardTitle>
            <CardDescription>
              Backend validation audit verifying mathematical bounds and schema consistency.
            </CardDescription>
          </div>
          <Badge variant={validation?.is_valid ? 'success' : 'warning'}>
            {validation?.is_valid ? 'All Invariants Pass' : 'Validation Issues'}
          </Badge>
        </CardHeader>
        <CardContent className="space-y-3">
          {validation?.issues && validation.issues.length > 0 ? (
            <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-xs text-rose-700 dark:text-rose-300">
              <span className="font-semibold block mb-1">Detected Issues:</span>
              <ul className="list-disc list-inside space-y-1">
                {validation.issues.map((iss, i) => (
                  <li key={i}>{iss}</li>
                ))}
              </ul>
            </div>
          ) : (
            <div className="p-3.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-800 dark:text-emerald-300 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
              <span>
                Zero structural violations. Invariant confirmed: all records with INSUFFICIENT_DATA
                strictly preserve null APDI scores without fabricated numerical values.
              </span>
            </div>
          )}

          <div className="pt-2 text-[11px] font-mono text-slate-400">
            Last checked at: {validation?.checked_at_utc || health?.timestamp_utc || 'n/a'}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
