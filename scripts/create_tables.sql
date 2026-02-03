-- Create database tables for SignalIQ

-- Stocks table
CREATE TABLE IF NOT EXISTS stocks (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    market VARCHAR(10) NOT NULL,
    sector VARCHAR(100),
    currency VARCHAR(10) NOT NULL DEFAULT 'USD',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_stocks_symbol ON stocks(symbol);
CREATE INDEX IF NOT EXISTS idx_stocks_market ON stocks(market);
CREATE INDEX IF NOT EXISTS idx_stocks_active ON stocks(is_active);

-- Stock prices table (TimescaleDB hypertable)
CREATE TABLE IF NOT EXISTS stock_prices (
    time TIMESTAMP WITH TIME ZONE NOT NULL,
    stock_id INTEGER NOT NULL REFERENCES stocks(id) ON DELETE CASCADE,
    open FLOAT NOT NULL,
    high FLOAT NOT NULL,
    low FLOAT NOT NULL,
    close FLOAT NOT NULL,
    volume FLOAT NOT NULL,
    PRIMARY KEY (time, stock_id)
);

CREATE INDEX IF NOT EXISTS idx_stock_prices_stock_time ON stock_prices(stock_id, time);

-- Fundamentals table
CREATE TABLE IF NOT EXISTS fundamentals (
    id SERIAL PRIMARY KEY,
    stock_id INTEGER NOT NULL REFERENCES stocks(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    revenue FLOAT,
    eps FLOAT,
    pe_ratio FLOAT,
    debt_ratio FLOAT,
    earnings_growth FLOAT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_fundamentals_stock_date ON fundamentals(stock_id, date);
CREATE INDEX IF NOT EXISTS idx_fundamentals_stock ON fundamentals(stock_id);

-- Technical indicators table
CREATE TABLE IF NOT EXISTS technical_indicators (
    id SERIAL PRIMARY KEY,
    stock_id INTEGER NOT NULL REFERENCES stocks(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    rsi FLOAT,
    macd FLOAT,
    macd_signal FLOAT,
    macd_histogram FLOAT,
    sma_20 FLOAT,
    sma_50 FLOAT,
    sma_200 FLOAT,
    ema_12 FLOAT,
    ema_26 FLOAT,
    bollinger_upper FLOAT,
    bollinger_lower FLOAT,
    bollinger_middle FLOAT,
    volume_avg FLOAT
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_technical_indicators_stock_date ON technical_indicators(stock_id, date);
CREATE INDEX IF NOT EXISTS idx_technical_indicators_stock ON technical_indicators(stock_id);

-- Signals table
CREATE TABLE IF NOT EXISTS signals (
    id SERIAL PRIMARY KEY,
    stock_id INTEGER NOT NULL REFERENCES stocks(id) ON DELETE CASCADE,
    signal_type VARCHAR(20) NOT NULL,
    confidence_score FLOAT NOT NULL,
    risk_level VARCHAR(20) NOT NULL,
    holding_period VARCHAR(20) NOT NULL,
    explanation JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_signals_stock ON signals(stock_id);
CREATE INDEX IF NOT EXISTS idx_signals_type ON signals(signal_type);
CREATE INDEX IF NOT EXISTS idx_signals_created ON signals(created_at);
CREATE INDEX IF NOT EXISTS idx_signals_stock_created ON signals(stock_id, created_at);

-- Signal history table
CREATE TABLE IF NOT EXISTS signal_history (
    id SERIAL PRIMARY KEY,
    signal_id INTEGER REFERENCES signals(id) ON DELETE CASCADE,
    stock_id INTEGER NOT NULL REFERENCES stocks(id) ON DELETE CASCADE,
    signal_type VARCHAR(20) NOT NULL,
    confidence_score FLOAT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_signal_history_stock ON signal_history(stock_id);
CREATE INDEX IF NOT EXISTS idx_signal_history_type ON signal_history(signal_type);
CREATE INDEX IF NOT EXISTS idx_signal_history_created ON signal_history(created_at);
CREATE INDEX IF NOT EXISTS idx_signal_history_stock_created ON signal_history(stock_id, created_at);
