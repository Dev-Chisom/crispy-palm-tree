# SignalIQ Backend

AI-powered investment intelligence platform backend for generating BUY/HOLD/SELL signals for US and Nigerian (NGX) stocks with explainable AI reasoning.

## Features

- **Multi-Market Support**: US stocks (via yfinance) and NGX stocks (Nigerian Stock Exchange)
- **AI Signal Generation**: Rule-based multi-factor analysis with explainable reasoning
- **Technical Analysis**: RSI, MACD, Moving Averages, Bollinger Bands, and more
- **Fundamental Analysis**: P/E ratios, earnings growth, revenue trends, debt ratios
- **Real-time Data**: Automated data ingestion with Celery background tasks
- **Caching**: Redis-based caching for optimal performance
- **RESTful API**: FastAPI with automatic OpenAPI documentation
- **TimescaleDB**: Optimized time-series data storage for stock prices

## Tech Stack

- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL with TimescaleDB extension
- **Cache**: Redis
- **Task Queue**: Celery with Redis broker
- **ML Libraries**: TensorFlow/Keras, scikit-learn, pandas, numpy, pandas-ta
- **Data Sources**: yfinance (US stocks), custom NGX API/scraper

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Settings and configuration
│   ├── database.py             # Database connection
│   ├── models/                 # SQLAlchemy models
│   │   ├── stock.py
│   │   ├── price.py
│   │   ├── signal.py
│   │   ├── fundamental.py
│   │   └── technical_indicator.py
│   ├── schemas/                # Pydantic schemas
│   │   ├── stock.py
│   │   ├── signal.py
│   │   ├── price.py
│   │   └── common.py
│   ├── api/
│   │   └── v1/
│   │       ├── stocks.py
│   │       ├── signals.py
│   │       └── markets.py
│   ├── services/
│   │   ├── data_fetcher.py     # yfinance, NGX
│   │   ├── signal_generator.py # Core signal logic
│   │   ├── indicator_calculator.py
│   │   ├── explanation_generator.py
│   │   └── cache.py
│   └── tasks/                  # Celery tasks
│       ├── data_ingestion.py
│       └── signal_generation.py
├── alembic/                    # Database migrations
├── tests/
├── requirements.txt
├── .env.example
└── README.md
```

## Setup Instructions

### Prerequisites

- Python 3.11+
- PostgreSQL 12+ with TimescaleDB extension
- Redis 6+
- Virtual environment (recommended)

### Installation

1. **Clone the repository** (if applicable) or navigate to the project directory:
   ```bash
   cd stock-backend
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` with your configuration:
   - Database URL
   - Redis URL
   - Celery broker URLs
   - API settings

5. **Set up PostgreSQL with TimescaleDB**:
   ```bash
   # Install TimescaleDB extension
   psql -U postgres -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"
   
   # Create database
   createdb signaliq_db
   ```

6. **Run database migrations**:
   ```bash
   alembic upgrade head
   ```

7. **Create TimescaleDB hypertable** (after migrations):
   ```sql
   SELECT create_hypertable('stock_prices', 'time');
   ```

### Running the Application

1. **Start Redis**:
   ```bash
   redis-server
   ```

2. **Start Celery worker** (in a separate terminal):
   ```bash
   celery -A app.tasks.celery_app worker --loglevel=info
   ```

3. **Start Celery beat** (for scheduled tasks, optional):
   ```bash
   celery -A app.tasks.celery_app beat --loglevel=info
   ```

4. **Start FastAPI server**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Access API documentation**:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## API Endpoints

### Stock Management
- `GET /api/v1/stocks` - List all stocks (with pagination, filters)
- `GET /api/v1/stocks/{symbol}` - Get stock details
- `GET /api/v1/stocks/{symbol}/prices` - Get OHLCV data
- `GET /api/v1/stocks/{symbol}/fundamentals` - Get latest fundamentals
- `GET /api/v1/stocks/{symbol}/indicators` - Get technical indicators

### Signal Generation
- `GET /api/v1/signals/{symbol}/signal` - Get current AI signal
- `POST /api/v1/signals/generate` - Generate signal for a stock
- `GET /api/v1/signals/top` - Get top signals today
- `GET /api/v1/signals/{symbol}/history` - Get historical signals

### Market Data
- `GET /api/v1/markets/{market}/stocks` - Get all stocks for a market
- `GET /api/v1/markets/{market}/highlights` - Market highlights

## Signal Generation

The system uses a multi-factor scoring approach:

- **Technical Analysis (40%)**: RSI, MACD, Moving Averages, Bollinger Bands, Volume
- **Fundamental Analysis (30%)**: P/E ratio, Earnings growth, Revenue trends, Debt ratios
- **Trend Analysis (20%)**: Short-term, medium-term, and long-term trends
- **Volatility & Risk (10%)**: Historical volatility, drawdown analysis

### Signal Types
- **BUY**: Score > 60, positive momentum, good fundamentals
- **HOLD**: Score 40-60, mixed signals
- **SELL**: Score < 40, negative momentum, poor fundamentals
- **NO_SIGNAL**: Insufficient data or conflicting signals

## Celery Tasks

### Data Ingestion
- `fetch_stock_prices(symbol, market)` - Fetch and store OHLCV data
- `update_fundamentals(symbol)` - Update fundamental data
- `calculate_indicators(symbol)` - Calculate technical indicators

### Signal Generation
- `generate_signal(symbol)` - Generate signal for a stock
- `batch_signal_generation(market)` - Generate signals for all active stocks

## Caching Strategy

- **Signals**: 1 hour TTL for active stocks, 24 hours for others
- **Price Data**: 5 minutes for latest, 1 hour for historical
- **Fundamentals**: 24 hours TTL
- **Top Signals**: 15 minutes TTL

## Development

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
black app/
```

### Type Checking
```bash
mypy app/
```

## Database Migrations

### Create a new migration:
```bash
alembic revision --autogenerate -m "Description of changes"
```

### Apply migrations:
```bash
alembic upgrade head
```

### Rollback migration:
```bash
alembic downgrade -1
```

## Environment Variables

See `.env.example` for all available configuration options. Key variables:

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection URL
- `CELERY_BROKER_URL`: Celery broker URL
- `CELERY_RESULT_BACKEND`: Celery result backend URL
- `YFINANCE_ENABLED`: Enable/disable yfinance data fetching
- `NGX_API_ENABLED`: Enable/disable NGX API integration

## Future Enhancements

- **Phase 2**: ML model integration (LSTM/TCN for forecasting)
- **Phase 2**: NGX stock data integration
- **Phase 2**: Backtesting endpoints
- **Phase 2**: Performance optimization and scaling

## License

[Your License Here]

## Contributing

[Contributing Guidelines]

## Support

For issues and questions, please open an issue on the repository.
# crispy-palm-tree
