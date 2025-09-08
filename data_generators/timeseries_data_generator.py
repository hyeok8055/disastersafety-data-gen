# LSTM 모델용 시계열 데이터 생성 모듈
# 대피소 통계, 소비 패턴, 수요 예측 데이터 생성

import pandas as pd
import numpy as np
from faker import Faker
from datetime import datetime, timedelta
import random
import math
import sys
import os

# 설정 파일 import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.data_config import *

class TimeSeriesDataGenerator:
    def __init__(self, seed=42):
        self.fake = Faker('ko_KR')
        Faker.seed(seed)
        random.seed(seed)
        np.random.seed(seed)
        self.config = DataConfig()
        
        # 시계열 데이터 생성을 위한 기준 날짜
        self.start_date = datetime.now() - timedelta(days=self.config.TIMESERIES_DAYS)
        self.end_date = datetime.now()
    
    def _generate_seasonal_pattern(self, days, base_value, amplitude=0.3, noise_level=0.1):
        """계절성 패턴이 있는 시계열 데이터 생성"""
        values = []
        for day in range(days):
            # 연간 계절성 (365일 주기)
            seasonal = amplitude * math.sin(2 * math.pi * day / 365)
            # 주간 패턴 (7일 주기)
            weekly = 0.1 * math.sin(2 * math.pi * day / 7)
            # 노이즈
            noise = random.gauss(0, noise_level)
            # 트렌드 (약간의 증가 추세)
            trend = 0.001 * day
            
            value = base_value * (1 + seasonal + weekly + trend + noise)
            values.append(max(0, value))  # 음수 방지
        
        return values
    
    def generate_demand_predictions(self, shelters_df, relief_items_df):
        """수요 예측 테이블 데이터 생성"""
        predictions = []
        prediction_id = 1
        
        # 각 대피소별로 시계열 데이터 생성
        for _, shelter in shelters_df.iterrows():
            # 각 구호품별로 예측 데이터 생성
            selected_items = relief_items_df.sample(n=random.randint(10, 20))
            
            for _, item in selected_items.iterrows():
                # 기본 수요량 설정 (대피소 규모에 비례)
                base_demand = shelter['capacity'] * random.uniform(0.1, 0.5)
                
                # 시계열 데이터 생성 (일주일 단위)
                for week in range(0, self.config.TIMESERIES_DAYS, 7):
                    prediction_date = self.start_date + timedelta(days=week)
                    
                    # 계절성과 노이즈가 포함된 수요 예측
                    seasonal_factor = 1 + 0.3 * math.sin(2 * math.pi * week / 365)
                    disaster_factor = random.uniform(0.8, 2.0) if random.random() < 0.1 else 1.0
                    
                    predicted_demand = base_demand * seasonal_factor * disaster_factor
                    confidence = random.uniform(0.6, 0.95)
                    
                    prediction = {
                        'prediction_id': f'pred_{prediction_id:08d}',
                        'shelter_id': shelter['shelter_id'],
                        'item_id': item['item_id'],
                        'prediction_date': prediction_date,
                        'predicted_demand': round(predicted_demand, 2),
                        'confidence_score': round(confidence, 3),
                        'prediction_horizon_days': 7,
                        'model_version': f'v{random.randint(1, 5)}.{random.randint(0, 9)}',
                        'created_at': prediction_date - timedelta(days=1),
                        'features_used': ','.join(random.sample(['weather', 'historical', 'seasonal', 'disaster_risk', 'population'], k=random.randint(3, 5)))
                    }
                    predictions.append(prediction)
                    prediction_id += 1
        
        return pd.DataFrame(predictions)
    
    def generate_shelter_statistics(self, shelters_df):
        """대피소 통계 테이블 데이터 생성"""
        statistics = []
        stat_id = 1
        
        for _, shelter in shelters_df.iterrows():
            # 일별 통계 데이터 생성
            current_occupancy = 0
            
            for day in range(self.config.TIMESERIES_DAYS):
                stat_date = self.start_date + timedelta(days=day)
                
                # 점유율 변화 시뮬레이션
                daily_change = random.randint(-10, 15)
                current_occupancy = max(0, min(shelter['capacity'], current_occupancy + daily_change))
                
                # 재난 발생 시 급격한 증가
                if random.random() < 0.02:  # 2% 확률로 재난 발생
                    current_occupancy = min(shelter['capacity'], current_occupancy + random.randint(50, 200))
                
                statistic = {
                    'stat_id': f'stat_{stat_id:08d}',
                    'shelter_id': shelter['shelter_id'],
                    'date': stat_date,
                    'occupancy_count': current_occupancy,
                    'occupancy_rate': round(current_occupancy / shelter['capacity'], 3),
                    'new_arrivals': max(0, daily_change) if daily_change > 0 else 0,
                    'departures': abs(daily_change) if daily_change < 0 else 0,
                    'total_meals_served': current_occupancy * 3 + random.randint(-10, 20),
                    'total_supplies_distributed': random.randint(0, current_occupancy * 2),
                    'emergency_requests': random.randint(0, 5) if random.random() < 0.1 else 0,
                    'staff_count': random.randint(5, 20),
                    'volunteer_count': random.randint(0, 30),
                    'created_at': stat_date + timedelta(hours=23, minutes=59)
                }
                statistics.append(statistic)
                stat_id += 1
        
        return pd.DataFrame(statistics)
    
    def generate_consumption_patterns(self, shelters_df, relief_items_df):
        """소비 패턴 테이블 데이터 생성"""
        patterns = []
        pattern_id = 1
        
        for _, shelter in shelters_df.iterrows():
            # 주요 구호품에 대한 소비 패턴 생성
            selected_items = relief_items_df.sample(n=random.randint(15, 25))
            
            for _, item in selected_items.iterrows():
                # 기본 소비량 설정
                base_consumption = random.uniform(10, 100)
                
                # 주별 소비 패턴 생성
                for week in range(0, self.config.TIMESERIES_DAYS, 7):
                    pattern_date = self.start_date + timedelta(days=week)
                    
                    # 계절성 및 트렌드 적용
                    seasonal_multiplier = 1 + 0.2 * math.sin(2 * math.pi * week / 365)
                    trend_multiplier = 1 + 0.001 * week  # 약간의 증가 추세
                    
                    # 구호품 카테고리별 특성 반영
                    if item['category'] == 'food':
                        consumption_rate = base_consumption * seasonal_multiplier * trend_multiplier
                    elif item['category'] == 'clothing':
                        # 겨울철 의류 수요 증가
                        winter_factor = 1.5 if (week % 365) in range(300, 365) or (week % 365) in range(0, 90) else 1.0
                        consumption_rate = base_consumption * winter_factor * trend_multiplier
                    else:
                        consumption_rate = base_consumption * trend_multiplier
                    
                    # 노이즈 추가
                    consumption_rate *= random.uniform(0.7, 1.3)
                    
                    pattern = {
                        'pattern_id': f'pattern_{pattern_id:08d}',
                        'shelter_id': shelter['shelter_id'],
                        'item_id': item['item_id'],
                        'date': pattern_date,
                        'consumption_rate': round(consumption_rate, 2),
                        'peak_hour': random.randint(8, 20),
                        'consumption_variance': round(random.uniform(0.1, 0.5), 3),
                        'day_of_week': pattern_date.weekday(),
                        'is_holiday': random.random() < 0.1,
                        'weather_condition': random.choice(['sunny', 'rainy', 'cloudy', 'snowy']),
                        'temperature': random.randint(-10, 35),
                        'created_at': pattern_date + timedelta(hours=23, minutes=59)
                    }
                    patterns.append(pattern)
                    pattern_id += 1
        
        return pd.DataFrame(patterns)
    
    def generate_prediction_accuracy(self, demand_predictions_df):
        """예측 정확도 테이블 데이터 생성"""
        accuracies = []
        accuracy_id = 1
        
        # 예측 데이터의 일부에 대해 정확도 데이터 생성
        sample_predictions = demand_predictions_df.sample(n=min(1000, len(demand_predictions_df)))
        
        for _, prediction in sample_predictions.iterrows():
            # 실제 수요량 시뮬레이션 (예측값 기준으로 변동)
            actual_demand = prediction['predicted_demand'] * random.uniform(0.7, 1.3)
            
            # 정확도 계산
            mae = abs(actual_demand - prediction['predicted_demand'])
            mape = (mae / max(actual_demand, 1)) * 100
            rmse = mae * random.uniform(0.8, 1.2)  # 근사치
            
            accuracy = {
                'accuracy_id': f'acc_{accuracy_id:08d}',
                'prediction_id': prediction['prediction_id'],
                'actual_demand': round(actual_demand, 2),
                'predicted_demand': prediction['predicted_demand'],
                'absolute_error': round(mae, 2),
                'percentage_error': round(mape, 2),
                'squared_error': round(mae ** 2, 2),
                'evaluation_date': prediction['prediction_date'] + timedelta(days=prediction['prediction_horizon_days']),
                'model_version': prediction['model_version'],
                'created_at': prediction['prediction_date'] + timedelta(days=prediction['prediction_horizon_days'] + 1)
            }
            accuracies.append(accuracy)
            accuracy_id += 1
        
        return pd.DataFrame(accuracies)
    
    def generate_all_timeseries_data(self, shelters_df, relief_items_df):
        """모든 시계열 데이터 생성 및 반환"""
        print("수요 예측 데이터 생성 중...")
        demand_predictions_df = self.generate_demand_predictions(shelters_df, relief_items_df)
        
        print("대피소 통계 데이터 생성 중...")
        shelter_statistics_df = self.generate_shelter_statistics(shelters_df)
        
        print("소비 패턴 데이터 생성 중...")
        consumption_patterns_df = self.generate_consumption_patterns(shelters_df, relief_items_df)
        
        print("예측 정확도 데이터 생성 중...")
        prediction_accuracy_df = self.generate_prediction_accuracy(demand_predictions_df)
        
        return {
            'demand_predictions': demand_predictions_df,
            'shelter_statistics': shelter_statistics_df,
            'consumption_patterns': consumption_patterns_df,
            'prediction_accuracy': prediction_accuracy_df
        }

if __name__ == "__main__":
    # 테스트용 더미 데이터
    shelters_data = {
        'shelter_id': ['shelter_0001', 'shelter_0002'],
        'capacity': [100, 200]
    }
    shelters_df = pd.DataFrame(shelters_data)
    
    relief_items_data = {
        'item_id': ['item_00001', 'item_00002', 'item_00003'],
        'category': ['food', 'clothing', 'medical']
    }
    relief_items_df = pd.DataFrame(relief_items_data)
    
    generator = TimeSeriesDataGenerator()
    data = generator.generate_all_timeseries_data(shelters_df, relief_items_df)
    
    # 데이터 요약 출력
    for table_name, df in data.items():
        print(f"\n{table_name}: {len(df)} 레코드 생성")
        print(f"컬럼: {list(df.columns)}")
        print(f"샘플 데이터:\n{df.head(2)}")