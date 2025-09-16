#!/usr/bin/env python3
"""LSTM 수량 예측 학습 스크립트 (Keras)
입력: models/data/lstm_forecast/train.csv
출력: models/data/lstm_forecast/model.keras(+meta), quick_stats.json
"""
import os
import json
import argparse
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split

from lstm_utils import window_sequences, build_lstm_model, save_checkpoint, FEATURE_COLS_DEFAULT, CATEGORICAL_PREFIXES

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA = os.path.join(ROOT, 'data', 'lstm_forecast', 'train.csv')
OUT_DIR = os.path.join(ROOT, 'data', 'lstm_forecast')
CKPT = os.path.join(OUT_DIR, 'model')
STATS = os.path.join(OUT_DIR, 'quick_stats.json')


def main():
    parser = argparse.ArgumentParser(description='LSTM 수량 예측 학습 (Keras)')
    parser.add_argument('--lookback', type=int, default=28)
    parser.add_argument('--batch_size', type=int, default=256)
    parser.add_argument('--epochs', type=int, default=10)
    parser.add_argument('--hidden', type=int, default=64)
    parser.add_argument('--layers', type=int, default=2)
    parser.add_argument('--dropout', type=float, default=0.1)
    parser.add_argument('--feature_cols', type=str, default=','.join(FEATURE_COLS_DEFAULT))
    args = parser.parse_args()

    df = pd.read_csv(DATA, encoding='utf-8-sig')
    if df.empty:
        raise SystemExit('lstm_forecast/train.csv 이 비어있습니다.')

    feature_cols = [c for c in args.feature_cols.split(',') if c in df.columns]
    if not feature_cols:
        feature_cols = FEATURE_COLS_DEFAULT
    # 자동 포함: seasonality_/disaster_severity_/weather_ 접두어 컬럼
    auto_cat = [c for c in df.columns if any(c.startswith(p) for p in CATEGORICAL_PREFIXES)]
    # 중복 제거, 순서 유지
    seen = set()
    all_features = []
    for c in feature_cols + auto_cat:
        if c not in seen:
            all_features.append(c)
            seen.add(c)
    feature_cols = all_features

    # pair 기준 스플릿
    pairs = df[['shelter_id','relief_item_id']].drop_duplicates()
    train_pairs, val_pairs = train_test_split(pairs, test_size=0.2, random_state=42)
    df_train = df.merge(train_pairs, on=['shelter_id','relief_item_id'])
    df_val = df.merge(val_pairs, on=['shelter_id','relief_item_id'])

    X_tr, y_tr, scaler_tr = window_sequences(df_train, lookback=args.lookback, feature_cols=feature_cols)
    X_va, y_va, _ = window_sequences(df_val, lookback=args.lookback, feature_cols=feature_cols)

    if len(X_tr) == 0 or len(X_va) == 0:
        raise SystemExit('학습/검증 시퀀스가 부족합니다. 데이터 수를 늘리거나 lookback을 줄여보세요.')

    model = build_lstm_model(input_dim=X_tr.shape[-1], hidden=args.hidden, layers_n=args.layers, dropout=args.dropout)

    os.makedirs(OUT_DIR, exist_ok=True)
    history = model.fit(
        X_tr, y_tr,
        validation_data=(X_va, y_va),
        epochs=args.epochs,
        batch_size=args.batch_size,
        verbose=1
    )

    # 최종 모델 저장(+스케일러/메타)
    val_loss = float(history.history['val_loss'][-1]) if 'val_loss' in history.history else None
    save_checkpoint(CKPT, model, scaler_tr, meta={
        'feature_cols': feature_cols,
        'continuous_cols': [c for c in feature_cols if c in FEATURE_COLS_DEFAULT],
        'lookback': args.lookback,
        'hidden': args.hidden,
        'layers': args.layers,
        'dropout': args.dropout,
        'val_loss': val_loss
    })

    info = {
        'rows': int(len(df)),
        'pairs': int(pairs.shape[0]),
        'val_mse': val_loss,
        'lookback': args.lookback,
        'features': feature_cols
    }
    with open(STATS, 'w', encoding='utf-8') as f:
        json.dump(info, f, ensure_ascii=False, indent=2)
    print('LSTM train quick stats:', info)

if __name__ == '__main__':
    main()
