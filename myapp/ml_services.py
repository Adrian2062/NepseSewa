import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, Input
from tensorflow.keras.optimizers import Adam
import datetime

class MLService:
    def __init__(self, data):
        """
        data: list of dictionaries from NEPSEPrice model values
        """
        self.df = pd.DataFrame(data)
        if not self.df.empty:
            self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
            self.df = self.df.sort_values('timestamp')
            self.df = self.df.set_index('timestamp')
        self.scaler = MinMaxScaler(feature_range=(0, 1))

    def prepare_data(self, window_size=30):
        """
        Prepare data for LSTM: cleaning, scaling, and sequence creation
        """
        # Feature Engineering core inputs (OHLCV)
        # Use 'close' as the primary target and feature
        if self.df.empty or len(self.df) < window_size:
            return None, None, None

        # Technical Indicators calculation (Optional but requested)
        # Moving Average (MA)
        self.df['MA10'] = self.df['close'].rolling(window=10).mean()
        self.df['MA30'] = self.df['close'].rolling(window=30).mean()
        
        # RSI calculation
        delta = self.df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        self.df['RSI'] = 100 - (100 / (1 + rs))

        # MACD calculation
        EMA12 = self.df['close'].ewm(span=12, adjust=False).mean()
        EMA26 = self.df['close'].ewm(span=26, adjust=False).mean()
        self.df['MACD'] = EMA12 - EMA26
        
        # Fill missing values created by indicators
        self.df = self.df.ffill().bfill()
        
        # Final set of features: Open, High, Low, Close, Volume, MA10, MA30, RSI, MACD
        features = ['open', 'high', 'low', 'close', 'volume', 'MA10', 'MA30', 'RSI', 'MACD']
        data_filtered = self.df[features].values
        
        # Scale the data
        scaled_data = self.scaler.fit_transform(data_filtered)
        
        X, y = [], []
        # Index 3 is 'close' in our feature list
        target_idx = 3
        
        for i in range(window_size, len(scaled_data)):
            X.append(scaled_data[i-window_size:i])
            y.append(scaled_data[i, target_idx]) # Next close price
            
        return np.array(X), np.array(y), scaled_data

    def build_model(self, input_shape):
        """
        Deep LSTM model architecture
        """
        model = Sequential([
            Input(shape=input_shape),
            LSTM(units=50, return_sequences=True),
            Dropout(0.2),
            LSTM(units=50, return_sequences=False),
            Dropout(0.2),
            Dense(units=25),
            Dense(units=1)
        ])
        
        model.compile(optimizer=Adam(learning_rate=0.001), loss='mean_squared_error')
        return model

    def train_and_predict(self, window_size=30):
        """
        Executes the full pipeline: Preprocess -> Train -> Predict
        """
        X, y, scaled_full_data = self.prepare_data(window_size)
        
        if X is None:
            return None, None, None, None

        # Split into train and test
        train_size = int(len(X) * 0.8)
        X_train, X_test = X[:train_size], X[train_size:]
        y_train, y_test = y[:train_size], y[train_size:]
        
        # Build and train
        model = self.build_model((X.shape[1], X.shape[2]))
        model.fit(X_train, y_train, batch_size=32, epochs=20, verbose=0)
        
        # Predictions for evaluation
        predictions = model.predict(X_test)
        
        # Metrics (RMSE and MAE)
        rmse = np.sqrt(np.mean((predictions - y_test)**2))
        mae = np.mean(np.abs(predictions - y_test))
        
        # Predict Next Day
        last_window = scaled_full_data[-window_size:].reshape(1, window_size, X.shape[2])
        next_day_scaled = model.predict(last_window)
        
        # Inverse transform to get actual price
        # We need a dummy array for inverse_transform
        dummy = np.zeros((1, X.shape[2]))
        dummy[0, 3] = next_day_scaled[0, 0] # Put prediction in "close" column
        next_day_price = self.scaler.inverse_transform(dummy)[0, 3]
        
        return float(next_day_price), float(rmse), float(mae), self.df['close'].iloc[-1]

def get_recommendation(current_price, predicted_price):
    """
    BUY → if predicted price increases by more than +1.5%
    SELL → if predicted price decreases by more than −1.5%
    HOLD → otherwise
    """
    change_pct = ((predicted_price - current_price) / current_price) * 100
    
    if change_pct > 1.5:
        return 1 # BUY
    elif change_pct < -1.5:
        return -1 # SELL
    else:
        return 0 # HOLD
