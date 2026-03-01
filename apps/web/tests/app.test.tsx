import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { vi } from 'vitest'

import App from '../src/App'

vi.mock('../src/lib/api', () => ({
  fetchHealth: async () => ({
    status: 'ok',
    database: 'ok',
    scheduler_running: true,
    last_runs: {},
    data_freshness_seconds: 0,
  }),
  fetchWatchlist: async () => [],
  fetchFeed: async () => [],
  fetchAsset: async () => ({
    symbol: 'AAPL',
    display_name: 'Apple',
    last_price: 0,
    change_percent: 0,
    volume: 0,
    pe_ratio: null,
    market_cap: null,
    updated_at: null,
  }),
  triggerRefresh: async () => ({ status: 'success' }),
}))

describe('App', () => {
  it('renders dashboard navigation', async () => {
    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>,
    )

    expect(await screen.findByText(/dashboard/i)).toBeTruthy()
  })
})
