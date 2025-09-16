#!/usr/bin/env python3
"""추천+수량 산정 데모
- RECS00(간이) 후보 아이템: 최근 인기 상위 K
- LSTM으로 각 후보 horizon 합계 예측 → 안전재고율 반영 수량 산정
"""
import os, json
import pandas as pd
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
LSTM_TRAIN = os.path.join(ROOT, 'data', 'lstm_forecast', 'train.csv')
PRED_OUT = os.path.join(ROOT, 'data', 'lstm_forecast', 'predictions.json')

from predict_lstm import main as predict_main


def topk_candidates(df: pd.DataFrame, shelter_id: str, k: int = 5):
    sub = df[df['shelter_id'] == shelter_id]
    pop = sub.groupby('relief_item_id')['y_t'].sum().reset_index().sort_values('y_t', ascending=False)
    return list(pop.head(k)['relief_item_id'])


def recommend_with_quantity(shelter_id: str, horizon: int = 7, k: int = 5, alpha: float = 0.2):
    df = pd.read_csv(LSTM_TRAIN, encoding='utf-8-sig')
    if df.empty:
        raise SystemExit('lstm_forecast/train.csv 이 비어있습니다.')
    # 후보 아이템 추출(간단 인기기반)
    cand_items = topk_candidates(df, shelter_id, k=k)
    results = []
    for item in cand_items:
        # predict_lstm.py를 함수로 재사용하기보단 간단 호출: 여기선 직접 호출 대신 동일 로직 구현 권장
        # 데모 목적상 스크립트 호출은 생략하고, 사용자는 실제 서비스에선 predict 함수를 재사용하세요.
        os.system(f"python {os.path.join(os.path.dirname(__file__), 'predict_lstm.py')} --shelter_id {shelter_id} --relief_item_id {item} --horizon {horizon}")
        with open(PRED_OUT, 'r', encoding='utf-8') as f:
            pred = json.load(f)
        results.append({
            'relief_item_id': item,
            'recommended_quantity': pred.get('recommended_quantity'),
            'pred_sum': sum(p['yhat'] for p in pred.get('preds', []))
        })
    return results


if __name__ == '__main__':
    # 가장 데이터 많은 shelter를 자동 선택
    df = pd.read_csv(LSTM_TRAIN, encoding='utf-8-sig')
    if df.empty:
        raise SystemExit('lstm_forecast/train.csv 이 비어있습니다.')
    sid = df.groupby('shelter_id').size().sort_values(ascending=False).index[0]
    out = recommend_with_quantity(shelter_id=sid, horizon=7, k=5, alpha=0.2)
    print('추천+수량 산정 결과:')
    for r in out:
        print(r)
