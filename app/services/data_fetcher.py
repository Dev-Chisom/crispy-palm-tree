"""Data fetcher service for retrieving stock data from Yahoo Finance."""

import yfinance as yf
import pandas as pd
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import time
from app.config import settings
from app.models.stock import Market


class DataFetcher:
    """Service for fetching stock data from various sources."""

    @staticmethod
    def fetch_us_stock_prices(
        symbol: str, period: str = "1y", interval: str = "1d", retry_count: int = 3
    ) -> Optional[pd.DataFrame]:
        """
        Fetch US stock prices using yfinance (Yahoo Finance).

        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            period: Period to fetch (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
            retry_count: Number of retry attempts on failure

        Returns:
            DataFrame with OHLCV data or None if fetch fails
        """
        if not settings.yfinance_enabled:
            return None

        for attempt in range(retry_count):
            try:
                ticker = yf.Ticker(symbol)
                # Add timeout to prevent hanging
                data = ticker.history(period=period, interval=interval, timeout=10)
                
                if data.empty:
                    # Try with different period if empty
                    if period != "max":
                        data = ticker.history(period="max", interval=interval, timeout=10)
                    if data.empty:
                        return None

                # Rename columns to match our schema
                data = data.rename(
                    columns={
                        "Open": "open",
                        "High": "high",
                        "Low": "low",
                        "Close": "close",
                        "Volume": "volume",
                    }
                )

                # Reset index to make datetime a column
                data = data.reset_index()
                data = data.rename(columns={"Date": "time"})

                # Ensure we have required columns
                required_cols = ["time", "open", "high", "low", "close", "volume"]
                if all(col in data.columns for col in required_cols):
                    return data[required_cols]
                else:
                    return None
                    
            except Exception as e:
                if attempt < retry_count - 1:
                    # Exponential backoff: wait 2^attempt seconds
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                    continue
                print(f"Error fetching US stock prices for {symbol} after {retry_count} attempts: {e}")
                return None
        
        return None

    @staticmethod
    def detect_asset_type(symbol: str, info: Dict[str, Any]) -> str:
        """
        Detect asset type from Yahoo Finance info.
        
        Args:
            symbol: Stock/ETF/Mutual Fund symbol
            info: Yahoo Finance info dictionary
            
        Returns:
            Asset type: 'STOCK', 'ETF', or 'MUTUAL_FUND'
        """
        quote_type = info.get("quoteType", "").upper()
        
        # Check quoteType field
        if quote_type == "ETF":
            return "ETF"
        elif quote_type == "MUTUALFUND":
            return "MUTUAL_FUND"
        
        # Check category
        category = info.get("category", "").upper()
        if "ETF" in category or "EXCHANGE TRADED FUND" in category:
            return "ETF"
        if "MUTUAL FUND" in category or "MUTUALFUND" in category:
            return "MUTUAL_FUND"
        
        # Default to STOCK
        return "STOCK"

    @staticmethod
    def fetch_us_stock_info(symbol: str, retry_count: int = 2) -> Optional[Dict[str, Any]]:
        """
        Fetch US stock/ETF/Mutual Fund information from Yahoo Finance.

        Args:
            symbol: Stock/ETF/Mutual Fund symbol
            retry_count: Number of retry attempts

        Returns:
            Dictionary with asset info or None
        """
        if not settings.yfinance_enabled:
            return None

        for attempt in range(retry_count):
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info

                if not info or len(info) == 0:
                    if attempt < retry_count - 1:
                        time.sleep(1)
                        continue
                    return None
                
                # Detect asset type
                asset_type = DataFetcher.detect_asset_type(symbol, info)
                info["asset_type"] = asset_type

                # Detect asset type
                asset_type = DataFetcher.detect_asset_type(symbol, info)
                
                return {
                    "symbol": symbol,
                    "name": info.get("longName") or info.get("shortName") or info.get("symbol", symbol),
                    "sector": info.get("sector"),
                    "currency": info.get("currency", "USD"),
                    "industry": info.get("industry"),
                    "market_cap": info.get("marketCap"),
                    "exchange": info.get("exchange"),
                    "asset_type": asset_type,
                }
            except Exception as e:
                if attempt < retry_count - 1:
                    time.sleep(1)
                    continue
                print(f"Error fetching US stock info for {symbol}: {e}")
                return None
        
        return None

    @staticmethod
    def fetch_us_stock_fundamentals(symbol: str, retry_count: int = 2) -> Optional[Dict[str, Any]]:
        """
        Fetch US stock fundamental data from Yahoo Finance.

        Args:
            symbol: Stock symbol
            retry_count: Number of retry attempts

        Returns:
            Dictionary with fundamental data or None
        """
        if not settings.yfinance_enabled:
            return None

        for attempt in range(retry_count):
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info

                if not info or len(info) == 0:
                    if attempt < retry_count - 1:
                        time.sleep(1)
                        continue
                    return None

                # Get financials (with error handling)
                financials = None
                income_stmt = None
                balance_sheet = None
                
                try:
                    financials = ticker.financials
                except:
                    pass
                
                try:
                    income_stmt = ticker.income_stmt
                except:
                    pass
                
                try:
                    balance_sheet = ticker.balance_sheet
                except:
                    pass

                revenue = None
                eps = None
                pe_ratio = info.get("trailingPE") or info.get("forwardPE")
                debt_ratio = None
                earnings_growth = info.get("earningsQuarterlyGrowth")

                # Try to extract revenue from financials
                if financials is not None and not financials.empty:
                    try:
                        if "Total Revenue" in financials.index:
                            revenue = float(financials.loc["Total Revenue"].iloc[0])
                    except:
                        pass

                # Try to extract EPS from income statement
                if income_stmt is not None and not income_stmt.empty:
                    try:
                        if "Basic EPS" in income_stmt.index:
                            eps = float(income_stmt.loc["Basic EPS"].iloc[0])
                        elif "Diluted EPS" in income_stmt.index:
                            eps = float(income_stmt.loc["Diluted EPS"].iloc[0])
                    except:
                        pass

                # Calculate debt ratio if available
                if balance_sheet is not None and not balance_sheet.empty:
                    try:
                        total_debt = None
                        total_assets = None
                        
                        if "Total Debt" in balance_sheet.index:
                            total_debt = float(balance_sheet.loc["Total Debt"].iloc[0])
                        elif "Total Liabilities Net Minority Interest" in balance_sheet.index:
                            total_debt = float(balance_sheet.loc["Total Liabilities Net Minority Interest"].iloc[0])
                        
                        if "Total Assets" in balance_sheet.index:
                            total_assets = float(balance_sheet.loc["Total Assets"].iloc[0])
                        
                        if total_debt and total_assets and total_assets > 0:
                            debt_ratio = (total_debt / total_assets) * 100
                    except:
                        pass

                # Get dividend information
                dividend_yield = info.get("dividendYield")
                if dividend_yield:
                    dividend_yield = dividend_yield * 100  # Convert to percentage
                
                dividend_rate = info.get("dividendRate")  # Annual dividend per share
                payout_ratio = info.get("payoutRatio")
                if payout_ratio:
                    payout_ratio = payout_ratio * 100  # Convert to percentage

                return {
                    "revenue": revenue,
                    "eps": eps,
                    "pe_ratio": pe_ratio,
                    "debt_ratio": debt_ratio,
                    "earnings_growth": earnings_growth * 100 if earnings_growth else None,  # Convert to percentage
                    "dividend_yield": dividend_yield,
                    "dividend_per_share": dividend_rate,
                    "dividend_payout_ratio": payout_ratio,
                }
            except Exception as e:
                if attempt < retry_count - 1:
                    time.sleep(1)
                    continue
                print(f"Error fetching US stock fundamentals for {symbol}: {e}")
                return None
        
        return None

    @staticmethod
    def fetch_ngx_stock_prices(symbol: str, start_date: datetime, end_date: datetime, retry_count: int = 3) -> Optional[pd.DataFrame]:
        """
        Fetch NGX stock prices using Yahoo Finance.
        
        Yahoo Finance supports NGX stocks with ticker format: SYMBOL.NG
        Example: DANGOTE.NG, GUARANTY.NG, ZENITH.NG

        Args:
            symbol: NGX stock symbol (with or without .NG suffix)
            start_date: Start date
            end_date: End date
            retry_count: Number of retry attempts

        Returns:
            DataFrame with OHLCV data or None if fetch fails
        """
        if not settings.yfinance_enabled:
            return None

        # Ensure symbol has .NG suffix for Yahoo Finance
        yahoo_symbol = symbol if symbol.endswith('.NG') else f"{symbol}.NG"

        # Calculate period from dates
        days_diff = (end_date - start_date).days
        if days_diff <= 5:
            period = "5d"
        elif days_diff <= 30:
            period = "1mo"
        elif days_diff <= 90:
            period = "3mo"
        elif days_diff <= 180:
            period = "6mo"
        elif days_diff <= 365:
            period = "1y"
        else:
            period = "max"

        for attempt in range(retry_count):
            try:
                ticker = yf.Ticker(yahoo_symbol)
                data = ticker.history(period=period, interval="1d", timeout=10)
                
                if data.empty:
                    if attempt < retry_count - 1:
                        time.sleep(2 ** attempt)
                        continue
                    return None

                # Filter by date range
                data = data[(data.index.date >= start_date.date()) & (data.index.date <= end_date.date())]
                
                if data.empty:
                    return None

                # Rename columns
                data = data.rename(
                    columns={
                        "Open": "open",
                        "High": "high",
                        "Low": "low",
                        "Close": "close",
                        "Volume": "volume",
                    }
                )

                # Reset index to make datetime a column
                data = data.reset_index()
                data = data.rename(columns={"Date": "time"})

                required_cols = ["time", "open", "high", "low", "close", "volume"]
                if all(col in data.columns for col in required_cols):
                    return data[required_cols]
                else:
                    return None
                    
            except Exception as e:
                if attempt < retry_count - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                    continue
                print(f"Error fetching NGX stock prices for {symbol} ({yahoo_symbol}): {e}")
                return None
        
        return None

    @staticmethod
    def fetch_ngx_stock_info(symbol: str, retry_count: int = 2) -> Optional[Dict[str, Any]]:
        """
        Fetch NGX stock information from Yahoo Finance.
        
        Yahoo Finance supports NGX stocks with ticker format: SYMBOL.NG

        Args:
            symbol: NGX stock symbol (with or without .NG suffix)
            retry_count: Number of retry attempts

        Returns:
            Dictionary with stock info or None
        """
        if not settings.yfinance_enabled:
            return None

        # Ensure symbol has .NG suffix for Yahoo Finance
        yahoo_symbol = symbol if symbol.endswith('.NG') else f"{symbol}.NG"

        for attempt in range(retry_count):
            try:
                ticker = yf.Ticker(yahoo_symbol)
                info = ticker.info

                if not info or len(info) == 0:
                    if attempt < retry_count - 1:
                        time.sleep(1)
                        continue
                    return None

                return {
                    "symbol": symbol.upper().replace('.NG', ''),
                    "name": info.get("longName") or info.get("shortName") or info.get("symbol", symbol),
                    "sector": info.get("sector"),
                    "currency": info.get("currency", "NGN"),
                    "industry": info.get("industry"),
                    "market_cap": info.get("marketCap"),
                    "exchange": info.get("exchange", "NGX"),
                }
            except Exception as e:
                if attempt < retry_count - 1:
                    time.sleep(1)
                    continue
                print(f"Error fetching NGX stock info for {symbol} ({yahoo_symbol}): {e}")
                return None
        
        return None
