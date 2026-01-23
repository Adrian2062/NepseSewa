import os
import django
import pandas as pd
import numpy as np
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NepseSewa.settings')
django.setup()

from myapp.models import NEPSEPrice

def check_label_distribution(symbol, forecast_horizon=5, threshold=0.02):
    print(f"--- Analyzing {symbol} ---")
    qs = NEPSEPrice.objects.filter(symbol=symbol).order_by('timestamp')
    data = list(qs.values('close'))
    
    if not data:
        print("No data found.")
        return

    df = pd.DataFrame(data)
    
    # Calculate returns
    df['future_close'] = df['close'].shift(-forecast_horizon)
    df['return'] = (df['future_close'] - df['close']) / df['close']
    
    # Label
    conditions = [
        (df['return'] <= -threshold),
        (df['return'] > -threshold) & (df['return'] < threshold),
        (df['return'] >= threshold)
    ]
    choices = ['SELL', 'HOLD', 'BUY']
    df['label'] = np.select(conditions, choices, default='HOLD')
    
    # Drop last rows where future is NaN
    df = df.dropna()
    
    # Stats
    counts = df['label'].value_counts()
    total = len(df)
    print(f"Total Data Points: {total}")
    print("Label Distribution:")
    for label in ['SELL', 'HOLD', 'BUY']:
        count = counts.get(label, 0)
        pct = (count / total) * 100 if total > 0 else 0
        print(f"  {label}: {count} ({pct:.1f}%)")
    print("-" * 30)

if __name__ == "__main__":
    # Check a few popular stocks
    check_label_distribution('NABIL', threshold=0.02)
    check_label_distribution('HIDCL', threshold=0.02)
    check_label_distribution('NICA', threshold=0.02)
