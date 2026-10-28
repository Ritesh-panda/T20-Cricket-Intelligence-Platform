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
  const navSections = [
    {
      label: 'Core Intelligence',
      items: [
        { name: 'Overview', to: '/', icon: LayoutDashboard, color: 'text-[#007AFF] bg-[#007AFF]/10' },
        { name: 'Matches', to: '/matches', icon: Trophy, color: 'text-[#FF9500] bg-[#FF9500]/10' },
        { name: 'Players', to: '/players', icon: Users, color: 'text-[#34C759] bg-[#34C759]/10' },
      ],
    },
    {
      label: 'Analytics & NLP',
      items: [
        { name: 'APDI Explorer', to: '/apdi', icon: Scale, highlight: true, color: 'text-[#AF52DE] bg-[#AF52DE]/10' },
        { name: 'Media Intelligence', to: '/media', icon: Newspaper, color: 'text-[#FF3B30] bg-[#FF3B30]/10' },
        { name: 'Topics & Narratives', to: '/narratives', icon: Network, color: 'text-[#5856D6] bg-[#5856D6]/10' },
      ],
    },
    {
      label: 'Platform Diagnostics',
      items: [
        { name: 'Data Sources', to: '/sources', icon: Database, color: 'text-[#5AC8FA] bg-[#5AC8FA]/10' },
        { name: 'System Health', to: '/health', icon: Activity, color: 'text-[#34C759] bg-[#34C759]/10' },
      ],
    },
  ];

  const sidebarContent = (
    <div className="flex flex-col h-full bg-white/75 dark:bg-[#12141A]/80 backdrop-blur-2xl border-r border-black/[0.06] dark:border-white/[0.08] text-slate-800 dark:text-slate-200 select-none transition-all duration-200">
      {/* Apple Studio Brand Header */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-black/[0.05] dark:border-white/[0.08]">
        <div className="flex items-center gap-3 overflow-hidden">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-[#007AFF] to-[#5856D6] flex items-center justify-center text-white font-bold shadow-sm shadow-[#007AFF]/25 shrink-0">
            <span className="text-[11px] font-bold tracking-tight">T20</span>
          </div>

          {!collapsed && (
            <div className="flex flex-col min-w-0">
              <span className="text-[13px] font-semibold tracking-tight truncate text-slate-900 dark:text-white">
                Cricket Intelligence
              </span>
              <span className="text-[10px] text-slate-400 dark:text-slate-500 font-medium tracking-wider uppercase truncate">
                APDI Research Studio
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

      {/* Nav List with Apple Category Headers */}
      <nav className="flex-1 px-3 py-4 space-y-5 overflow-y-auto">
        {navSections.map((section, idx) => (
          <div key={idx} className="space-y-1">
            {!collapsed && (
              <div className="px-3 pb-1 text-[10px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
                {section.label}
              </div>
            )}
            <div className="space-y-0.5">
              {section.items.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  onClick={() => setMobileOpen(false)}
                  className={({ isActive }) =>
                    clsx(
                      'flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs sm:text-[13px] font-medium transition-all duration-150 group relative tracking-tight',
                      isActive
                        ? 'bg-[#007AFF] text-white font-medium shadow-xs'
                        : 'text-slate-600 dark:text-slate-400 hover:bg-black/[0.04] dark:hover:bg-white/[0.06] hover:text-slate-900 dark:hover:text-white'
                    )
                  }
                >
                  {({ isActive }) => (
                    <>
                      <div
                        className={clsx(
                          'w-6 h-6 rounded-lg flex items-center justify-center shrink-0 transition-transform duration-150 group-hover:scale-105',
                          isActive ? 'bg-white/20 text-white' : item.color
                        )}
                      >
                        <item.icon className="w-3.5 h-3.5" />
                      </div>

                      {!collapsed && (
                        <span className="truncate flex-1 font-medium">{item.name}</span>
                      )}

                      {item.highlight && !collapsed && (
                        <span
                          className={clsx(
                            'text-[9px] font-bold uppercase px-1.5 py-0.5 rounded-full shrink-0 border',
                            isActive
                              ? 'bg-white/20 text-white border-white/30'
                              : 'bg-[#AF52DE]/15 text-[#AF52DE] dark:text-[#BF5AF2] border-[#AF52DE]/25'
                          )}
                        >
                          Core
                        </span>
                      )}
                    </>
                  )}
                </NavLink>
              ))}
            </div>
          </div>
        ))}
      </nav>

      {/* Bottom Status Pill & Collapse Toggle */}
      <div className="p-3 border-t border-black/[0.05] dark:border-white/[0.08] flex items-center justify-between text-xs text-slate-400">
        {!collapsed && (
          <div className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-black/[0.03] dark:bg-white/[0.04] border border-black/[0.04] dark:border-white/[0.06] max-w-[190px]">
            <span className="w-1.5 h-1.5 rounded-full bg-[#34C759] shrink-0" />
            <span className="text-[10px] font-medium text-slate-600 dark:text-slate-400 truncate">
              ICC T20 WC '24 • Verified
            </span>
          </div>
        )}

        <button
          onClick={() => setCollapsed(!collapsed)}
          className="hidden md:flex p-1.5 rounded-lg text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-black/[0.04] dark:hover:bg-white/[0.06] transition-colors ml-auto"
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? (
            <ChevronRight className="w-4 h-4" />
          ) : (
            <ChevronLeft className="w-4 h-4" />
          )}
        </button>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop sidebar */}
      <aside
        className={clsx(
          'hidden md:block shrink-0 transition-all duration-200 h-screen sticky top-0 z-30',
          collapsed ? 'w-20' : 'w-64'
        )}
      >
        {sidebarContent}
      </aside>

      {/* Mobile drawer overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm md:hidden animate-fade-in"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Mobile slide-over drawer */}
      <div
        className={clsx(
          'fixed inset-y-0 left-0 z-50 w-72 md:hidden transition-transform duration-200 ease-in-out',
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        {sidebarContent}
      </div>
    </>
  );
};
