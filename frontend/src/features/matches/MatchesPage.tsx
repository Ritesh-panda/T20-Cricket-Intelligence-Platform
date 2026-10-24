import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Trophy,
  Calendar,
  MapPin,
  ChevronRight,
  Filter,
  X,
  Activity,
  Layers,
} from 'lucide-react';
import { api, extractErrorMessage } from '../../lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/Card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/Table';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { EmptyState } from '../../components/ui/EmptyState';
import { ErrorState } from '../../components/ui/ErrorState';
import { Skeleton } from '../../components/ui/Skeleton';
import type { MatchPerformanceScorecard, MatchResponse } from '../../types/api';

export const MatchesPage: React.FC = () => {
  const [tournament, setTournament] = useState<string>('');
  const [season, setSeason] = useState<string>('');
  const [selectedMatchId, setSelectedMatchId] = useState<string | null>(null);
  const [page, setPage] = useState<number>(0);
  const limit = 15;

  const {
    data: matchesData,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['matches', tournament, season, page],
    queryFn: () =>
      api.getMatches({
        tournament: tournament || undefined,
        season: season || undefined,
        limit,
        offset: page * limit,
      }),
  });

  // Query performance scorecard for selected match
  const {
    data: scorecard,
    isLoading: isScorecardLoading,
    error: scorecardError,
  } = useQuery<MatchPerformanceScorecard>({
    queryKey: ['matchPerformance', selectedMatchId],
    queryFn: () => api.getMatchPerformance(selectedMatchId!),
    enabled: !!selectedMatchId,
  });

  return (
    <div className="space-y-6">
      {/* Header and Filter Toolbar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 rounded-xl bg-white dark:bg-cricket-navy-900 border border-slate-200 dark:border-cricket-navy-800 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
            <Trophy className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">
              Matches Directory
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Canonical match scorecards derived strictly from Cricsheet delivery facts.
            </p>
          </div>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-2 w-full sm:w-auto">
          <input
            type="text"
            placeholder="Filter tournament..."
            value={tournament}
            onChange={(e) => {
              setTournament(e.target.value);
              setPage(0);
            }}
            className="px-3 py-1.5 rounded-lg text-xs bg-slate-50 dark:bg-cricket-navy-950 border border-slate-200 dark:border-cricket-navy-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-emerald-500 w-full sm:w-44"
          />
          <input
            type="text"
            placeholder="Season..."
            value={season}
            onChange={(e) => {
              setSeason(e.target.value);
              setPage(0);
            }}
            className="px-3 py-1.5 rounded-lg text-xs bg-slate-50 dark:bg-cricket-navy-950 border border-slate-200 dark:border-cricket-navy-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-emerald-500 w-24"
          />
          {(tournament || season) && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setTournament('');
                setSeason('');
                setPage(0);
              }}
              title="Clear filters"
            >
              <X className="w-3.5 h-3.5" />
            </Button>
          )}
        </div>
      </div>

      {error ? (
        <ErrorState
          title="Failed to Load Matches"
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
      ) : matchesData?.items.length === 0 ? (
        <EmptyState
          title="No Match Records Found"
          description={
            tournament || season
              ? 'No matches match your active filter criteria. Clear filters to see all matches.'
              : 'The database currently contains 0 structured match records. Ingest tournament data to view match scorecards.'
          }
          icon="database"
          secondaryInfo="Ingest matches via CLI: python -m src.pipeline run --source cricsheet"
        />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Matches List */}
          <div className="lg:col-span-2">
            <Card>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Match Date</TableHead>
                    <TableHead>Teams</TableHead>
                    <TableHead>Venue</TableHead>
                    <TableHead>Result</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {matchesData?.items.map((m: MatchResponse) => (
                    <TableRow
                      key={m.match_id}
                      className={
                        selectedMatchId === m.match_id
                          ? 'bg-emerald-500/10 dark:bg-emerald-500/15'
                          : ''
                      }
                    >
                      <TableCell className="font-mono text-xs">
                        <span className="flex items-center gap-1.5 text-slate-600 dark:text-slate-400">
                          <Calendar className="w-3.5 h-3.5 text-slate-400" />
                          {m.match_date}
                        </span>
                      </TableCell>
                      <TableCell>
                        <div className="font-semibold text-xs text-slate-900 dark:text-slate-100">
                          {m.team1_id} vs {m.team2_id}
                        </div>
                        <div className="text-[10px] text-slate-500 dark:text-slate-400 font-mono">
                          {m.tournament}
                        </div>
                      </TableCell>
                      <TableCell className="text-xs">
                        <span className="flex items-center gap-1 text-slate-600 dark:text-slate-400 truncate max-w-[160px]">
                          <MapPin className="w-3 h-3 shrink-0 text-slate-400" />
                          {m.venue}
                        </span>
                      </TableCell>
                      <TableCell>
                        {m.winner_id ? (
                          <Badge variant="success">
                            Won by {m.winner_id}
                          </Badge>
                        ) : (
                          <Badge variant="neutral">No Result</Badge>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setSelectedMatchId(m.match_id)}
                          className="text-xs py-1 px-2.5 h-7"
                        >
                          Scorecard
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {/* Pagination */}
              {matchesData && matchesData.pagination.total > limit && (
                <div className="p-3 border-t border-slate-100 dark:border-cricket-navy-800 flex items-center justify-between text-xs text-slate-500">
                  <span>
                    Showing {page * limit + 1}–
                    {Math.min((page + 1) * limit, matchesData.pagination.total)} of{' '}
                    {matchesData.pagination.total}
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
                      disabled={!matchesData.pagination.has_more}
                      onClick={() => setPage((p) => p + 1)}
                    >
                      Next
                    </Button>
                  </div>
                </div>
              )}
            </Card>
          </div>

          {/* Match Scorecard Drawer */}
          <div>
            <Card className="sticky top-20">
              <CardHeader>
                <div>
                  <CardTitle>Delivery-Derived Scorecard</CardTitle>
                  <CardDescription>
                    {selectedMatchId ? `Match ID: ${selectedMatchId}` : 'Select a match to inspect'}
                  </CardDescription>
                </div>
                {selectedMatchId && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setSelectedMatchId(null)}
                  >
                    <X className="w-4 h-4" />
                  </Button>
                )}
              </CardHeader>

              <CardContent className="space-y-4">
                {!selectedMatchId ? (
                  <div className="py-12 text-center text-xs text-slate-400 dark:text-slate-500">
                    Click "Scorecard" on any match to calculate batting & bowling performance.
                  </div>
                ) : isScorecardLoading ? (
                  <div className="space-y-3 py-6">
                    <Skeleton className="h-6 w-3/4" />
                    <Skeleton className="h-8 w-full" />
                    <Skeleton className="h-8 w-full" />
                  </div>
                ) : scorecardError ? (
                  <p className="text-xs text-rose-500 py-4 font-mono">
                    {extractErrorMessage(scorecardError)}
                  </p>
                ) : scorecard ? (
                  <div className="space-y-4">
                    {/* Innings Totals */}
                    <div className="space-y-2">
                      <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                        Innings Totals
                      </span>
                      {scorecard.team_scores.map((t, i) => (
                        <div
                          key={i}
                          className="flex items-center justify-between p-2.5 rounded-lg bg-slate-50 dark:bg-cricket-navy-950 border border-slate-100 dark:border-cricket-navy-800 text-xs"
                        >
                          <span className="font-semibold text-slate-800 dark:text-slate-200">
                            {t.team_id} (Innings {t.innings})
                          </span>
                          <span className="font-mono font-bold text-slate-900 dark:text-slate-100">
                            {t.total_runs}/{t.total_wickets}{' '}
                            <span className="text-[10px] font-normal text-slate-400">
                              ({t.legal_overs} ov)
                            </span>
                          </span>
                        </div>
                      ))}
                    </div>

                    {/* Top Batters */}
                    <div className="space-y-2">
                      <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                        Top Batters
                      </span>
                      <div className="space-y-1.5">
                        {scorecard.batters.slice(0, 5).map((b, i) => (
                          <div
                            key={i}
                            className="flex items-center justify-between text-xs py-1 border-b border-slate-100 dark:border-cricket-navy-800 last:border-0"
                          >
                            <div>
                              <span className="font-medium text-slate-800 dark:text-slate-200">
                                {b.player_id}
                              </span>
                              {b.is_out && (
                                <span className="ml-1 text-[10px] text-slate-400">
                                  ({b.dismissal_kind || 'out'})
                                </span>
                              )}
                            </div>
                            <div className="font-mono text-right">
                              <span className="font-bold">{b.runs}</span>
                              <span className="text-slate-400 ml-1 text-[11px]">
                                ({b.balls})
                              </span>
                              <span className="text-emerald-600 dark:text-emerald-400 ml-2 text-[10px]">
                                SR {b.strike_rate ?? '-'}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Top Bowlers */}
                    <div className="space-y-2">
                      <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                        Top Bowlers
                      </span>
                      <div className="space-y-1.5">
                        {scorecard.bowlers.slice(0, 5).map((bw, i) => (
                          <div
                            key={i}
                            className="flex items-center justify-between text-xs py-1 border-b border-slate-100 dark:border-cricket-navy-800 last:border-0"
                          >
                            <span className="font-medium text-slate-800 dark:text-slate-200">
                              {bw.player_id}
                            </span>
                            <div className="font-mono text-right">
                              <span className="font-bold text-emerald-600 dark:text-emerald-400">
                                {bw.wickets}/{bw.runs_conceded}
                              </span>
                              <span className="text-slate-400 ml-1 text-[11px]">
                                ({bw.overs} ov)
                              </span>
                              <span className="text-slate-500 ml-2 text-[10px]">
                                Econ {bw.economy ?? '-'}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                ) : null}
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
};
