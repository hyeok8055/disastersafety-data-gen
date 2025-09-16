# 프로젝트 워크플로우 가이드

이 문서는 "이어드림" 프로젝트의 전체 과정을 단계별로 설명합니다. 원본 대피소 데이터를 시작으로 합성데이터 생성, 학습데이터 구축, LSTM 학습 및 예측까지의 흐름을 안내합니다. 각 단계에서 필요한 명령어와 파일 경로를 포함했습니다.

## 1. 원본 대피소 데이터 준비
- **목적**: 실제 대피소 정보를 기반으로 합성데이터를 만들기 위한 기초 데이터.
- **파일 위치**: `대피소추가_API/` 폴더
  - `shelter_schema_대구.csv`: 대구 지역 대피소 정보.
  - `shelter_schema_전국.csv`: 전국 대피소 정보.
  - `대구_대피소_데이터.csv`: 대구 대피소 상세 데이터.
  - `전국_대피소_데이터.csv`: 전국 대피소 상세 데이터.
- **안내**: 이 데이터는 재난 시 대피소 위치와 정보를 제공합니다. 합성데이터 생성 시 실제 위치를 반영합니다.

## 2. 합성데이터 생성
- **목적**: 실제 데이터를 기반으로 가상의 사용자, 대피소, 구호품, 소비 기록 등을 생성. ML 학습에 사용할 데이터 양을 늘립니다.
- **스크립트**: `tools/generate_fake_data.py` 또는 `tools/generate_fake_data_csv.py`
- **실행 명령어** (Windows PowerShell):
  ```powershell
  # JSON 형식 데이터 생성 (기본)
  python tools/generate_fake_data.py

  # CSV 형식으로 생성 (ML 학습용)
  python tools/generate_fake_data_csv.py --no_auto_adjust
  ```
- **출력 파일**: `tools/output_csv/` 폴더에 CSV 파일들 (users.csv, shelters.csv, consumption_info.csv 등).
- **안내**: `--no_auto_adjust` 옵션으로 대피소 수 제한 없이 데이터를 생성합니다. 생성된 데이터는 실제 대피소 위치를 기반으로 합니다.

## 3. 학습데이터 구축 (LSTM, 추천시스템 등)
- **목적**: 생성된 합성데이터를 ML 모델 학습에 맞게 정리. LSTM용 시계열 데이터와 추천시스템용 데이터셋을 만듭니다.
- **스크립트**: `models/data/build_datasets.py`
- **실행 명령어**:
  ```powershell
  # 기본 실행 (LSTM, RECS00, RECS01 데이터셋 생성)
  python models/data/build_datasets.py

  # 특정 소스 디렉터리 지정
  python models/data/build_datasets.py --sources_dir tools/output_csv
  ```
- **출력 파일**:
  - LSTM: `models/data/lstm_forecast/train.csv` (시계열 패널 데이터).
  - 추천시스템: `models/data/recs00_item_rec/train.csv`, `models/data/recs01_matching/train.csv`.
- **안내**: 이 단계에서 이동평균, 계절/재난/날씨 one-hot 인코딩 등이 자동으로 추가됩니다. LSTM 데이터는 y_t, cons_ma7/14/28 등을 포함합니다.

## 4. LSTM 학습
- **목적**: 구축된 학습데이터로 LSTM 모델을 훈련. 과거 데이터를 보고 미래 소비량을 예측하는 모델을 만듭니다.
- **스크립트**: `models/code/train_lstm.py`
- **실행 명령어**:
  ```powershell
  # 기본 학습 (lookback=28, epochs=10)
  python models/code/train_lstm.py

  # 파라미터 조정 (예: 에포크 5회, 배치 256)
  python models/code/train_lstm.py --epochs 5 --batch_size 256
  ```
- **출력 파일**:
  - 모델: `models/data/lstm_forecast/model.keras`
  - 메타 정보: `models/data/lstm_forecast/model.keras.meta.json` (feature 목록 등)
  - 통계: `models/data/lstm_forecast/quick_stats.json`
- **안내**: 학습 시 자동으로 범주형 feature (seasonality_*, disaster_severity_*, weather_*)를 포함합니다. val_loss가 낮을수록 좋은 모델입니다.

## 5. LSTM 예측
- **목적**: 학습된 모델로 특정 대피소-품목 조합의 미래 소비량을 예측하고 권장 수량을 산출.
- **스크립트**: `models/code/predict_lstm.py`
- **실행 명령어**:
  ```powershell
  # 7일 예측 (자동으로 데이터가 많은 pair 선택)
  python models/code/predict_lstm.py --horizon 7

  # 특정 pair 지정
  python models/code/predict_lstm.py --shelter_id SH_008766 --relief_item_id relief_item_000322 --horizon 7
  ```
- **출력 파일**: `models/data/lstm_forecast/predictions.json` (일별 예측 yhat, 권장 수량 recommended_quantity).
- **안내**: 예측 시 학습 메타를 사용해 동일한 feature를 적용합니다. 결과는 JSON으로 저장되며, 권장 수량은 예측 합계에 20% 여유를 더합니다.

## 전체 워크플로우 요약
1. **준비**: 원본 대피소 데이터 확인 (`대피소추가_API/`).
2. **생성**: 합성데이터 만들기 (`tools/generate_fake_data_csv.py`).
3. **구축**: 학습데이터 정리 (`models/data/build_datasets.py`).
4. **학습**: LSTM 모델 훈련 (`models/code/train_lstm.py`).
5. **예측**: 소비량 예측 (`models/code/predict_lstm.py`).

## 주의사항
- 각 단계는 순서대로 실행하세요. 이전 단계의 출력이 다음 입력으로 사용됩니다.
- 오류 시: 데이터 파일 존재 확인, Python 환경 (TensorFlow 설치) 검증.
- 추가 옵션: `models/code/demo_recommend_with_quantity.py`로 추천 + 수량 데모 실행 가능.

이 가이드를 따라 전체 과정을 진행하면 재난 구호품 수량 예측 시스템을 구축할 수 있습니다. 궁금한 점 있으면 물어보세요!