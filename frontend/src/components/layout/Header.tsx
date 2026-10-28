import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Menu,
  Sun,
  Moon,
  Calendar,
  Sparkles,
} from 'lucide-react';
import { useTheme } from '../../context/ThemeContext';
import { api } from '../../lib/api';

interface HeaderProps {
  onMenuClick: () => void;
  title?: string;
}

export const Header: React.FC<HeaderProps> = ({ onMenuClick, title }) => {
  const { theme, toggleTheme } = useTheme();

  // Query API readiness to display genuine live status
  const { data: health, isError: isHealthError, isLoading: isHealthLoading } = useQuery({
    queryKey: ['apiHealth'],
    queryFn: api.getHealth,
    refetchInterval: 30000,
    retry: 1,
  });

  const { data: readiness, isError: isReadinessError } = useQuery({
    queryKey: ['apiReadiness'],
    queryFn: api.getReadiness,
    refetchInterval: 30000,
    retry: 1,
  });

  const { data: status } = useQuery({
    queryKey: ['systemStatus'],
    queryFn: () => api.getStatus(),
    staleTime: 60000,
  });

  const isConnected = !isHealthError && !isReadinessError && health?.status === 'healthy';
  const isDbReady = readiness?.database_accessible === true;

  return (
    <header className="h-16 px-4 sm:px-6 apple-glass sticky top-0 z-20 flex items-center justify-between border-b border-black/[0.06] dark:border-white/[0.08] transition-colors">
      <div className="flex items-center gap-3">
        <button
          onClick={onMenuClick}
          className="md:hidden p-2 rounded-xl text-slate-500 hover:text-slate-800 dark:hover:text-slate-100 hover:bg-black/[0.04] dark:hover:bg-white/[0.06] transition-colors"
          aria-label="Open navigation menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        {title && (
          <div className="flex items-center gap-2">
            <h1 className="text-base sm:text-lg font-semibold tracking-tight text-slate-900 dark:text-white">
              {title}
            </h1>
          </div>
        )}
      </div>

      <div className="flex items-center gap-2 sm:gap-3">
        {/* Active Tournament Dynamic Capsule */}
        <div className="hidden sm:flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-black/[0.03] dark:bg-white/[0.05] text-slate-700 dark:text-slate-300 border border-black/[0.06] dark:border-white/[0.08] shadow-[inset_0_1px_1px_rgba(255,255,255,0.4)]">
          <Calendar className="w-3.5 h-3.5 text-[#007AFF]" />
          <span className="tracking-tight">{status?.tournament || "ICC Men's T20 World Cup"}</span>
        </div>

        {/* API Connectivity Status Capsule (Apple Dynamic Island style) */}
        <div
          className={`flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium border shadow-[inset_0_1px_1px_rgba(255,255,255,0.3)] transition-all ${
            isConnected && isDbReady
              ? 'bg-emerald-500/10 dark:bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 border-emerald-500/20'
              : isHealthLoading
              ? 'bg-amber-500/10 text-amber-700 dark:text-amber-300 border-amber-500/20'
              : 'bg-rose-500/10 text-rose-700 dark:text-rose-300 border-rose-500/20'
          }`}
          title={
            isConnected
              ? `FastAPI ${health?.version} (Tables: ${readiness?.database_tables_count || 0})`
              : 'Backend disconnected. Ensure FastAPI is running on http://127.0.0.1:8000'
          }
        >
          {isHealthLoading ? (
            <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping" />
          ) : isConnected && isDbReady ? (
            <>
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#34C759] opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-[#34C759]"></span>
              </span>
              <span className="hidden sm:inline font-medium tracking-tight">API Online</span>
            </>
          ) : (
            <>
              <span className="w-2 h-2 rounded-full bg-[#FF3B30] ring-2 ring-rose-500/30" />
              <span className="hidden sm:inline font-medium tracking-tight">API Offline</span>
            </>
          )}
        </div>

        {/* Apple Segmented Theme Toggle Pill */}
        <button
          onClick={toggleTheme}
          className="p-2 rounded-full text-slate-600 dark:text-slate-300 bg-black/[0.04] dark:bg-white/[0.06] hover:bg-black/[0.08] dark:hover:bg-white/[0.12] border border-black/[0.06] dark:border-white/[0.08] shadow-sm hover:scale-105 active:scale-95 transition-all"
          title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
          aria-label="Toggle visual theme"
        >
          {theme === 'dark' ? (
            <Sun className="w-4 h-4 text-[#FF9500] transition-transform duration-300 rotate-0 hover:rotate-45" />
          ) : (
            <Moon className="w-4 h-4 text-[#5856D6] transition-transform duration-300 rotate-0 hover:-rotate-12" />
          )}
        </button>
      </div>
    </header>
  );
};
