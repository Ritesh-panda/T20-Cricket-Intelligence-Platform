import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Network,
  Tag,
  Clock,
  GitCompare,
  CheckCircle,
  HelpCircle,
  AlertTriangle,
  Info,
} from 'lucide-react';
import { api, extractErrorMessage } from '../../lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/Card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/Table';
import { Badge } from '../../components/ui/Badge';
import { EmptyState } from '../../components/ui/EmptyState';
import { ErrorState } from '../../components/ui/ErrorState';
import { Skeleton } from '../../components/ui/Skeleton';
import type { TopicClusterResponse, EntityMentionResponse, NarrativeTimelineResponse, CrossSourceMatchResponse } from '../../types/api';

export const NarrativesPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'topics' | 'entities' | 'timeline' | 'alignments'>('topics');

  // Topics
  const { data: topicsData, isLoading: isTopicsLoading, error: topicsError } = useQuery({
    queryKey: ['topics'],
    queryFn: () => api.getTopics(),
    enabled: activeTab === 'topics',
  });

  // Entities
  const { data: entitiesData, isLoading: isEntitiesLoading, error: entitiesError } = useQuery({
    queryKey: ['entities'],
    queryFn: () => api.getEntities({ limit: 25 }),
    enabled: activeTab === 'entities',
  });

  // Timeline
  const { data: timelineData, isLoading: isTimelineLoading, error: timelineError } = useQuery({
    queryKey: ['narrativeTimeline'],
    queryFn: () => api.getNarrativeTimeline(),
    enabled: activeTab === 'timeline',
  });

  // Alignments
  const { data: alignmentsData, isLoading: isAlignmentsLoading, error: alignmentsError } = useQuery({
    queryKey: ['crossSourceMatches'],
    queryFn: () => api.getCrossSourceMatches(),
    enabled: activeTab === 'alignments',
  });

  return (
    <div className="space-y-6">
      {/* Header and Tab Selector */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 rounded-xl bg-white dark:bg-cricket-navy-900 border border-slate-200 dark:border-cricket-navy-800 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
            <Network className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">
              Topics & Narrative Intelligence
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Unsupervised semantic clustering, NER mentions, and cross-source event alignments.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1 border border-slate-200 dark:border-cricket-navy-800 p-1 rounded-lg bg-slate-50 dark:bg-cricket-navy-950">
          <button
            onClick={() => setActiveTab('topics')}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
              activeTab === 'topics'
                ? 'bg-white dark:bg-cricket-navy-800 text-emerald-600 dark:text-emerald-400 shadow-sm font-semibold'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
            }`}
          >
            Topics ({topicsData?.items?.length || 0})
          </button>
          <button
            onClick={() => setActiveTab('entities')}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
              activeTab === 'entities'
                ? 'bg-white dark:bg-cricket-navy-800 text-emerald-600 dark:text-emerald-400 shadow-sm font-semibold'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
            }`}
          >
            Entity Mentions
          </button>
          <button
            onClick={() => setActiveTab('timeline')}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
              activeTab === 'timeline'
                ? 'bg-white dark:bg-cricket-navy-800 text-emerald-600 dark:text-emerald-400 shadow-sm font-semibold'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
            }`}
          >
            Narrative Timeline
          </button>
          <button
            onClick={() => setActiveTab('alignments')}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
              activeTab === 'alignments'
                ? 'bg-white dark:bg-cricket-navy-800 text-emerald-600 dark:text-emerald-400 shadow-sm font-semibold'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
            }`}
          >
            Cross-Source Alignments
          </button>
        </div>
      </div>

      {/* Model vs Fact Notice */}
      <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-cricket-navy-900/40 border border-slate-200 dark:border-cricket-navy-800 flex items-start gap-2.5 text-xs text-slate-600 dark:text-slate-400">
        <Info className="w-4 h-4 shrink-0 text-emerald-500 mt-0.5" />
        <p>
          <span className="font-semibold text-slate-800 dark:text-slate-200">
            Epistemological distinction:
          </span>{' '}
          Topic clusters and semantic embeddings group passages by statistical text similarity.
          They are distinct from ground-truth match events, which are verified independently through
          structured Cricsheet delivery facts.
        </p>
      </div>

      {/* Topics Tab */}
      {activeTab === 'topics' && (
        <>
          {topicsError ? (
            <ErrorState title="Failed to Load Topics" message={extractErrorMessage(topicsError)} />
          ) : isTopicsLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Skeleton className="h-32 w-full" />
              <Skeleton className="h-32 w-full" />
            </div>
          ) : topicsData?.items.length === 0 ? (
            <EmptyState
              title="No Topic Clusters Discovered"
              description="Unsupervised topic discovery requires normalized paragraph embeddings. Run clustering on the indexed corpus to extract theme centroids."
              icon="database"
              secondaryInfo="Discover topics via: python -m src.pipeline cluster-topics --k 5"
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {topicsData?.items.map((t: TopicClusterResponse) => (
                <Card key={t.cluster_id} className="p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs text-emerald-600 dark:text-emerald-400 font-semibold">
                      Cluster #{t.cluster_index}
                    </span>
                    <Badge variant={t.is_noise ? 'neutral' : 'success'}>
                      {t.doc_count} docs
                    </Badge>
                  </div>
                  <h3 className="font-semibold text-sm text-slate-900 dark:text-slate-100">
                    {t.topic_label}
                  </h3>
                  <div className="flex flex-wrap gap-1">
                    {t.keywords.map((kw: string, i: number) => (
                      <span
                        key={i}
                        className="px-2 py-0.5 rounded bg-slate-100 dark:bg-cricket-navy-800 text-[11px] font-mono text-slate-600 dark:text-slate-300"
                      >
                        {kw}
                      </span>
                    ))}
                  </div>
                  {t.intra_cluster_similarity !== null && (
                    <div className="pt-2 border-t border-slate-100 dark:border-cricket-navy-800 text-[11px] text-slate-500 flex justify-between font-mono">
                      <span>Cohesion Similarity:</span>
                      <span>{t.intra_cluster_similarity.toFixed(3)}</span>
                    </div>
                  )}
                </Card>
              ))}
            </div>
          )}
        </>
      )}

      {/* Entity Mentions Tab */}
      {activeTab === 'entities' && (
        <>
          {entitiesError ? (
            <ErrorState title="Failed to Load Entities" message={extractErrorMessage(entitiesError)} />
          ) : isEntitiesLoading ? (
            <Skeleton className="h-48 w-full" />
          ) : entitiesData?.items.length === 0 ? (
            <EmptyState
              title="No Entity Mentions Extracted"
              description="Entity mentions extracted via Cricket NER and gazetteers will appear here."
              icon="database"
              secondaryInfo="Run NER pipeline: python -m src.pipeline process-text"
            />
          ) : (
            <Card>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Surface Text</TableHead>
                    <TableHead>Entity Type</TableHead>
                    <TableHead>Resolved ID</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Confidence</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {entitiesData?.items.map((e: EntityMentionResponse) => (
                    <TableRow key={e.mention_id}>
                      <TableCell className="font-semibold text-xs text-slate-900 dark:text-slate-100">
                        {e.surface_text}
                      </TableCell>
                      <TableCell>
                        <Badge variant="neutral" className="text-[10px]">
                          {e.entity_type}
                        </Badge>
                      </TableCell>
                      <TableCell className="font-mono text-xs text-slate-600 dark:text-slate-400">
                        {e.resolved_id || <span className="text-slate-400 italic">unresolved</span>}
                      </TableCell>
                      <TableCell>
                        {e.resolution_status === 'RESOLVED' ? (
                          <Badge variant="success" className="gap-1">
                            <CheckCircle className="w-3 h-3" /> Resolved
                          </Badge>
                        ) : e.resolution_status === 'AMBIGUOUS' ? (
                          <Badge variant="warning" className="gap-1">
                            <AlertTriangle className="w-3 h-3" /> Ambiguous
                          </Badge>
                        ) : (
                          <Badge variant="neutral" className="gap-1">
                            <HelpCircle className="w-3 h-3" /> Unresolved
                          </Badge>
                        )}
                      </TableCell>
                      <TableCell className="font-mono text-xs font-semibold">
                        {(e.confidence * 100).toFixed(0)}%
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Card>
          )}
        </>
      )}

      {/* Narrative Timeline Tab */}
      {activeTab === 'timeline' && (
        <>
          {timelineError ? (
            <ErrorState title="Failed to Load Timeline" message={extractErrorMessage(timelineError)} />
          ) : isTimelineLoading ? (
            <Skeleton className="h-48 w-full" />
          ) : timelineData?.items.length === 0 ? (
            <EmptyState
              title="No Timeline Snapshots Recorded"
              description="Chronological narrative trajectory points tracking editorial shifts over match dates have not been synthesized."
              icon="database"
              secondaryInfo="Synthesize timeline: python -m src.pipeline narrative-timeline"
            />
          ) : (
            <div className="space-y-4">
              {timelineData?.items.map((snap: NarrativeTimelineResponse) => (
                <Card key={snap.snapshot_id} className="p-4">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-mono font-semibold text-emerald-600 dark:text-emerald-400">
                      Bucket: {snap.bucket_label}
                    </span>
                    <span className="text-slate-500">
                      {snap.doc_count} passages • Mean Sentiment: {snap.mean_sentiment.toFixed(2)}
                    </span>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </>
      )}

      {/* Cross-Source Alignments Tab */}
      {activeTab === 'alignments' && (
        <>
          {alignmentsError ? (
            <ErrorState title="Failed to Load Alignments" message={extractErrorMessage(alignmentsError)} />
          ) : isAlignmentsLoading ? (
            <Skeleton className="h-48 w-full" />
          ) : alignmentsData?.items.length === 0 ? (
            <EmptyState
              title="No Cross-Source Alignments Established"
              description="Two-stage narrative-to-event alignment pairs connecting editorial claims to commentary facts will be listed here."
              icon="database"
            />
          ) : (
            <Card>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Link ID</TableHead>
                    <TableHead>Match</TableHead>
                    <TableHead>Method</TableHead>
                    <TableHead>Similarity</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {alignmentsData?.items.map((link: CrossSourceMatchResponse) => (
                    <TableRow key={link.match_link_id}>
                      <TableCell className="font-mono text-xs">{link.match_link_id}</TableCell>
                      <TableCell className="font-mono text-xs">{link.match_id || '-'}</TableCell>
                      <TableCell className="text-xs">{link.matching_method}</TableCell>
                      <TableCell className="font-mono text-xs font-semibold text-emerald-600">
                        {(link.similarity_score * 100).toFixed(1)}%
                      </TableCell>
                      <TableCell>
                        <Badge variant="success">{link.status}</Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Card>
          )}
        </>
      )}
    </div>
  );
};
