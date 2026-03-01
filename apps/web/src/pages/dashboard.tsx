import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import {
  fetchFeed,
  fetchHealth,
  fetchWatchlist,
  triggerRefresh,
} from '../lib/api'
import type { FeedItem, Health, WatchlistQuote } from '../types'

export function DashboardPage() {
  const [health, setHealth] = useState<Health | null>(null)
  const [watchlist, setWatchlist] = useState<WatchlistQuote[]>([])
  const [latestFeed, setLatestFeed] = useState<FeedItem[]>([])
  const [error, setError] = useState<string | null>(null)

  const freshnessLabel = useMemo(() => {
    if (
      !health?.data_freshness_seconds &&
      health?.data_freshness_seconds !== 0
    ) {
      return 'unknown'
    }
    const mins = Math.floor(health.data_freshness_seconds / 60)
    return `${mins}m ago`
  }, [health])

  const load = useCallback(async () => {
    try {
      const [healthPayload, watchlistPayload, feedPayload] = await Promise.all([
        fetchHealth(),
        fetchWatchlist(),
        fetchFeed({ limit: 10 }),
      ])
      setHealth(healthPayload)
      setWatchlist(watchlistPayload)
      setLatestFeed(feedPayload)
      setError(null)
    } catch (err) {
      setError((err as Error).message)
    }
  }, [])

  useEffect(() => {
    void load()
    const timer = window.setInterval(load, 60_000)
    return () => window.clearInterval(timer)
  }, [load])

  return (
    <section className="grid">
      <article className="card">
        <div className="card-header">
          <h2>System Health</h2>
          <button
            className="btn"
            onClick={async () => {
              try {
                await triggerRefresh()
                await load()
              } catch (err) {
                setError((err as Error).message)
              }
            }}
          >
            Refresh Now
          </button>
        </div>
        <p>Status: {health?.status ?? 'loading'}</p>
        <p>Scheduler: {health?.scheduler_running ? 'running' : 'stopped'}</p>
        <p>Data Freshness: {freshnessLabel}</p>
        {error ? <p className="error">{error}</p> : null}
      </article>

      <article className="card">
        <h2>Watchlist Snapshot</h2>
        <table className="table">
          <thead>
            <tr>
              <th>Symbol</th>
              <th>Price</th>
              <th>Change %</th>
              <th>Volume</th>
            </tr>
          </thead>
          <tbody>
            {watchlist.map((row) => (
              <tr key={row.symbol}>
                <td>
                  <Link to={`/assets/${row.symbol}`}>{row.symbol}</Link>
                </td>
                <td>{row.price?.toFixed(2) ?? '-'}</td>
                <td>{row.change_percent?.toFixed(2) ?? '-'}</td>
                <td>{row.volume?.toLocaleString() ?? '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </article>

      <article className="card">
        <div className="card-header">
          <h2>Latest Feed</h2>
          <Link className="plain-link" to="/feed">
            See all
          </Link>
        </div>
        <ul className="feed-list">
          {latestFeed.map((item) => (
            <li key={item.id}>
              <a href={item.url} target="_blank" rel="noreferrer">
                {item.title}
              </a>
              <div className="muted">
                {item.source_id} | {item.symbol ?? 'n/a'}
              </div>
            </li>
          ))}
        </ul>
      </article>
    </section>
  )
}
