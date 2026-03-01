import { type FormEvent, useCallback, useEffect, useState } from 'react'

import { fetchFeed } from '../lib/api'
import type { FeedItem } from '../types'

export function FeedStreamPage() {
  const [items, setItems] = useState<FeedItem[]>([])
  const [symbol, setSymbol] = useState('')
  const [tag, setTag] = useState('')
  const [sourceId, setSourceId] = useState('')
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(
    async (params?: { symbol?: string; tag?: string; sourceId?: string }) => {
      const nextSymbol = params?.symbol ?? symbol
      const nextTag = params?.tag ?? tag
      const nextSourceId = params?.sourceId ?? sourceId

      try {
        const payload = await fetchFeed({
          symbol: nextSymbol || undefined,
          tag: nextTag || undefined,
          sourceId: nextSourceId || undefined,
        })
        setItems(payload)
        setError(null)
      } catch (err) {
        setError((err as Error).message)
      }
    },
    [symbol, tag, sourceId],
  )

  useEffect(() => {
    void load({ symbol: '', tag: '', sourceId: '' })
  }, [load])

  function onSubmit(event: FormEvent) {
    event.preventDefault()
    void load()
  }

  return (
    <section className="card">
      <h2>Feed Stream</h2>
      <form className="filters" onSubmit={onSubmit}>
        <input
          value={symbol}
          onChange={(e) => setSymbol(e.target.value)}
          placeholder="Symbol (AAPL)"
        />
        <input
          value={tag}
          onChange={(e) => setTag(e.target.value)}
          placeholder="Tag (macro)"
        />
        <input
          value={sourceId}
          onChange={(e) => setSourceId(e.target.value)}
          placeholder="Source (reuters_business)"
        />
        <button className="btn" type="submit">
          Apply
        </button>
      </form>

      {error ? <p className="error">{error}</p> : null}

      <ul className="feed-list">
        {items.map((item) => (
          <li key={item.id}>
            <a href={item.url} target="_blank" rel="noreferrer">
              {item.title}
            </a>
            <p>{item.summary}</p>
            <div className="muted">
              {item.source_id} | {item.symbol ?? 'n/a'} | {item.tags.join(', ')}
            </div>
          </li>
        ))}
      </ul>
    </section>
  )
}
