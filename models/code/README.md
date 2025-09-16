# 이어드림 모델 베이스라인 실행 가이드

이 디렉터리는 `models/data`에서 생성된 CSV 데이터셋을 사용해 간단한 베이스라인/통계 스크립트를 실행합니다.

## 사전 조건
1) 데이터셋 생성이 완료되어 있어야 합니다.
- `models/data/build_datasets.py` 실행으로 `models/data/*/train.csv`가 준비되어 있어야 합니다.

2) 패키지 설치
```powershell
python -m pip install -r tools\requirements.txt
```

## 스크립트
- RECS01 매칭: `train_recs01_baseline.py`
  - 입력: `models/data/recs01_matching/train.csv`
  - 출력: `models/data/recs01_matching/model_metrics.json`

- RECS00 추천: `train_recs00_baseline.py`
  - 입력: `models/data/recs00_item_rec/train.csv`
  - 출력: `models/data/recs00_item_rec/model_metrics.json`

- LSTM 템플릿: `train_lstm_template.py`
  - 입력: `models/data/lstm_forecast/train.csv`
  - 출력: `models/data/lstm_forecast/quick_stats.json`

- LSTM 학습(Keras): `train_lstm.py`
  - 입력: `models/data/lstm_forecast/train.csv`
  - 출력: `models/data/lstm_forecast/model.keras`(+`.meta.json`), `quick_stats.json`

- LSTM 예측(Keras): `predict_lstm.py`
  - 입력: `models/data/lstm_forecast/train.csv`, `model.ckpt`
  - 출력: `models/data/lstm_forecast/predictions.json`

## 실행 예시
```powershell
python models\code\train_recs01_baseline.py
python models\code\train_recs00_baseline.py
python models\code\train_lstm_template.py
python models\code\train_lstm.py --epochs 5 --lookback 28
python models\code\predict_lstm.py --horizon 7
```

## 참고
- RECS01의 라벨이 단일 클래스인 경우 ROC/PR 계산을 생략합니다. 데이터 생성 시 네거티브 샘플 수를 조절하거나 라벨 규칙을 조정해 보세요.
- 모든 CSV는 UTF-8-SIG 인코딩으로 저장됩니다.
 - LSTM은 Keras(TensorFlow)로 동작합니다. CPU 기준 설치는 `tensorflow==2.15.0`입니다.
