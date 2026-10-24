import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Menu,
  Sun,
  Moon,
  CheckCircle2,
  AlertCircle,
  Database,
  Calendar,
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

  const isConnected = !isHealthError && !isReadinessError && health?.status === 'healthy';
  const isDbReady = readiness?.database_accessible === true;

  return (
    <header className="h-16 px-4 sm:px-6 bg-white/80 dark:bg-cricket-navy-900/80 backdrop-blur-md border-b border-slate-200 dark:border-cricket-navy-800 sticky top-0 z-20 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <button
          onClick={onMenuClick}
          className="md:hidden p-2 rounded-lg text-slate-500 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-cricket-navy-800"
          aria-label="Open navigation menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        {title && (
          <h1 className="text-base sm:text-lg font-semibold tracking-tight text-slate-900 dark:text-slate-100">
            {title}
          </h1>
        )}
      </div>

      <div className="flex items-center gap-2 sm:gap-4">
        {/* Active Tournament Indicator */}
        <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 dark:bg-cricket-navy-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-cricket-navy-700">
          <Calendar className="w-3.5 h-3.5 text-emerald-500" />
          <span>T20 World Cup 2024</span>
        </div>

        {/* API Connectivity Status Indicator */}
        <div
          className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono font-medium border transition-colors"
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
              <span className="w-2 h-2 rounded-full bg-emerald-500 ring-2 ring-emerald-500/30" />
              <span className="hidden sm:inline text-emerald-700 dark:text-emerald-400 font-sans">
                API Online
              </span>
            </>
          ) : (
            <>
              <span className="w-2 h-2 rounded-full bg-rose-500 ring-2 ring-rose-500/30" />
              <span className="hidden sm:inline text-rose-700 dark:text-rose-400 font-sans">
                API Offline
              </span>
            </>
          )}
        </div>

        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          className="p-2 rounded-lg text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-100 hover:bg-slate-100 dark:hover:bg-cricket-navy-800 transition-colors"
          title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
          aria-label="Toggle visual theme"
        >
          {theme === 'dark' ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4" />}
        </button>
      </div>
    </header>
  );
};
