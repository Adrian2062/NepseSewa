import os
import django
import numpy as np
import pandas as pd
import sys

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NepseSewa.settings')
django.setup()

from myapp.ml_services import MLService

def generate_dummy_data(n_days=1000):
    dates = pd.date_range(end=pd.Timestamp.now(), periods=n_days)
    data = []
    price = 100.0
    for date in dates:
        change = np.random.normal(0, 0.02) # 2% std dev
        price = price * (1 + change)
        high = price * (1 + abs(np.random.normal(0, 0.01)))
        low = price * (1 - abs(np.random.normal(0, 0.01)))
        
        data.append({
            'timestamp': date,
            'open': price,
            'high': high,
            'low': low,
            'close': price,
            'volume': np.random.randint(1000, 100000)
        })
    return data

def test_pipeline():
    print("Testing LSTM Pipeline...")
    
    # 1. Generate Data
    print("Generating dummy data...")
    raw_data = generate_dummy_data(500)
    
    # 2. Initialize Service
    ml = MLService(raw_data)
    
    # 3. Test Preparation
    print("Testing data preparation (split/scale/label)...")
    try:
        X_train, y_train, X_test, y_test, last_window = ml.prepare_data(window_size=30)
        print(f"X_train shape: {X_train.shape}")
        print(f"y_train shape: {y_train.shape}")
        print(f"Sample Targets: {np.unique(y_train, return_counts=True)}")
        
        if len(np.unique(y_train)) < 3:
            print("WARNING: Not all 3 classes (0, 1, 2) generated in dummy data. This might happen with random data.")
            
    except Exception as e:
        print(f"FAILED prepare_data: {e}")
        import traceback
        traceback.print_exc()
        return

    # 4. Test Train and Predict
    print("\nTesting train_and_predict execution...")
    try:
        predicted_class, confidence, last_close = ml.train_and_predict(window_size=30)
        print(f"Result: Class={predicted_class}, Conf={confidence}, LastClose={last_close}")
        
        if predicted_class in [0, 1, 2] and 0.0 <= confidence <= 1.0:
            print("SUCCESS: Valid output received.")
        else:
            print("FAILURE: Invalid output values.")
            
    except Exception as e:
        print(f"FAILED train_and_predict: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pipeline()
