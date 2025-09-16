#!/usr/bin/env python3
"""Keras 기반 LSTM 학습/예측 유틸리티
- window_sequences: (shelter_id, relief_item_id)별 시계열에서 lookback 윈도우 생성
- build_lstm_model: 간단한 회귀 LSTM 모델 구성
- StandardScaler1D: 단일 스케일러로 연속 피처 스케일링/역변환
"""
import os
import json
import numpy as np
import pandas as pd
from typing import List, Tuple, Dict

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

FEATURE_COLS_DEFAULT = ['y_t','cons_ma7','cons_ma14','cons_ma28']
CATEGORICAL_PREFIXES = ['seasonality_', 'disaster_severity_', 'weather_']
INDEX_COLS = ['shelter_id','relief_item_id','date']
TARGET_COL = 'y_t'

class StandardScaler1D:
    def __init__(self):
        self.mean_ = None
        self.std_ = None
    def fit(self, x: np.ndarray):
        self.mean_ = float(np.mean(x))
        self.std_ = float(np.std(x) + 1e-8)
        return self
    def transform(self, x: np.ndarray):
        return (x - self.mean_) / self.std_
    def inverse_transform(self, x: np.ndarray):
        return x * self.std_ + self.mean_
    def to_dict(self):
        return {'mean': self.mean_, 'std': self.std_}
    @staticmethod
    def from_dict(d):
        s = StandardScaler1D()
        s.mean_ = float(d['mean'])
        s.std_ = float(d['std'])
        return s

def prepare_panel(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(INDEX_COLS)
    return df

def window_sequences(df: pd.DataFrame, lookback: int = 28, feature_cols: List[str] = None):
    feature_cols = feature_cols or FEATURE_COLS_DEFAULT
    df = prepare_panel(df)
    groups = list(df.groupby(['shelter_id','relief_item_id']))
    scaler = StandardScaler1D().fit(df[TARGET_COL].values)
    # 연속형 컬럼만 스케일: 기본 연속형(y_t, cons_ma7/14/28)
    continuous_cols = [c for c in feature_cols if c in FEATURE_COLS_DEFAULT]
    for col in continuous_cols:
        df[col] = scaler.transform(df[col].values)
    X, y = [], []
    for (_, _), g in groups:
        if len(g) <= lookback:
            continue
        vals = g[feature_cols].values.astype('float32')
        target = g[TARGET_COL].values.astype('float32')
        for s in range(0, len(g) - lookback):
            X.append(vals[s:s+lookback])
            # y_{t+1}를 선호, 없으면 마지막 시점으로 대체
            idx = s + lookback
            if idx < len(g):
                y.append(target[idx])
            else:
                y.append(target[idx-1])
    if not X:
        return np.zeros((0, lookback, len(feature_cols)), dtype='float32'), np.zeros((0,), dtype='float32'), scaler
    return np.stack(X), np.array(y), scaler

def build_lstm_model(input_dim: int, hidden: int = 64, layers_n: int = 2, dropout: float = 0.1):
    inputs = keras.Input(shape=(None, input_dim))
    x = inputs
    for i in range(layers_n - 1):
        x = layers.LSTM(hidden, return_sequences=True, dropout=dropout)(x)
    x = layers.LSTM(hidden, return_sequences=False, dropout=dropout)(x)
    x = layers.Dense(hidden//2, activation='relu')(x)
    x = layers.Dropout(dropout)(x)
    outputs = layers.Dense(1, activation='linear')(x)
    model = keras.Model(inputs, outputs)
    model.compile(optimizer=keras.optimizers.Adam(1e-3), loss='mse')
    return model

def save_checkpoint(path: str, model: keras.Model, scaler: StandardScaler1D, meta: Dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    model_path = path if path.endswith('.keras') else path + '.keras'
    model.save(model_path)
    with open(model_path + '.meta.json', 'w', encoding='utf-8') as f:
        json.dump({'scaler': scaler.to_dict(), 'meta': meta}, f, ensure_ascii=False, indent=2)

def load_checkpoint(path: str):
    model_path = path if path.endswith('.keras') else path + '.keras'
    model = keras.models.load_model(model_path)
    with open(model_path + '.meta.json', 'r', encoding='utf-8') as f:
        meta_all = json.load(f)
    scaler = StandardScaler1D.from_dict(meta_all['scaler'])
    meta = meta_all.get('meta', {})
    return model, scaler, meta
