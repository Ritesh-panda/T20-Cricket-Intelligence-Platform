import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
  variant?: 'glass' | 'elevated' | 'flat';
}

export const Card: React.FC<CardProps> = ({ children, className, variant = 'glass', ...props }) => {
  const variantStyles = {
    glass: 'apple-glass-card',
    elevated: 'bg-white/95 dark:bg-[#1C1F26]/90 backdrop-blur-2xl border border-black/[0.06] dark:border-white/[0.12] shadow-apple-float',
    flat: 'bg-black/[0.02] dark:bg-white/[0.03] border border-black/[0.04] dark:border-white/[0.06]',
  };

  return (
    <div
      className={twMerge(
        clsx(
          'rounded-2xl transition-all duration-200',
          variantStyles[variant],
          className
        )
      )}
      {...props}
    >
      {children}
    </div>
  );
};

export const CardHeader: React.FC<CardProps> = ({ children, className, ...props }) => {
  return (
    <div
      className={twMerge(
        clsx(
          'px-5 py-4 border-b border-black/[0.04] dark:border-white/[0.06] flex items-center justify-between',
          className
        )
      )}
      {...props}
    >
      {children}
    </div>
  );
};

export const CardTitle: React.FC<React.HTMLAttributes<HTMLHeadingElement>> = ({
  children,
  className,
  ...props
}) => {
  return (
    <h3
      className={twMerge(
        clsx(
          'text-sm sm:text-base font-semibold text-slate-900 dark:text-white tracking-tight',
          className
        )
      )}
      {...props}
    >
      {children}
    </h3>
  );
};

export const CardDescription: React.FC<React.HTMLAttributes<HTMLParagraphElement>> = ({
  children,
  className,
  ...props
}) => {
  return (
    <p
      className={twMerge(
        clsx('text-xs text-slate-500 dark:text-slate-400 mt-0.5 tracking-normal', className)
      )}
      {...props}
    >
      {children}
    </p>
  );
};

export const CardContent: React.FC<CardProps> = ({ children, className, ...props }) => {
  return (
    <div className={twMerge(clsx('p-5', className))} {...props}>
      {children}
    </div>
  );
};

export const CardFooter: React.FC<CardProps> = ({ children, className, ...props }) => {
  return (
    <div
      className={twMerge(
        clsx(
          'px-5 py-3.5 border-t border-black/[0.04] dark:border-white/[0.06] bg-black/[0.01] dark:bg-white/[0.02] rounded-b-2xl flex items-center justify-between text-xs',
          className
        )
      )}
      {...props}
    >
      {children}
    </div>
  );
};
