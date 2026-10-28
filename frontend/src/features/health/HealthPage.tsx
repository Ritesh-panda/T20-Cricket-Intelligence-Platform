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
      {/* Header and Refresh Toolbar - Apple Frosted Capsule */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-5 rounded-2xl apple-glass-card shadow-apple-card dark:shadow-apple-card-dark">
        <div className="flex items-center gap-3.5">
          <div className="w-11 h-11 rounded-2xl bg-[#34C759]/15 text-[#34C759] flex items-center justify-center shadow-inner">
            <Activity className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-slate-900 dark:text-white tracking-tight">
              System Health & Diagnostics
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Independent four-tier status: Process Liveness, Persistence Readiness, Data Inventory, and Analytical Sufficiency.
            </p>
          </div>
        </div>

        <Button
          variant="secondary"
          size="sm"
          onClick={refetchAll}
          className="gap-2 text-xs rounded-full px-4 shadow-sm"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Probes</span>
        </Button>
      </div>

      {/* Four Distinct Independent Health Tiers - Apple Diagnostics Tiles */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Tier 1: Process Liveness */}
        <Card className="p-4 space-y-3 rounded-2xl">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              1. API Liveness
            </span>
            <div className="w-7 h-7 rounded-xl bg-[#007AFF]/10 text-[#007AFF] flex items-center justify-center">
              <Server className="w-3.5 h-3.5" />
            </div>
          </div>
          <div className="flex items-center gap-2">
            {isAppAlive ? (
              <>
                <span className="relative flex h-2.5 w-2.5">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#34C759] opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-[#34C759]"></span>
                </span>
                <span className="text-sm font-bold text-slate-900 dark:text-white">
                  Process Running
                </span>
              </>
            ) : (
              <>
                <span className="w-2.5 h-2.5 rounded-full bg-[#FF3B30]" />
                <span className="text-sm font-bold text-[#FF3B30]">Offline</span>
              </>
            )}
          </div>
          <p className="text-[11px] text-slate-500 font-mono">
            FastAPI v{health?.version || 'unknown'}
          </p>
        </Card>

        {/* Tier 2: Persistence Readiness */}
        <Card className="p-4 space-y-3 rounded-2xl">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              2. SQLite Persistence
            </span>
            <div className="w-7 h-7 rounded-xl bg-[#5856D6]/10 text-[#5856D6] flex items-center justify-center">
              <Database className="w-3.5 h-3.5" />
            </div>
          </div>
          <div className="flex items-center gap-2">
            {isDbReady ? (
              <>
                <span className="w-2.5 h-2.5 rounded-full bg-[#34C759] ring-2 ring-[#34C759]/20" />
                <span className="text-sm font-bold text-slate-900 dark:text-white">
                  DB Accessible
                </span>
              </>
            ) : (
              <>
                <span className="w-2.5 h-2.5 rounded-full bg-[#FF3B30] ring-2 ring-[#FF3B30]/20" />
                <span className="text-sm font-bold text-[#FF3B30]">Connection Failed</span>
              </>
            )}
          </div>
          <p className="text-[11px] text-slate-500 font-mono">
            Schema v{readiness?.schema_version || 5} • {readiness?.database_tables_count || 0} tables
          </p>
        </Card>

        {/* Tier 3: Data Inventory Availability */}
        <Card className="p-4 space-y-3 rounded-2xl">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              3. Data Availability
            </span>
            <div className="w-7 h-7 rounded-xl bg-[#FF9500]/10 text-[#FF9500] flex items-center justify-center">
              <Layers className="w-3.5 h-3.5" />
            </div>
          </div>
          <div className="flex items-center gap-2">
            {isDataAvailable ? (
              <>
                <span className="w-2.5 h-2.5 rounded-full bg-[#34C759] ring-2 ring-[#34C759]/20" />
                <span className="text-sm font-bold text-slate-900 dark:text-white">
                  Corpus Present
                </span>
              </>
            ) : (
              <>
                <span className="w-2.5 h-2.5 rounded-full bg-[#FF9500] ring-2 ring-[#FF9500]/20" />
                <span className="text-sm font-bold text-[#FF9500]">
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
        <Card className="p-4 space-y-3 rounded-2xl">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              4. Analytics Quality Gate
            </span>
            <div className="w-7 h-7 rounded-xl bg-[#34C759]/10 text-[#34C759] flex items-center justify-center">
              <ShieldCheck className="w-3.5 h-3.5" />
            </div>
          </div>
          <div className="flex items-center gap-2">
            {isAnalyticsReady ? (
              <>
                <span className="w-2.5 h-2.5 rounded-full bg-[#34C759] ring-2 ring-[#34C759]/20" />
                <span className="text-sm font-bold text-slate-900 dark:text-white">
                  Evidence Sufficient
                </span>
              </>
            ) : (
              <>
                <span className="w-2.5 h-2.5 rounded-full bg-[#FF9500] ring-2 ring-[#FF9500]/20" />
                <span className="text-sm font-bold text-[#FF9500]">
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
