import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import os

# Suppress TensorFlow logging noise
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 
import logging
logging.getLogger('tensorflow').setLevel(logging.ERROR)

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, Input
from tensorflow.keras.optimizers import Adam
from tensorflow.keras import backend as K
import datetime

class MLService:
    def __init__(self, data):
        """
        data: list of dictionaries from NEPSEPrice model values
        Requirements: Last 60 trading days (~3 months)
        """
        self.df = pd.DataFrame(data)
        if not self.df.empty:
            self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
            self.df = self.df.sort_values('timestamp').reset_index(drop=True)
        
        self.scaler = MinMaxScaler(feature_range=(0, 1))

    def compute_indicators(self):
        """
        Compute Institutional Indicators:
        1. Wilder's RSI (14) - REFACTORED
        2. EMA (10, 20)
        3. MACD (12, 26, 9)
        4. ATR (14)
        5. Volume MA (20)
        """
        df = self.df.copy()
        
        # 1. Wilder's RSI (14)
        # Formula: RSI = 100 - (100 / (1 + RS))
        # RS = AvgGain / AvgLoss
        # Wilder's Smoothing: (PrevAvg * 13 + Curr) / 14
        delta = df['close'].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        
        avg_gain = [np.nan] * len(df)
        avg_loss = [np.nan] * len(df)
        
        # Initial average (Simple average of first 14)
        if len(df) > 14:
            avg_gain[14] = gain[1:15].mean()
            avg_loss[14] = loss[1:15].mean()
            
            # Wilder's Smoothing for the rest
            for i in range(15, len(df)):
                avg_gain[i] = (avg_gain[i-1] * 13 + gain.iloc[i]) / 14
                avg_loss[i] = (avg_loss[i-1] * 13 + loss.iloc[i]) / 14
        
        df['avg_gain'] = avg_gain
        df['avg_loss'] = avg_loss
        rs = df['avg_gain'] / df['avg_loss'].replace(0, np.nan)
        df['rsi'] = 100 - (100 / (1 + rs))
        df['rsi'] = df['rsi'].ffill().fillna(50.0) # Conservative default but ffill prioritizes latest math

        # 2. EMA Cluster
        df['ema10'] = df['close'].ewm(span=10, adjust=False).mean()
        df['ema20'] = df['close'].ewm(span=20, adjust=False).mean()

        # 3. MACD
        exp12 = df['close'].ewm(span=12, adjust=False).mean()
        exp26 = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = exp12 - exp26
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()

        # 4. ATR (14)
        high_low = df['high'] - df['low']
        high_cp = np.abs(df['high'] - df['close'].shift())
        low_cp = np.abs(df['low'] - df['close'].shift())
        tr = pd.concat([high_low, high_cp, low_cp], axis=1).max(axis=1)
        df['atr'] = tr.rolling(window=14).mean()

        # 5. Volume MA
        df['vol_ma20'] = df['volume'].rolling(window=20).mean()

        # Final Clean
        df = df.ffill().bfill()
        self.df = df
        return df

    def prepare_data(self, window_size=20):
        """
        Prepare multi-step data: 10 input features, next 3 days CLOSE target
        Features: OHLCV + RSI + EMA10 + EMA20 + MACD + MACD_Signal
        """
        self.compute_indicators()
        
        features = ['open', 'high', 'low', 'close', 'volume', 'rsi', 'ema10', 'ema20', 'macd', 'macd_signal']
        if len(self.df) < (window_size + 3):
            return None, None, None

        data_values = self.df[features].values
        scaled_data = self.scaler.fit_transform(data_values)

        X, y = [], []
        # target_idx is 3 ('close')
        target_idx = 3

        for i in range(window_size, len(scaled_data) - 3):
            X.append(scaled_data[i-window_size:i])
            # Next 3 days close prices
            y.append(scaled_data[i:i+3, target_idx])

        return np.array(X), np.array(y), scaled_data

    def build_model(self, input_shape):
        """
        Architecture from requirements:
        LSTM(64, return_sequences=True) -> Dropout(0.3) -> LSTM(32) -> Dropout(0.3) -> Dense(16) -> Dense(3)
        """
        model = Sequential([
            Input(shape=input_shape),
            LSTM(units=64, return_sequences=True),
            Dropout(0.3),
            LSTM(units=32, return_sequences=False),
            Dropout(0.3),
            Dense(units=16, activation='relu'),
            Dense(units=3) # Output: 3 days close prices
        ])
        
        model.compile(optimizer=Adam(learning_rate=0.001), loss='mean_squared_error')
        return model

    def train_and_predict(self, window_size=20):
        """
        Executes robust multi-step pipeline with tuned anti-overfit parameters
        """
        try:
            X, y, scaled_full_data = self.prepare_data(window_size)
            if X is None or len(X) < 10:
                return None

            # Train on available data (rolling model)
            model = self.build_model((X.shape[1], X.shape[2]))
            model.fit(X, y, batch_size=8, epochs=30, verbose=0)

            # Performance on last known sample (for RMSE approximation)
            last_actual_X = X[-1:]
            last_actual_y = y[-1:]
            pred_eval = model.predict(last_actual_X, verbose=0)
            rmse = np.sqrt(np.mean((pred_eval - last_actual_y)**2))
            mae = np.mean(np.abs(pred_eval - last_actual_y))

            # Future Prediction
            last_window = scaled_full_data[-window_size:].reshape(1, window_size, X.shape[2])
            future_scaled = model.predict(last_window, verbose=0)[0]

            # Inverse scale targets
            prices_3d = []
            for val in future_scaled:
                dummy = np.zeros((1, X.shape[2]))
                dummy[0, 3] = val
                # Senior Practice: Explicitly cast to float to prevent NumPy scalar issues in Django
                prices_3d.append(float(self.scaler.inverse_transform(dummy)[0, 3]))

            K.clear_session()

            # Metadata for Signal Logic
            meta = {
                'current_close': float(self.df['close'].iloc[-1]),
                'ema10': float(self.df['ema10'].iloc[-1]),
                'ema20': float(self.df['ema20'].iloc[-1]),
                'macd': float(self.df['macd'].iloc[-1]),
                'macd_signal': float(self.df['macd_signal'].iloc[-1]),
                'rsi': float(self.df['rsi'].iloc[-1]),
                'prev_rsi': float(self.df['rsi'].iloc[-2]) if len(self.df) > 1 else float(self.df['rsi'].iloc[-1]),
                'atr': float(self.df['atr'].iloc[-1]),
                'vol_ma20': float(self.df['vol_ma20'].iloc[-1]),
                'volume': float(self.df['volume'].iloc[-1])
            }

            return {
                'predictions': prices_3d,
                'rmse': float(rmse),
                'mae': float(mae),
                'meta': meta
            }
        except Exception as e:
            K.clear_session()
            print(f"ML Service Error: {e}")
            return None

def get_recommendation_data(ml_result):
    """
    Refined RSI Quantitative Trading Engine (Strict Rules).
    Interprets RSI momentum strictly for NEPSE.
    """
    if ml_result is None:
        return None

    meta = ml_result['meta']
    preds = ml_result['predictions']
    
    curr_close = float(meta['current_close'])
    rsi = float(meta['rsi'])
    prev_rsi = float(meta['prev_rsi'])
    atr = float(meta['atr'])
    pred_avg = float(np.mean(preds))
    expected_move_pct = float(((pred_avg - curr_close) / curr_close) * 100)

    # Trend Direction
    rsi_rising = rsi > prev_rsi
    rsi_falling = rsi < prev_rsi

    # Decision logic based on user rules
    market_condition = "Sideways"
    trend = "Neutral"
    recommendation = 0 # HOLD
    reason = "No clear momentum direction."

    # 1. BUY SIGNALS
    # a) Oversold Buy (RSI < 30 and Rising)
    if rsi < 30:
        market_condition = "Oversold"
        trend = "Bearish (Reversal Possible)"
        if rsi_rising:
            recommendation = 1
            reason = "Stock is oversold and showing early recovery momentum."
        else:
            recommendation = 0
            reason = "Stock is oversold but lacks recovery momentum."

    # b) Bullish Momentum Buy (60 <= RSI < 70)
    elif 60 <= rsi < 70:
        market_condition = "Bullish"
        trend = "Bullish"
        recommendation = 1
        reason = "Strong bullish momentum with healthy trend continuation."

    # 2. HOLD SIGNALS
    # a) Sideways Market (40 <= RSI < 60)
    elif 40 <= rsi < 60:
        market_condition = "Sideways"
        trend = "Neutral"
        recommendation = 0
        if 45 <= rsi <= 55:
            reason = "RSI in Neutral No-Trade Zone (45-55)."
        else:
            reason = "No clear bullish or bearish momentum."

    # b) Near Overbought (70 <= RSI <= 75)
    elif 70 <= rsi <= 75:
        market_condition = "Bullish"
        trend = "Bullish"
        recommendation = 0
        reason = "Bullish trend but nearing overbought zone; risk increasing."

    # 3. SELL SIGNALS
    # a) Overbought Sell (RSI > 75)
    elif rsi > 75:
        market_condition = "Overbought"
        trend = "Bullish (Exhausted)"
        recommendation = -1
        reason = "Overbought condition with high probability of pullback."

    # b) Momentum Breakdown Sell (RSI < 40 and Falling)
    elif rsi < 40:
        market_condition = "Weak Bearish"
        trend = "Bearish"
        if rsi_falling:
            recommendation = -1
            reason = "Bearish momentum strengthening."
        else:
            recommendation = 0
            reason = "Downward momentum building but stabilizing."

    # Forced HOLD for No-Trade Zone constraint
    if 45 <= rsi <= 55:
        recommendation = 0

    # Build Levels
    levels = {'entry': None, 'exit': None, 'target': None, 'stop_loss': None}
    if recommendation == 1:
        levels['entry'] = curr_close
        levels['stop_loss'] = curr_close - (1.2 * atr)
        levels['target'] = curr_close + (2.0 * atr)
    elif recommendation == -1:
        levels['exit'] = curr_close
        levels['stop_loss'] = curr_close + (1.2 * atr)
        levels['target'] = curr_close - (2.0 * atr)

    conf_score = 1.0 - min(ml_result['rmse'], 1.0)
    
    return {
        'symbol': '', # Filled by caller
        'signal': recommendation,
        'trend': trend,
        'market_condition': market_condition,
        'rsi': round(rsi, 2),
        'expected_move': round(expected_move_pct, 2),
        'reason': reason,
        'confidence': round(conf_score * 100, 1),
        'levels': levels,
        'rmse': ml_result['rmse'],
        'mae': ml_result['mae'],
        'predicted_price': float(pred_avg)
    }
