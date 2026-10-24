import React from 'react';
import { Card, CardContent } from './Card';
import { LucideIcon } from 'lucide-react';
import { clsx } from 'clsx';

interface MetricCardProps {
  label: string;
  value: string | number;
  subtext?: string;
  icon?: LucideIcon;
  badge?: React.ReactNode;
  trend?: {
    direction: 'up' | 'down' | 'neutral';
    text: string;
  };
  className?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  subtext,
  icon: Icon,
  badge,
  className,
}) => {
  return (
    <Card className={clsx('relative overflow-hidden', className)}>
      <CardContent className="p-4 sm:p-5">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium text-slate-500 dark:text-slate-400 tracking-wider uppercase">
            {label}
          </span>
          {Icon && (
            <div className="p-2 rounded-lg bg-slate-100 dark:bg-cricket-navy-800 text-slate-600 dark:text-slate-300">
              <Icon className="w-4 h-4" />
            </div>
          )}
        </div>
        <div className="mt-3 flex items-baseline justify-between">
          <div className="text-2xl sm:text-3xl font-semibold tracking-tight text-slate-900 dark:text-slate-50 font-mono">
            {value}
          </div>
          {badge}
        </div>
        {subtext && (
          <p className="mt-1.5 text-xs text-slate-500 dark:text-slate-400">
            {subtext}
          </p>
        )}
      </CardContent>
    </Card>
  );
};
