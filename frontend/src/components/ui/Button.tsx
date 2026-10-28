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
  const base =
    'inline-flex items-center justify-center font-medium transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#007AFF]/40 disabled:opacity-40 disabled:pointer-events-none rounded-xl active:scale-[0.98] tracking-tight select-none';

  const variants = {
    primary:
      'bg-gradient-to-b from-[#0A84FF] to-[#007AFF] hover:from-[#007AFF] hover:to-[#0062CC] text-white shadow-sm shadow-[#007AFF]/25 border border-white/20 font-semibold',
    secondary:
      'bg-black/[0.05] dark:bg-white/[0.08] text-slate-800 dark:text-slate-100 hover:bg-black/[0.08] dark:hover:bg-white/[0.12] border border-black/[0.04] dark:border-white/[0.06]',
    outline:
      'border border-black/[0.12] dark:border-white/[0.14] bg-white/50 dark:bg-white/[0.03] text-slate-700 dark:text-slate-200 hover:bg-black/[0.04] dark:hover:bg-white/[0.06] backdrop-blur-sm',
    ghost:
      'bg-transparent text-slate-700 dark:text-slate-300 hover:bg-black/[0.04] dark:hover:bg-white/[0.06]',
    danger:
      'bg-gradient-to-b from-[#FF453A] to-[#FF3B30] text-white hover:from-[#FF3B30] hover:to-[#E0241A] shadow-sm shadow-[#FF3B30]/25 font-semibold',
  };

  const sizes = {
    sm: 'text-xs px-2.5 py-1.5 gap-1.5',
    md: 'text-xs sm:text-sm px-3.5 py-1.5 sm:py-2 gap-2',
    lg: 'text-sm sm:text-base px-4 py-2 sm:py-2.5 gap-2.5',
  };

  return (
    <button
      className={twMerge(clsx(base, variants[variant], sizes[size], className))}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading && (
        <svg
          className="animate-spin -ml-0.5 h-3.5 w-3.5 text-current"
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
