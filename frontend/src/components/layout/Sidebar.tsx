import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Trophy,
  Users,
  Newspaper,
  Network,
  Scale,
  Database,
  Activity,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  X,
} from 'lucide-react';
import { clsx } from 'clsx';

interface SidebarProps {
  collapsed: boolean;
  setCollapsed: (val: boolean) => void;
  mobileOpen: boolean;
  setMobileOpen: (val: boolean) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  collapsed,
  setCollapsed,
  mobileOpen,
  setMobileOpen,
}) => {
  const navItems = [
    { name: 'Overview', to: '/', icon: LayoutDashboard },
    { name: 'Matches', to: '/matches', icon: Trophy },
    { name: 'Players', to: '/players', icon: Users },
    { name: 'Media Intelligence', to: '/media', icon: Newspaper },
    { name: 'Topics & Narratives', to: '/narratives', icon: Network },
    { name: 'APDI Explorer', to: '/apdi', icon: Scale, highlight: true },
    { name: 'Data Sources', to: '/sources', icon: Database },
    { name: 'System Health', to: '/health', icon: Activity },
  ];

  const sidebarContent = (
    <div className="flex flex-col h-full bg-white dark:bg-cricket-navy-900 border-r border-slate-200 dark:border-cricket-navy-800 text-slate-800 dark:text-slate-200 select-none">
      {/* Brand Header */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-slate-100 dark:border-cricket-navy-800">
        <div className="flex items-center gap-3 overflow-hidden">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-700 flex items-center justify-center text-white font-bold shadow-md shadow-emerald-500/20 shrink-0">
            <span className="text-sm font-mono tracking-tighter">T20</span>
          </div>
          {!collapsed && (
            <div className="flex flex-col min-w-0">
              <span className="text-sm font-semibold tracking-tight truncate text-slate-900 dark:text-slate-100">
                Cricket Intel
              </span>
              <span className="text-[10px] font-mono text-emerald-600 dark:text-emerald-400 font-medium tracking-wide uppercase truncate">
                Research Platform
              </span>
            </div>
          )}
        </div>

        {/* Mobile close button */}
        <button
          onClick={() => setMobileOpen(false)}
          className="md:hidden p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-lg"
          aria-label="Close menu"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Nav List */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            onClick={() => setMobileOpen(false)}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs sm:text-sm font-medium transition-all group relative',
                isActive
                  ? 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 font-semibold'
                  : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-cricket-navy-800 hover:text-slate-900 dark:hover:text-slate-200',
                item.highlight && !isActive && 'text-amber-600 dark:text-amber-400'
              )
            }
          >
            {({ isActive }) => (
              <>
                <item.icon
                  className={clsx(
                    'w-4 h-4 shrink-0 transition-transform duration-200',
                    isActive
                      ? 'text-emerald-600 dark:text-emerald-400'
                      : 'text-slate-400 dark:text-slate-500 group-hover:text-slate-700 dark:group-hover:text-slate-300',
                    item.highlight && !isActive && 'text-amber-500 dark:text-amber-400'
                  )}
                />
                {!collapsed && <span className="truncate">{item.name}</span>}
                {item.highlight && !collapsed && (
                  <span className="ml-auto inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
                    Core
                  </span>
                )}
                {isActive && (
                  <span className="absolute left-0 top-2 bottom-2 w-1 bg-emerald-500 rounded-r-full" />
                )}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Methodology Tag */}
      {!collapsed && (
        <div className="p-3 m-3 rounded-xl bg-slate-50 dark:bg-cricket-navy-950/70 border border-slate-200/70 dark:border-cricket-navy-800">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-800 dark:text-slate-200">
            <Sparkles className="w-3.5 h-3.5 text-emerald-500" />
            <span>APDI Framework</span>
          </div>
          <p className="mt-1 text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
            Measures media attention vs objective performance across role cohorts.
          </p>
        </div>
      )}

      {/* Collapse Desktop Footer */}
      <div className="hidden md:flex items-center justify-between p-3 border-t border-slate-100 dark:border-cricket-navy-800">
        {!collapsed && (
          <span className="text-[11px] font-mono text-slate-400 dark:text-slate-500">
            Phase 6C v1.0.0
          </span>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-cricket-navy-800 ml-auto transition-colors"
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop sidebar */}
      <aside
        className={clsx(
          'hidden md:block shrink-0 transition-all duration-300 ease-in-out h-screen sticky top-0 z-30',
          collapsed ? 'w-16' : 'w-64'
        )}
      >
        {sidebarContent}
      </aside>

      {/* Mobile drawer backdrop */}
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-slate-900/60 dark:bg-black/80 backdrop-blur-sm z-40 md:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Mobile drawer */}
      <div
        className={clsx(
          'fixed inset-y-0 left-0 w-72 z-50 md:hidden transform transition-transform duration-300 ease-in-out',
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        {sidebarContent}
      </div>
    </>
  );
};
