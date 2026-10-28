import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Users,
  Search,
  Flame,
  Award,
  X,
  Sparkles,
  TrendingUp,
  TrendingDown,
  Target,
  BarChart2,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Filter,
  ArrowRight,
  Shield,
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
import type { PlayerResponse } from '../../types/api';

// Curated cohort spotlights for quick research selection
const FEATURED_PLAYERS = [
  { id: 'player_v_kohli', name: 'Virat Kohli', team: 'IND', role: 'Batter', gradient: 'from-[#007AFF] to-[#5856D6]' },
  { id: 'player_jj_bumrah', name: 'Jasprit Bumrah', team: 'IND', role: 'Bowler', gradient: 'from-[#34C759] to-[#30B0C7]' },
  { id: 'player_a_johnson', name: 'Aaron Johnson', team: 'CAN', role: 'Batter', gradient: 'from-[#FF9500] to-[#FF3B30]' },
  { id: 'player_a_zampa', name: 'Adam Zampa', team: 'AUS', role: 'Bowler', gradient: 'from-[#34C759] to-[#007AFF]' },
  { id: 'player_mustafizur_rahman', name: 'Mustafizur Rahman', team: 'BAN', role: 'Bowler', gradient: 'from-[#AF52DE] to-[#FF2D55]' },
  { id: 'player_hardik_pandya', name: 'Hardik Pandya', team: 'IND', role: 'All-Rounder', gradient: 'from-[#FF9500] to-[#AF52DE]' },
];

export const PlayersPage: React.FC = () => {
  const [search, setSearch] = useState<string>('');
  const [roleFilter, setRoleFilter] = useState<'all' | 'batter' | 'bowler' | 'all_rounder'>('all');
  const [selectedPlayer, setSelectedPlayer] = useState<PlayerResponse | null>(null);
  const [page, setPage] = useState<number>(0);
  const limit = 15;

  const {
    data: playersData,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['players', search, roleFilter, page],
    queryFn: () =>
      api.getPlayers({
        role: roleFilter === 'all' ? undefined : roleFilter,
        search: search.trim() || undefined,
        limit,
        offset: page * limit,
      }),
  });

  // Query performance stats for selected player
  const { data: playerPerf, isLoading: isLoadingPerf } = useQuery({
    queryKey: ['playerPerformance', selectedPlayer?.player_id],
    queryFn: () =>
      api.getPerformanceMetrics({
        entity_id: selectedPlayer!.player_id,
      }),
    enabled: !!selectedPlayer,
  });

  // Query media attention metrics for selected player
  const { data: playerAtt, isLoading: isLoadingAtt } = useQuery({
    queryKey: ['playerAttention', selectedPlayer?.player_id],
    queryFn: () =>
      api.getMediaAttention({
        entity_id: selectedPlayer!.player_id,
      }),
    enabled: !!selectedPlayer,
  });

  // Query APDI evaluation for selected player
  const { data: playerAPDI } = useQuery({
    queryKey: ['playerAPDI', selectedPlayer?.player_id],
    queryFn: () => api.getEntityAPDI(selectedPlayer!.player_id).catch(() => null),
    enabled: !!selectedPlayer,
  });

  const perfRecord = playerPerf?.items?.[0];
  const attRecord = playerAtt?.items?.[0];

  const handleSelectFeatured = async (playerId: string) => {
    try {
      const res = await api.getPlayers({ search: playerId, limit: 1 });
      if (res.items.length > 0) {
        setSelectedPlayer(res.items[0]);
      } else {
        const match = FEATURED_PLAYERS.find((f) => f.id === playerId);
        if (match) {
          const nameRes = await api.getPlayers({ search: match.name, limit: 1 });
          if (nameRes.items.length > 0) setSelectedPlayer(nameRes.items[0]);
        }
      }
    } catch {
      // ignore
    }
  };

  // Helper for role styling
  const getRoleBadge = (role?: string | null) => {
    switch (role) {
      case 'bowler':
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-[#34C759]/15 text-[#248A3D] dark:text-[#30D158] border border-[#34C759]/25">
            Bowler
          </span>
        );
      case 'all_rounder':
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-[#AF52DE]/15 text-[#8944AB] dark:text-[#BF5AF2] border border-[#AF52DE]/25">
            All-Rounder
          </span>
        );
      case 'batter':
      default:
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-[#007AFF]/15 text-[#007AFF] dark:text-[#0A84FF] border border-[#007AFF]/25">
            Batter
          </span>
        );
    }
  };

  // Helper for role gradient avatar
  const getRoleGradient = (role?: string | null) => {
    switch (role) {
      case 'bowler':
        return 'bg-gradient-to-br from-[#34C759] to-[#30B0C7] text-white shadow-xs';
      case 'all_rounder':
        return 'bg-gradient-to-br from-[#FF9500] to-[#AF52DE] text-white shadow-xs';
      case 'batter':
      default:
        return 'bg-gradient-to-br from-[#007AFF] to-[#5856D6] text-white shadow-xs';
    }
  };

  // Helper for clean cricket discipline description
  const getDisciplineText = (p: PlayerResponse) => {
    if (p.role === 'bowler' || p.role === 'all_rounder') {
      if (p.bowling_style && !p.bowling_style.startsWith('None')) {
        return p.bowling_style;
      }
    }
    if (p.bowling_style && p.bowling_style.includes('Wicketkeeper')) {
      return 'Wicketkeeper Batter';
    }
    return p.batting_style ? `${p.batting_style} bat` : 'Specialist Batter';
  };

  // Helper for team badge styling
  const getTeamBadge = (teamId?: string | null) => {
    const tid = teamId || 'IND';
    const teamColors: Record<string, string> = {
      IND: 'bg-[#007AFF]/15 text-[#007AFF] dark:text-[#0A84FF] border-[#007AFF]/25',
      AUS: 'bg-[#FFCC00]/20 text-[#B28900] dark:text-[#FFD60A] border-[#FFCC00]/30',
      ENG: 'bg-[#FF3B30]/15 text-[#FF3B30] dark:text-[#FF453A] border-[#FF3B30]/25',
      PAK: 'bg-[#34C759]/15 text-[#248A3D] dark:text-[#30D158] border-[#34C759]/25',
      CAN: 'bg-[#FF3B30]/15 text-[#FF3B30] dark:text-[#FF453A] border-[#FF3B30]/25',
      WES: 'bg-[#AF52DE]/15 text-[#AF52DE] dark:text-[#BF5AF2] border-[#AF52DE]/25',
      SOU: 'bg-[#30B0C7]/15 text-[#30B0C7] border-[#30B0C7]/25',
      UNI: 'bg-[#5856D6]/15 text-[#5856D6] dark:text-[#5E5CE6] border-[#5856D6]/25',
      USA: 'bg-[#5856D6]/15 text-[#5856D6] dark:text-[#5E5CE6] border-[#5856D6]/25',
      BAN: 'bg-[#34C759]/15 text-[#248A3D] dark:text-[#30D158] border-[#34C759]/25',
    };
    const colorClass = teamColors[tid] || 'bg-black/[0.04] dark:bg-white/[0.06] text-slate-700 dark:text-slate-300 border-black/[0.05] dark:border-white/[0.08]';

    return (
      <span className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold border ${colorClass}`}>
        {tid}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      {/* Search & Role Filter Toolbar - Apple Frosted Sheet */}
      <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4 p-4 sm:p-5 rounded-3xl apple-glass-card">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-[#007AFF] to-[#5856D6] text-white flex items-center justify-center shadow-sm shadow-[#007AFF]/20 shrink-0">
            <Users className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-slate-900 dark:text-white tracking-tight">
              Player Directory & Profiles
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Canonical tournament registry with empirical role classifications.
            </p>
          </div>
        </div>

        {/* Search Input & Role Filters */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2.5">
          {/* Apple Segmented Control for Roles */}
          <div className="apple-segmented-group flex items-center text-xs font-medium">
            <button
              onClick={() => {
                setRoleFilter('all');
                setPage(0);
              }}
              className={`px-3 py-1 rounded-xl transition-all ${
                roleFilter === 'all'
                  ? 'apple-segmented-item-active'
                  : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              All (107)
            </button>
            <button
              onClick={() => {
                setRoleFilter('batter');
                setPage(0);
              }}
              className={`px-3 py-1 rounded-xl transition-all ${
                roleFilter === 'batter'
                  ? 'apple-segmented-item-active'
                  : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              Batters (47)
            </button>
            <button
              onClick={() => {
                setRoleFilter('bowler');
                setPage(0);
              }}
              className={`px-3 py-1 rounded-xl transition-all ${
                roleFilter === 'bowler'
                  ? 'apple-segmented-item-active'
                  : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              Bowlers (55)
            </button>
            <button
              onClick={() => {
                setRoleFilter('all_rounder');
                setPage(0);
              }}
              className={`px-3 py-1 rounded-xl transition-all ${
                roleFilter === 'all_rounder'
                  ? 'apple-segmented-item-active'
                  : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              All-Rounders (5)
            </button>
          </div>

          {/* Search Box */}
          <div className="relative w-full sm:w-60">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
            <input
              type="text"
              placeholder="Search player or alias..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(0);
              }}
              className="w-full pl-9 pr-8 py-2 rounded-2xl text-xs bg-black/[0.03] dark:bg-white/[0.05] border border-black/[0.06] dark:border-white/[0.08] text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#007AFF]/30 transition-all font-medium"
            />
            {search && (
              <button
                onClick={() => setSearch('')}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-full"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Main Master-Detail Grid */}
      {error ? (
        <ErrorState
          title="Failed to Load Players"
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
      ) : playersData?.items.length === 0 ? (
        <EmptyState
          title="No Players Found"
          description={
            search
              ? `No players matched "${search}" in the selected cohort.`
              : 'No players match the current criteria.'
          }
          icon="database"
          secondaryInfo="Try clearing filters or resetting the search box."
        />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Players Table (7 cols on desktop) */}
          <div className="lg:col-span-7">
            <Card className="rounded-3xl overflow-hidden apple-card">
              <Table>
                <TableHeader>
                  <TableRow className="border-b border-black/[0.05] dark:border-white/[0.07]">
                    <TableHead className="text-xs font-semibold uppercase tracking-wider text-slate-400">Player</TableHead>
                    <TableHead className="text-xs font-semibold uppercase tracking-wider text-slate-400">Team</TableHead>
                    <TableHead className="text-xs font-semibold uppercase tracking-wider text-slate-400">Role & Discipline</TableHead>
                    <TableHead className="text-right text-xs font-semibold uppercase tracking-wider text-slate-400">Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {playersData?.items.map((p) => {
                    const isSelected = selectedPlayer?.player_id === p.player_id;
                    const initials = p.full_name
                      .split(' ')
                      .map((n) => n[0])
                      .slice(0, 2)
                      .join('')
                      .toUpperCase();

                    return (
                      <TableRow
                        key={p.player_id}
                        onClick={() => setSelectedPlayer(p)}
                        className={`cursor-pointer transition-all duration-150 border-b border-black/[0.03] dark:border-white/[0.04] ${
                          isSelected
                            ? 'bg-[#007AFF]/10 dark:bg-[#007AFF]/15 font-medium'
                            : 'hover:bg-black/[0.02] dark:hover:bg-white/[0.03]'
                        }`}
                      >
                        <TableCell className="py-3">
                          <div className="flex items-center gap-3">
                            <div
                              className={`w-9 h-9 rounded-2xl flex items-center justify-center text-xs font-bold shrink-0 transition-transform ${getRoleGradient(
                                p.role
                              )} ${isSelected ? 'scale-110 ring-2 ring-[#007AFF]' : ''}`}
                            >
                              {initials}
                            </div>
                            <div className="min-w-0">
                              <div className="font-semibold text-xs text-slate-900 dark:text-white flex items-center gap-1.5 truncate">
                                <span>{p.full_name}</span>
                                {isSelected && (
                                  <span className="w-1.5 h-1.5 rounded-full bg-[#007AFF]" />
                                )}
                              </div>
                              {p.aliases && p.aliases.length > 0 && (
                                <div className="text-[10px] text-slate-400 truncate max-w-[170px]">
                                  aka: {p.aliases.slice(0, 2).join(', ')}
                                </div>
                              )}
                            </div>
                          </div>
                        </TableCell>

                        <TableCell className="py-3">
                          {getTeamBadge(p.primary_team_id)}
                        </TableCell>

                        <TableCell className="py-3">
                          <div className="space-y-0.5">
                            <div>{getRoleBadge(p.role)}</div>
                            <div className="text-[11px] text-slate-500 dark:text-slate-400 truncate max-w-[150px]">
                              {getDisciplineText(p)}
                            </div>
                          </div>
                        </TableCell>

                        <TableCell className="py-3 text-right">
                          <Button
                            variant={isSelected ? 'primary' : 'outline'}
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedPlayer(p);
                            }}
                            className={`text-xs py-1 px-3 h-7 rounded-full shadow-xs transition-transform ${
                              isSelected ? 'bg-[#007AFF] text-white' : ''
                            }`}
                          >
                            Dossier
                          </Button>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>

              {/* Pagination */}
              {playersData && playersData.pagination.total > limit && (
                <div className="p-3.5 border-t border-black/[0.05] dark:border-white/[0.07] flex items-center justify-between text-xs text-slate-500">
                  <span className="tabular-nums">
                    Showing {page * limit + 1}–
                    {Math.min((page + 1) * limit, playersData.pagination.total)} of{' '}
                    {playersData.pagination.total} {roleFilter === 'all' ? 'players' : `${roleFilter}s`}
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
                      disabled={!playersData.pagination.has_more}
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

          {/* Player Research Dossier (5 cols on desktop) */}
          <div className="lg:col-span-5 sticky top-20">
            <Card className="rounded-3xl apple-card overflow-hidden">
              <CardHeader className="pb-3 border-b border-black/[0.05] dark:border-white/[0.07]">
                <div className="flex items-center justify-between w-full">
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-[#007AFF]" />
                    <CardTitle className="text-sm font-semibold">
                      {selectedPlayer ? 'Player Research Dossier' : 'Spotlight Cohort Roster'}
                    </CardTitle>
                  </div>
                  {selectedPlayer && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setSelectedPlayer(null)}
                      className="h-7 w-7 p-0 rounded-full hover:bg-black/[0.05] dark:hover:bg-white/[0.08]"
                      title="Close dossier"
                    >
                      <X className="w-4 h-4" />
                    </Button>
                  )}
                </div>
              </CardHeader>

              <CardContent className="p-5">
                {selectedPlayer ? (
                  <div className="space-y-5">
                    {/* Player Hero Lockup */}
                    <div className="flex items-center gap-3.5 pb-4 border-b border-black/[0.05] dark:border-white/[0.07]">
                      <div
                        className={`w-14 h-14 rounded-2xl flex items-center justify-center font-bold text-lg shadow-sm shrink-0 ${getRoleGradient(
                          selectedPlayer.role
                        )}`}
                      >
                        {selectedPlayer.full_name
                          .split(' ')
                          .map((n) => n[0])
                          .slice(0, 2)
                          .join('')
                          .toUpperCase()}
                      </div>
                      <div className="min-w-0 flex-1">
                        <h3 className="font-bold text-base text-slate-900 dark:text-white tracking-tight truncate">
                          {selectedPlayer.full_name}
                        </h3>
                        <div className="flex items-center gap-2 mt-1">
                          {getTeamBadge(selectedPlayer.primary_team_id)}
                          {getRoleBadge(selectedPlayer.role)}
                          <span className="text-xs text-slate-500 dark:text-slate-400 truncate">
                            {getDisciplineText(selectedPlayer)}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* APDI Discrepancy Status */}
                    {playerAPDI && (
                      <div className="p-3.5 rounded-2xl bg-black/[0.02] dark:bg-white/[0.03] border border-black/[0.05] dark:border-white/[0.07] space-y-2">
                        <div className="flex items-center justify-between text-xs">
                          <span className="font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                            <Target className="w-3.5 h-3.5 text-[#007AFF]" />
                            <span>APDI Discrepancy Status</span>
                          </span>
                          <Badge
                            variant={
                              playerAPDI.discrepancy_category === 'OVER_ATTENDED'
                                ? 'over_attended'
                                : playerAPDI.discrepancy_category === 'UNDER_ATTENDED'
                                ? 'under_attended'
                                : playerAPDI.discrepancy_category === 'BALANCED'
                                ? 'balanced'
                                : 'insufficient_data'
                            }
                            className="text-[10px] font-semibold"
                          >
                            {playerAPDI.discrepancy_category.replace('_', ' ')}
                          </Badge>
                        </div>
                        {playerAPDI.apdi_value !== null ? (
                          <div className="flex items-baseline justify-between pt-1">
                            <span className="text-xs text-slate-500">APDI Index:</span>
                            <span className="font-mono text-base font-bold text-slate-900 dark:text-white tabular-nums">
                              {playerAPDI.apdi_value > 0 ? '+' : ''}
                              {playerAPDI.apdi_value.toFixed(2)}
                            </span>
                          </div>
                        ) : (
                          <p className="text-[11px] text-slate-400 dark:text-slate-500 pt-0.5">
                            Sample size below evaluation threshold. Score withheld to avoid statistical hallucination.
                          </p>
                        )}
                      </div>
                    )}

                    {/* Objective Performance Facts */}
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                        <span className="flex items-center gap-1.5">
                          <Award className="w-3.5 h-3.5 text-[#007AFF]" />
                          <span>Objective Match Facts</span>
                        </span>
                        {perfRecord && (
                          <span className="text-[10px] font-mono text-slate-400 capitalize">
                            {perfRecord.role}
                          </span>
                        )}
                      </div>

                      {isLoadingPerf ? (
                        <Skeleton className="h-20 w-full rounded-2xl" />
                      ) : perfRecord ? (
                        <div className="space-y-2.5">
                          {/* Batting Box */}
                          <div className="p-3 rounded-2xl bg-black/[0.02] dark:bg-white/[0.03] border border-black/[0.05] dark:border-white/[0.07]">
                            <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                              Batting Statistics
                            </div>
                            <div className="grid grid-cols-4 gap-2 text-center text-xs">
                              <div className="p-2 rounded-xl bg-white dark:bg-white/[0.04] border border-black/[0.04] dark:border-white/[0.06] shadow-2xs">
                                <span className="text-[10px] text-slate-400 block">Runs</span>
                                <span className="font-mono font-bold text-sm text-slate-900 dark:text-white tabular-nums">
                                  {perfRecord.runs_scored}
                                </span>
                              </div>
                              <div className="p-2 rounded-xl bg-white dark:bg-white/[0.04] border border-black/[0.04] dark:border-white/[0.06] shadow-2xs">
                                <span className="text-[10px] text-slate-400 block">Balls</span>
                                <span className="font-mono font-medium text-xs tabular-nums">
                                  {perfRecord.balls_faced}
                                </span>
                              </div>
                              <div className="p-2 rounded-xl bg-white dark:bg-white/[0.04] border border-black/[0.04] dark:border-white/[0.06] shadow-2xs">
                                <span className="text-[10px] text-slate-400 block">SR</span>
                                <span className="font-mono font-bold text-xs text-[#34C759] tabular-nums">
                                  {perfRecord.strike_rate ? perfRecord.strike_rate.toFixed(1) : '-'}
                                </span>
                              </div>
                              <div className="p-2 rounded-xl bg-white dark:bg-white/[0.04] border border-black/[0.04] dark:border-white/[0.06] shadow-2xs">
                                <span className="text-[10px] text-slate-400 block">4s / 6s</span>
                                <span className="font-mono text-xs tabular-nums">
                                  {perfRecord.fours} / {perfRecord.sixes}
                                </span>
                              </div>
                            </div>
                          </div>

                          {/* Bowling Box */}
                          {perfRecord.overs_bowled > 0 && (
                            <div className="p-3 rounded-2xl bg-black/[0.02] dark:bg-white/[0.03] border border-black/[0.05] dark:border-white/[0.07]">
                              <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                                Bowling Statistics
                              </div>
                              <div className="grid grid-cols-4 gap-2 text-center text-xs">
                                <div className="p-2 rounded-xl bg-white dark:bg-white/[0.04] border border-black/[0.04] dark:border-white/[0.06] shadow-2xs">
                                  <span className="text-[10px] text-slate-400 block">Wickets</span>
                                  <span className="font-mono font-bold text-sm text-[#34C759] tabular-nums">
                                    {perfRecord.wickets_taken}
                                  </span>
                                </div>
                                <div className="p-2 rounded-xl bg-white dark:bg-white/[0.04] border border-black/[0.04] dark:border-white/[0.06] shadow-2xs">
                                  <span className="text-[10px] text-slate-400 block">Overs</span>
                                  <span className="font-mono font-medium text-xs tabular-nums">
                                    {perfRecord.overs_bowled.toFixed(1)}
                                  </span>
                                </div>
                                <div className="p-2 rounded-xl bg-white dark:bg-white/[0.04] border border-black/[0.04] dark:border-white/[0.06] shadow-2xs">
                                  <span className="text-[10px] text-slate-400 block">Conceded</span>
                                  <span className="font-mono font-medium text-xs tabular-nums">
                                    {perfRecord.runs_conceded}
                                  </span>
                                </div>
                                <div className="p-2 rounded-xl bg-white dark:bg-white/[0.04] border border-black/[0.04] dark:border-white/[0.06] shadow-2xs">
                                  <span className="text-[10px] text-slate-400 block">Econ</span>
                                  <span className="font-mono text-xs tabular-nums">
                                    {perfRecord.bowling_economy ? perfRecord.bowling_economy.toFixed(2) : '-'}
                                  </span>
                                </div>
                              </div>
                            </div>
                          )}
                        </div>
                      ) : (
                        <div className="p-4 rounded-2xl bg-black/[0.02] dark:bg-white/[0.03] border border-dashed border-black/[0.06] dark:border-white/[0.08] text-center text-xs text-slate-400">
                          No delivery events recorded in current match index.
                        </div>
                      )}
                    </div>

                    {/* Media Prominence & Narrative Attention */}
                    <div className="space-y-2">
                      <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                        <Flame className="w-3.5 h-3.5 text-[#FF9500]" />
                        <span>Media Visibility & Editorial Reach</span>
                      </div>

                      {isLoadingAtt ? (
                        <Skeleton className="h-16 w-full rounded-2xl" />
                      ) : attRecord ? (
                        <div className="p-3 rounded-2xl bg-black/[0.02] dark:bg-white/[0.03] border border-black/[0.05] dark:border-white/[0.07] space-y-2">
                          <div className="grid grid-cols-3 gap-2 text-center text-xs">
                            <div className="p-2 rounded-xl bg-white dark:bg-white/[0.04] border border-black/[0.04] dark:border-white/[0.06] shadow-2xs">
                              <span className="text-[10px] text-slate-400 block">Mentions</span>
                              <span className="font-mono font-bold text-sm text-slate-900 dark:text-white tabular-nums">
                                {attRecord.raw_mention_count}
                              </span>
                            </div>
                            <div className="p-2 rounded-xl bg-white dark:bg-white/[0.04] border border-black/[0.04] dark:border-white/[0.06] shadow-2xs">
                              <span className="text-[10px] text-slate-400 block">Reach</span>
                              <span className="font-mono font-bold text-sm text-slate-900 dark:text-white tabular-nums">
                                {attRecord.article_reach}
                              </span>
                            </div>
                            <div className="p-2 rounded-xl bg-white dark:bg-white/[0.04] border border-black/[0.04] dark:border-white/[0.06] shadow-2xs">
                              <span className="text-[10px] text-slate-400 block">Prominence</span>
                              <span className="font-mono font-bold text-sm text-[#FF9500] tabular-nums">
                                {attRecord.prominence_score.toFixed(1)}
                              </span>
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div className="p-4 rounded-2xl bg-black/[0.02] dark:bg-white/[0.03] border border-dashed border-black/[0.06] dark:border-white/[0.08] text-center text-xs text-slate-400">
                          Zero media mentions in current journalism corpus.
                        </div>
                      )}
                    </div>
                  </div>
                ) : (
                  /* Engaging Spotlight View When No Player Is Selected */
                  <div className="space-y-4">
                    <div className="p-4 rounded-2xl bg-black/[0.02] dark:bg-white/[0.03] border border-black/[0.05] dark:border-white/[0.07]">
                      <div className="flex items-center gap-2 text-xs font-semibold text-slate-900 dark:text-white mb-1">
                        <Activity className="w-4 h-4 text-[#007AFF]" />
                        <span>Interactive Research Spotlights</span>
                      </div>
                      <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                        Select a featured athlete below to immediately inspect objective ball-by-ball facts, media attention metrics, and APDI classification:
                      </p>
                    </div>

                    <div className="space-y-2">
                      {FEATURED_PLAYERS.map((fp) => (
                        <button
                          key={fp.id}
                          onClick={() => handleSelectFeatured(fp.id)}
                          className="w-full p-3 rounded-2xl bg-white dark:bg-white/[0.04] border border-black/[0.05] dark:border-white/[0.07] hover:border-[#007AFF]/40 dark:hover:border-[#007AFF]/40 hover:shadow-sm flex items-center justify-between text-left transition-all duration-150 group"
                        >
                          <div className="flex items-center gap-3">
                            <div
                              className={`w-9 h-9 rounded-2xl bg-gradient-to-br ${fp.gradient} text-white flex items-center justify-center font-bold text-xs shadow-2xs shrink-0`}
                            >
                              {fp.name
                                .split(' ')
                                .map((n) => n[0])
                                .slice(0, 2)
                                .join('')}
                            </div>
                            <div>
                              <div className="text-xs font-semibold text-slate-900 dark:text-white group-hover:text-[#007AFF] transition-colors">
                                {fp.name}
                              </div>
                              <div className="text-[10px] text-slate-400 flex items-center gap-1.5 mt-0.5">
                                <span>{fp.team}</span>
                                <span>•</span>
                                <span>{fp.role}</span>
                              </div>
                            </div>
                          </div>
                          <ArrowRight className="w-4 h-4 text-slate-300 group-hover:text-[#007AFF] group-hover:translate-x-0.5 transition-all" />
                        </button>
                      ))}
                    </div>

                    <div className="p-3.5 rounded-2xl bg-[#007AFF]/5 border border-[#007AFF]/15 text-[11px] text-slate-600 dark:text-slate-400 space-y-1">
                      <div className="font-semibold text-[#007AFF] flex items-center gap-1.5">
                        <Shield className="w-3.5 h-3.5" />
                        <span>Research Quality Principle:</span>
                      </div>
                      <p>
                        All entities are reconciled using the Levenshtein Gazetteer against official Cricsheet IDs. Scores are normalized within cohorts to eliminate role bias.
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
