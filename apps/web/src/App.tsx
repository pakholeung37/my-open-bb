import { Navigate, Route, Routes } from 'react-router-dom'

import { Layout } from './components/layout'
import { AssetDetailPage } from './pages/asset-detail'
import { DashboardPage } from './pages/dashboard'
import { FeedStreamPage } from './pages/feed-stream'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<DashboardPage />} />
        <Route path="feed" element={<FeedStreamPage />} />
        <Route path="assets/:symbol" element={<AssetDetailPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}
