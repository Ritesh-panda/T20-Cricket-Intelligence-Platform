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
      {/* Header and Search Toolbar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 rounded-xl bg-white dark:bg-cricket-navy-900 border border-slate-200 dark:border-cricket-navy-800 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
            <Users className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">
              Player Directory & Profiles
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Canonical player identities, match performance, media visibility, and APDI classification.
            </p>
          </div>
        </div>

        {/* Search */}
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search name, team, or alias..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(0);
            }}
            className="pl-9 pr-8 py-1.5 rounded-lg text-xs bg-slate-50 dark:bg-cricket-navy-950 border border-slate-200 dark:border-cricket-navy-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-emerald-500 w-full"
          />
          {search && (
            <button
              onClick={() => {
                setSearch('');
                setPage(0);
              }}
              className="absolute right-2.5 top-2 text-slate-400 hover:text-slate-600"
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
          <Skeleton className="h-6 w-1/4" />
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
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
                            ? 'bg-emerald-500/10 dark:bg-emerald-500/20 font-medium'
                            : 'hover:bg-slate-50 dark:hover:bg-cricket-navy-800/60'
                        }`}
                      >
                        <TableCell>
                          <div className="font-semibold text-xs text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                            {isSelected && (
                              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
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
                          <Badge variant="neutral" className="text-[10px] py-0 px-1.5 font-semibold">
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
                            className={`text-xs py-1 px-2.5 h-7 ${
                              isSelected
                                ? 'bg-emerald-600 hover:bg-emerald-700 text-white'
                                : ''
                            }`}
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

          {/* Player Detail & Cross-Domain Metrics */}
          <div>
            <Card className="sticky top-20">
              <CardHeader className="pb-3 border-b border-slate-100 dark:border-cricket-navy-800">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-sm font-bold flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-emerald-500" />
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
                      className="h-7 w-7 p-0"
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
                    <p className="font-medium text-slate-600 dark:text-slate-400">
                      Select a player from the directory
                    </p>
                    <p className="text-[11px] text-slate-400 dark:text-slate-500 max-w-[200px] mx-auto">
                      Click anywhere on a row or the "Profile" button to inspect performance facts and media visibility.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {/* Identity Overview */}
                    <div className="p-3 rounded-lg bg-slate-50 dark:bg-cricket-navy-950 border border-slate-100 dark:border-cricket-navy-800 space-y-2 text-xs">
                      <div className="flex justify-between items-center">
                        <span className="text-slate-500">Player ID:</span>
                        <span className="font-mono font-medium text-slate-800 dark:text-slate-200">
                          {selectedPlayer.player_id}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-slate-500">Primary Team:</span>
                        <Badge variant="neutral" className="font-semibold text-[10px] py-0 px-2">
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
                        <div className="flex justify-between items-start pt-1 border-t border-slate-100 dark:border-cricket-navy-800">
                          <span className="text-slate-500">Aliases:</span>
                          <span className="text-slate-700 dark:text-slate-300 text-right truncate max-w-[170px] text-[11px]">
                            {selectedPlayer.aliases.join(', ')}
                          </span>
                        </div>
                      )}
                    </div>

                    {/* APDI Status Badge (if available) */}
                    {playerAPDI && (
                      <div className="p-2.5 rounded-lg border bg-gradient-to-r from-emerald-500/5 via-blue-500/5 to-transparent border-slate-200 dark:border-cricket-navy-800 flex items-center justify-between text-xs">
                        <div className="flex items-center gap-1.5">
                          <Target className="w-3.5 h-3.5 text-emerald-500" />
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
                          <Award className="w-3.5 h-3.5 text-emerald-500" />
                          <span>Objective Performance</span>
                        </div>
                        {perfRecord && (
                          <span className="text-[10px] font-normal text-slate-400 lowercase">
                            {perfRecord.role}
                          </span>
                        )}
                      </div>

                      {isLoadingPerf ? (
                        <Skeleton className="h-16 w-full" />
                      ) : perfRecord ? (
                        <div className="space-y-2">
                          {/* Batting Card */}
                          <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-cricket-navy-950 border border-slate-100 dark:border-cricket-navy-800">
                            <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                              Batting Statistics
                            </div>
                            <div className="grid grid-cols-4 gap-2 text-center text-xs">
                              <div>
                                <span className="text-[10px] text-slate-400 block">Runs</span>
                                <span className="font-mono font-bold text-sm text-slate-900 dark:text-slate-100">
                                  {perfRecord.runs_scored}
                                </span>
                              </div>
                              <div>
                                <span className="text-[10px] text-slate-400 block">Balls</span>
                                <span className="font-mono font-medium text-xs">
                                  {perfRecord.balls_faced}
                                </span>
                              </div>
                              <div>
                                <span className="text-[10px] text-slate-400 block">SR</span>
                                <span className="font-mono font-medium text-xs text-emerald-600 dark:text-emerald-400">
                                  {perfRecord.strike_rate ? perfRecord.strike_rate.toFixed(1) : '-'}
                                </span>
                              </div>
                              <div>
                                <span className="text-[10px] text-slate-400 block">4s / 6s</span>
                                <span className="font-mono text-xs">
                                  {perfRecord.fours} / {perfRecord.sixes}
                                </span>
                              </div>
                            </div>
                          </div>

                          {/* Bowling Card (if bowled) */}
                          {perfRecord.overs_bowled > 0 && (
                            <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-cricket-navy-950 border border-slate-100 dark:border-cricket-navy-800">
                              <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                                Bowling Statistics
                              </div>
                              <div className="grid grid-cols-4 gap-2 text-center text-xs">
                                <div>
                                  <span className="text-[10px] text-slate-400 block">Wickets</span>
                                  <span className="font-mono font-bold text-sm text-emerald-600 dark:text-emerald-400">
                                    {perfRecord.wickets_taken}
                                  </span>
                                </div>
                                <div>
                                  <span className="text-[10px] text-slate-400 block">Overs</span>
                                  <span className="font-mono font-medium text-xs">
                                    {perfRecord.overs_bowled.toFixed(1)}
                                  </span>
                                </div>
                                <div>
                                  <span className="text-[10px] text-slate-400 block">Runs</span>
                                  <span className="font-mono font-medium text-xs">
                                    {perfRecord.runs_conceded}
                                  </span>
                                </div>
                                <div>
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
                        <div className="p-3 rounded-lg bg-slate-50/50 dark:bg-cricket-navy-950/50 border border-dashed border-slate-200 dark:border-cricket-navy-800 text-[11px] text-slate-400 dark:text-slate-500 italic text-center">
                          No delivery events recorded for this player in current fixtures.
                        </div>
                      )}
                    </div>

                    {/* Media Attention Profile */}
                    <div className="space-y-2">
                      <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                        <Flame className="w-3.5 h-3.5 text-amber-500" />
                        <span>Media Attention & Prominence</span>
                      </div>

                      {isLoadingAtt ? (
                        <Skeleton className="h-16 w-full" />
                      ) : attRecord ? (
                        <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-cricket-navy-950 border border-slate-100 dark:border-cricket-navy-800 space-y-2">
                          <div className="grid grid-cols-3 gap-2 text-center text-xs">
                            <div className="p-1.5 rounded bg-white dark:bg-cricket-navy-900 border border-slate-100 dark:border-cricket-navy-800">
                              <span className="text-[10px] text-slate-400 block">Mentions</span>
                              <span className="font-mono font-bold text-sm text-slate-900 dark:text-slate-100">
                                {attRecord.raw_mention_count}
                              </span>
                            </div>
                            <div className="p-1.5 rounded bg-white dark:bg-cricket-navy-900 border border-slate-100 dark:border-cricket-navy-800">
                              <span className="text-[10px] text-slate-400 block">Article Reach</span>
                              <span className="font-mono font-bold text-sm text-slate-900 dark:text-slate-100">
                                {attRecord.article_reach}
                              </span>
                            </div>
                            <div className="p-1.5 rounded bg-white dark:bg-cricket-navy-900 border border-slate-100 dark:border-cricket-navy-800">
                              <span className="text-[10px] text-slate-400 block">Prominence</span>
                              <span className="font-mono font-bold text-sm text-amber-500">
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
                        <div className="p-3 rounded-lg bg-slate-50/50 dark:bg-cricket-navy-950/50 border border-dashed border-slate-200 dark:border-cricket-navy-800 text-[11px] text-slate-400 dark:text-slate-500 italic text-center">
                          No media attention mentions recorded for this player in current editorial corpus.
                        </div>
                      )}
                    </div>

                    {/* Editorial Sentiment Framing */}
                    {playerFraming && playerFraming.total_framed_passages > 0 && (
                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                          <div className="flex items-center gap-1.5">
                            <BarChart2 className="w-3.5 h-3.5 text-blue-500" />
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
                            className="text-[10px] py-0 px-1.5 font-semibold"
                          >
                            {playerFraming.net_framing_score > 0.05
                              ? 'Positive'
                              : playerFraming.net_framing_score < -0.05
                              ? 'Critical'
                              : 'Neutral'}
                          </Badge>
                        </div>

                        <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-cricket-navy-950 border border-slate-100 dark:border-cricket-navy-800 text-xs">
                          <div className="flex items-center justify-between text-[11px] mb-1.5">
                            <span className="text-slate-500">Net Framing Score:</span>
                            <span className="font-mono font-bold text-slate-800 dark:text-slate-200">
                              {playerFraming.net_framing_score > 0 ? '+' : ''}
                              {playerFraming.net_framing_score.toFixed(3)}
                            </span>
                          </div>
                          <div className="grid grid-cols-3 gap-1.5 text-center text-[10px]">
                            <div className="p-1 rounded bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 font-medium">
                              +{playerFraming.positive_count} Pos
                            </div>
                            <div className="p-1 rounded bg-slate-100 dark:bg-cricket-navy-900 text-slate-600 dark:text-slate-400 font-medium">
                              {playerFraming.neutral_count} Neu
                            </div>
                            <div className="p-1 rounded bg-rose-500/10 text-rose-700 dark:text-rose-400 font-medium">
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
