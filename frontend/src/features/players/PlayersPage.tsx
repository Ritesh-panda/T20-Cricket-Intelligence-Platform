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

export const PlayersPage: React.FC = () => {
  const [search, setSearch] = useState<string>('');
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

  return (
    <div className="space-y-6">
      {/* Header and Search Toolbar - Apple Frosted Capsule */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-5 rounded-2xl apple-glass-card shadow-apple-card dark:shadow-apple-card-dark">
        <div className="flex items-center gap-3.5">
          <div className="w-11 h-11 rounded-2xl bg-[#5856D6]/15 text-[#5856D6] flex items-center justify-center shadow-inner">
            <Users className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-slate-900 dark:text-white tracking-tight">
              Player Directory & Profiles
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Canonical player identities, match performance, media visibility, and APDI classification.
            </p>
          </div>
        </div>

        {/* Search - Apple Capsule Input */}
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 absolute left-3.5 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search name, team, or alias..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(0);
            }}
            className="pl-9 pr-8 py-1.5 rounded-full text-xs bg-black/[0.03] dark:bg-white/[0.05] border border-black/[0.06] dark:border-white/[0.08] text-slate-900 dark:text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#5856D6]/30 w-full transition-all"
          />
          {search && (
            <button
              onClick={() => {
                setSearch('');
                setPage(0);
              }}
              className="absolute right-3 top-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {error ? (
        <ErrorState
          title="Failed to Load Players"
          message={extractErrorMessage(error)}
          onRetry={() => refetch()}
        />
      ) : isLoading ? (
        <Card className="p-6 space-y-3">
          <Skeleton className="h-6 w-1/4 rounded-lg" />
          <Skeleton className="h-10 w-full rounded-xl" />
          <Skeleton className="h-10 w-full rounded-xl" />
        </Card>
      ) : playersData?.items.length === 0 ? (
        <EmptyState
          title="No Player Records Found"
          description={
            search
              ? `No players matched the search "${search}". Try searching by another name or alias.`
              : 'The canonical player register is currently empty. Run tournament ingestion to populate player profiles.'
          }
          icon="database"
          secondaryInfo="Ingest player gazetteer via: python -m src.pipeline run"
        />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Players Table */}
          <div className="lg:col-span-2">
            <Card>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Player</TableHead>
                    <TableHead>Primary Team</TableHead>
                    <TableHead>Batting Style</TableHead>
                    <TableHead>Bowling Style</TableHead>
                    <TableHead className="text-right">Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {playersData?.items.map((p) => {
                    const isSelected = selectedPlayer?.player_id === p.player_id;
                    return (
                      <TableRow
                        key={p.player_id}
                        onClick={() => setSelectedPlayer(p)}
                        className={`cursor-pointer transition-colors ${
                          isSelected
                            ? 'bg-[#007AFF]/10 dark:bg-[#007AFF]/15 font-medium'
                            : 'hover:bg-black/[0.02] dark:hover:bg-white/[0.03]'
                        }`}
                      >
                        <TableCell>
                          <div className="font-semibold text-xs text-slate-900 dark:text-slate-100 flex items-center gap-2">
                            {isSelected && (
                              <span className="w-2 h-2 rounded-full bg-[#007AFF] ring-2 ring-[#007AFF]/30 animate-pulse" />
                            )}
                            {p.full_name}
                          </div>
                          {p.aliases && p.aliases.length > 0 && (
                            <div className="text-[10px] text-slate-500 dark:text-slate-400">
                              aka: {p.aliases.slice(0, 2).join(', ')}
                            </div>
                          )}
                        </TableCell>
                        <TableCell className="font-mono text-xs">
                          <Badge variant="neutral" className="text-[10px] py-0 px-2 font-semibold rounded-full">
                            {p.primary_team_id || '-'}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-xs text-slate-600 dark:text-slate-400">
                          {p.batting_style || '-'}
                        </TableCell>
                        <TableCell className="text-xs text-slate-600 dark:text-slate-400">
                          {p.bowling_style || '-'}
                        </TableCell>
                        <TableCell className="text-right">
                          <Button
                            variant={isSelected ? 'primary' : 'outline'}
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedPlayer(p);
                            }}
                            className="text-xs py-1 px-3 h-7 rounded-full shadow-sm"
                          >
                            Profile
                          </Button>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>

              {/* Pagination */}
              {playersData && playersData.pagination.total > limit && (
                <div className="p-3 border-t border-slate-100 dark:border-cricket-navy-800 flex items-center justify-between text-xs text-slate-500">
                  <span>
                    Showing {page * limit + 1}–
                    {Math.min((page + 1) * limit, playersData.pagination.total)} of{' '}
                    {playersData.pagination.total}
                  </span>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={page === 0}
                      onClick={() => setPage((p) => Math.max(0, p - 1))}
                    >
                      Previous
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={!playersData.pagination.has_more}
                      onClick={() => setPage((p) => p + 1)}
                    >
                      Next
                    </Button>
                  </div>
                </div>
              )}
            </Card>
          </div>

          {/* Player Detail & Cross-Domain Metrics - Apple Contact Sheet */}
          <div>
            <Card className="sticky top-20 shadow-apple-card dark:shadow-apple-card-dark rounded-2xl">
              <CardHeader className="pb-3 border-b border-black/[0.06] dark:border-white/[0.08]">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-sm font-bold flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-[#5856D6]" />
                      Player Research Profile
                    </CardTitle>
                    <CardDescription className="text-xs mt-0.5">
                      {selectedPlayer
                        ? selectedPlayer.full_name
                        : 'Click on any player to view analytics'}
                    </CardDescription>
                  </div>
                  {selectedPlayer && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setSelectedPlayer(null)}
                      className="h-7 w-7 p-0 rounded-full hover:bg-black/[0.05] dark:hover:bg-white/[0.08]"
                    >
                      <X className="w-4 h-4" />
                    </Button>
                  )}
                </div>
              </CardHeader>

              <CardContent className="pt-4 space-y-4">
                {!selectedPlayer ? (
                  <div className="py-14 text-center text-xs text-slate-400 dark:text-slate-500 space-y-2">
                    <Users className="w-8 h-8 mx-auto text-slate-300 dark:text-slate-600" />
                    <p className="font-medium text-slate-700 dark:text-slate-300">
                      Select a player from the directory
                    </p>
                    <p className="text-[11px] text-slate-400 dark:text-slate-500 max-w-[200px] mx-auto">
                      Click anywhere on a row or the "Profile" button to inspect performance facts and media visibility.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {/* Apple Contact Header (Initials Squircle) */}
                    <div className="flex items-center gap-3 p-3.5 rounded-2xl bg-gradient-to-br from-[#007AFF]/10 via-[#5856D6]/5 to-transparent border border-black/[0.05] dark:border-white/[0.08]">
                      <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-[#007AFF] to-[#5856D6] text-white flex items-center justify-center font-bold text-base shadow-sm">
                        {selectedPlayer.full_name
                          .split(' ')
                          .map((n) => n[0])
                          .slice(0, 2)
                          .join('')
                          .toUpperCase()}
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="font-bold text-sm text-slate-900 dark:text-white truncate">
                          {selectedPlayer.full_name}
                        </div>
                        <div className="text-[11px] text-slate-500 dark:text-slate-400 font-mono truncate">
                          {selectedPlayer.primary_team_id || 'Free Agent'} • {selectedPlayer.batting_style || 'Batter'}
                        </div>
                      </div>
                    </div>

                    {/* Identity Overview */}
                    <div className="p-3.5 rounded-2xl bg-black/[0.02] dark:bg-white/[0.03] border border-black/[0.05] dark:border-white/[0.07] space-y-2 text-xs">
                      <div className="flex justify-between items-center">
                        <span className="text-slate-500">Player ID:</span>
                        <span className="font-mono font-medium text-slate-800 dark:text-slate-200">
                          {selectedPlayer.player_id}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-slate-500">Primary Team:</span>
                        <Badge variant="neutral" className="font-semibold text-[10px] py-0 px-2 rounded-full">
                          {selectedPlayer.primary_team_id || 'Free Agent'}
                        </Badge>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-slate-500">Batting Style:</span>
                        <span className="text-slate-700 dark:text-slate-300 font-medium">
                          {selectedPlayer.batting_style || 'Unspecified'}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-slate-500">Bowling Style:</span>
                        <span className="text-slate-700 dark:text-slate-300 font-medium truncate max-w-[170px]">
                          {selectedPlayer.bowling_style || 'None'}
                        </span>
                      </div>
                      {selectedPlayer.cricsheet_id && (
                        <div className="flex justify-between items-center">
                          <span className="text-slate-500">Cricsheet ID:</span>
                          <span className="font-mono text-slate-400 text-[11px]">
                            {selectedPlayer.cricsheet_id}
                          </span>
                        </div>
                      )}
                      {selectedPlayer.aliases && selectedPlayer.aliases.length > 0 && (
                        <div className="flex justify-between items-start pt-1.5 border-t border-black/[0.05] dark:border-white/[0.06]">
                          <span className="text-slate-500">Aliases:</span>
                          <span className="text-slate-700 dark:text-slate-300 text-right truncate max-w-[170px] text-[11px]">
                            {selectedPlayer.aliases.join(', ')}
                          </span>
                        </div>
                      )}
                    </div>

                    {/* APDI Status Badge (if available) */}
                    {playerAPDI && (
                      <div className="p-3 rounded-2xl border bg-black/[0.02] dark:bg-white/[0.03] border-black/[0.05] dark:border-white/[0.07] flex items-center justify-between text-xs">
                        <div className="flex items-center gap-1.5">
                          <Target className="w-3.5 h-3.5 text-[#007AFF]" />
                          <span className="font-medium text-slate-700 dark:text-slate-300">
                            APDI Status
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
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
                            className="text-[10px] font-semibold uppercase"
                          >
                            {playerAPDI.discrepancy_category.replace('_', ' ')}
                          </Badge>
                          {playerAPDI.apdi_value !== null && (
                            <span className="font-mono text-xs font-bold text-slate-800 dark:text-slate-200">
                              {playerAPDI.apdi_value > 0 ? '+' : ''}
                              {playerAPDI.apdi_value.toFixed(2)}
                            </span>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Objective Match Performance */}
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                        <div className="flex items-center gap-1.5">
                          <Award className="w-3.5 h-3.5 text-[#007AFF]" />
                          <span>Objective Performance</span>
                        </div>
                        {perfRecord && (
                          <span className="text-[10px] font-normal text-slate-400 lowercase">
                            {perfRecord.role}
                          </span>
                        )}
                      </div>

                      {isLoadingPerf ? (
                        <Skeleton className="h-16 w-full rounded-2xl" />
                      ) : perfRecord ? (
                        <div className="space-y-2.5">
                          {/* Batting Card */}
                          <div className="p-3 rounded-2xl bg-black/[0.02] dark:bg-white/[0.03] border border-black/[0.05] dark:border-white/[0.07]">
                            <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
                              Batting Statistics
                            </div>
                            <div className="grid grid-cols-4 gap-2 text-center text-xs">
                              <div className="p-2 rounded-xl bg-black/[0.02] dark:bg-white/[0.04]">
                                <span className="text-[10px] text-slate-400 block">Runs</span>
                                <span className="font-mono font-bold text-sm text-slate-900 dark:text-white">
                                  {perfRecord.runs_scored}
                                </span>
                              </div>
                              <div className="p-2 rounded-xl bg-black/[0.02] dark:bg-white/[0.04]">
                                <span className="text-[10px] text-slate-400 block">Balls</span>
                                <span className="font-mono font-medium text-xs">
                                  {perfRecord.balls_faced}
                                </span>
                              </div>
                              <div className="p-2 rounded-xl bg-black/[0.02] dark:bg-white/[0.04]">
                                <span className="text-[10px] text-slate-400 block">SR</span>
                                <span className="font-mono font-medium text-xs text-[#34C759]">
                                  {perfRecord.strike_rate ? perfRecord.strike_rate.toFixed(1) : '-'}
                                </span>
                              </div>
                              <div className="p-2 rounded-xl bg-black/[0.02] dark:bg-white/[0.04]">
                                <span className="text-[10px] text-slate-400 block">4s / 6s</span>
                                <span className="font-mono text-xs">
                                  {perfRecord.fours} / {perfRecord.sixes}
                                </span>
                              </div>
                            </div>
                          </div>

                          {/* Bowling Card (if bowled) */}
                          {perfRecord.overs_bowled > 0 && (
                            <div className="p-3 rounded-2xl bg-black/[0.02] dark:bg-white/[0.03] border border-black/[0.05] dark:border-white/[0.07]">
                              <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
                                Bowling Statistics
                              </div>
                              <div className="grid grid-cols-4 gap-2 text-center text-xs">
                                <div className="p-2 rounded-xl bg-black/[0.02] dark:bg-white/[0.04]">
                                  <span className="text-[10px] text-slate-400 block">Wickets</span>
                                  <span className="font-mono font-bold text-sm text-[#34C759]">
                                    {perfRecord.wickets_taken}
                                  </span>
                                </div>
                                <div className="p-2 rounded-xl bg-black/[0.02] dark:bg-white/[0.04]">
                                  <span className="text-[10px] text-slate-400 block">Overs</span>
                                  <span className="font-mono font-medium text-xs">
                                    {perfRecord.overs_bowled.toFixed(1)}
                                  </span>
                                </div>
                                <div className="p-2 rounded-xl bg-black/[0.02] dark:bg-white/[0.04]">
                                  <span className="text-[10px] text-slate-400 block">Runs</span>
                                  <span className="font-mono font-medium text-xs">
                                    {perfRecord.runs_conceded}
                                  </span>
                                </div>
                                <div className="p-2 rounded-xl bg-black/[0.02] dark:bg-white/[0.04]">
                                  <span className="text-[10px] text-slate-400 block">Econ</span>
                                  <span className="font-mono text-xs">
                                    {perfRecord.bowling_economy ? perfRecord.bowling_economy.toFixed(2) : '-'}
                                  </span>
                                </div>
                              </div>
                            </div>
                          )}

                          <div className="flex items-center justify-between text-[11px] text-slate-400 px-1">
                            <span>Matches: {perfRecord.matches_played}</span>
                            <span>Raw Composite: {perfRecord.raw_performance_composite.toFixed(2)}</span>
                          </div>
                        </div>
                      ) : (
                        <div className="p-3.5 rounded-2xl bg-black/[0.02] dark:bg-white/[0.03] border border-dashed border-black/[0.08] dark:border-white/[0.08] text-[11px] text-slate-400 italic text-center">
                          No delivery events recorded for this player in current fixtures.
                        </div>
                      )}
                    </div>

                    {/* Media Attention Profile */}
                    <div className="space-y-2">
                      <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                        <Flame className="w-3.5 h-3.5 text-[#FF9500]" />
                        <span>Media Attention & Prominence</span>
                      </div>

                      {isLoadingAtt ? (
                        <Skeleton className="h-16 w-full rounded-2xl" />
                      ) : attRecord ? (
                        <div className="p-3 rounded-2xl bg-black/[0.02] dark:bg-white/[0.03] border border-black/[0.05] dark:border-white/[0.07] space-y-2.5">
                          <div className="grid grid-cols-3 gap-2 text-center text-xs">
                            <div className="p-2 rounded-xl bg-white dark:bg-white/[0.05] border border-black/[0.05] dark:border-white/[0.08] shadow-sm">
                              <span className="text-[10px] text-slate-400 block">Mentions</span>
                              <span className="font-mono font-bold text-sm text-slate-900 dark:text-white">
                                {attRecord.raw_mention_count}
                              </span>
                            </div>
                            <div className="p-2 rounded-xl bg-white dark:bg-white/[0.05] border border-black/[0.05] dark:border-white/[0.08] shadow-sm">
                              <span className="text-[10px] text-slate-400 block">Article Reach</span>
                              <span className="font-mono font-bold text-sm text-slate-900 dark:text-white">
                                {attRecord.article_reach}
                              </span>
                            </div>
                            <div className="p-2 rounded-xl bg-white dark:bg-white/[0.05] border border-black/[0.05] dark:border-white/[0.08] shadow-sm">
                              <span className="text-[10px] text-slate-400 block">Prominence</span>
                              <span className="font-mono font-bold text-sm text-[#FF9500]">
                                {attRecord.prominence_score.toFixed(1)}
                              </span>
                            </div>
                          </div>

                          <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1">
                            <span>Publishers: {attRecord.source_diversity_count}</span>
                            <span>Headline Mentions: {attRecord.headline_mentions}</span>
                          </div>
                        </div>
                      ) : (
                        <div className="p-3.5 rounded-2xl bg-black/[0.02] dark:bg-white/[0.03] border border-dashed border-black/[0.08] dark:border-white/[0.08] text-[11px] text-slate-400 italic text-center">
                          No media attention mentions recorded for this player in current editorial corpus.
                        </div>
                      )}
                    </div>

                    {/* Editorial Sentiment Framing */}
                    {playerFraming && playerFraming.total_framed_passages > 0 && (
                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                          <div className="flex items-center gap-1.5">
                            <BarChart2 className="w-3.5 h-3.5 text-[#007AFF]" />
                            <span>Editorial Framing</span>
                          </div>
                          <Badge
                            variant={
                              playerFraming.net_framing_score > 0.05
                                ? 'success'
                                : playerFraming.net_framing_score < -0.05
                                ? 'danger'
                                : 'neutral'
                            }
                            className="text-[10px] py-0 px-2 font-semibold"
                          >
                            {playerFraming.net_framing_score > 0.05
                              ? 'Positive'
                              : playerFraming.net_framing_score < -0.05
                              ? 'Critical'
                              : 'Neutral'}
                          </Badge>
                        </div>

                        <div className="p-3 rounded-2xl bg-black/[0.02] dark:bg-white/[0.03] border border-black/[0.05] dark:border-white/[0.07] text-xs">
                          <div className="flex items-center justify-between text-[11px] mb-2">
                            <span className="text-slate-500">Net Framing Score:</span>
                            <span className="font-mono font-bold text-slate-800 dark:text-slate-200">
                              {playerFraming.net_framing_score > 0 ? '+' : ''}
                              {playerFraming.net_framing_score.toFixed(3)}
                            </span>
                          </div>
                          <div className="grid grid-cols-3 gap-2 text-center text-[10px]">
                            <div className="p-1.5 rounded-xl bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 font-semibold border border-emerald-500/20">
                              +{playerFraming.positive_count} Pos
                            </div>
                            <div className="p-1.5 rounded-xl bg-black/[0.04] dark:bg-white/[0.06] text-slate-700 dark:text-slate-300 font-semibold border border-black/[0.04] dark:border-white/[0.06]">
                              {playerFraming.neutral_count} Neu
                            </div>
                            <div className="p-1.5 rounded-xl bg-rose-500/10 text-rose-700 dark:text-rose-300 font-semibold border border-rose-500/20">
                              -{playerFraming.negative_count} Neg
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
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
