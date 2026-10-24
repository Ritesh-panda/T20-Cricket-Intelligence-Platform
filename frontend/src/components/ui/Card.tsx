import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
}

export const Card: React.FC<CardProps> = ({ children, className, ...props }) => {
  return (
    <div
      className={twMerge(
        clsx(
          'rounded-xl border border-slate-200 dark:border-cricket-navy-800 bg-white dark:bg-cricket-navy-900 shadow-sm transition-all',
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
          'px-5 py-4 border-b border-slate-100 dark:border-cricket-navy-800 flex items-center justify-between',
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
          'text-base font-semibold text-slate-900 dark:text-slate-100 tracking-tight',
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
        clsx('text-xs text-slate-500 dark:text-slate-400 mt-0.5', className)
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
          'px-5 py-3 border-t border-slate-100 dark:border-cricket-navy-800 bg-slate-50/50 dark:bg-cricket-navy-900/50 rounded-b-xl',
          className
        )
      )}
      {...props}
    >
      {children}
    </div>
  );
};
