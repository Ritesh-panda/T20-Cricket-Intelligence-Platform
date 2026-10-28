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
  const [activeInnings, setActiveInnings] = useState<number>(1);
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
      {/* Header and Filter Toolbar - Apple Frosted Capsule */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-5 rounded-2xl apple-glass-card shadow-apple-card dark:shadow-apple-card-dark">
        <div className="flex items-center gap-3.5">
          <div className="w-11 h-11 rounded-2xl bg-[#007AFF]/15 text-[#007AFF] flex items-center justify-center shadow-inner">
            <Trophy className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-slate-900 dark:text-white tracking-tight">
              Matches Directory
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Canonical match scorecards derived strictly from Cricsheet delivery facts.
            </p>
          </div>
        </div>

        {/* Filters - Apple Pill Inputs */}
        <div className="flex items-center gap-2 w-full sm:w-auto">
          <input
            type="text"
            placeholder="Filter tournament..."
            value={tournament}
            onChange={(e) => {
              setTournament(e.target.value);
              setPage(0);
            }}
            className="px-3.5 py-1.5 rounded-full text-xs bg-black/[0.03] dark:bg-white/[0.05] border border-black/[0.06] dark:border-white/[0.08] text-slate-900 dark:text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#007AFF]/30 w-full sm:w-44 transition-all"
          />
          <input
            type="text"
            placeholder="Season..."
            value={season}
            onChange={(e) => {
              setSeason(e.target.value);
              setPage(0);
            }}
            className="px-3.5 py-1.5 rounded-full text-xs bg-black/[0.03] dark:bg-white/[0.05] border border-black/[0.06] dark:border-white/[0.08] text-slate-900 dark:text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-[#007AFF]/30 w-24 transition-all"
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
              className="rounded-full w-8 h-8 p-0"
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
          <Skeleton className="h-6 w-1/4 rounded-lg" />
          <Skeleton className="h-10 w-full rounded-xl" />
          <Skeleton className="h-10 w-full rounded-xl" />
          <Skeleton className="h-10 w-full rounded-xl" />
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
                          ? 'bg-[#007AFF]/10 dark:bg-[#007AFF]/15 font-medium'
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
                          variant={selectedMatchId === m.match_id ? 'primary' : 'outline'}
                          size="sm"
                          onClick={() => {
                            setSelectedMatchId(m.match_id);
                            setActiveInnings(1);
                          }}
                          className="text-xs py-1 px-3 h-7 rounded-full shadow-sm"
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

          {/* Match Scorecard Drawer - Apple Sequoia Floating Card */}
          <div>
            <Card className="sticky top-20 shadow-apple-card dark:shadow-apple-card-dark rounded-2xl">
              <CardHeader className="pb-3 border-b border-black/[0.06] dark:border-white/[0.08]">
                <div className="flex items-start justify-between w-full">
                  <div>
                    <CardTitle className="text-sm font-bold flex items-center gap-2">
                      <Trophy className="w-4 h-4 text-[#007AFF]" />
                      Detailed Match Scorecard
                    </CardTitle>
                    <CardDescription className="text-xs mt-0.5">
                      {selectedMatchId
                        ? `Delivery-audited ball-by-ball performance`
                        : 'Select any match from the directory to inspect its full scorecard'}
                    </CardDescription>
                  </div>
                  {selectedMatchId && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setSelectedMatchId(null)}
                      className="h-7 w-7 p-0 rounded-full hover:bg-black/[0.05] dark:hover:bg-white/[0.08]"
                    >
                      <X className="w-4 h-4" />
                    </Button>
                  )}
                </div>
              </CardHeader>

              <CardContent className="pt-4 space-y-4">
                {!selectedMatchId ? (
                  <div className="py-16 text-center text-xs text-slate-400 dark:text-slate-500">
                    <Activity className="w-8 h-8 mx-auto mb-2 text-slate-300 dark:text-slate-600" />
                    Select "Scorecard" on any fixture to calculate complete batting and bowling breakdowns.
                  </div>
                ) : isScorecardLoading ? (
                  <div className="space-y-3 py-6">
                    <Skeleton className="h-10 w-full rounded-xl" />
                    <Skeleton className="h-20 w-full rounded-xl" />
                    <Skeleton className="h-40 w-full rounded-xl" />
                  </div>
                ) : scorecardError ? (
                  <p className="text-xs text-[#FF3B30] py-4 font-mono">
                    {extractErrorMessage(scorecardError)}
                  </p>
                ) : scorecard ? (
                  <div className="space-y-5">
                    {/* Match Context Pill */}
                    <div className="p-3.5 rounded-2xl bg-black/[0.02] dark:bg-white/[0.03] border border-black/[0.05] dark:border-white/[0.07] space-y-2.5">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-semibold text-slate-800 dark:text-slate-200">
                          {scorecard.venue}
                        </span>
                        <span className="text-[10px] text-slate-400 font-mono">
                          {scorecard.match_date}
                        </span>
                      </div>
                      {scorecard.winner_id ? (
                        <div className="text-xs font-semibold text-[#34C759] flex items-center gap-1.5">
                          <span>🏆</span>
                          <span>{scorecard.winner_id} won match</span>
                        </div>
                      ) : (
                        <div className="text-xs text-slate-500">Match concluded / No result</div>
                      )}

                      {/* Innings Tabs / Scores (Apple Segmented Control) */}
                      <div className="grid grid-cols-2 gap-2 pt-1">
                        {scorecard.team_scores.map((t) => (
                          <button
                            key={t.innings}
                            onClick={() => setActiveInnings(t.innings)}
                            className={`p-2.5 rounded-xl text-left transition-all border ${
                              activeInnings === t.innings
                                ? 'bg-white dark:bg-white/[0.1] border-black/[0.1] dark:border-white/[0.2] shadow-sm text-slate-900 dark:text-white'
                                : 'bg-transparent border-transparent hover:bg-black/[0.03] dark:hover:bg-white/[0.04] text-slate-600 dark:text-slate-400'
                            }`}
                          >
                            <div className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">
                              Innings {t.innings} • {t.team_id}
                            </div>
                            <div className="text-sm font-bold font-mono tracking-tight mt-0.5">
                              {t.total_runs}/{t.total_wickets}
                              <span className="text-[10px] font-normal text-slate-500 ml-1">
                                ({t.legal_overs} ov)
                              </span>
                            </div>
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Active Innings Batting Card */}
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-[11px] font-semibold text-slate-600 dark:text-slate-400 uppercase tracking-wider">
                        <span>
                          Batting (Innings {activeInnings})
                        </span>
                        <span className="text-[10px] font-mono lowercase">
                          r • b • 4s • 6s • sr
                        </span>
                      </div>
                      <div className="overflow-x-auto rounded-lg border border-slate-200 dark:border-cricket-navy-800">
                        <table className="w-full text-xs text-left">
                          <thead className="bg-slate-50 dark:bg-cricket-navy-950 text-slate-500 text-[10px] uppercase font-semibold">
                            <tr>
                              <th className="py-1.5 px-2.5">Batter</th>
                              <th className="py-1.5 px-1.5">Dismissal</th>
                              <th className="py-1.5 px-1.5 text-right">R</th>
                              <th className="py-1.5 px-1.5 text-right">B</th>
                              <th className="py-1.5 px-1.5 text-right">4s</th>
                              <th className="py-1.5 px-1.5 text-right">6s</th>
                              <th className="py-1.5 px-2 text-right">SR</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-100 dark:divide-cricket-navy-800 bg-white dark:bg-cricket-navy-900">
                            {scorecard.batters
                              .filter((b) => !b.innings || b.innings === activeInnings)
                              .map((b, i) => (
                                <tr key={i} className="hover:bg-slate-50/50 dark:hover:bg-cricket-navy-800/40">
                                  <td className="py-1.5 px-2.5 font-medium text-slate-900 dark:text-slate-100 truncate max-w-[120px]">
                                    {b.player_name || b.player_id.replace('player_', '').replace(/_/g, ' ')}
                                  </td>
                                  <td className="py-1.5 px-1.5 text-[10px] text-slate-500 dark:text-slate-400 truncate max-w-[90px]">
                                    {b.is_out ? (
                                      <span className="text-rose-500/90 dark:text-rose-400">
                                        {b.dismissal_kind || 'out'}
                                      </span>
                                    ) : (
                                      <span className="text-emerald-600 dark:text-emerald-400 font-semibold">
                                        not out
                                      </span>
                                    )}
                                  </td>
                                  <td className="py-1.5 px-1.5 text-right font-mono font-bold text-slate-900 dark:text-slate-100">
                                    {b.runs}
                                  </td>
                                  <td className="py-1.5 px-1.5 text-right font-mono text-slate-500">
                                    {b.balls}
                                  </td>
                                  <td className="py-1.5 px-1.5 text-right font-mono text-slate-500">
                                    {b.fours}
                                  </td>
                                  <td className="py-1.5 px-1.5 text-right font-mono text-slate-500">
                                    {b.sixes}
                                  </td>
                                  <td className="py-1.5 px-2 text-right font-mono text-slate-700 dark:text-slate-300">
                                    {b.strike_rate != null ? b.strike_rate.toFixed(1) : '-'}
                                  </td>
                                </tr>
                              ))}
                          </tbody>
                        </table>
                      </div>

                      {/* Extras & Total Row */}
                      {(() => {
                        const activeTeamScore = scorecard.team_scores.find((t) => t.innings === activeInnings);
                        return activeTeamScore ? (
                          <div className="flex items-center justify-between px-2.5 py-1.5 bg-slate-50 dark:bg-cricket-navy-950 rounded-md text-[11px] font-mono border border-slate-200/60 dark:border-cricket-navy-800">
                            <span className="text-slate-500">
                              Extras: <strong className="text-slate-800 dark:text-slate-200">{activeTeamScore.extras ?? 0}</strong>
                            </span>
                            <span className="font-semibold text-slate-900 dark:text-slate-100">
                              Total: {activeTeamScore.total_runs}/{activeTeamScore.total_wickets} ({activeTeamScore.legal_overs} ov)
                            </span>
                          </div>
                        ) : null;
                      })()}
                    </div>

                    {/* Active Innings Bowling Card */}
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-[11px] font-semibold text-slate-600 dark:text-slate-400 uppercase tracking-wider">
                        <span>
                          Bowling (Innings {activeInnings})
                        </span>
                        <span className="text-[10px] font-mono lowercase">
                          o • m • r • w • econ
                        </span>
                      </div>
                      <div className="overflow-x-auto rounded-lg border border-slate-200 dark:border-cricket-navy-800">
                        <table className="w-full text-xs text-left">
                          <thead className="bg-slate-50 dark:bg-cricket-navy-950 text-slate-500 text-[10px] uppercase font-semibold">
                            <tr>
                              <th className="py-1.5 px-2.5">Bowler</th>
                              <th className="py-1.5 px-1.5 text-right">O</th>
                              <th className="py-1.5 px-1.5 text-right">M</th>
                              <th className="py-1.5 px-1.5 text-right">R</th>
                              <th className="py-1.5 px-1.5 text-right">W</th>
                              <th className="py-1.5 px-2 text-right">Econ</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-100 dark:divide-cricket-navy-800 bg-white dark:bg-cricket-navy-900">
                            {scorecard.bowlers
                              .filter((bw) => !bw.innings || bw.innings === activeInnings)
                              .map((bw, i) => (
                                <tr key={i} className="hover:bg-slate-50/50 dark:hover:bg-cricket-navy-800/40">
                                  <td className="py-1.5 px-2.5 font-medium text-slate-900 dark:text-slate-100 truncate max-w-[120px]">
                                    {bw.player_name || bw.player_id.replace('player_', '').replace(/_/g, ' ')}
                                  </td>
                                  <td className="py-1.5 px-1.5 text-right font-mono text-slate-600 dark:text-slate-300">
                                    {bw.overs.toFixed(1)}
                                  </td>
                                  <td className="py-1.5 px-1.5 text-right font-mono text-slate-500">
                                    {bw.maidens ?? 0}
                                  </td>
                                  <td className="py-1.5 px-1.5 text-right font-mono text-slate-600 dark:text-slate-300">
                                    {bw.runs_conceded}
                                  </td>
                                  <td className="py-1.5 px-1.5 text-right font-mono font-bold text-emerald-600 dark:text-emerald-400">
                                    {bw.wickets}
                                  </td>
                                  <td className="py-1.5 px-2 text-right font-mono text-slate-500">
                                    {bw.economy != null ? bw.economy.toFixed(2) : '-'}
                                  </td>
                                </tr>
                              ))}
                          </tbody>
                        </table>
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
