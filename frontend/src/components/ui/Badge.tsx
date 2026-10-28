import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

type BadgeVariant =
  | 'neutral'
  | 'success'
  | 'warning'
  | 'danger'
  | 'info'
  | 'purple'
  | 'over_attended'
  | 'under_attended'
  | 'balanced'
  | 'insufficient_data';

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  children: React.ReactNode;
  variant?: BadgeVariant;
  className?: string;
  dot?: boolean;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'neutral',
  className,
  dot = false,
  ...props
}) => {
  const base =
    'inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold tracking-tight transition-colors select-none';

  const variants: Record<BadgeVariant, string> = {
    neutral:
      'bg-black/[0.04] dark:bg-white/[0.08] text-slate-700 dark:text-slate-300 border border-black/[0.05] dark:border-white/[0.08]',
    success:
      'bg-[#34C759]/15 text-[#248A3D] dark:text-[#30D158] border border-[#34C759]/25',
    warning:
      'bg-[#FF9500]/15 text-[#C97000] dark:text-[#FF9F0A] border border-[#FF9500]/25',
    danger:
      'bg-[#FF3B30]/15 text-[#D70015] dark:text-[#FF453A] border border-[#FF3B30]/25',
    info:
      'bg-[#007AFF]/15 text-[#007AFF] dark:text-[#0A84FF] border border-[#007AFF]/25',
    purple:
      'bg-[#AF52DE]/15 text-[#8944AB] dark:text-[#BF5AF2] border border-[#AF52DE]/25',
    over_attended:
      'bg-[#FF9500]/15 text-[#C97000] dark:text-[#FF9F0A] border border-[#FF9500]/30',
    under_attended:
      'bg-[#007AFF]/15 text-[#007AFF] dark:text-[#0A84FF] border border-[#007AFF]/30',
    balanced:
      'bg-[#34C759]/15 text-[#248A3D] dark:text-[#30D158] border border-[#34C759]/30',
    insufficient_data:
      'bg-slate-500/10 text-slate-600 dark:text-slate-400 border border-slate-500/20',
  };

  const dotColors: Record<BadgeVariant, string> = {
    neutral: 'bg-slate-400',
    success: 'bg-[#34C759]',
    warning: 'bg-[#FF9500]',
    danger: 'bg-[#FF3B30]',
    info: 'bg-[#007AFF]',
    purple: 'bg-[#AF52DE]',
    over_attended: 'bg-[#FF9500]',
    under_attended: 'bg-[#007AFF]',
    balanced: 'bg-[#34C759]',
    insufficient_data: 'bg-slate-400',
  };

  return (
    <span className={twMerge(clsx(base, variants[variant], className))} {...props}>
      {dot && <span className={clsx('w-1.5 h-1.5 rounded-full shrink-0', dotColors[variant])} />}
      {children}
    </span>
  );
};
