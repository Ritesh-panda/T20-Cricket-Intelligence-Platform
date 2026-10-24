import React from 'react';
import { Database, Search, AlertCircle } from 'lucide-react';
import { Button } from './Button';
import { clsx } from 'clsx';

interface EmptyStateProps {
  title: string;
  description: string;
  icon?: 'database' | 'search' | 'alert';
  actionLabel?: string;
  onAction?: () => void;
  className?: string;
  variant?: 'corpus_empty' | 'filter_no_results' | 'insufficient_evidence';
  secondaryInfo?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  icon = 'database',
  actionLabel,
  onAction,
  className,
  variant = 'corpus_empty',
  secondaryInfo,
}) => {
  const icons = {
    database: <Database className="w-8 h-8 text-slate-400 dark:text-slate-500" />,
    search: <Search className="w-8 h-8 text-slate-400 dark:text-slate-500" />,
    alert: <AlertCircle className="w-8 h-8 text-amber-500" />,
  };

  return (
    <div
      className={clsx(
        'rounded-xl border border-dashed border-slate-300 dark:border-cricket-navy-800 bg-white/50 dark:bg-cricket-navy-900/40 p-8 sm:p-12 text-center flex flex-col items-center justify-center max-w-2xl mx-auto my-6',
        className
      )}
    >
      <div className="p-3.5 rounded-full bg-slate-100 dark:bg-cricket-navy-800 mb-4 ring-8 ring-slate-50 dark:ring-cricket-navy-950">
        {icons[icon]}
      </div>
      <h3 className="text-base sm:text-lg font-semibold text-slate-900 dark:text-slate-100 tracking-tight">
        {title}
      </h3>
      <p className="mt-2 text-sm text-slate-500 dark:text-slate-400 max-w-md text-balance leading-relaxed">
        {description}
      </p>

      {secondaryInfo && (
        <div className="mt-4 px-3.5 py-2 rounded-lg bg-slate-100 dark:bg-cricket-navy-800/80 text-xs font-mono text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-cricket-navy-700 max-w-md">
          {secondaryInfo}
        </div>
      )}

      {actionLabel && onAction && (
        <div className="mt-6">
          <Button variant="outline" size="sm" onClick={onAction}>
            {actionLabel}
          </Button>
        </div>
      )}
    </div>
  );
};
