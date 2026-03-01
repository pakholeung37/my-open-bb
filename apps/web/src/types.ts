export type FeedItem = {
  id: number
  source_id: string
  title: string
  summary: string | null
  url: string
  published_at: string | null
  symbol: string | null
  tags: string[]
}

export type WatchlistQuote = {
  symbol: string
  display_name: string
  price: number | null
  change_percent: number | null
  volume: number | null
  fetched_at: string | null
}

export type AssetOverview = {
  symbol: string
  display_name: string | null
  last_price: number | null
  change_percent: number | null
  volume: number | null
  pe_ratio: number | null
  market_cap: number | null
  updated_at: string | null
}

export type Health = {
  status: string
  database: string
  scheduler_running: boolean
  last_runs: Record<
    string,
    {
      status: string
      message: string | null
      started_at: string
      finished_at: string
    }
  >
  data_freshness_seconds: number | null
}
