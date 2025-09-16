#!/usr/bin/env python3
"""
이어드림 모델 학습용 데이터셋 빌더
- 입력: tools/generate_fake_data(_csv).py 로 생성되는 원천 테이블(JSON/CSV)
- 실제 전국 대피소 CSV(우선) + 합성 데이터 결합
- 출력: models/data/ 아래 3개 모델(RECS01/RECS00/LSTM)용 학습 데이터 산출물

사용 예시(Windows PowerShell):
  python models/data/build_datasets.py --real_shelter_csv "tools/대피소추가_API/shelter_schema_전국.csv" --seed 42

출력 폴더 구조:
  models/data/
    raw/  # 원천 스냅샷(copy)
    recs01_matching/
            train.csv, schema.json
    recs00_item_rec/
            train.csv, schema.json
    lstm_forecast/
            train.csv, stats.json, schema.json
"""
import os
import json
import argparse
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
TOOLS_DIR = os.path.join(ROOT, 'tools')
OUTPUT_CSV_DIR = os.path.join(TOOLS_DIR, 'output_csv')  # 기본값(옵션으로 덮어씀)
RAW_DIR = os.path.join(os.path.dirname(__file__), 'raw')

# 안전한 디렉토리 생성
os.makedirs(RAW_DIR, exist_ok=True)


def _read_csv(path):
    return pd.read_csv(path, encoding='utf-8-sig') if os.path.exists(path) else None


def load_or_generate_sources(sources_dir: str, real_shelter_csv: str | None, seed: int | None):
    """지정된 sources_dir에서 원천 CSV를 로드합니다. 없으면 생성 안내를 제공합니다."""
    # 1) 지정 경로에서 사용
    files = {
        'users': os.path.join(sources_dir, 'users.csv'),
        'shelters': os.path.join(sources_dir, 'shelters.csv'),
        'relief_items': os.path.join(sources_dir, 'relief_items.csv'),
        'wishes': os.path.join(sources_dir, 'user_donation_wishes.csv'),
        'requests': os.path.join(sources_dir, 'shelter_relief_requests.csv'),
        'matches': os.path.join(sources_dir, 'donation_matches.csv'),
        'incidents': os.path.join(sources_dir, 'disaster_incidents.csv'),
        'consumptions': os.path.join(sources_dir, 'consumption_info.csv'),
    }
    have_all = all(os.path.exists(p) for p in files.values())

    # 2) 없으면 사용자에게 생성 안내 (자동 실행은 argparse 구조상 안전하지 않음)
    if not have_all:
        raise RuntimeError(
            '원천 CSV가 없습니다. 먼저 tools/generate_fake_data_csv.py를 실행해 주세요. '
            '예: python tools/generate_fake_data_csv.py --real_shelter_csv "tools/대피소추가_API/shelter_schema_전국.csv" --out tools/output_csv')

    # 3) 로드
    dfs = {k: _read_csv(v) for k, v in files.items()}

    # 4) raw 백업
    for k, df in dfs.items():
        if df is not None:
            df.to_csv(os.path.join(RAW_DIR, f'{k}.csv'), index=False, encoding='utf-8-sig')

    return dfs


def _ensure_min_rows(df: pd.DataFrame, min_rows: int, jitter_cols: list[str] | None = None, jitter_scale: float = 0.05) -> pd.DataFrame:
    if len(df) >= min_rows or len(df) == 0:
        return df
    reps = int(np.ceil(min_rows / len(df)))
    aug = pd.concat([df] * reps, ignore_index=True)
    aug = aug.iloc[:min_rows].copy()
    # 수치형 피처에 약간의 잡음 추가하여 완전 중복 방지
    if jitter_cols:
        for c in jitter_cols:
            if c in aug.columns:
                base = aug[c].astype(float).fillna(0)
                noise = np.random.normal(loc=0.0, scale=(np.std(base) + 1e-6) * jitter_scale, size=len(base))
                aug[c] = (base + noise).clip(lower=0)
    return aug


def build_recs01_matching(dfs: dict, out_dir: str, min_rows: int = 30000):
    os.makedirs(out_dir, exist_ok=True)
    users = dfs['users']
    wishes = dfs['wishes']
    requests = dfs['requests']
    shelters = dfs['shelters']
    items = dfs['relief_items']
    matches = dfs['matches']

    # 학습용 샘플 스키마: (user_id, wish_id, request_id, label, features...)
    req_need = requests.copy()
    req_need['remaining_need'] = (req_need['requested_quantity']
                                  - req_need['current_stock']
                                  - req_need.get('total_matched_quantity', 0)).clip(lower=0)

    # 후보 조인: 동일 item 기반
    cand = wishes.merge(req_need, left_on='relief_item_id', right_on='relief_item_id', how='inner', suffixes=('_wish','_req'))

    # 거리 계산: 사용자 좌표가 없으므로 간단한 근사 - 한국 범위 난수 좌표 부여 후 계산
    KO_LAT_MIN, KO_LAT_MAX = 33.0, 38.6
    KO_LON_MIN, KO_LON_MAX = 124.6, 131.9
    def _rand_latlon(n):
        lat = np.random.uniform(KO_LAT_MIN, KO_LAT_MAX, size=n)
        lon = np.random.uniform(KO_LON_MIN, KO_LON_MAX, size=n)
        return lat, lon
    def _haversine(lat1, lon1, lat2, lon2):
        R = 6371.0
        lat1 = np.radians(lat1); lon1 = np.radians(lon1)
        lat2 = np.radians(lat2); lon2 = np.radians(lon2)
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = np.sin(dlat/2)**2 + np.cos(lat1)*np.cos(lat2)*np.sin(dlon/2)**2
        c = 2*np.arcsin(np.sqrt(a))
        return R * c
    # 사용자별 난수 좌표 부여(세션 수준 근사). 실제 서비스에서는 지오코딩/최근 위치 사용 권장
    user_coords = {}
    for uid in cand['user_id'].unique():
        lat, lon = _rand_latlon(1)
        user_coords[uid] = (float(lat[0]), float(lon[0]))
    cand['user_lat'] = cand['user_id'].map(lambda u: user_coords.get(u, (np.nan, np.nan))[0])
    cand['user_lon'] = cand['user_id'].map(lambda u: user_coords.get(u, (np.nan, np.nan))[1])
    cand['distance_km'] = _haversine(cand['user_lat'], cand['user_lon'], cand['latitude'], cand['longitude']) if {'latitude','longitude'}.issubset(cand.columns) else np.nan

    # 라벨: 실제 매칭 존재 여부
    pos = matches[['donation_wish_id','relief_request_id']].drop_duplicates()
    pos['label'] = 1
    cand = cand.merge(pos, left_on=['wish_id','request_id'], right_on=['donation_wish_id','relief_request_id'], how='left')
    cand['label'] = cand['label'].fillna(0).astype(int)

    # 피처 예시
    # merge 후 공통 컬럼은 접미사가 붙음: remaining_quantity_wish / remaining_quantity_req
    wish_rem_col = 'remaining_quantity_wish' if 'remaining_quantity_wish' in cand.columns else (
        'remaining_quantity' if 'remaining_quantity' in cand.columns else None
    )
    if wish_rem_col is None:
        cand['wish_remaining_quantity'] = 0
    else:
        cand['wish_remaining_quantity'] = cand[wish_rem_col]

    # need_ratio = min(기부자 잔량, 요청 잔여 필요)/요청 잔여 필요
    denom = cand['remaining_need'].replace(0, np.nan)
    cand['need_ratio'] = np.minimum(cand['wish_remaining_quantity'], cand['remaining_need']) / denom
    cand['need_ratio'] = cand['need_ratio'].fillna(0).clip(0,1)

    # urgency_level: 범주 → 수치
    urgency_map = {'높음': 1.0, '중간': 0.6, '낮음': 0.3}
    cand['urgency_score'] = cand['urgency_level'].map(urgency_map).fillna(0.5)

    # 선택 컬럼 정리
    cols = [
        'user_id','wish_id','request_id','relief_item_id',
        'shelter_id','requested_quantity','current_stock','wish_remaining_quantity','remaining_need',
        'urgency_score','need_ratio','distance_km','label'
    ]
    # 누락 컬럼 방어
    cand_out = cand.reindex(columns=[c for c in cols if c in cand.columns]).copy()
    # 최소 행수 보장(증강)
    cand_out = _ensure_min_rows(cand_out, min_rows, jitter_cols=['requested_quantity','current_stock','wish_remaining_quantity','remaining_need','urgency_score','need_ratio','distance_km'])
    # 저장: CSV 고정
    cand_out.to_csv(os.path.join(out_dir, 'train.csv'), index=False, encoding='utf-8-sig')

    # 스키마/피처 정의 저장
    schema = {
        'primary_key': ['user_id','wish_id','request_id'],
        'label': 'label',
        'features': ['requested_quantity','current_stock','wish_remaining_quantity','remaining_need','urgency_score','need_ratio','distance_km']
    }
    with open(os.path.join(out_dir, 'schema.json'),'w',encoding='utf-8') as f:
        json.dump(schema, f, ensure_ascii=False, indent=2)


def build_recs00_item_rec(dfs: dict, out_dir: str, min_rows: int = 30000):
    os.makedirs(out_dir, exist_ok=True)
    shelters = dfs['shelters']
    items = dfs['relief_items']
    consumptions = dfs['consumptions']
    requests = dfs['requests']

    # 대피소-품목 pair 생성: 과거 소비 또는 현재 요청 존재
    cons_item = consumptions.groupby(['shelter_id','relief_item_id']).agg(
        consumed_days=('duration_days','sum'),
        consumed_qty=('consumed_quantity','sum'),
        daily_rate=('daily_consumption_rate','mean'),
        seasons=('seasonality', lambda x: ','.join(sorted(set(x.astype(str)))))
    ).reset_index()

    req_item = requests.groupby(['shelter_id','relief_item_id']).agg(
        total_requested=('requested_quantity','sum'),
        total_remaining=('remaining_quantity','sum'),
        urgent=('urgent_quantity','sum')
    ).reset_index()

    pair = cons_item.merge(req_item, on=['shelter_id','relief_item_id'], how='outer').fillna(0)

    # 프로필 피처(간단): occupancy_rate는 0으로 초기화되어 있어 요청/소비 스케일로 대체 특징 사용
    pair['popularity'] = pair['consumed_qty'] + pair['total_requested']

    # 라벨: 다음 기간 추천 채택 여부 대용 → 현재 remaining > 0이면 1로 간주 (베이스라인)
    pair['label'] = (pair['total_remaining'] > 0).astype(int)

    # 출력 저장
    # 최소 행수 보장(증강)
    pair = _ensure_min_rows(pair, min_rows, jitter_cols=['consumed_days','consumed_qty','daily_rate','total_requested','total_remaining','urgent','popularity'])
    pair.to_csv(os.path.join(out_dir, 'train.csv'), index=False, encoding='utf-8-sig')
    schema = {
        'primary_key': ['shelter_id','relief_item_id'],
        'label': 'label',
        'features': ['consumed_days','consumed_qty','daily_rate','total_requested','total_remaining','urgent','popularity']
    }
    with open(os.path.join(out_dir, 'schema.json'),'w',encoding='utf-8') as f:
        json.dump(schema, f, ensure_ascii=False, indent=2)


def build_lstm_forecast(dfs: dict, out_dir: str, lookback: int = 28, min_rows: int = 30000):
    os.makedirs(out_dir, exist_ok=True)
    consumptions = dfs['consumptions']
    shelters = dfs['shelters']

    # 일단위 패널 생성: consumption 기간을 일 단위로 펼치기
    rows = []
    for _, r in consumptions.iterrows():
        start = pd.to_datetime(r['start_date'])
        end = pd.to_datetime(r['end_date'])
        days = (end - start).days
        if days <= 0:
            continue
        base = r['daily_consumption_rate'] if 'daily_consumption_rate' in r else r['consumed_quantity']/max(1,days)
        for d in range(days):
            date = (start + pd.Timedelta(days=d)).date()
            rows.append({
                'shelter_id': r['shelter_id'],
                'relief_item_id': r['relief_item_id'],
                'date': date,
                'y_t': base,
                'seasonality': r.get('seasonality',''),
                'disaster_severity': r.get('disaster_severity','중간'),
                'weather': r.get('weather_conditions','일반')
            })
    panel = pd.DataFrame(rows)
    if panel.empty:
        # 패널이 비면 더미 방어
        panel = pd.DataFrame(columns=['shelter_id','relief_item_id','date','y_t'])

    # 이동통계 피처 생성
    panel = panel.sort_values(['shelter_id','relief_item_id','date'])
    def add_roll(df):
        df['cons_ma7'] = df['y_t'].rolling(window=7, min_periods=1).mean()
        df['cons_ma14'] = df['y_t'].rolling(window=14, min_periods=1).mean()
        df['cons_ma28'] = df['y_t'].rolling(window=28, min_periods=1).mean()
        return df
    panel = panel.groupby(['shelter_id','relief_item_id'], group_keys=False).apply(add_roll)

    # 원-핫: 간단 인코딩
    for col in ['seasonality','disaster_severity','weather']:
        if col in panel.columns:
            dummies = pd.get_dummies(panel[col].astype(str), prefix=col)
            panel = pd.concat([panel.drop(columns=[col]), dummies], axis=1)

    # 최소 행수 보장(증강)
    panel = _ensure_min_rows(panel, min_rows, jitter_cols=['y_t','cons_ma7','cons_ma14','cons_ma28'])
    panel.to_csv(os.path.join(out_dir, 'train.csv'), index=False, encoding='utf-8-sig')

    # 통계치 저장(정규화용 예시)
    stats = panel.describe(include='all').to_dict()
    # JSON 직렬화 호환 변환
    def _to_serializable(obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
        if isinstance(obj, (pd.Timestamp,)):
            return obj.isoformat()
        if hasattr(obj, 'isoformat'):
            try:
                return obj.isoformat()
            except Exception:
                return str(obj)
        return obj
    stats_serializable = json.loads(json.dumps(stats, default=_to_serializable))
    with open(os.path.join(out_dir, 'stats.json'),'w',encoding='utf-8') as f:
        json.dump(stats_serializable, f, ensure_ascii=False, indent=2)

    schema = {
        'index': ['shelter_id','relief_item_id','date'],
        'target': 'y_t',
        'features_example': ['cons_ma7','cons_ma14','cons_ma28']
    }
    with open(os.path.join(out_dir, 'schema.json'),'w',encoding='utf-8') as f:
        json.dump(schema, f, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(description='이어드림 모델 학습 데이터셋 빌더')
    parser.add_argument('--real_shelter_csv', type=str, default=os.path.join('tools','대피소추가_API','shelter_schema_전국.csv'))
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--min_rows', type=int, default=30000, help='각 데이터셋 최소 행수(부족 시 부트스트랩 증강)')
    parser.add_argument('--sources_dir', type=str, default=OUTPUT_CSV_DIR, help='원천 CSV 폴더 경로(기본: tools/output_csv)')
    args = parser.parse_args()

    dfs = load_or_generate_sources(args.sources_dir, args.real_shelter_csv, args.seed)

    # RECS01
    build_recs01_matching(dfs, os.path.join(os.path.dirname(__file__), 'recs01_matching'), min_rows=args.min_rows)
    # RECS00
    build_recs00_item_rec(dfs, os.path.join(os.path.dirname(__file__), 'recs00_item_rec'), min_rows=args.min_rows)
    # LSTM
    build_lstm_forecast(dfs, os.path.join(os.path.dirname(__file__), 'lstm_forecast'), min_rows=args.min_rows)

    print('✅ 학습 데이터셋 생성 완료: models/data 아래 하위 폴더를 확인하세요.')


if __name__ == '__main__':
    main()
