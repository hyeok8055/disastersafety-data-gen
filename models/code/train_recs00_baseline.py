#!/usr/bin/env python3
"""RECS00 대피소 조건 추천 베이스라인: 간단 GBDT(Classifier)
입력: models/data/recs00_item_rec/train.csv
출력: models/data/recs00_item_rec/model_metrics.json
"""
import os, json
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, average_precision_score
from sklearn.ensemble import GradientBoostingClassifier

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA = os.path.join(ROOT, 'data', 'recs00_item_rec', 'train.csv')
OUT = os.path.join(ROOT, 'data', 'recs00_item_rec', 'model_metrics.json')


def main():
    df = pd.read_csv(DATA, encoding='utf-8-sig')
    y = df['label']
    feature_cols = [c for c in ['consumed_days','consumed_qty','daily_rate','total_requested','total_remaining','urgent','popularity'] if c in df.columns]
    X = df[feature_cols].fillna(0)
    classes = y.unique()
    if len(classes) < 2:
        metrics = {
            'note': 'single-class labels; skipped ROC/PR',
            'positive_rate': float(y.mean()),
            'features': feature_cols,
            'samples': int(len(df))
        }
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with open(OUT, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, ensure_ascii=False, indent=2)
        print('RECS00 baseline metrics:', metrics)
        return
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    clf = GradientBoostingClassifier(random_state=42)
    clf.fit(X_train, y_train)
    proba = clf.predict_proba(X_test)[:,1]

    metrics = {}
    try:
        metrics['roc_auc'] = float(roc_auc_score(y_test, proba))
    except Exception as e:
        metrics['roc_auc'] = None
        metrics['roc_auc_error'] = str(e)
    try:
        metrics['pr_auc'] = float(average_precision_score(y_test, proba))
    except Exception as e:
        metrics['pr_auc'] = None
        metrics['pr_auc_error'] = str(e)
    metrics['features'] = feature_cols
    metrics['samples'] = int(len(df))
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)
    print('RECS00 baseline metrics:', metrics)

if __name__ == '__main__':
    main()
