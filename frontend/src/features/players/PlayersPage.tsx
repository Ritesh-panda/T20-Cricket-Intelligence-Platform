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
  { id: 'player_a_johnson', name: 'Aaron Johnson', team: 'CAN', role: 'Batter', gradient: 'from-[#FF9500] to-[#FF3B30]' },
  { id: 'player_a_zampa', name: 'Adam Zampa', team: 'AUS', role: 'Bowler', gradient: 'from-[#34C759] to-[#007AFF]' },
  { id: 'player_mustafizur_rahman', name: 'Mustafizur Rahman', team: 'BAN', role: 'Bowler', gradient: 'from-[#AF52DE] to-[#FF2D55]' },
  { id: 'player_a_markram', name: 'Aiden Markram', team: 'SOU', role: 'Batter', gradient: 'from-[#30B0C7] to-[#007AFF]' },
];

export const PlayersPage: React.FC = () => {
  const [search, setSearch] = useState<string>('');
  const [roleFilter, setRoleFilter] = useState<'all' | 'bat' | 'bowl'>('all');
  const [selectedPlayer, setSelectedPlayer] = useState<PlayerResponse | null>(null);
  const [page, setPage] = useState<number>(0);
  const limit = 15;

  const {
    data: playersData,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['players', search, page],
    queryFn: () =>
      api.getPlayers({
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

  // Query sentiment framing for selected player
  const { data: playerFraming } = useQuery({
    queryKey: ['playerFraming', selectedPlayer?.player_id],
    queryFn: () => api.getEntityFraming(selectedPlayer!.player_id).catch(() => null),
    enabled: !!selectedPlayer,
  });

  const perfRecord = playerPerf?.items?.[0];
  const attRecord = playerAtt?.items?.[0];

  // Client-side role filtering if applied
  const filteredPlayers = (playersData?.items || []).filter((p) => {
    if (roleFilter === 'bat') {
      return (
        (p.batting_style && p.batting_style !== '-') ||
        (perfRecord && perfRecord.role === 'batter')
      );
    }
    if (roleFilter === 'bowl') {
      return (
        (p.bowling_style && p.bowling_style !== '-' && p.bowling_style !== 'None') ||
        (perfRecord && perfRecord.role === 'bowler')
      );
    }
    return true;
  });

  const handleSelectFeatured = async (playerId: string) => {
    try {
      const res = await api.getPlayers({ search: playerId, limit: 1 });
      if (res.items.length > 0) {
        setSelectedPlayer(res.items[0]);
      } else {
        // Fallback search by name
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
              Canonical player identities, performance facts, and media visibility.
            </p>
          </div>
        </div>

        {/* Search Input & Role Filters */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2.5">
          {/* Apple Segmented Control for Roles */}
          <div className="apple-segmented-group flex items-center text-xs font-medium">
            <button
              onClick={() => setRoleFilter('all')}
              className={`px-3 py-1 rounded-xl transition-all ${
                roleFilter === 'all'
                  ? 'apple-segmented-item-active'
                  : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              All
            </button>
            <button
              onClick={() => setRoleFilter('bat')}
              className={`px-3 py-1 rounded-xl transition-all ${
                roleFilter === 'bat'
                  ? 'apple-segmented-item-active'
                  : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              Batters
            </button>
            <button
              onClick={() => setRoleFilter('bowl')}
              className={`px-3 py-1 rounded-xl transition-all ${
                roleFilter === 'bowl'
                  ? 'apple-segmented-item-active'
                  : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              Bowlers
            </button>
          </div>

          {/* Search Box */}
          <div className="relative w-full sm:w-64">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
            <input
              type="text"
              placeholder="Search name, team, or alias..."
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
        <Card className="p-6 space-y-3 rounded-3xl">
          <Skeleton className="h-6 w-1/4 rounded-lg" />
          <Skeleton className="h-12 w-full rounded-2xl" />
          <Skeleton className="h-12 w-full rounded-2xl" />
          <Skeleton className="h-12 w-full rounded-2xl" />
        </Card>
      ) : filteredPlayers.length === 0 ? (
        <EmptyState
          title="No Player Records Found"
          description={
            search
              ? `No players matched "${search}". Try searching by another name or alias.`
              : 'The canonical player register is currently empty. Run tournament ingestion to populate player profiles.'
          }
          icon="database"
          secondaryInfo="Ingest player gazetteer via: python -m src.pipeline run"
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
                    <TableHead className="text-xs font-semibold uppercase tracking-wider text-slate-400">Style</TableHead>
                    <TableHead className="text-right text-xs font-semibold uppercase tracking-wider text-slate-400">Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredPlayers.map((p) => {
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
                              className={`w-8 h-8 rounded-xl flex items-center justify-center text-xs font-bold shrink-0 transition-transform ${
                                isSelected
                                  ? 'bg-[#007AFF] text-white shadow-xs scale-105'
                                  : 'bg-black/[0.04] dark:bg-white/[0.06] text-slate-700 dark:text-slate-300'
                              }`}
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
                                <div className="text-[10px] text-slate-400 truncate max-w-[190px]">
                                  aka: {p.aliases.slice(0, 2).join(', ')}
                                </div>
                              )}
                            </div>
                          </div>
                        </TableCell>

                        <TableCell className="py-3">
                          <Badge variant="neutral" className="text-[10px] py-0.5 px-2 font-mono font-medium rounded-full">
                            {p.primary_team_id || 'IND'}
                          </Badge>
                        </TableCell>

                        <TableCell className="py-3 text-xs text-slate-600 dark:text-slate-400">
                          <div className="truncate max-w-[130px]">
                            {p.batting_style || p.bowling_style || 'All-Rounder'}
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
                    {playersData.pagination.total} players
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
                      <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-[#007AFF] via-[#5856D6] to-[#AF52DE] text-white flex items-center justify-center font-bold text-lg shadow-sm shadow-[#007AFF]/25 shrink-0">
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
                          <Badge variant="neutral" className="font-mono text-[10px] py-0 px-2 rounded-full">
                            {selectedPlayer.primary_team_id || 'IND'}
                          </Badge>
                          <span className="text-xs text-slate-500 dark:text-slate-400 truncate">
                            {selectedPlayer.batting_style || 'Right-handed'}
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
                              className={`w-9 h-9 rounded-xl bg-gradient-to-br ${fp.gradient} text-white flex items-center justify-center font-bold text-xs shadow-2xs shrink-0`}
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
                              <div className="text-[10px] text-slate-400">
                                {fp.team} • {fp.role}
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
