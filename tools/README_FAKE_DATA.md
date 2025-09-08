# 가상 데이터 생성기 (Faker - ko_KR)

프로젝트에 맞춘 가상 데이터를 생성하는 간단한 스크립트입니다.

설치:

1. 가상환경을 만든 뒤 아래를 실행하세요.

```powershell
python -m pip install -r tools\requirements.txt
```

tools 폴더 내부에서 사용법 (JSON):

```powershell
python tools\generate_fake_data.py --users 100 --shelters 30 --relief_items 50
```

tools 폴더 내부에서 사용법 (CSV, UTF-8-sig):

```powershell
python generate_fake_data_csv.py --seed 42 --users 200 --shelters 80 --relief_items 160 --wishes 300 --requests 250 --matches 200 --incidents 30 --consumptions 100
```

출력:

- JSON: 프로젝트 루트의 `output/` 폴더에 각 테이블별 JSON 파일 생성
- CSV: 프로젝트 루트의 `output_csv/` 폴더에 각 테이블별 CSV 파일 생성 (인코딩: UTF-8-sig)

노트:
- 좌표는 대한민국 범위 내에서 랜덤 생성합니다.
- Faker의 한국어 로케일(`ko_KR`)을 사용합니다.
- `tools/generate_fake_data.py`에서 생성 로직을 재사용합니다.

Jupyter 노트북:

- `tools/notebooks/generate_fake_data.ipynb` 파일을 통해 단계별 실행과 설명을 제공합니다.
