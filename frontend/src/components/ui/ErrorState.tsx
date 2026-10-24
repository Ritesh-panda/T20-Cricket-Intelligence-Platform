import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';
import { Button } from './Button';
import { clsx } from 'clsx';

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  className?: string;
  status?: number;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'API Request Failed',
  message,
  onRetry,
  className,
}) => {
  return (
    <div
      className={clsx(
        'rounded-xl border border-rose-200 dark:border-rose-950/60 bg-rose-50/50 dark:bg-rose-950/20 p-6 sm:p-8 text-center flex flex-col items-center justify-center max-w-xl mx-auto my-6',
        className
      )}
    >
      <div className="p-3 rounded-full bg-rose-100 dark:bg-rose-900/40 text-rose-600 dark:text-rose-400 mb-3">
        <AlertTriangle className="w-6 h-6" />
      </div>
      <h3 className="text-base font-semibold text-rose-900 dark:text-rose-200">
        {title}
      </h3>
      <p className="mt-1.5 text-xs sm:text-sm text-rose-700 dark:text-rose-300/90 leading-relaxed font-mono">
        {message}
      </p>

      {onRetry && (
        <div className="mt-5">
          <Button variant="outline" size="sm" onClick={onRetry} className="gap-2">
            <RefreshCw className="w-3.5 h-3.5" />
            Retry Request
          </Button>
        </div>
      )}
    </div>
  );
};
