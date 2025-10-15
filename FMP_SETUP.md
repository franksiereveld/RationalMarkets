# Financial Modeling Prep (FMP) API Setup

## Overview

RationalMarkets uses Financial Modeling Prep (FMP) as the primary data source for real-time stock market data, with yfinance as a fallback for free delayed data.

## API Key Configuration

### Railway Environment Variable

Add the following environment variable in your Railway project:

```
FMP_API_KEY=rQXOZ2SD6TzS62yPV91UFoyxGzCaWxPA
```

### How to Add in Railway

1. Go to Railway Dashboard
2. Select your RationalMarkets project
3. Click on "Variables" tab
4. Click "New Variable"
5. Add:
   - **Variable**: `FMP_API_KEY`
   - **Value**: `rQXOZ2SD6TzS62yPV91UFoyxGzCaWxPA`
6. Click "Add"
7. Railway will automatically redeploy

## Data Source Fallback Chain

The application uses a smart fallback system:

1. **Primary**: FMP API (real-time data)
   - Requires `FMP_API_KEY` environment variable
   - Provides real-time stock prices, financials, news
   - Free tier: 250 requests/day

2. **Fallback**: yfinance (delayed data)
   - No API key required
   - Free unlimited requests (with rate limiting)
   - Delayed data (15-20 minutes)

3. **Last Resort**: Demo/Mock data
   - Used when both APIs fail
   - Provides realistic sample data for testing

## Testing

After adding the FMP API key, test the integration:

```bash
curl -X POST https://your-app.railway.app/api/analyze-trade \
  -H "Content-Type: application/json" \
  -d '{
    "tradeName": "Test FMP",
    "tradeDescription": "Long AAPL, short TSLA"
  }'
```

Look for real stock data in the response (prices, P/E ratios, market cap, etc.)

## API Limits

### FMP Free Tier
- 250 API calls per day
- Real-time data
- Historical data
- Company financials
- Stock news

### yfinance (Fallback)
- Unlimited requests
- Rate limited (avoid too many requests per second)
- Delayed data (15-20 minutes)
- No API key required

## Monitoring Usage

Monitor your FMP API usage at:
https://financialmodelingprep.com/developer/docs/dashboard

## Upgrading

If you need more than 250 requests/day, consider upgrading:
- **Starter**: $14/month - 750 calls/day
- **Professional**: $29/month - 3000 calls/day
- **Enterprise**: Custom pricing

## Troubleshooting

### "Data temporarily unavailable" Error

This can happen when:
1. FMP API key not set → Falls back to yfinance
2. yfinance rate limited → Falls back to demo data
3. Network issues → Falls back to demo data

### Check Which Data Source is Being Used

Look at the Railway logs after deployment:
- `Using Financial Modeling Prep (FMP) API for market data (real-time)` → FMP working
- `Using yfinance for market data (free, delayed)` → Fallback to yfinance
- `Using sandbox financial data module` → Using demo data

## Support

- FMP Documentation: https://financialmodelingprep.com/developer/docs/
- yfinance Documentation: https://pypi.org/project/yfinance/
