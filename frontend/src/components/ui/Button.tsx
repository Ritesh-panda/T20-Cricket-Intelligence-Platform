import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'secondary',
  size = 'md',
  isLoading = false,
  className,
  disabled,
  ...props
}) => {
  const base = 'inline-flex items-center justify-center font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cricket-pitch disabled:opacity-50 disabled:pointer-events-none rounded-lg';

  const variants = {
    primary: 'bg-cricket-pitch text-white hover:bg-emerald-600 active:bg-emerald-700 shadow-sm shadow-emerald-950/20',
    secondary: 'bg-slate-200 dark:bg-cricket-navy-800 text-slate-800 dark:text-slate-100 hover:bg-slate-300 dark:hover:bg-cricket-navy-700',
    outline: 'border border-slate-300 dark:border-cricket-navy-700 bg-transparent text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-cricket-navy-800',
    ghost: 'bg-transparent text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-cricket-navy-800',
    danger: 'bg-rose-600 text-white hover:bg-rose-700',
  };

  const sizes = {
    sm: 'text-xs px-2.5 py-1.5 gap-1.5',
    md: 'text-sm px-3.5 py-2 gap-2',
    lg: 'text-base px-4 py-2.5 gap-2.5',
  };

  return (
    <button
      className={twMerge(clsx(base, variants[variant], sizes[size], className))}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading && (
        <svg
          className="animate-spin -ml-0.5 h-4 w-4 text-current"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
      )}
      {children}
    </button>
  );
};
