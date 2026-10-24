import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from './context/ThemeContext';
import { AppLayout } from './components/layout/AppLayout';

// Features
import { OverviewPage } from './features/overview/OverviewPage';
import { MatchesPage } from './features/matches/MatchesPage';
import { PlayersPage } from './features/players/PlayersPage';
import { MediaPage } from './features/media/MediaPage';
import { NarrativesPage } from './features/narratives/NarrativesPage';
import { APDIPage } from './features/apdi/APDIPage';
import { SourcesPage } from './features/sources/SourcesPage';
import { HealthPage } from './features/health/HealthPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60, // 1 minute
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<AppLayout />}>
              <Route index element={<OverviewPage />} />
              <Route path="overview" element={<OverviewPage />} />
              <Route path="matches" element={<MatchesPage />} />
              <Route path="players" element={<PlayersPage />} />
              <Route path="media" element={<MediaPage />} />
              <Route path="narratives" element={<NarrativesPage />} />
              <Route path="apdi" element={<APDIPage />} />
              <Route path="sources" element={<SourcesPage />} />
              <Route path="health" element={<HealthPage />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </ThemeProvider>
    </QueryClientProvider>
  );
};

export default App;
