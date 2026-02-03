#!/usr/bin/env python3
"""Test script to check if Yahoo Finance supports NGX stocks."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import yfinance as yf
    print("✅ yfinance installed")
except ImportError:
    print("❌ yfinance not installed. Install with: pip install yfinance")
    sys.exit(1)

# Common NGX stock symbols to test
ngx_symbols = [
    "DANGOTE.NG",  # Dangote Cement
    "GUARANTY.NG",  # Guaranty Trust Bank
    "ZENITH.NG",  # Zenith Bank
    "ACCESS.NG",  # Access Bank
    "MTNN.NG",  # MTN Nigeria
    "DANGSUGAR.NG",  # Dangote Sugar
]

print("\n🔍 Testing NGX stocks on Yahoo Finance...\n")

for symbol in ngx_symbols:
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        if info and len(info) > 0:
            name = info.get("longName") or info.get("shortName", "N/A")
            currency = info.get("currency", "N/A")
            print(f"✅ {symbol}: {name} ({currency})")
            
            # Try to get price data
            data = ticker.history(period="1mo")
            if not data.empty:
                print(f"   📊 Price data available: {len(data)} days")
                print(f"   💰 Latest close: {data['Close'].iloc[-1]:.2f}")
            else:
                print(f"   ⚠️  No price data available")
        else:
            print(f"❌ {symbol}: No data available")
    except Exception as e:
        print(f"❌ {symbol}: Error - {str(e)[:50]}")

print("\n💡 If any symbols work, we can use Yahoo Finance for NGX stocks!")
print("   Ticker format: SYMBOL.NG")
