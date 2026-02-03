#!/usr/bin/env python3
"""Script to train ML models for SignalIQ."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ml.training import train_lstm_model, train_classifier_model
from app.database import SessionLocal
from app.models.stock import Stock
import argparse


def main():
    parser = argparse.ArgumentParser(description="Train ML models for SignalIQ")
    parser.add_argument("--model", choices=["lstm", "classifier", "all"], default="all",
                       help="Which model to train")
    parser.add_argument("--symbol", type=str, help="Stock symbol for LSTM training")
    parser.add_argument("--epochs", type=int, default=50, help="Number of training epochs")
    parser.add_argument("--sequence-length", type=int, default=60, help="LSTM sequence length")

    args = parser.parse_args()

    db = SessionLocal()

    try:
        if args.model in ["lstm", "all"]:
            if args.symbol:
                stock = db.query(Stock).filter(Stock.symbol == args.symbol.upper()).first()
                if not stock:
                    print(f"❌ Stock {args.symbol} not found")
                    return
                
                print(f"🚀 Training LSTM model for {args.symbol}...")
                result = train_lstm_model(
                    stock_id=stock.id,
                    sequence_length=args.sequence_length,
                    epochs=args.epochs
                )
                print(f"✅ LSTM training complete!")
                print(f"   Model saved to: {result['model_path']}")
                print(f"   Final loss: {result['final_loss']:.4f}")
            else:
                print("⚠️  LSTM training requires --symbol argument")
                print("   Example: python scripts/train_models.py --model lstm --symbol AAPL")

        if args.model in ["classifier", "all"]:
            print("🚀 Training signal classifier model...")
            result = train_classifier_model(epochs=args.epochs)
            print(f"✅ Classifier training complete!")
            print(f"   Model saved to: {result['model_path']}")
            print(f"   Training samples: {result['training_samples']}")
            print(f"   Final accuracy: {result['final_accuracy']:.4f}")

    except Exception as e:
        print(f"❌ Training failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
