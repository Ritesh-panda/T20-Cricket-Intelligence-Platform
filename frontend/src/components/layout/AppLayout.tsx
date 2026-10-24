import React, { useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';

export const AppLayout: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();

  const getPageTitle = (pathname: string) => {
    switch (pathname) {
      case '/':
      case '/overview':
        return 'Research Overview';
      case '/matches':
        return 'Matches Explorer';
      case '/players':
        return 'Player Explorer';
      case '/media':
        return 'Media Intelligence & Framing';
      case '/narratives':
        return 'Topics & Narrative Intelligence';
      case '/apdi':
        return 'Attention vs Performance Discrepancy Index (APDI)';
      case '/sources':
        return 'Data Sources & Pipeline Observability';
      case '/health':
        return 'System Health & Analytical Readiness';
      default:
        return 'T20 Cricket Intelligence';
    }
  };

  return (
    <div className="flex min-h-screen bg-slate-50 dark:bg-cricket-navy-950 text-slate-900 dark:text-slate-100 font-sans transition-colors">
      <Sidebar
        collapsed={collapsed}
        setCollapsed={setCollapsed}
        mobileOpen={mobileOpen}
        setMobileOpen={setMobileOpen}
      />

      <div className="flex-1 flex flex-col min-w-0">
        <Header
          onMenuClick={() => setMobileOpen(true)}
          title={getPageTitle(location.pathname)}
        />
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
