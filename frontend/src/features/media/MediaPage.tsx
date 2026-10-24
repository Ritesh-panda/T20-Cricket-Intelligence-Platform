import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Newspaper,
  MessageSquare,
  Globe,
  Calendar,
  ExternalLink,
  Flame,
  FileText,
  X,
  PieChart as PieChartIcon,
} from 'lucide-react';
import { api, extractErrorMessage } from '../../lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/Card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/Table';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { EmptyState } from '../../components/ui/EmptyState';
import { ErrorState } from '../../components/ui/ErrorState';
import { Skeleton } from '../../components/ui/Skeleton';
import type { ArticleDetailResponse, ArticleParagraphResponse, ArticleResponse, CommentaryResponse } from '../../types/api';

export const MediaPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'articles' | 'commentary' | 'framing'>('articles');
  const [sourceFilter, setSourceFilter] = useState<string>('');
  const [selectedArticleId, setSelectedArticleId] = useState<string | null>(null);
  const [entityFilter, setEntityFilter] = useState<string>('p_kohli');
  const [page, setPage] = useState<number>(0);
  const limit = 10;

  // Query articles
  const {
    data: articlesData,
    isLoading: isArticlesLoading,
    error: articlesError,
    refetch: refetchArticles,
  } = useQuery({
    queryKey: ['articles', sourceFilter, page],
    queryFn: () =>
      api.getArticles({
        source_domain: sourceFilter.trim() || undefined,
        limit,
        offset: page * limit,
      }),
    enabled: activeTab === 'articles',
  });

  // Query single article detail
  const { data: articleDetail, isLoading: isDetailLoading } = useQuery<ArticleDetailResponse>({
    queryKey: ['articleDetail', selectedArticleId],
    queryFn: () => api.getArticle(selectedArticleId!),
    enabled: !!selectedArticleId,
  });

  // Query article paragraphs
  const { data: paragraphsData } = useQuery({
    queryKey: ['articleParagraphs', selectedArticleId],
    queryFn: () => api.getArticleParagraphs(selectedArticleId!, { limit: 50 }),
    enabled: !!selectedArticleId,
  });

  // Query commentary
  const {
    data: commentaryData,
    isLoading: isCommentaryLoading,
    error: commentaryError,
    refetch: refetchCommentary,
  } = useQuery({
    queryKey: ['commentary', sourceFilter, page],
    queryFn: () =>
      api.getCommentary({
        source_domain: sourceFilter.trim() || undefined,
        limit,
        offset: page * limit,
      }),
    enabled: activeTab === 'commentary',
  });

  // Query entity framing breakdown
  const {
    data: framingData,
    isLoading: isFramingLoading,
    error: framingError,
  } = useQuery({
    queryKey: ['entityFraming', entityFilter],
    queryFn: () => api.getEntityFraming(entityFilter),
    enabled: activeTab === 'framing' && !!entityFilter,
  });

  return (
    <div className="space-y-6">
      {/* Tab and Filter Toolbar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 rounded-xl bg-white dark:bg-cricket-navy-900 border border-slate-200 dark:border-cricket-navy-800 shadow-sm">
        <div className="flex items-center gap-2 border border-slate-200 dark:border-cricket-navy-800 p-1 rounded-lg bg-slate-50 dark:bg-cricket-navy-950">
          <button
            onClick={() => {
              setActiveTab('articles');
              setPage(0);
            }}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors flex items-center gap-1.5 ${
              activeTab === 'articles'
                ? 'bg-white dark:bg-cricket-navy-800 text-emerald-600 dark:text-emerald-400 shadow-sm font-semibold'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
            }`}
          >
            <Newspaper className="w-3.5 h-3.5" />
            <span>Articles</span>
          </button>
          <button
            onClick={() => {
              setActiveTab('commentary');
              setPage(0);
            }}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors flex items-center gap-1.5 ${
              activeTab === 'commentary'
                ? 'bg-white dark:bg-cricket-navy-800 text-emerald-600 dark:text-emerald-400 shadow-sm font-semibold'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
            }`}
          >
            <MessageSquare className="w-3.5 h-3.5" />
            <span>Ball-by-Ball Commentary</span>
          </button>
          <button
            onClick={() => setActiveTab('framing')}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors flex items-center gap-1.5 ${
              activeTab === 'framing'
                ? 'bg-white dark:bg-cricket-navy-800 text-emerald-600 dark:text-emerald-400 shadow-sm font-semibold'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
            }`}
          >
            <Flame className="w-3.5 h-3.5 text-amber-500" />
            <span>Narrative Framing</span>
          </button>
        </div>

        {activeTab !== 'framing' ? (
          <div className="flex items-center gap-2 w-full sm:w-auto">
            <input
              type="text"
              placeholder="Filter by publisher domain..."
              value={sourceFilter}
              onChange={(e) => {
                setSourceFilter(e.target.value);
                setPage(0);
              }}
              className="px-3 py-1.5 rounded-lg text-xs bg-slate-50 dark:bg-cricket-navy-950 border border-slate-200 dark:border-cricket-navy-700 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-1 focus:ring-emerald-500 w-full sm:w-56"
            />
            {sourceFilter && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setSourceFilter('');
                  setPage(0);
                }}
              >
                <X className="w-3.5 h-3.5" />
              </Button>
            )}
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500">Target Entity:</span>
            <input
              type="text"
              placeholder="Player ID (e.g. p_kohli)"
              value={entityFilter}
              onChange={(e) => setEntityFilter(e.target.value)}
              className="px-3 py-1.5 rounded-lg text-xs bg-slate-50 dark:bg-cricket-navy-950 border border-slate-200 dark:border-cricket-navy-700 text-slate-900 dark:text-slate-100 font-mono w-40"
            />
          </div>
        )}
      </div>

      {/* Articles Tab */}
      {activeTab === 'articles' && (
        <>
          {articlesError ? (
            <ErrorState
              title="Failed to Load Articles"
              message={extractErrorMessage(articlesError)}
              onRetry={() => refetchArticles()}
            />
          ) : isArticlesLoading ? (
            <Card className="p-6 space-y-3">
              <Skeleton className="h-6 w-1/4" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </Card>
          ) : articlesData?.items.length === 0 ? (
            <EmptyState
              title="No News Articles Available"
              description={
                sourceFilter
                  ? `No articles found from domain "${sourceFilter}". Clear filter to view all sources.`
                  : 'The news articles collection is currently empty. Run the discovery and acquisition pipeline to harvest tournament journalism.'
              }
              icon="database"
              secondaryInfo="Harvest news articles via: python -m src.pipeline run --source espncricinfo"
            />
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Articles Table */}
              <div className="lg:col-span-2">
                <Card>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Headline & Publisher</TableHead>
                        <TableHead>Published</TableHead>
                        <TableHead className="text-right">Action</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {articlesData?.items.map((art: ArticleResponse) => (
                        <TableRow
                          key={art.article_id}
                          className={
                            selectedArticleId === art.article_id
                              ? 'bg-emerald-500/10 dark:bg-emerald-500/15'
                              : ''
                          }
                        >
                          <TableCell>
                            <div className="font-semibold text-xs text-slate-900 dark:text-slate-100 leading-snug">
                              {art.headline}
                            </div>
                            <div className="flex items-center gap-2 mt-1 text-[11px] text-slate-500 dark:text-slate-400">
                              <span className="font-mono text-emerald-600 dark:text-emerald-400">
                                {art.source_domain}
                              </span>
                              {art.author && <span>by {art.author}</span>}
                            </div>
                          </TableCell>
                          <TableCell className="font-mono text-xs text-slate-500">
                            {art.published_at_utc ? art.published_at_utc.slice(0, 10) : 'n/a'}
                          </TableCell>
                          <TableCell className="text-right">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => setSelectedArticleId(art.article_id)}
                              className="text-xs py-1 px-2.5 h-7"
                            >
                              Inspect
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>

                  {/* Pagination */}
                  {articlesData && articlesData.pagination.total > limit && (
                    <div className="p-3 border-t border-slate-100 dark:border-cricket-navy-800 flex items-center justify-between text-xs text-slate-500">
                      <span>
                        Showing {page * limit + 1}–
                        {Math.min((page + 1) * limit, articlesData.pagination.total)} of{' '}
                        {articlesData.pagination.total}
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
                          disabled={!articlesData.pagination.has_more}
                          onClick={() => setPage((p) => p + 1)}
                        >
                          Next
                        </Button>
                      </div>
                    </div>
                  )}
                </Card>
              </div>

              {/* Article Paragraph Inspector */}
              <div>
                <Card className="sticky top-20">
                  <CardHeader>
                    <div>
                      <CardTitle>Article & Paragraph Inspector</CardTitle>
                      <CardDescription>
                        {selectedArticleId ? `Article ID: ${selectedArticleId}` : 'Select an article to view body'}
                      </CardDescription>
                    </div>
                    {selectedArticleId && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setSelectedArticleId(null)}
                      >
                        <X className="w-4 h-4" />
                      </Button>
                    )}
                  </CardHeader>
                  <CardContent className="space-y-4 max-h-[600px] overflow-y-auto">
                    {!selectedArticleId ? (
                      <div className="py-12 text-center text-xs text-slate-400 dark:text-slate-500">
                        Select an article from the left to view parsed paragraph blocks and source provenance.
                      </div>
                    ) : isDetailLoading ? (
                      <div className="space-y-3 py-6">
                        <Skeleton className="h-6 w-full" />
                        <Skeleton className="h-24 w-full" />
                      </div>
                    ) : articleDetail ? (
                      <div className="space-y-4 text-xs">
                        <div className="p-3 rounded-lg bg-slate-50 dark:bg-cricket-navy-950 border border-slate-100 dark:border-cricket-navy-800 space-y-1">
                          <h4 className="font-semibold text-slate-900 dark:text-slate-100">
                            {articleDetail.headline}
                          </h4>
                          <a
                            href={articleDetail.canonical_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-[11px] text-emerald-600 dark:text-emerald-400 hover:underline flex items-center gap-1 font-mono truncate"
                          >
                            <span>Canonical Source</span>
                            <ExternalLink className="w-3 h-3 shrink-0" />
                          </a>
                        </div>

                        {/* Paragraph Segments */}
                        <div className="space-y-2">
                          <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                            Discrete Paragraph Segments ({paragraphsData?.items.length || 0})
                          </span>
                          <div className="space-y-2">
                            {paragraphsData?.items.map((p) => (
                              <div
                                key={p.paragraph_id}
                                className="p-2.5 rounded bg-slate-50/70 dark:bg-cricket-navy-950/70 border border-slate-200/60 dark:border-cricket-navy-800 text-slate-700 dark:text-slate-300 leading-relaxed font-sans"
                              >
                                <span className="font-mono text-[10px] text-slate-400 block mb-1">
                                  #{p.paragraph_index} • {p.char_count} chars
                                </span>
                                {p.text}
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
        </>
      )}

      {/* Commentary Tab */}
      {activeTab === 'commentary' && (
        <>
          {commentaryError ? (
            <ErrorState
              title="Failed to Load Commentary"
              message={extractErrorMessage(commentaryError)}
              onRetry={() => refetchCommentary()}
            />
          ) : isCommentaryLoading ? (
            <Card className="p-6 space-y-3">
              <Skeleton className="h-6 w-1/4" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </Card>
          ) : commentaryData?.items.length === 0 ? (
            <EmptyState
              title="No Commentary Records Indexed"
              description="Ball-by-ball written commentary entries have not yet been acquired into the relational store."
              icon="database"
              secondaryInfo="Harvest commentary via: python -m src.pipeline run --source cricbuzz"
            />
          ) : (
            <Card>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Over / Ball</TableHead>
                    <TableHead>Match</TableHead>
                    <TableHead>Bowler to Batter</TableHead>
                    <TableHead>Commentary Narration</TableHead>
                    <TableHead>Event Tags</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {commentaryData?.items.map((comm: CommentaryResponse) => (
                    <TableRow key={comm.commentary_id}>
                      <TableCell className="font-mono text-xs font-bold text-emerald-600 dark:text-emerald-400">
                        {comm.over_num}.{comm.ball_num}
                      </TableCell>
                      <TableCell className="font-mono text-xs text-slate-500">
                        {comm.match_id}
                      </TableCell>
                      <TableCell className="text-xs">
                        <span className="font-medium text-slate-900 dark:text-slate-100">
                          {comm.bowler_raw}
                        </span>{' '}
                        <span className="text-slate-400">to</span>{' '}
                        <span className="font-medium text-slate-900 dark:text-slate-100">
                          {comm.batter_raw}
                        </span>
                      </TableCell>
                      <TableCell className="text-xs text-slate-700 dark:text-slate-300 max-w-md">
                        {comm.text}
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-wrap gap-1">
                          {comm.event_tags.map((tag, i) => (
                            <Badge key={i} variant="neutral" className="text-[10px]">
                              {tag}
                            </Badge>
                          ))}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Card>
          )}
        </>
      )}

      {/* Narrative Framing Tab */}
      {activeTab === 'framing' && (
        <div className="space-y-6">
          {framingError ? (
            <ErrorState
              title="Failed to Load Framing"
              message={extractErrorMessage(framingError)}
            />
          ) : isFramingLoading ? (
            <Card className="p-6 space-y-3">
              <Skeleton className="h-6 w-1/4" />
              <Skeleton className="h-20 w-full" />
            </Card>
          ) : framingData ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Sentiment Summary */}
              <Card>
                <CardHeader>
                  <CardTitle>Editorial Tone Summary</CardTitle>
                  <CardDescription>
                    Sentiment breakdown around {framingData.entity_id}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-3 gap-2 text-center">
                    <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                      <span className="text-[10px] text-emerald-600 uppercase font-semibold">Positive</span>
                      <p className="text-xl font-bold font-mono text-emerald-600 mt-1">
                        {framingData.positive_count}
                      </p>
                    </div>
                    <div className="p-3 rounded-lg bg-slate-100 dark:bg-cricket-navy-800 border border-slate-200 dark:border-cricket-navy-700">
                      <span className="text-[10px] text-slate-500 uppercase font-semibold">Neutral</span>
                      <p className="text-xl font-bold font-mono text-slate-600 dark:text-slate-300 mt-1">
                        {framingData.neutral_count}
                      </p>
                    </div>
                    <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20">
                      <span className="text-[10px] text-rose-600 uppercase font-semibold">Negative</span>
                      <p className="text-xl font-bold font-mono text-rose-600 mt-1">
                        {framingData.negative_count}
                      </p>
                    </div>
                  </div>

                  <div className="p-3 rounded-lg bg-slate-50 dark:bg-cricket-navy-950 border border-slate-100 dark:border-cricket-navy-800 flex justify-between items-center text-xs">
                    <span className="text-slate-500">Net Framing Score (pos - neg) / total:</span>
                    <span className="font-mono font-bold text-sm text-slate-900 dark:text-slate-100">
                      {framingData.net_framing_score.toFixed(3)}
                    </span>
                  </div>
                </CardContent>
              </Card>

              {/* Publisher Breakdown */}
              <Card className="md:col-span-2">
                <CardHeader>
                  <CardTitle>Publisher Framing Variance</CardTitle>
                  <CardDescription>Distribution of sentiment across news sources</CardDescription>
                </CardHeader>
                <CardContent>
                  {Object.keys(framingData.source_framing_breakdown).length === 0 ? (
                    <p className="text-xs text-slate-400 py-6 text-center italic">
                      No publisher-attributed framing passages found for this entity.
                    </p>
                  ) : (
                    <div className="space-y-3">
                      {Object.entries(framingData.source_framing_breakdown).map(([domain, counts]) => (
                        <div
                          key={domain}
                          className="p-3 rounded-lg bg-slate-50 dark:bg-cricket-navy-950 border border-slate-100 dark:border-cricket-navy-800 flex items-center justify-between text-xs"
                        >
                          <span className="font-semibold text-slate-800 dark:text-slate-200 font-mono">
                            {domain}
                          </span>
                          <div className="flex items-center gap-3 font-mono">
                            <span className="text-emerald-600">+{counts.positive}</span>
                            <span className="text-slate-400">{counts.neutral}</span>
                            <span className="text-rose-600">-{counts.negative}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
};
