#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
데이터 생성 설정 파일
재난 안전 더미 데이터 생성을 위한 설정값들
"""

class DataConfig:
    """데이터 생성 설정 클래스"""
    
    # 데이터 생성 규모 설정
    USER_COUNT = 1000      # 사용자 수
    SHELTER_COUNT = 100    # 대피소 수
    RELIEF_ITEM_COUNT = 200  # 구호품 종류 수
    
    # 재난 유형
    DISASTER_TYPES = [
        '지진', '태풍', '홍수', '산불', '폭설', 
        '가뭄', '폭염', '한파', '산사태', '해일'
    ]
    
    # 구호품 카테고리
    RELIEF_CATEGORIES = {
        'food': ['쌀', '라면', '통조림', '생수', '빵', '과자'],
        'clothing': ['티셔츠', '바지', '속옷', '양말', '신발', '외투'],
        'medical': ['반창고', '소독약', '해열제', '마스크', '체온계', '붕대'],
        'daily': ['칫솔', '치약', '비누', '수건', '휴지', '세제'],
        'shelter': ['담요', '베개', '매트', '텐트', '침낭', '랜턴'],
        'hygiene': ['샴푸', '린스', '로션', '생리대', '기저귀', '물티슈'],
        'education': ['노트', '펜', '연필', '지우개', '책', '태블릿'],
        'other': ['배터리', '충전기', '라디오', '손전등', '로프', '공구']
    }
    
    # 지역 정보 (시도)
    REGIONS = [
        '서울특별시', '부산광역시', '대구광역시', '인천광역시',
        '광주광역시', '대전광역시', '울산광역시', '세종특별자치시',
        '경기도', '강원도', '충청북도', '충청남도',
        '전라북도', '전라남도', '경상북도', '경상남도', '제주특별자치도'
    ]
    
    # 사용자 역할
    USER_ROLES = ['donor', 'recipient', 'volunteer', 'admin']
    
    # 배송 상태
    DELIVERY_STATUS = ['pending', 'in_transit', 'delivered', 'failed']
    
    # 추천 알고리즘 타입
    RECOMMENDATION_TYPES = ['content_based', 'collaborative', 'hybrid']

    # 데이터 생성 개수 설정
    DONATION_COUNT = 1000  # 기부 데이터 개수
    REQUEST_COUNT = 500    # 기부 요청 데이터 개수
    BEHAVIOR_COUNT = 2000  # 사용자 행동 데이터 개수
    PREFERENCE_COUNT = 800 # 사용자 선호도 데이터 개수
    RECOMMENDATION_COUNT = 1500  # 추천 로그 데이터 개수
    
    # 시계열 데이터 설정
    TIMESERIES_DAYS = 365  # 시계열 데이터 기간 (일)
    PREDICTION_HORIZON = 30  # 예측 기간 (일)
    
    # 출력 파일 경로
    OUTPUT_DIR = "output"
    
    # CSV 파일명
    CSV_FILES = {
        'users': 'users.csv',
        'shelters': 'shelters.csv',
        'relief_items': 'relief_items.csv',
        'shelter_inventories': 'shelter_inventories.csv',
        'donations': 'donations.csv',
        'donation_requests': 'donation_requests.csv',
        'donation_matches': 'donation_matches.csv',
        'shipments': 'shipments.csv',
        'demand_predictions': 'demand_predictions.csv',
        'shelter_statistics': 'shelter_statistics.csv',
        'consumption_patterns': 'consumption_patterns.csv',
        'prediction_accuracy': 'prediction_accuracy.csv',
        'user_behaviors': 'user_behaviors.csv',
        'user_preferences': 'user_preferences.csv',
        'recommendation_logs': 'recommendation_logs.csv',
        'similarity_matrix': 'similarity_matrix.csv'
    }