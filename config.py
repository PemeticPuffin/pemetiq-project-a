"""Global constants, model config, and API endpoints."""

# Claude model
CLAUDE_MODEL = "claude-sonnet-4-6"
CLAUDE_MAX_TOKENS_PER_SOURCE = 4096
CLAUDE_MAX_TOKENS_SYNTHESIS = 8192
CLAUDE_TEMPERATURE = 0.3

# SEC EDGAR
SEC_BASE_URL = "https://data.sec.gov"
SEC_SEARCH_URL = "https://efts.sec.gov/LATEST/search-index"
SEC_COMPANY_SEARCH_URL = "https://efts.sec.gov/LATEST/search-index?q=%22{query}%22&dateRange=custom&startdt=2020-01-01&enddt=2099-01-01&forms=10-K"
SEC_USER_AGENT = "Pemetiq Cadillaq hello@pemetiq.com"
SEC_RATE_LIMIT_RPS = 10

# Finnhub
NEWS_LOOKBACK_DAYS = 30

# Timeouts and retries
REQUEST_TIMEOUT = 30
MAX_RETRIES = 2
