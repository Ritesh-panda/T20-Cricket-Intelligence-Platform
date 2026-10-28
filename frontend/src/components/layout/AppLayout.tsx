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
    <div className="relative flex min-h-screen bg-[#F5F5F7] dark:bg-[#0B0D11] text-slate-900 dark:text-slate-100 font-sans transition-colors selection:bg-[#007AFF]/20 selection:text-[#007AFF]">
      {/* Apple Ambient Atmospheric Glows */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden z-0">
        <div className="absolute -top-[20%] -right-[10%] w-[600px] h-[600px] rounded-full bg-gradient-to-br from-[#007AFF]/10 to-[#5856D6]/5 dark:from-[#007AFF]/15 dark:to-[#5856D6]/10 blur-3xl" />
        <div className="absolute top-[40%] -left-[10%] w-[500px] h-[500px] rounded-full bg-gradient-to-tr from-[#34C759]/5 to-[#007AFF]/5 dark:from-[#34C759]/10 dark:to-[#007AFF]/5 blur-3xl" />
      </div>

      <Sidebar
        collapsed={collapsed}
        setCollapsed={setCollapsed}
        mobileOpen={mobileOpen}
        setMobileOpen={setMobileOpen}
      />

      <div className="flex-1 flex flex-col min-w-0 relative z-10">
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

