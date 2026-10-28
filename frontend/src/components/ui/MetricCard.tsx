import React from 'react';
import { Card, CardContent } from './Card';
import { LucideIcon } from 'lucide-react';
import { clsx } from 'clsx';

interface MetricCardProps {
  label: string;
  value: string | number;
  subtext?: string;
  icon?: LucideIcon;
  iconColor?: 'blue' | 'green' | 'orange' | 'purple' | 'red' | 'indigo';
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
  iconColor = 'blue',
  badge,
  className,
}) => {
  const iconThemes = {
    blue: 'bg-[#007AFF]/12 text-[#007AFF] dark:text-[#0A84FF]',
    green: 'bg-[#34C759]/12 text-[#248A3D] dark:text-[#30D158]',
    orange: 'bg-[#FF9500]/12 text-[#C97000] dark:text-[#FF9F0A]',
    purple: 'bg-[#AF52DE]/12 text-[#8944AB] dark:text-[#BF5AF2]',
    red: 'bg-[#FF3B30]/12 text-[#D70015] dark:text-[#FF453A]',
    indigo: 'bg-[#5856D6]/12 text-[#5856D6] dark:text-[#5E5CE6]',
  };

  return (
    <Card className={clsx('relative overflow-hidden group hover:shadow-apple-float transition-all duration-300', className)}>
      <CardContent className="p-4 sm:p-5">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-semibold text-slate-400 dark:text-slate-400 tracking-wider uppercase">
            {label}
          </span>
          {Icon && (
            <div className={clsx('p-2 rounded-xl transition-transform duration-200 group-hover:scale-105', iconThemes[iconColor])}>
              <Icon className="w-4 h-4" />
            </div>
          )}
        </div>
        <div className="mt-2.5 flex items-baseline justify-between gap-2">
          <div className="text-2xl sm:text-3xl font-semibold tracking-tight text-slate-900 dark:text-white tabular-nums">
            {value}
          </div>
          {badge}
        </div>
        {subtext && (
          <p className="mt-1.5 text-xs text-slate-500 dark:text-slate-400 truncate tracking-normal">
            {subtext}
          </p>
        )}
      </CardContent>
    </Card>
  );
};
