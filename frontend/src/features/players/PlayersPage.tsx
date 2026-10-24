import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Users,
  Search,
  UserCheck,
  Shield,
  Activity,
  Flame,
  Award,
  X,
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
  const { data: playerPerf } = useQuery({
    queryKey: ['playerPerformance', selectedPlayer?.player_id],
    queryFn: () =>
      api.getPerformanceMetrics({
        entity_id: selectedPlayer!.player_id,
      }),
    enabled: !!selectedPlayer,
  });

  // Query media attention metrics for selected player
  const { data: playerAtt } = useQuery({
    queryKey: ['playerAttention', selectedPlayer?.player_id],
    queryFn: () =>
      api.getMediaAttention({
        entity_id: selectedPlayer!.player_id,
      }),
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
              Player Directory
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Canonical player identities, batting/bowling profiles, and aliases.
            </p>
          </div>
        </div>

        {/* Search */}
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search name or alias..."
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
                  {playersData?.items.map((p) => (
                    <TableRow
                      key={p.player_id}
                      className={
                        selectedPlayer?.player_id === p.player_id
                          ? 'bg-emerald-500/10 dark:bg-emerald-500/15'
                          : ''
                      }
                    >
                      <TableCell>
                        <div className="font-semibold text-xs text-slate-900 dark:text-slate-100">
                          {p.full_name}
                        </div>
                        {p.aliases && p.aliases.length > 0 && (
                          <div className="text-[10px] text-slate-500 dark:text-slate-400">
                            aka: {p.aliases.slice(0, 2).join(', ')}
                          </div>
                        )}
                      </TableCell>
                      <TableCell className="font-mono text-xs">
                        {p.primary_team_id || '-'}
                      </TableCell>
                      <TableCell className="text-xs text-slate-600 dark:text-slate-400">
                        {p.batting_style || '-'}
                      </TableCell>
                      <TableCell className="text-xs text-slate-600 dark:text-slate-400">
                        {p.bowling_style || '-'}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setSelectedPlayer(p)}
                          className="text-xs py-1 px-2.5 h-7"
                        >
                          Profile
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
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
              <CardHeader>
                <div>
                  <CardTitle>Player Research Profile</CardTitle>
                  <CardDescription>
                    {selectedPlayer
                      ? selectedPlayer.full_name
                      : 'Select a player to view analytics'}
                  </CardDescription>
                </div>
                {selectedPlayer && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setSelectedPlayer(null)}
                  >
                    <X className="w-4 h-4" />
                  </Button>
                )}
              </CardHeader>
              <CardContent className="space-y-4">
                {!selectedPlayer ? (
                  <div className="py-12 text-center text-xs text-slate-400 dark:text-slate-500">
                    Click "Profile" on any player to inspect objective match performance and media attention.
                  </div>
                ) : (
                  <div className="space-y-4">
                    {/* Identity Overview */}
                    <div className="p-3 rounded-lg bg-slate-50 dark:bg-cricket-navy-950 border border-slate-100 dark:border-cricket-navy-800 space-y-2 text-xs">
                      <div className="flex justify-between">
                        <span className="text-slate-500">Player ID:</span>
                        <span className="font-mono font-medium">{selectedPlayer.player_id}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">Cricsheet ID:</span>
                        <span className="font-mono text-slate-400">
                          {selectedPlayer.cricsheet_id || 'unlinked'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">Aliases Catalog:</span>
                        <span className="text-slate-700 dark:text-slate-300 truncate max-w-[160px]">
                          {selectedPlayer.aliases.join(', ') || 'none'}
                        </span>
                      </div>
                    </div>

                    {/* Objective Performance Section */}
                    <div className="space-y-2">
                      <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                        <Award className="w-3.5 h-3.5 text-emerald-500" />
                        <span>Objective Performance</span>
                      </div>
                      {perfRecord ? (
                        <div className="grid grid-cols-2 gap-2 text-xs">
                          <div className="p-2 rounded bg-slate-50 dark:bg-cricket-navy-950 border border-slate-100 dark:border-cricket-navy-800">
                            <span className="text-slate-400 block text-[10px]">Runs Scored</span>
                            <span className="font-mono font-bold text-sm">
                              {perfRecord.runs_scored}
                            </span>
                            <span className="text-[10px] text-slate-400 block">
                              SR: {perfRecord.strike_rate ?? '-'}
                            </span>
                          </div>
                          <div className="p-2 rounded bg-slate-50 dark:bg-cricket-navy-950 border border-slate-100 dark:border-cricket-navy-800">
                            <span className="text-slate-400 block text-[10px]">Wickets Taken</span>
                            <span className="font-mono font-bold text-sm">
                              {perfRecord.wickets_taken}
                            </span>
                            <span className="text-[10px] text-slate-400 block">
                              Econ: {perfRecord.bowling_economy ?? '-'}
                            </span>
                          </div>
                        </div>
                      ) : (
                        <p className="text-[11px] text-slate-400 dark:text-slate-500 italic">
                          No delivery performance records computed for this player.
                        </p>
                      )}
                    </div>

                    {/* Media Attention Section */}
                    <div className="space-y-2">
                      <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                        <Flame className="w-3.5 h-3.5 text-amber-500" />
                        <span>Media Attention Profile</span>
                      </div>
                      {attRecord ? (
                        <div className="grid grid-cols-2 gap-2 text-xs">
                          <div className="p-2 rounded bg-slate-50 dark:bg-cricket-navy-950 border border-slate-100 dark:border-cricket-navy-800">
                            <span className="text-slate-400 block text-[10px]">Raw Mentions</span>
                            <span className="font-mono font-bold text-sm">
                              {attRecord.raw_mention_count}
                            </span>
                          </div>
                          <div className="p-2 rounded bg-slate-50 dark:bg-cricket-navy-950 border border-slate-100 dark:border-cricket-navy-800">
                            <span className="text-slate-400 block text-[10px]">Prominence Score</span>
                            <span className="font-mono font-bold text-sm text-amber-500">
                              {attRecord.prominence_score.toFixed(2)}
                            </span>
                          </div>
                        </div>
                      ) : (
                        <p className="text-[11px] text-slate-400 dark:text-slate-500 italic">
                          No media attention metrics recorded for this player in current tournament scope.
                        </p>
                      )}
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
