import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

type BadgeVariant =
  | 'neutral'
  | 'success'
  | 'warning'
  | 'danger'
  | 'info'
  | 'over_attended'
  | 'under_attended'
  | 'balanced'
  | 'insufficient_data';

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  children: React.ReactNode;
  variant?: BadgeVariant;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'neutral',
  className,
  ...props
}) => {
  const variantStyles: Record<BadgeVariant, string> = {
    neutral: 'bg-slate-100 text-slate-700 dark:bg-cricket-navy-800 dark:text-slate-300 border-slate-200 dark:border-cricket-navy-700',
    success: 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-500/20',
    warning: 'bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-500/20',
    danger: 'bg-rose-500/10 text-rose-700 dark:text-rose-400 border-rose-500/20',
    info: 'bg-sky-500/10 text-sky-700 dark:text-sky-400 border-sky-500/20',
    over_attended: 'bg-amber-500/15 text-amber-700 dark:text-amber-300 border-amber-500/30 font-medium',
    under_attended: 'bg-indigo-500/15 text-indigo-700 dark:text-indigo-300 border-indigo-500/30 font-medium',
    balanced: 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 border-emerald-500/30 font-medium',
    insufficient_data: 'bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border-slate-300 dark:border-slate-700 italic font-mono text-[10px]',
  };

  return (
    <span
      className={twMerge(
        clsx(
          'inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border transition-colors',
          variantStyles[variant],
          className
        )
      )}
      {...props}
    >
      {children}
    </span>
  );
};
