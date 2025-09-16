#!/usr/bin/env python3
"""LSTM 수량 예측 템플릿(간단) - 학습 스크립트
입력: models/data/lstm_forecast/train.csv
출력: models/data/lstm_forecast/quick_stats.json (간단 지표)
"""
import os, json
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA = os.path.join(ROOT, 'data', 'lstm_forecast', 'train.csv')
OUT = os.path.join(ROOT, 'data', 'lstm_forecast', 'quick_stats.json')


def main():
    df = pd.read_csv(DATA, encoding='utf-8-sig')
    info = {
        'rows': int(len(df)),
        'pairs': int(df[['shelter_id','relief_item_id']].drop_duplicates().shape[0]) if {'shelter_id','relief_item_id'}.issubset(df.columns) else 0,
        'date_range': [str(df['date'].min()) if 'date' in df.columns else None, str(df['date'].max()) if 'date' in df.columns else None],
        'target_mean': float(df['y_t'].mean()) if 'y_t' in df.columns else None
    }
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(info, f, ensure_ascii=False, indent=2)
    print('LSTM quick stats:', info)

if __name__ == '__main__':
    main()
