#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
재난 안전 더미 데이터 생성기
다변량 LSTM 예측 모델과 트위터 기반 추천시스템용 데이터 생성
"""

import os
import sys
import pandas as pd
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_generators.master_data_generator import MasterDataGenerator
from data_generators.timeseries_data_generator import TimeSeriesDataGenerator
from data_generators.recommendation_data_generator import RecommendationDataGenerator
from data_generators.donation_data_generator import DonationDataGenerator
from config.data_config import DataConfig

class DataValidator:
    """데이터 검증 클래스"""
    
    @staticmethod
    def validate_dataframe(df, table_name, required_columns=None):
        """DataFrame 기본 검증"""
        print(f"\n=== {table_name} 검증 ===")
        print(f"행 수: {len(df)}")
        print(f"열 수: {len(df.columns)}")
        print(f"컬럼: {list(df.columns)}")
        
        if required_columns:
            missing_cols = set(required_columns) - set(df.columns)
            if missing_cols:
                print(f"⚠️ 누락된 컬럼: {missing_cols}")
            else:
                print("✅ 모든 필수 컬럼 존재")
        
        # 중복 데이터 확인
        if len(df) > 0:
            duplicates = df.duplicated().sum()
            print(f"중복 행: {duplicates}")
            
            # 결측값 확인
            null_counts = df.isnull().sum()
            if null_counts.sum() > 0:
                print("결측값:")
                for col, count in null_counts[null_counts > 0].items():
                    print(f"  {col}: {count}")
            else:
                print("✅ 결측값 없음")
        
        return True
    
    @staticmethod
    def validate_foreign_keys(df, foreign_key_col, reference_df, reference_key_col, table_name):
        """외래키 검증"""
        if foreign_key_col in df.columns and reference_key_col in reference_df.columns:
            invalid_keys = set(df[foreign_key_col]) - set(reference_df[reference_key_col])
            if invalid_keys:
                print(f"⚠️ {table_name}에서 유효하지 않은 {foreign_key_col}: {len(invalid_keys)}개")
                return False
            else:
                print(f"✅ {table_name}의 {foreign_key_col} 외래키 검증 통과")
                return True
        return True

class DisasterSafetyDataGenerator:
    """재난 안전 데이터 생성기 메인 클래스"""
    
    def __init__(self):
        self.config = DataConfig()
        self.master_generator = MasterDataGenerator()
        self.timeseries_generator = TimeSeriesDataGenerator()
        self.recommendation_generator = RecommendationDataGenerator()
        self.donation_generator = DonationDataGenerator()
        self.validator = DataValidator()
        
        # 출력 디렉토리 생성
        os.makedirs(self.config.OUTPUT_DIR, exist_ok=True)
        
    def generate_all_data(self):
        """모든 데이터 생성"""
        print("🚀 재난 안전 더미 데이터 생성을 시작합니다...")
        print(f"생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # 1. 마스터 데이터 생성
        print("\n📊 1단계: 마스터 데이터 생성")
        master_data = self.master_generator.generate_all_master_data()
        
        # 2. 시계열 데이터 생성 (LSTM용)
        print("\n📈 2단계: 시계열 데이터 생성 (LSTM용)")
        timeseries_data = self.timeseries_generator.generate_all_timeseries_data(
            master_data['shelters'], 
            master_data['relief_items']
        )
        
        # 3. 추천시스템 데이터 생성
        print("\n🎯 3단계: 추천시스템 데이터 생성")
        recommendation_data = self.recommendation_generator.generate_all_recommendation_data(
            master_data['users'], 
            master_data['shelters'], 
            master_data['relief_items']
        )
        
        # 4. 기부 및 매칭 데이터 생성
        print("\n💝 4단계: 기부 및 매칭 데이터 생성")
        donation_data = self.donation_generator.generate_all_donation_data(
            master_data['users'], 
            master_data['shelters'], 
            master_data['relief_items']
        )
        
        # 모든 데이터 통합
        all_data = {
            **master_data,
            **timeseries_data,
            **recommendation_data,
            **donation_data
        }
        
        return all_data
    
    def validate_all_data(self, data):
        """모든 데이터 검증"""
        print("\n🔍 5단계: 데이터 검증")
        print("=" * 40)
        
        # 기본 검증
        for table_name, df in data.items():
            if isinstance(df, pd.DataFrame):
                self.validator.validate_dataframe(df, table_name)
        
        # 외래키 검증
        print("\n🔗 외래키 관계 검증")
        
        # 사용자 관련 외래키
        if 'donations' in data and 'users' in data:
            self.validator.validate_foreign_keys(
                data['donations'], 'user_id', 
                data['users'], 'user_id', 
                'donations'
            )
        
        # 대피소 관련 외래키
        if 'shelter_inventories' in data and 'shelters' in data:
            self.validator.validate_foreign_keys(
                data['shelter_inventories'], 'shelter_id', 
                data['shelters'], 'shelter_id', 
                'shelter_inventories'
            )
        
        # 구호품 관련 외래키
        if 'donations' in data and 'relief_items' in data:
            self.validator.validate_foreign_keys(
                data['donations'], 'item_id', 
                data['relief_items'], 'item_id', 
                'donations'
            )
        
        print("\n✅ 데이터 검증 완료")
    
    def save_to_csv(self, data):
        """CSV 파일로 저장"""
        print("\n💾 6단계: CSV 파일 저장")
        print("=" * 30)
        
        saved_files = []
        
        for table_name, df in data.items():
            if isinstance(df, pd.DataFrame) and len(df) > 0:
                filename = f"{table_name}.csv"
                filepath = os.path.join(self.config.OUTPUT_DIR, filename)
                
                try:
                    df.to_csv(filepath, index=False, encoding='utf-8-sig')
                    print(f"✅ {filename} 저장 완료 ({len(df)}행)")
                    saved_files.append(filepath)
                except Exception as e:
                    print(f"❌ {filename} 저장 실패: {e}")
        
        return saved_files
    
    def generate_summary_report(self, data, saved_files):
        """요약 보고서 생성"""
        print("\n📋 7단계: 요약 보고서 생성")
        print("=" * 40)
        
        report = []
        report.append("# 재난 안전 더미 데이터 생성 보고서")
        report.append(f"생성 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("\n## 생성된 데이터 요약")
        
        total_rows = 0
        for table_name, df in data.items():
            if isinstance(df, pd.DataFrame):
                rows = len(df)
                cols = len(df.columns)
                total_rows += rows
                report.append(f"- {table_name}: {rows:,}행 {cols}열")
        
        report.append(f"\n**총 데이터 행 수: {total_rows:,}행**")
        
        report.append("\n## 저장된 파일 목록")
        for filepath in saved_files:
            filename = os.path.basename(filepath)
            file_size = os.path.getsize(filepath) / 1024  # KB
            report.append(f"- {filename} ({file_size:.1f} KB)")
        
        report.append("\n## 데이터 용도")
        report.append("### LSTM 예측 모델용 데이터")
        report.append("- demand_predictions.csv: 수요 예측 시계열 데이터")
        report.append("- shelter_statistics.csv: 대피소 통계 시계열 데이터")
        report.append("- consumption_patterns.csv: 소비 패턴 시계열 데이터")
        report.append("- prediction_accuracy.csv: 예측 정확도 시계열 데이터")
        
        report.append("\n### 추천시스템용 데이터")
        report.append("- user_behaviors.csv: 사용자 행동 로그 데이터")
        report.append("- user_preferences.csv: 사용자 선호도 데이터")
        report.append("- recommendation_logs.csv: 추천 로그 데이터")
        report.append("- similarity_matrix.csv: 유사도 매트릭스 데이터")
        
        # 보고서 저장
        report_path = os.path.join(self.config.OUTPUT_DIR, "data_generation_report.md")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))
        
        print(f"📄 보고서 저장: {report_path}")
        
        # 콘솔에 요약 출력
        print("\n" + "=" * 60)
        print("🎉 데이터 생성 완료!")
        print(f"📊 총 {len(data)}개 테이블, {total_rows:,}행 데이터 생성")
        print(f"💾 {len(saved_files)}개 CSV 파일 저장")
        print(f"📁 출력 디렉토리: {self.config.OUTPUT_DIR}")
        print("=" * 60)
    
    def run(self):
        """전체 프로세스 실행"""
        try:
            # 데이터 생성
            data = self.generate_all_data()
            
            # 데이터 검증
            self.validate_all_data(data)
            
            # CSV 저장
            saved_files = self.save_to_csv(data)
            
            # 요약 보고서
            self.generate_summary_report(data, saved_files)
            
            return True
            
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """메인 함수"""
    generator = DisasterSafetyDataGenerator()
    success = generator.run()
    
    if success:
        print("\n✅ 모든 작업이 성공적으로 완료되었습니다.")
        return 0
    else:
        print("\n❌ 작업 중 오류가 발생했습니다.")
        return 1

if __name__ == "__main__":
    exit(main())