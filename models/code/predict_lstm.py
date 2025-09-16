#!/usr/bin/env python3
"""LSTM 수량 예측 예측 스크립트 (Keras)
- 특정 (shelter_id, relief_item_id) 페어의 최근 lookback 구간을 읽어 horizon-step 예측
입력: models/data/lstm_forecast/train.csv, model.keras
출력: models/data/lstm_forecast/predictions.json
"""
import os
import json
import argparse
import pandas as pd
import numpy as np

from lstm_utils import load_checkpoint, FEATURE_COLS_DEFAULT

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA = os.path.join(ROOT, 'data', 'lstm_forecast', 'train.csv')
OUT = os.path.join(ROOT, 'data', 'lstm_forecast', 'predictions.json')
CKPT = os.path.join(ROOT, 'data', 'lstm_forecast', 'model')


def main():
    parser = argparse.ArgumentParser(description='LSTM 예측 (Keras)')
    parser.add_argument('--shelter_id', type=str, default=None)
    parser.add_argument('--relief_item_id', type=str, default=None)
    parser.add_argument('--lookback', type=int, default=28)
    parser.add_argument('--horizon', type=int, default=7, help='며칠 예측할지 (오토리그레시브)')
    # feature_cols는 모델이 학습 시 사용한 메타 정보로 강제 일치시킵니다(옵션 제거)
    args = parser.parse_args()

    df = pd.read_csv(DATA, encoding='utf-8-sig')

    # 체크포인트 로드(메타에서 feature_cols/continuous_cols 확보)
    model, scaler, meta = load_checkpoint(CKPT)
    feature_cols = meta.get('feature_cols', FEATURE_COLS_DEFAULT)
    # 혹시 데이터에 없는 컬럼이 있다면 0으로 채워 추가(주로 one-hot 안전장치)
    for c in feature_cols:
        if c not in df.columns:
            df[c] = 0.0

    # 대상 pair 자동 선택(미지정 시 가장 데이터가 많은 페어)
    if not args.shelter_id or not args.relief_item_id:
        cnt = df.groupby(['shelter_id','relief_item_id']).size().reset_index(name='n').sort_values('n', ascending=False)
        if cnt.empty:
            raise SystemExit('예측할 시계열이 없습니다.')
        args.shelter_id = str(cnt.iloc[0]['shelter_id'])
        args.relief_item_id = str(cnt.iloc[0]['relief_item_id'])

    sub = df[(df['shelter_id']==args.shelter_id) & (df['relief_item_id']==args.relief_item_id)].copy()
    sub['date'] = pd.to_datetime(sub['date'])
    sub = sub.sort_values('date')
    if len(sub) < args.lookback:
        raise SystemExit('해당 pair의 데이터가 lookback보다 적습니다.')

    # 마지막 lookback 윈도우 준비 (스케일러 적용)
    window = sub.iloc[-args.lookback:]
    # 연속/범주 분리: 메타에 continuous_cols 있으면 사용
    continuous_cols = meta.get('continuous_cols', [c for c in feature_cols if c in FEATURE_COLS_DEFAULT])
    x_df = window[feature_cols].copy()
    for c in continuous_cols:
        if c in x_df.columns:
            x_df[c] = scaler.transform(x_df[c].values.astype('float32'))
    x = x_df.values.astype('float32')
    x = x[np.newaxis, :, :]  # (1, lookback, feat)

    preds = []
    last_known_date = window['date'].max()
    # y_t 컬럼 인덱스(없다면 0으로 폴백)
    y_idx = feature_cols.index('y_t') if 'y_t' in feature_cols else 0
    for h in range(args.horizon):
        yhat_scaled = model.predict(x, verbose=0).ravel()[0]
        yhat = float(scaler.inverse_transform(yhat_scaled))
        next_date = (last_known_date + pd.Timedelta(days=1)).date()
        preds.append({'date': str(next_date), 'yhat': yhat})

        # 간단한 오토리그레시브 업데이트: y_t만 새 예측으로 대체
        new_row = x[:, -1, :].copy()
        # y_t 위치를 메타 기반 인덱스로 업데이트
        new_row[0, y_idx] = yhat_scaled
        x = np.concatenate([x[:, 1:, :], new_row[:, np.newaxis, :]], axis=1)
        last_known_date = pd.Timestamp(next_date)

    # 권장 수량 예시: 예측 합계 * (1+alpha)
    alpha = 0.2
    recommended_quantity = int(np.ceil(sum(p['yhat'] for p in preds) * (1+alpha)))
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump({'shelter_id': args.shelter_id, 'relief_item_id': args.relief_item_id, 'horizon': args.horizon, 'preds': preds, 'recommended_quantity': recommended_quantity}, f, ensure_ascii=False, indent=2)
    print(f"Saved predictions to {OUT}")


if __name__ == '__main__':
    main()
