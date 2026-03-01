import type { AssetOverview, FeedItem, Health, WatchlistQuote } from '../types'

const baseUrl = import.meta.env.VITE_API_BASE_URL ?? '/api/v1'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${baseUrl}${path}`, init)
  if (!response.ok) {
    const detail = await response.text()
    throw new Error(`${response.status} ${detail}`)
  }
  return response.json() as Promise<T>
}

export function fetchHealth() {
  return request<Health>('/health')
}

export function fetchWatchlist() {
  return request<WatchlistQuote[]>('/market/watchlist')
}

export function fetchFeed(
  params: {
    sourceId?: string
    symbol?: string
    tag?: string
    limit?: number
  } = {},
) {
  const query = new URLSearchParams()
  if (params.sourceId) query.set('source_id', params.sourceId)
  if (params.symbol) query.set('symbol', params.symbol.toUpperCase())
  if (params.tag) query.set('tag', params.tag)
  query.set('limit', String(params.limit ?? 50))
  return request<FeedItem[]>(`/feed?${query.toString()}`)
}

export function fetchAsset(symbol: string) {
  return request<AssetOverview>(`/assets/${symbol.toUpperCase()}`)
}

export function triggerRefresh() {
  return request<{ status: string }>('/refresh', { method: 'POST' })
}
