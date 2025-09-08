# 추천시스템용 사용자 행동 데이터 생성 모듈
# 사용자 행동 로그, 선호도, 유사도 매트릭스 데이터 생성

import pandas as pd
import numpy as np
from faker import Faker
from datetime import datetime, timedelta
import random
import math
import sys
import os
from scipy.spatial.distance import cosine

# 설정 파일 import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.data_config import *

class RecommendationDataGenerator:
    def __init__(self, seed=42):
        self.fake = Faker('ko_KR')
        self.config = DataConfig()
        Faker.seed(seed)
        random.seed(seed)
        np.random.seed(seed)
        
        # 행동 유형 정의
        self.action_types = [
            'view_shelter', 'view_item', 'donate_item', 'request_item',
            'search_shelter', 'search_item', 'bookmark_shelter', 'share_shelter',
            'rate_shelter', 'review_shelter', 'contact_shelter', 'volunteer_register'
        ]
        
        # 행동 가중치 (추천 알고리즘에서 사용)
        self.action_weights = {
            'view_shelter': 1.0, 'view_item': 1.0, 'donate_item': 5.0, 'request_item': 4.0,
            'search_shelter': 2.0, 'search_item': 2.0, 'bookmark_shelter': 3.0, 'share_shelter': 3.0,
            'rate_shelter': 4.0, 'review_shelter': 4.0, 'contact_shelter': 3.0, 'volunteer_register': 5.0
        }
    
    def generate_user_behaviors(self, users_df, shelters_df, relief_items_df):
        """사용자 행동 테이블 데이터 생성"""
        behaviors = []
        behavior_id = 1
        
        # 각 사용자별로 행동 데이터 생성
        for _, user in users_df.iterrows():
            # 사용자별 활동 수준 결정 (일부는 매우 활발, 일부는 비활발)
            activity_level = np.random.choice(['low', 'medium', 'high'], p=[0.4, 0.4, 0.2])
            
            if activity_level == 'low':
                num_actions = random.randint(1, 10)
            elif activity_level == 'medium':
                num_actions = random.randint(10, 50)
            else:  # high
                num_actions = random.randint(50, 200)
            
            # 사용자의 관심 카테고리 결정
            preferred_categories = random.sample(list(self.config.RELIEF_CATEGORIES.keys()), k=random.randint(1, 3))
            
            for _ in range(num_actions):
                action_type = random.choice(self.action_types)
                action_time = self.fake.date_time_between(start_date='-6m', end_date='now')
                
                # 행동 유형에 따른 대상 결정
                if 'shelter' in action_type:
                    target_id = random.choice(shelters_df['shelter_id'].tolist())
                    target_type = 'shelter'
                elif 'item' in action_type:
                    # 선호 카테고리에서 아이템 선택 (70% 확률)
                    if random.random() < 0.7 and preferred_categories:
                        preferred_cat = random.choice(preferred_categories)
                        cat_items = relief_items_df[relief_items_df['category'] == preferred_cat]
                        if not cat_items.empty:
                            target_id = random.choice(cat_items['item_id'].tolist())
                        else:
                            target_id = random.choice(relief_items_df['item_id'].tolist())
                    else:
                        target_id = random.choice(relief_items_df['item_id'].tolist())
                    target_type = 'item'
                else:
                    # 기타 행동
                    target_id = random.choice(shelters_df['shelter_id'].tolist())
                    target_type = 'shelter'
                
                # 세션 정보
                session_id = f'session_{random.randint(1, 10000):06d}'
                
                behavior = {
                    'behavior_id': f'behavior_{behavior_id:08d}',
                    'user_id': user['user_id'],
                    'action_type': action_type,
                    'target_id': target_id,
                    'target_type': target_type,
                    'session_id': session_id,
                    'timestamp': action_time,
                    'duration_seconds': random.randint(5, 300) if 'view' in action_type else random.randint(1, 60),
                    'device_type': random.choice(['mobile', 'desktop', 'tablet']),
                    'ip_address': self.fake.ipv4(),
                    'user_agent': self.fake.user_agent(),
                    'referrer_url': random.choice([None, 'google.com', 'naver.com', 'facebook.com']) if random.random() < 0.3 else None,
                    'location_lat': round(random.uniform(33.0, 38.5), 6),
                    'location_lng': round(random.uniform(125.0, 131.0), 6),
                    'created_at': action_time
                }
                behaviors.append(behavior)
                behavior_id += 1
        
        return pd.DataFrame(behaviors)
    
    def generate_user_preferences(self, users_df, relief_items_df, user_behaviors_df):
        """사용자 선호도 테이블 데이터 생성"""
        preferences = []
        preference_id = 1
        
        # 각 사용자별로 선호도 데이터 생성
        for _, user in users_df.iterrows():
            user_behaviors = user_behaviors_df[user_behaviors_df['user_id'] == user['user_id']]
            
            # 사용자가 상호작용한 아이템들의 카테고리 분석
            interacted_items = user_behaviors[user_behaviors['target_type'] == 'item']['target_id'].tolist()
            
            if interacted_items:
                # 실제 상호작용 기반 선호도 계산
                category_scores = {}
                for item_id in interacted_items:
                    item_info = relief_items_df[relief_items_df['item_id'] == item_id]
                    if not item_info.empty:
                        category = item_info.iloc[0]['category']
                        action_type = user_behaviors[
                            (user_behaviors['user_id'] == user['user_id']) & 
                            (user_behaviors['target_id'] == item_id)
                        ]['action_type'].iloc[0]
                        
                        weight = self.action_weights.get(action_type, 1.0)
                        category_scores[category] = category_scores.get(category, 0) + weight
                
                # 정규화
                total_score = sum(category_scores.values())
                if total_score > 0:
                    for category, score in category_scores.items():
                        preference = {
                            'preference_id': f'pref_{preference_id:08d}',
                            'user_id': user['user_id'],
                            'item_category': category,
                            'preference_score': round(score / total_score, 4),
                            'interaction_count': len([item for item in interacted_items 
                                                    if relief_items_df[relief_items_df['item_id'] == item]['category'].iloc[0] == category]),
                            'last_interaction': user_behaviors['timestamp'].max(),
                            'created_at': datetime.now(),
                            'updated_at': datetime.now()
                        }
                        preferences.append(preference)
                        preference_id += 1
            else:
                # 상호작용이 없는 사용자는 랜덤 선호도 생성
                selected_categories = random.sample(list(self.config.RELIEF_CATEGORIES.keys()), k=random.randint(1, 3))
                scores = np.random.dirichlet(np.ones(len(selected_categories)))
                
                for i, category in enumerate(selected_categories):
                    preference = {
                        'preference_id': f'pref_{preference_id:08d}',
                        'user_id': user['user_id'],
                        'item_category': category,
                        'preference_score': round(scores[i], 4),
                        'interaction_count': 0,
                        'last_interaction': None,
                        'created_at': datetime.now(),
                        'updated_at': datetime.now()
                    }
                    preferences.append(preference)
                    preference_id += 1
        
        return pd.DataFrame(preferences)
    
    def generate_recommendation_logs(self, users_df, shelters_df, relief_items_df):
        """추천 로그 테이블 데이터 생성"""
        logs = []
        log_id = 1
        
        # 각 사용자별로 추천 로그 생성
        for _, user in users_df.iterrows():
            # 사용자별 추천 횟수 (활발한 사용자일수록 많은 추천)
            num_recommendations = random.randint(5, 50)
            
            for _ in range(num_recommendations):
                recommendation_time = self.fake.date_time_between(start_date='-3m', end_date='now')
                
                # 추천 유형 결정
                recommendation_type = random.choice(['shelter_recommendation', 'item_recommendation', 'donation_matching'])
                algorithm_type = random.choice(self.config.RECOMMENDATION_TYPES)
                
                # 추천 대상 결정
                if recommendation_type == 'shelter_recommendation':
                    recommended_items = random.sample(shelters_df['shelter_id'].tolist(), k=random.randint(3, 10))
                    target_type = 'shelter'
                elif recommendation_type == 'item_recommendation':
                    recommended_items = random.sample(relief_items_df['item_id'].tolist(), k=random.randint(5, 15))
                    target_type = 'item'
                else:  # donation_matching
                    recommended_items = random.sample(shelters_df['shelter_id'].tolist(), k=random.randint(2, 8))
                    target_type = 'shelter'
                
                # 추천 점수 생성
                recommendation_scores = [round(random.uniform(0.1, 1.0), 4) for _ in recommended_items]
                
                # 사용자 반응 시뮬레이션
                user_clicked = random.random() < 0.3  # 30% 클릭률
                clicked_item = random.choice(recommended_items) if user_clicked else None
                
                # 추천 성과 측정
                conversion = False
                if user_clicked and random.random() < 0.2:  # 클릭 후 20% 전환율
                    conversion = True
                
                log = {
                    'log_id': f'rec_log_{log_id:08d}',
                    'user_id': user['user_id'],
                    'recommendation_type': recommendation_type,
                    'algorithm_type': algorithm_type,
                    'recommended_items': ','.join(recommended_items),
                    'recommendation_scores': ','.join(map(str, recommendation_scores)),
                    'context_features': ','.join(random.sample(['time_of_day', 'location', 'weather', 'recent_activity', 'user_profile'], k=random.randint(2, 4))),
                    'timestamp': recommendation_time,
                    'user_clicked': user_clicked,
                    'clicked_item': clicked_item,
                    'conversion': conversion,
                    'session_id': f'session_{random.randint(1, 10000):06d}',
                    'ab_test_group': random.choice(['A', 'B', 'control']),
                    'created_at': recommendation_time
                }
                logs.append(log)
                log_id += 1
        
        return pd.DataFrame(logs)
    
    def generate_similarity_matrix(self, users_df, user_preferences_df):
        """유사도 매트릭스 테이블 데이터 생성"""
        similarities = []
        similarity_id = 1
        
        # 사용자 선호도 벡터 생성
        user_vectors = {}
        all_categories = list(self.config.RELIEF_CATEGORIES.keys())
        
        for _, user in users_df.iterrows():
            user_prefs = user_preferences_df[user_preferences_df['user_id'] == user['user_id']]
            vector = [0.0] * len(all_categories)
            
            for _, pref in user_prefs.iterrows():
                if pref['item_category'] in all_categories:
                    idx = all_categories.index(pref['item_category'])
                    vector[idx] = pref['preference_score']
            
            user_vectors[user['user_id']] = vector
        
        # 사용자 간 유사도 계산 (샘플링하여 계산량 줄임)
        user_ids = list(user_vectors.keys())
        sample_size = min(100, len(user_ids))  # 최대 100명의 사용자만 샘플링
        sampled_users = random.sample(user_ids, sample_size)
        
        for i, user1 in enumerate(sampled_users):
            for j, user2 in enumerate(sampled_users[i+1:], i+1):
                vector1 = user_vectors[user1]
                vector2 = user_vectors[user2]
                
                # 코사인 유사도 계산
                if sum(vector1) > 0 and sum(vector2) > 0:
                    similarity_score = 1 - cosine(vector1, vector2)
                else:
                    similarity_score = 0.0
                
                # 유사도가 임계값 이상인 경우만 저장
                if similarity_score > 0.1:
                    similarity = {
                        'similarity_id': f'sim_{similarity_id:08d}',
                        'user_id_1': user1,
                        'user_id_2': user2,
                        'similarity_score': round(similarity_score, 4),
                        'similarity_type': 'cosine',
                        'feature_vector_1': ','.join(map(str, vector1)),
                        'feature_vector_2': ','.join(map(str, vector2)),
                        'calculated_at': datetime.now(),
                        'is_valid': True,
                        'created_at': datetime.now()
                    }
                    similarities.append(similarity)
                    similarity_id += 1
        
        return pd.DataFrame(similarities)
    
    def generate_all_recommendation_data(self, users_df, shelters_df, relief_items_df):
        """모든 추천시스템 데이터 생성 및 반환"""
        print("사용자 행동 데이터 생성 중...")
        user_behaviors_df = self.generate_user_behaviors(users_df, shelters_df, relief_items_df)
        
        print("사용자 선호도 데이터 생성 중...")
        user_preferences_df = self.generate_user_preferences(users_df, relief_items_df, user_behaviors_df)
        
        print("추천 로그 데이터 생성 중...")
        recommendation_logs_df = self.generate_recommendation_logs(users_df, shelters_df, relief_items_df)
        
        print("유사도 매트릭스 데이터 생성 중...")
        similarity_matrix_df = self.generate_similarity_matrix(users_df, user_preferences_df)
        
        return {
            'user_behaviors': user_behaviors_df,
            'user_preferences': user_preferences_df,
            'recommendation_logs': recommendation_logs_df,
            'similarity_matrix': similarity_matrix_df
        }

if __name__ == "__main__":
    # 테스트용 더미 데이터
    users_data = {
        'user_id': ['user_000001', 'user_000002', 'user_000003'],
    }
    users_df = pd.DataFrame(users_data)
    
    shelters_data = {
        'shelter_id': ['shelter_0001', 'shelter_0002'],
    }
    shelters_df = pd.DataFrame(shelters_data)
    
    relief_items_data = {
        'item_id': ['item_00001', 'item_00002', 'item_00003'],
        'category': ['food', 'clothing', 'medical']
    }
    relief_items_df = pd.DataFrame(relief_items_data)
    
    generator = RecommendationDataGenerator()
    data = generator.generate_all_recommendation_data(users_df, shelters_df, relief_items_df)
    
    # 데이터 요약 출력
    for table_name, df in data.items():
        print(f"\n{table_name}: {len(df)} 레코드 생성")
        print(f"컬럼: {list(df.columns)}")
        print(f"샘플 데이터:\n{df.head(2)}")