import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import warnings
import os
import re
warnings.filterwarnings('ignore')

# 페이지 설정
st.set_page_config(
    page_title="공동구매 플랫폼 운영자 대시보드",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일
st.markdown("""
<style>
    .main > div {
        padding-top: 1rem;
    }
    
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border: 1px solid #e1e8ed;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin: 0.5rem 0;
    }
    
    .dashboard-title {
        text-align: center;
        color: #2c3e50;
        margin-bottom: 2rem;
    }
    
    .insight-box {
        background: linear-gradient(135deg, #e3ffe7 0%, #d9e7ff 100%);
        border-left: 5px solid #4CAF50;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 5px;
    }
    
    .warning-box {
        background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
        border-left: 5px solid #ff9800;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 5px;
    }
    
    .sidebar-metric {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
  """데이터 로드"""
  data = {}

  csv_files = {
      'products': 'products_dummy_860.csv',
      'categories': 'categories_dummy_211.csv',
      'users': 'users_dummy_200.csv',
      'favorite': 'favorite_products_dummy_3000_updated.csv',
      'participants': 'participants_dummy_2312.csv',
      'group_products': 'group_products_dummy_366.csv',
      'group_boards': 'group_boards_dummy_366_title_change.csv'
  }

  for key, filename in csv_files.items():
    for base_path in ['', 'data/']:
      filepath = base_path + filename
      try:
        if os.path.exists(filepath):
          data[key] = pd.read_csv(filepath)
          break
      except:
        continue
    else:
      data[key] = pd.DataFrame()

  return data

def convert_date_columns(data):
  """날짜 컬럼 변환"""
  date_columns = {
      'products': ['created_at'],
      'group_boards': ['created_at', 'deadline', 'updated_at'],
      'participants': ['joined_at', 'read_at'],
      'favorite': ['created_at'],
      'users': ['created_at', 'updated_at']
  }

  for table, columns in date_columns.items():
    if table in data and not data[table].empty:
      for col in columns:
        if col in data[table].columns:
          try:
            data[table][col] = pd.to_datetime(data[table][col], errors='coerce')
          except:
            pass
  return data

def extract_district_from_address(address):
  """주소에서 구 단위 추출"""
  if pd.isna(address):
    return "기타"

  # 구 단위 추출 (예: "서울특별시 강남구 역삼동" -> "강남구")
  district_pattern = r'([가-힣]+구)'
  match = re.search(district_pattern, str(address))
  if match:
    return match.group(1)

  # 구가 없으면 시 단위 추출
  city_pattern = r'([가-힣]+시)'
  match = re.search(city_pattern, str(address))
  if match:
    return match.group(1)

  return "기타"

def main():
  # 제목
  st.markdown("<h1 class='dashboard-title'>뭉치 운영자 대시보드</h1>", unsafe_allow_html=True)

  # 데이터 로드
  data = load_data()
  data = convert_date_columns(data)

  # 기본 통계 계산
  total_products = len(data.get('products', pd.DataFrame()))
  total_users = len(data.get('users', pd.DataFrame()))
  total_participants = len(data.get('participants', pd.DataFrame()))
  total_groups = len(data.get('group_boards', pd.DataFrame()))

  # 찜하기 관련 전역 변수 계산
  total_favorites = 0
  unique_products = 0
  unique_users = 0

  if not data.get('favorite', pd.DataFrame()).empty:
    total_favorites = len(data['favorite'])
    unique_products = data['favorite']['product_id'].nunique()
    unique_users = data['favorite']['user_id'].nunique()

  # 사이드바
  st.sidebar.markdown("## 플랫폼 현황")

  st.sidebar.markdown(f"""
    <div class="sidebar-metric">
        <h4>전체 현황</h4>
        <p>• 등록 상품: <strong>{total_products:,}개</strong></p>
        <p>• 가입 사용자: <strong>{total_users:,}명</strong></p>
        <p>• 공구 참여: <strong>{total_participants:,}건</strong></p>
    </div>
    """, unsafe_allow_html=True)

  # KPI 계산
  st.markdown("## 핵심 성과 지표")

  col1, col2, col3, col4 = st.columns(4)

  with col1:
    st.metric(
        label="총 상품 수",
        value=f"{total_products:,}개"
    )

  with col2:
    st.metric(
        label="총 사용자 수",
        value=f"{total_users:,}명"
    )

  with col3:
    # 거래 완료율 계산
    if not data.get('participants', pd.DataFrame()).empty and 'trade_completed' in data['participants'].columns:
      completed = data['participants']['trade_completed'].sum()
      total = len(data['participants'])
      completion_rate = (completed / total) * 100
      st.metric(
          label="거래 완료율",
          value=f"{completion_rate:.1f}%"
      )
    else:
      st.metric(label="거래 완료율", value="데이터 없음")

  with col4:
    # 리더 비율 수정 - 'L'이 포함된 role을 리더로 인식
    if not data.get('participants', pd.DataFrame()).empty and 'role' in data['participants'].columns:
      # 'L'이 포함된 역할을 리더로 분류
      leaders = data['participants']['role'].str.contains('L', case=False, na=False).sum()
      total = len(data['participants'])
      leader_ratio = (leaders / total) * 100
      st.metric(
          label="리더 비율",
          value=f"{leader_ratio:.1f}%"
      )
    else:
      st.metric(label="리더 비율", value="데이터 없음")

  # 탭 구성
  tab1, tab2, tab3, tab4, tab5 = st.tabs([
      "사용자 참여 현황", "상품 및 카테고리", "찜하기 분석", "지역별 현황", "데이터 인사이트"
  ])

  with tab1:
    st.markdown("### 사용자 참여 현황")

    col1, col2 = st.columns(2)

    with col1:
      # 사용자별 참여 횟수 분포
      if not data.get('participants', pd.DataFrame()).empty:
        user_participation = data['participants'].groupby('user_id').size()
        participation_dist = user_participation.value_counts().sort_index()

        if len(participation_dist) > 0:
          chart_data = pd.DataFrame({
              '참여 횟수': participation_dist.index,
              '사용자 수': participation_dist.values
          })

          fig = px.bar(
              chart_data,
              x='참여 횟수',
              y='사용자 수',
              title="사용자별 참여 횟수 분포",
              color='사용자 수',
              color_continuous_scale='Blues'
          )
          fig.update_layout(height=400)
          st.plotly_chart(fig, use_container_width=True, key="participation_distribution")

    with col2:
      # 수정된 역할별 분포
      if not data.get('participants', pd.DataFrame()).empty and 'role' in data['participants'].columns:
        # 'L'이 포함된 역할을 리더로 재분류
        data['participants']['role_cleaned'] = data['participants']['role'].apply(
            lambda x: '리더' if 'L' in str(x) else '참여자'
        )
        role_counts = data['participants']['role_cleaned'].value_counts()

        fig = px.pie(
            values=role_counts.values,
            names=role_counts.index,
            title="참여자 역할 분포",
            color_discrete_sequence=['#ff9999', '#66b3ff']
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True, key="role_distribution")

    # 참여 현황 요약
    if not data.get('participants', pd.DataFrame()).empty:
      total_unique_users = data['participants']['user_id'].nunique()
      avg_participation = data['participants'].groupby('user_id').size().mean()

      st.markdown(f"""
            <div class="insight-box">
                <strong>참여 현황 요약</strong><br>
                • 총 활성 사용자: <strong>{total_unique_users:,}명</strong><br>
                • 사용자당 평균 참여: <strong>{avg_participation:.1f}회</strong><br>
                • 총 참여 건수: <strong>{total_participants:,}건</strong>
            </div>
            """, unsafe_allow_html=True)

  with tab2:
    st.markdown("### 상품 및 카테고리 분석")

    col1, col2 = st.columns(2)

    with col1:
      # 카테고리별 상품 수 - 카테고리 이름과 함께 표시
      if (not data.get('products', pd.DataFrame()).empty and 'category_id' in data['products'].columns and
              not data.get('categories', pd.DataFrame()).empty):

        # 상품과 카테고리 조인
        products_with_category = pd.merge(
            data['products'],
            data['categories'],
            left_on='category_id',
            right_on='id',
            how='left'
        )

        if 'large_category' in products_with_category.columns:
          category_counts = products_with_category['large_category'].value_counts().head(10)

          chart_data = pd.DataFrame({
              '카테고리': category_counts.index,
              '상품 수': category_counts.values
          })

          fig = px.bar(
              chart_data,
              x='상품 수',
              y='카테고리',
              orientation='h',
              title="카테고리별 상품 수 (Top 10)",
              color='상품 수',
              color_continuous_scale='Greens'
          )
          fig.update_layout(height=500)
          st.plotly_chart(fig, use_container_width=True, key="category_products")
        else:
          # 카테고리 정보가 없으면 ID로 표시
          category_counts = data['products']['category_id'].value_counts().head(10)
          chart_data = pd.DataFrame({
              '카테고리': [f'카테고리 {cat_id}' for cat_id in category_counts.index],
              '상품 수': category_counts.values
          })

          fig = px.bar(
              chart_data,
              x='상품 수',
              y='카테고리',
              orientation='h',
              title="카테고리별 상품 수 (Top 10)",
              color='상품 수',
              color_continuous_scale='Greens'
          )
          fig.update_layout(height=500)
          st.plotly_chart(fig, use_container_width=True, key="category_products_by_id")

    with col2:
      # 상품 가격 분포
      if not data.get('products', pd.DataFrame()).empty and 'price' in data['products'].columns:
        # 가격 데이터가 있는지 확인
        price_data = data['products']['price'].dropna()
        if len(price_data) > 0:
          fig = px.histogram(
              x=price_data,
              nbins=25,
              title="상품 가격 분포",
              labels={'x': '가격(원)', 'y': '상품 수'}
          )
          fig.update_layout(height=400)
          st.plotly_chart(fig, use_container_width=True, key="price_distribution")
        else:
          st.warning("가격 데이터가 없습니다.")
      else:
        st.warning("상품 가격 정보를 찾을 수 없습니다.")

    # 가격대별 상품 분포
    if not data.get('products', pd.DataFrame()).empty and 'price' in data['products'].columns:
      price_data = data['products']['price'].dropna()
      if len(price_data) > 0:
        price_ranges = pd.cut(price_data,
                              bins=[0, 10000, 30000, 50000, 100000, float('inf')],
                              labels=['1만원 미만', '1-3만원', '3-5만원', '5-10만원', '10만원 이상'])
        price_dist = price_ranges.value_counts()

        st.markdown("### 가격대별 상품 분포")

        col1, col2 = st.columns(2)

        with col1:
          # 가격대별 분포 시각화
          chart_data = pd.DataFrame({
              '가격대': price_dist.index,
              '상품 수': price_dist.values
          })

          fig = px.pie(
              chart_data,
              values='상품 수',
              names='가격대',
              title="가격대별 상품 분포",
              color_discrete_sequence=px.colors.qualitative.Set3
          )
          fig.update_layout(height=400)
          st.plotly_chart(fig, use_container_width=True, key="price_range_pie")

        with col2:
          # 가격대별 상세 현황
          st.markdown("**가격대별 상세 현황**")
          st.write("")

          for price_range, count in price_dist.items():
            percentage = (count / len(price_data)) * 100
            st.markdown(f"""
                        **{price_range}**  
                        {count}개 상품 ({percentage:.1f}%)
                        """)
            st.progress(percentage / 100)
            st.write("")

        # 요약 통계를 전체 폭으로 배치
        st.markdown("""
                <div class="insight-box">
                    <strong>요약 통계</strong><br>
                    • 평균 가격: {avg_price:,.0f}원<br>
                    • 최고 가격: {max_price:,.0f}원<br>
                    • 최저 가격: {min_price:,.0f}원<br>
                    • 중간값: {median_price:,.0f}원<br>
                    • 총 상품 수: {total_count:,}개
                </div>
                """.format(
            avg_price=price_data.mean(),
            max_price=price_data.max(),
            min_price=price_data.min(),
            median_price=price_data.median(),
            total_count=len(price_data)
        ), unsafe_allow_html=True)

  with tab3:
    st.markdown("### 찜하기 분석")

    col1, col2 = st.columns(2)

    with col1:
      # 상품별 찜 횟수 TOP 10 차트 (상품명과 함께)
      if not data.get('favorite', pd.DataFrame()).empty and 'product_id' in data['favorite'].columns:
        product_favorites = data['favorite']['product_id'].value_counts().head(10)

        if len(product_favorites) > 0 and not data.get('products', pd.DataFrame()).empty:
          # products 테이블과 조인하여 상품명 가져오기
          popularity_df = pd.DataFrame({
              'product_id': product_favorites.index,
              'favorite_count': product_favorites.values
          })

          # products 테이블과 조인
          products_with_favorites = pd.merge(
              popularity_df,
              data['products'][['id', 'name']],
              left_on='product_id',
              right_on='id',
              how='left'
          )

          # 상품명이 없는 경우 상품 ID로 대체, 긴 상품명은 줄임
          products_with_favorites['display_name'] = products_with_favorites['name'].fillna(
              products_with_favorites['product_id'].astype(str).apply(lambda x: f'상품 {x}')
          ).apply(lambda x: x[:25] + '...' if len(str(x)) > 25 else str(x))

          chart_data = pd.DataFrame({
              '상품명': products_with_favorites['display_name'],
              '찜 횟수': products_with_favorites['favorite_count']
          })

          fig = px.bar(
              chart_data,
              x='찜 횟수',
              y='상품명',
              orientation='h',
              title="인기 상품 찜 Top 10",
              color='찜 횟수',
              color_continuous_scale='Oranges'
          )
          fig.update_layout(height=500, margin=dict(l=200))  # 왼쪽 여백 증가
          st.plotly_chart(fig, use_container_width=True, key="top_favorites")

          # 인기 상품 전체 이름 표시
          st.markdown("**인기 상품 전체 이름 (Top 5)**")
          for i, row in products_with_favorites.head(5).iterrows():
            full_name = row['name'] if pd.notna(row['name']) else f"상품 {row['product_id']}"
            st.write(f"**{i + 1}위**: {full_name} ({row['favorite_count']}회 찜)")
        else:
          st.info("찜 데이터를 찾을 수 없습니다.")

    with col2:
      # 사용자별 찜 활동도 분석
      if not data.get('favorite', pd.DataFrame()).empty and 'user_id' in data['favorite'].columns:
        user_favorites = data['favorite']['user_id'].value_counts()
        favorites_activity = user_favorites.value_counts().sort_index()

        chart_data = pd.DataFrame({
            '찜 개수': favorites_activity.index,
            '사용자 수': favorites_activity.values
        })

        fig = px.bar(
            chart_data,
            x='찜 개수',
            y='사용자 수',
            title="사용자별 찜 활동도 분포",
            color='사용자 수',
            color_continuous_scale='Blues'
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True, key="user_favorite_activity")

    # 찜하기 인사이트와 사용자 찜 활동 분석을 같은 위치에서 시작
    col1, col2 = st.columns(2)

    with col1:
      # 찜하기 인사이트
      if not data.get('favorite', pd.DataFrame()).empty and 'product_id' in data['favorite'].columns:
        product_favorites = data['favorite']['product_id'].value_counts()
        if len(product_favorites) > 0:
          # 가장 인기있는 상품의 실제 이름 찾기
          top_product_id = product_favorites.index[0]
          top_product_name = "알 수 없는 상품"

          if not data.get('products', pd.DataFrame()).empty:
            product_info = data['products'][data['products']['id'] == top_product_id]
            if not product_info.empty and 'name' in product_info.columns:
              product_name = product_info['name'].iloc[0]
              if pd.notna(product_name):
                top_product_name = product_name[:30] + "..." if len(str(product_name)) > 30 else str(product_name)

          max_favorite = product_favorites.iloc[0]
          st.markdown(f"""
                    <div class="insight-box">
                        <strong>찜하기 인사이트</strong><br>
                        • 가장 인기있는 상품: {top_product_name} ({max_favorite}번 찜)<br>
                        • 찜 받은 상품 비율: {(unique_products / total_products) * 100:.1f}%<br>
                        • 사용자당 평균 찜: {total_favorites / unique_users:.1f}개
                    </div>
                    """, unsafe_allow_html=True)

    with col2:
      # 사용자 찜 활동 분석
      if not data.get('favorite', pd.DataFrame()).empty and 'user_id' in data['favorite'].columns:
        user_favorites = data['favorite']['user_id'].value_counts()
        high_activity_users = (user_favorites >= 5).sum()
        avg_favorites = user_favorites.mean()

        st.markdown(f"""
                <div class="insight-box">
                    <strong>사용자 찜 활동 분석</strong><br>
                    • 5개 이상 찜한 활성 사용자: <strong>{high_activity_users:,}명</strong><br>
                    • 사용자당 평균 찜: <strong>{avg_favorites:.1f}개</strong><br>
                    • 찜 활동 참여율: <strong>{(unique_users / total_users) * 100:.1f}%</strong>
                </div>
                """, unsafe_allow_html=True)

    # 월별 찜하기 트렌드
    if not data.get('favorite', pd.DataFrame()).empty and 'created_at' in data['favorite'].columns:
      favorites_with_date = data['favorite'].dropna(subset=['created_at'])
      if len(favorites_with_date) > 0:
        favorites_with_date['month'] = favorites_with_date['created_at'].dt.to_period('M')
        monthly_favorites = favorites_with_date.groupby('month').size()

        if len(monthly_favorites) > 1:
          st.markdown("### 월별 찜하기 트렌드")

          chart_data = pd.DataFrame({
              '월': [str(m) for m in monthly_favorites.index],
              '찜 횟수': monthly_favorites.values
          })

          fig = px.line(
              chart_data,
              x='월',
              y='찜 횟수',
              title="월별 찜하기 추이",
              markers=True
          )
          fig.update_layout(height=400)
          st.plotly_chart(fig, use_container_width=True, key="monthly_favorites_trend")

    # 찜하기 통계 및 요약 (페이지 하단)
    if not data.get('favorite', pd.DataFrame()).empty:
      total_favorites = len(data['favorite'])
      unique_products = data['favorite']['product_id'].nunique()
      unique_users = data['favorite']['user_id'].nunique()

      col1, col2, col3 = st.columns(3)

      with col1:
        st.metric(
            label="총 찜하기",
            value=f"{total_favorites:,}건"
        )

      with col2:
        st.metric(
            label="찜 받은 상품",
            value=f"{unique_products:,}개"
        )

      with col3:
        st.metric(
            label="찜한 사용자",
            value=f"{unique_users:,}명"
        )

      # 찜하기 현황 요약
      st.markdown(f"""
            <div class="insight-box">
                <strong>찜하기 현황 요약</strong><br>
                • 총 찜하기: <strong>{total_favorites:,}건</strong><br>
                • 찜 받은 상품: <strong>{unique_products:,}개</strong><br>
                • 찜한 사용자: <strong>{unique_users:,}명</strong><br>
                • 사용자당 평균 찜: <strong>{total_favorites / unique_users:.1f}개</strong><br>
                • 찜 활동 참여율: <strong>{(unique_users / total_users) * 100:.1f}%</strong>
            </div>
            """, unsafe_allow_html=True)

  with tab4:
    st.markdown("### 지역별 현황")

    col1, col2 = st.columns(2)

    with col1:
      # 지역별 사용자 분포
      if not data.get('users', pd.DataFrame()).empty and 'address' in data['users'].columns:
        # 주소에서 구 단위 추출
        data['users']['district'] = data['users']['address'].apply(extract_district_from_address)
        district_counts = data['users']['district'].value_counts().head(10)

        chart_data = pd.DataFrame({
            '지역': district_counts.index,
            '사용자 수': district_counts.values
        })

        fig = px.bar(
            chart_data,
            x='지역',
            y='사용자 수',
            title="지역별 사용자 분포 (구 단위)",
            color='사용자 수',
            color_continuous_scale='Viridis'
        )
        fig.update_layout(height=400)
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(fig, use_container_width=True, key="regional_users")

    with col2:
      # 지역별 공구방 분포
      if not data.get('group_boards', pd.DataFrame()).empty and 'location' in data['group_boards'].columns:
        # 공구방 위치에서 구 단위 추출
        data['group_boards']['district'] = data['group_boards']['location'].apply(extract_district_from_address)
        district_counts = data['group_boards']['district'].value_counts().head(10)

        chart_data = pd.DataFrame({
            '지역': district_counts.index,
            '공구방 수': district_counts.values
        })

        fig = px.bar(
            chart_data,
            x='지역',
            y='공구방 수',
            title="지역별 공구방 분포 (구 단위)",
            color='공구방 수',
            color_continuous_scale='Reds'
        )
        fig.update_layout(height=400)
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(fig, use_container_width=True, key="regional_groups")

    # 지역별 요약 통계
    if (not data.get('users', pd.DataFrame()).empty and 'district' in data['users'].columns and
            not data.get('group_boards', pd.DataFrame()).empty and 'district' in data['group_boards'].columns):

      st.markdown("### 지역별 요약 (구 단위)")

      user_districts = data['users']['district'].value_counts()
      group_districts = data['group_boards']['district'].value_counts()

      # 공통 지역만 표시
      common_districts = set(user_districts.index) & set(group_districts.index)

      summary_data = []
      for district in list(common_districts)[:8]:  # 상위 8개 지역만
        users = user_districts.get(district, 0)
        groups = group_districts.get(district, 0)
        summary_data.append({
            '지역': district,
            '사용자 수': users,
            '공구방 수': groups,
            '공구방/사용자 비율': f"{(groups / users):.2f}" if users > 0 else "0"
        })

      summary_df = pd.DataFrame(summary_data)
      st.dataframe(summary_df, use_container_width=True)

  with tab5:
    st.markdown("### 운영자를 위한 데이터 기반 인사이트")

    # 현재 상황 분석
    completion_rate = 0
    favorite_participation_rate = 0
    avg_participation = 0

    if not data.get('participants', pd.DataFrame()).empty:
      total_unique_users = data['participants']['user_id'].nunique()
      avg_participation = data['participants'].groupby('user_id').size().mean()
      completion_rate = (data['participants']['trade_completed'].sum() / len(data['participants'])) * 100 if 'trade_completed' in data['participants'].columns else 0

    if total_favorites > 0:
      favorite_participation_rate = (unique_users / total_users) * 100

    # 주요 지표 요약
    st.markdown("#### 핵심 운영 지표 현황")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
      st.metric("사용자 참여율", f"{(total_unique_users / total_users) * 100:.1f}%")
    with col2:
      st.metric("거래 완료율", f"{completion_rate:.1f}%")
    with col3:
      st.metric("찜 참여율", f"{favorite_participation_rate:.1f}%")
    with col4:
      st.metric("평균 참여횟수", f"{avg_participation:.1f}회")

    st.markdown("---")

    # 운영자 관점 인사이트
    col1, col2 = st.columns(2)

    with col1:
      st.markdown("#### 현재 상황 분석")
      st.markdown("**긍정적 신호**")
      st.write("• 찜하기 기능이 활발히 사용되고 있어 사용자 관심도가 높음")
      st.write("• 다양한 가격대의 상품이 골고루 분포되어 있음")
      st.write("• 지역별로 사용자가 고르게 분포되어 시장 확장 가능성 있음")

      st.markdown("**주의가 필요한 부분**")
      st.write("• 일부 사용자에게 참여가 집중되는 경향")
      st.write("• 특정 카테고리에 상품이 편중될 가능성")
      st.write("• 찜하기에서 실제 구매로의 전환 최적화 필요")

    with col2:
      st.markdown("#### 전략적 개선 방향")

      st.markdown("**1. 사용자 활성화 전략**")
      st.write("• 신규 사용자 온보딩 프로그램 강화")
      st.write("• 비활성 사용자 재참여 유도 캠페인")
      st.write("• 리더 양성 프로그램으로 공구방 다양성 확보")

      st.markdown("**2. 상품 포트폴리오 최적화**")
      st.write("• 인기 카테고리 상품 확대")
      st.write("• 틈새 카테고리 발굴 및 테스트")
      st.write("• 1인 가구 맞춤 상품 큐레이션")

      st.markdown("**3. 전환율 개선**")
      st.write("• 찜→구매 전환 분석 및 개선")
      st.write("• 개인화 추천 시스템 도입")
      st.write("• 공구방 성공률 향상 방안 모색")

    # 구체적 액션 플랜
    st.markdown("#### 즉시 실행 가능한 액션 플랜")

    col1, col2, col3 = st.columns(3)

    with col1:
      st.markdown("""
            **단기 액션 (1-2주)**
            - [ ] 인기 상품 분석하여 유사 상품 확대
            - [ ] inactive 사용자 재활성화 이벤트 기획
            - [ ] 리더 활동 인센티브 프로그램 런칭
            - [ ] 사용자 피드백 수집 시스템 구축
            """)

    with col2:
      st.markdown("""
            **중기 전략 (1-2개월)**
            - [ ] 사용자 세그먼트별 맞춤 마케팅
            - [ ] 카테고리별 전문 리더 육성
            - [ ] 지역 기반 오프라인 이벤트 기획
            - [ ] 찜→구매 전환 분석 시스템 구축
            """)

    with col3:
      st.markdown("""
            **장기 목표 (3-6개월)**
            - [ ] 크로스셀링/업셀링 전략 수립
            - [ ] 플랫폼 확장 (새로운 지역/카테고리)
            - [ ] 데이터 기반 자동화 시스템 구축
            - [ ] 사용자 생명주기 관리 시스템
            """)

    # 성과 측정 지표
    st.markdown("---")
    st.markdown("#### 성과 측정 KPI")

    kpi_data = {
        "지표": ["월간 활성 사용자(MAU)", "공구방 성공률", "찜→구매 전환율", "사용자당 평균 거래액", "신규 사용자 유지율"],
        "현재 목표": ["증가", f"{completion_rate:.1f}%", "측정 필요", "측정 필요", "측정 필요"],
        "3개월 목표": ["20% 증가", "85%+", "15%+", "50만원+", "70%+"],
        "측정 주기": ["주간", "주간", "주간", "월간", "월간"]
    }

    kpi_df = pd.DataFrame(kpi_data)
    st.dataframe(kpi_df, use_container_width=True)

    # 마지막 권고사항
    st.markdown("#### 운영자 핵심 권고사항")

    st.markdown("**1. 데이터 기반 의사결정 강화**")
    st.write("정기적인 대시보드 모니터링으로 트렌드 파악")

    st.markdown("**2. 사용자 중심 개선**")
    st.write("찜하기 패턴을 분석하여 실제 수요에 맞는 상품 확대")

    st.markdown("**3. 커뮤니티 활성화**")
    st.write("리더-구매자 간 신뢰 관계 구축이 플랫폼 성장의 핵심")

    st.markdown("**4. 지속적 실험**")
    st.write("A/B 테스트를 통한 기능 개선 및 사용자 경험 최적화")

if __name__ == "__main__":
  main()
