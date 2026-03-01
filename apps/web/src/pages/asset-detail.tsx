import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { fetchAsset, fetchFeed } from '../lib/api'
import type { AssetOverview, FeedItem } from '../types'

export function AssetDetailPage() {
  const { symbol = '' } = useParams()
  const [asset, setAsset] = useState<AssetOverview | null>(null)
  const [items, setItems] = useState<FeedItem[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function load() {
      try {
        const [assetPayload, feedPayload] = await Promise.all([
          fetchAsset(symbol),
          fetchFeed({ symbol, limit: 20 }),
        ])
        setAsset(assetPayload)
        setItems(feedPayload)
        setError(null)
      } catch (err) {
        setError((err as Error).message)
      }
    }

    if (symbol) {
      load()
    }
  }, [symbol])

  return (
    <section className="card">
      <div className="card-header">
        <h2>Asset Detail: {symbol.toUpperCase()}</h2>
        <Link className="plain-link" to="/">
          Back to Dashboard
        </Link>
      </div>
      {error ? <p className="error">{error}</p> : null}

      <div className="metrics">
        <div>
          <span className="muted">Price</span>
          <p>{asset?.last_price?.toFixed(2) ?? '-'}</p>
        </div>
        <div>
          <span className="muted">Change %</span>
          <p>{asset?.change_percent?.toFixed(2) ?? '-'}</p>
        </div>
        <div>
          <span className="muted">PE</span>
          <p>{asset?.pe_ratio?.toFixed(2) ?? '-'}</p>
        </div>
        <div>
          <span className="muted">Market Cap</span>
          <p>{asset?.market_cap?.toLocaleString() ?? '-'}</p>
        </div>
      </div>

      <h3>Related Feed</h3>
      <ul className="feed-list">
        {items.map((item) => (
          <li key={item.id}>
            <a href={item.url} target="_blank" rel="noreferrer">
              {item.title}
            </a>
            <div className="muted">{item.source_id}</div>
          </li>
        ))}
      </ul>
    </section>
  )
}
