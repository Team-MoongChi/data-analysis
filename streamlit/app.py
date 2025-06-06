import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import warnings
import numpy as np
warnings.filterwarnings('ignore')

# 페이지 설정
st.set_page_config(
    page_title="공동구매 플랫폼 운영자 페이지",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 스타일 설정
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .stAlert > div {
        background-color: #ffeaa7;
        color: #2d3436;
    }
</style>
""", unsafe_allow_html=True)

# 샘플 데이터 생성 함수
@st.cache_data
def create_sample_data():
    """샘플 데이터를 생성하는 함수"""
    np.random.seed(42)
    
    # 카테고리 데이터
    categories = ['식품', '생활용품', '화장품', '의류', '가전제품', '도서', '스포츠', '문구', '건강식품', '반려동물용품']
    category_df = pd.DataFrame({
        'category_id': range(1, len(categories) + 1),
        'name': categories,
        'level': 'medium',
        'parent_category_id': np.random.randint(1, 4, len(categories))
    })
    
    # 상품 데이터
    products_df = pd.DataFrame({
        'product_id': range(1, 201),
        'category_id': np.random.randint(1, len(categories) + 1, 200),
        'name': [f'상품_{i}' for i in range(1, 201)],
        'price': np.random.randint(5000, 100000, 200),
        'rating': np.random.uniform(3.0, 5.0, 200).round(1)
    })
    
    # 공구 상품 데이터
    group_product_df = pd.DataFrame({
        'group_product_id': range(1, 501),
        'product_id': np.random.randint(1, 201, 500),
        'category_id': np.random.randint(1, len(categories) + 1, 500),
        'discount_rate': np.random.randint(10, 50, 500),
        'min_quantity': np.random.randint(10, 100, 500)
    })
    
    # 공구 게시판 데이터
    locations = ['서울', '부산', '대구', '인천', '광주', '대전', '울산', '세종', '경기', '강원']
    statuses = ['모집중', '공구성공', '공구실패', '마감']
    
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)
    date_range = pd.date_range(start=start_date, end=end_date, freq='H')
    
    group_boards_df = pd.DataFrame({
        'group_board_id': range(1, 501),
        'group_product_id': np.random.randint(1, 501, 500),
        'location': np.random.choice(locations, 500),
        'status': np.random.choice(statuses, 500, p=[0.3, 0.4, 0.1, 0.2]),
        'created_at': np.random.choice(date_range, 500),
        'deadline': None,  # 나중에 설정
        'updated_at': None,  # 나중에 설정
        'title': [f'공구방_{i}' for i in range(1, 501)],
        'current_participants': np.random.randint(5, 50, 500),
        'max_participants': np.random.randint(50, 200, 500)
    })
    
    # deadline과 updated_at 설정
    group_boards_df['deadline'] = group_boards_df['created_at'] + pd.Timedelta(days=7)
    group_boards_df['updated_at'] = group_boards_df['created_at'] + pd.Timedelta(days=np.random.randint(1, 8, 500))
    
    # 참여자 데이터
    roles = ['리더', '참여자']
    participants_df = pd.DataFrame({
        'participant_id': range(1, 3001),
        'group_board_id': np.random.randint(1, 501, 3000),
        'user_id': np.random.randint(1, 1000, 3000),
        'role': np.random.choice(roles, 3000, p=[0.2, 0.8]),
        'joined_at': np.random.choice(date_range, 3000),
        'quantity': np.random.randint(1, 10, 3000)
    })
    
    # 사용자 데이터
    user_df = pd.DataFrame({
        'user_id': range(1, 1001),
        'username': [f'user_{i}' for i in range(1, 1001)],
        'email': [f'user_{i}@example.com' for i in range(1, 1001)],
        'location': np.random.choice(locations, 1000),
        'joined_date': np.random.choice(pd.date_range('2023-01-01', '2024-12-31'), 1000)
    })
    
    return products_df, group_product_df, category_df, participants_df, group_boards_df, user_df

# 데이터 로드 함수
@st.cache_data
def load_data():
    """데이터를 로드하는 함수 (파일이 없으면 샘플 데이터 생성)"""
    try:
        # 실제 파일이 있으면 로드
        products_df = pd.read_csv('../data/products_df_final.csv')
        group_product_df = pd.read_csv('../data/group_product_df_final.csv')
        category_df = pd.read_csv('../data/category_df_final.csv')
        participants_df = pd.read_csv('../data/participants_dummy_data_3000.csv')
        group_boards_df = pd.read_csv('../data/group_boards_dummy_data_500.csv')
        user_df = pd.read_csv('../data/user_df_final.csv', encoding='utf-8')
        
        # 날짜 변환
        group_boards_df['created_at'] = pd.to_datetime(group_boards_df['created_at'])
        group_boards_df['deadline'] = pd.to_datetime(group_boards_df['deadline'])
        if 'updated_at' in group_boards_df.columns:
            group_boards_df['updated_at'] = pd.to_datetime(group_boards_df['updated_at'])
        participants_df['joined_at'] = pd.to_datetime(participants_df['joined_at'])
        
        return products_df, group_product_df, category_df, participants_df, group_boards_df, user_df
        
    except FileNotFoundError:
        st.warning("실제 데이터 파일을 찾을 수 없어 샘플 데이터를 사용합니다.")
        return create_sample_data()
    except Exception as e:
        st.error(f"데이터 로드 중 오류 발생: {e}")
        st.info("샘플 데이터를 생성합니다.")
        return create_sample_data()

# 안전한 계산 함수들
def safe_len(df):
    """안전한 길이 계산"""
    return len(df) if df is not None else 0

def safe_calculation(func, default=0):
    """안전한 계산 실행"""
    try:
        result = func()
        return result if result is not None else default
    except:
        return default

# 메인 헤더
st.markdown('<h1 class="main-header">공동구매 플랫폼 운영자 페이지</h1>', unsafe_allow_html=True)

# 데이터 로드
with st.spinner('데이터를 로드하는 중...'):
    try:
        data = load_data()
        if any(df is None for df in data):
            st.error("데이터 로드에 실패했습니다.")
            st.stop()
        
        products_df, group_product_df, category_df, participants_df, group_boards_df, user_df = data
        st.success("데이터가 성공적으로 로드되었습니다!")
        
    except Exception as e:
        st.error(f"데이터 로드 중 치명적 오류: {e}")
        st.stop()

# 탭으로 분석 메뉴 구성
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📋 전체 요약", 
    "📊 공구 마감률 추이", 
    "💼 거래 상태 분석", 
    "👑 리더 활동 통계", 
    "🗺️ 지역별 분석", 
    "⭐ 카테고리별 인기도"
])

# 탭 1: 전체 요약
with tab1:
    st.header("플랫폼 전체 요약")
    
    # 주요 지표 계산 (안전한 계산)
    total_boards = safe_len(group_boards_df)
    total_participants = safe_len(participants_df)
    total_leaders = safe_len(participants_df[participants_df['role'] == '리더']) if participants_df is not None else 0
    
    success_rate = safe_calculation(
        lambda: len(group_boards_df[group_boards_df['status'] == '공구성공']) / len(group_boards_df) * 100
    )
    
    # 메트릭 표시
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("총 공구방 수", f"{total_boards:,}개")
    with col2:
        st.metric("총 참여자 수", f"{total_participants:,}명")
    with col3:
        st.metric("총 리더 수", f"{total_leaders:,}명")
    with col4:
        st.metric("공구 성공률", f"{success_rate:.1f}%")
    
    # 최근 활동 트렌드
    if total_boards > 0:
        st.subheader("최근 활동 트렌드")
        group_boards_df['year_month'] = group_boards_df['created_at'].dt.to_period('M')
        monthly_trend = group_boards_df.groupby('year_month').size()
        
        fig_trend = px.line(
            x=monthly_trend.index.astype(str), 
            y=monthly_trend.values,
            title="월별 공구방 개설 추이",
            labels={'x': '월', 'y': '공구방 수'}
        )
        fig_trend.update_traces(line=dict(width=3, color='#1f77b4'))
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("표시할 데이터가 없습니다.")

# 탭 2: 공구 마감률 추이 분석
with tab2:
    st.header("공구 마감률 추이 분석")
    
    if safe_len(group_boards_df) > 0:
        # 월별 상태 분포
        group_boards_df['year_month'] = group_boards_df['created_at'].dt.to_period('M')
        monthly_status = group_boards_df.groupby(['year_month', 'status']).size().unstack(fill_value=0)
        
        # Plotly 시각화
        fig = go.Figure()
        
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
        for i, status in enumerate(monthly_status.columns):
            fig.add_trace(go.Scatter(
                x=monthly_status.index.astype(str),
                y=monthly_status[status],
                mode='lines+markers',
                name=status,
                line=dict(width=3, color=colors[i % len(colors)]),
                marker=dict(size=8)
            ))
        
        fig.update_layout(
            title="월별 공구 상태 추이",
            xaxis_title="월",
            yaxis_title="공구 수",
            hovermode='x unified',
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 상태별 통계
        st.subheader("상태별 통계")
        status_summary = group_boards_df['status'].value_counts()
        
        col1, col2 = st.columns(2)
        with col1:
            st.dataframe(status_summary.to_frame('개수'))
        with col2:
            fig_pie = px.pie(
                values=status_summary.values,
                names=status_summary.index,
                title="공구 상태 분포"
            )
            st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("표시할 데이터가 없습니다.")

# 탭 3: 거래 상태 분석
with tab3:
    st.header("거래 상태 종합 분석")
    
    if safe_len(group_boards_df) > 0 and safe_len(participants_df) > 0:
        # 월별 데이터 준비
        group_boards_df['created_month'] = group_boards_df['created_at'].dt.to_period('M')
        participants_df['joined_month'] = participants_df['joined_at'].dt.to_period('M')
        
        monthly_creation = group_boards_df.groupby('created_month').size()
        monthly_completion = group_boards_df[group_boards_df['status'] == '공구성공'].groupby('created_month').size()
        monthly_new_leaders = participants_df[participants_df['role'] == '리더'].groupby('joined_month').size()
        monthly_participants = participants_df.groupby('joined_month').size()
        
        # 서브플롯 생성
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=['월별 공구 개설 수', '월별 공구 완료 수', '월별 신규 리더 수', '월별 참가자 수'],
            vertical_spacing=0.15
        )
        
        # 차트 추가
        fig.add_trace(
            go.Scatter(
                x=monthly_creation.index.astype(str),
                y=monthly_creation.values,
                mode='lines+markers',
                name="개설수",
                line=dict(color='blue', width=3),
                marker=dict(size=8)
            ),
            row=1, col=1
        )
        
        if len(monthly_completion) > 0:
            fig.add_trace(
                go.Scatter(
                    x=monthly_completion.index.astype(str),
                    y=monthly_completion.values,
                    mode='lines+markers',
                    name="완료수",
                    line=dict(color='green', width=3),
                    marker=dict(size=8)
                ),
                row=1, col=2
            )
        
        fig.add_trace(
            go.Bar(
                x=monthly_new_leaders.index.astype(str),
                y=monthly_new_leaders.values,
                name="신규리더",
                marker_color='orange'
            ),
            row=2, col=1
        )
        
        fig.add_trace(
            go.Bar(
                x=monthly_participants.index.astype(str),
                y=monthly_participants.values,
                name="참가자수",
                marker_color='purple'
            ),
            row=2, col=2
        )
        
        fig.update_layout(
            title="월별 거래 흐름 종합 분석",
            height=800,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("표시할 데이터가 없습니다.")

# 탭 4: 리더 활동 통계
with tab4:
    st.header("리더 활동 통계 분석")
    
    if safe_len(participants_df) > 0:
        # 리더 참여 통계
        leader_data = participants_df[participants_df['role'] == '리더']
        
        if len(leader_data) > 0:
            leader_participation = leader_data.groupby('user_id').size().reset_index()
            leader_participation.columns = ['user_id', 'participation_count']
            
            total_unique_leaders = leader_participation['user_id'].nunique()
            repeated_leaders = leader_participation[leader_participation['participation_count'] >= 2]['user_id'].nunique()
            repeated_rate = (repeated_leaders / total_unique_leaders) * 100 if total_unique_leaders > 0 else 0
            leader_avg_boards = leader_participation['participation_count'].mean()
            
            # 주요 지표
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("평균 개설 수", f"{leader_avg_boards:.2f}회")
            with col2:
                st.metric("재참여율", f"{repeated_rate:.1f}%")
            with col3:
                st.metric("최대 개설 수", f"{leader_participation['participation_count'].max()}회")
            with col4:
                st.metric("중앙값", f"{leader_participation['participation_count'].median():.0f}회")
            
            # 리더별 개설 수 분포
            st.subheader("리더별 공구 개설 수 분포")
            fig_hist = px.histogram(
                leader_participation, 
                x='participation_count',
                nbins=min(20, len(leader_participation)),
                title="리더별 공구 개설 수 분포",
                labels={'participation_count': '공구 개설 수', 'count': '리더 수'}
            )
            fig_hist.add_vline(x=leader_avg_boards, line_dash="dash", line_color="red", 
                              annotation_text=f"평균: {leader_avg_boards:.2f}")
            st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.info("리더 데이터가 없습니다.")
        
        # 카테고리별 활동 분포
        if safe_len(group_boards_df) > 0 and safe_len(group_product_df) > 0:
            st.subheader("카테고리별 공구 활동 분포")
            
            # 데이터 결합
            group_product_info = pd.merge(group_boards_df, group_product_df,
                                         left_on='group_product_id', right_on='group_product_id', how='left')
            group_product_info = pd.merge(group_product_info, category_df[['category_id', 'name']],
                                         left_on='category_id', right_on='category_id', how='left')
            group_product_info.rename(columns={'name': 'category_name'}, inplace=True)
            
            if len(group_product_info) > 0:
                category_distribution = group_product_info.groupby('category_name').size().reset_index()
                category_distribution.columns = ['category_name', 'board_count']
                category_distribution = category_distribution.sort_values('board_count', ascending=False).head(10)
                
                fig_cat = px.bar(
                    category_distribution, 
                    x='board_count', 
                    y='category_name',
                    orientation='h',
                    title="카테고리별 공구 게시판 수 (상위 10개)",
                    labels={'board_count': '공구 게시판 수', 'category_name': '카테고리'}
                )
                st.plotly_chart(fig_cat, use_container_width=True)
    else:
        st.info("표시할 데이터가 없습니다.")

# 탭 5: 지역별 분석
with tab5:
    st.header("지역별 분석")
    
    if safe_len(participants_df) > 0 and safe_len(group_boards_df) > 0:
        # 데이터 결합
        df = pd.merge(participants_df, group_boards_df, on='group_board_id', how='inner')
        
        if len(df) > 0:
            # 지역별 통계
            group_boards_unique = df.drop_duplicates(subset='group_board_id')
            region_group_counts = group_boards_unique['location'].value_counts().reset_index()
            region_group_counts.columns = ['지역', '공구방 수']
            
            region_participant_counts = df.groupby('location')['user_id'].nunique().reset_index()
            region_participant_counts.columns = ['지역', '참여자 수']
            
            leaders = df[df['role'] == '리더']
            region_leader_counts = leaders.groupby('location')['user_id'].nunique().reset_index()
            region_leader_counts.columns = ['지역', '리더 수']
            
            # 3개 차트를 나란히 배치
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.subheader("공구방 수")
                fig1 = px.bar(region_group_counts, x='지역', y='공구방 수', 
                             color='공구방 수', color_continuous_scale='Blues')
                fig1.update_xaxes(tickangle=45)
                st.plotly_chart(fig1, use_container_width=True)
            
            with col2:
                st.subheader("참여자 수")
                fig2 = px.bar(region_participant_counts, x='지역', y='참여자 수',
                             color='참여자 수', color_continuous_scale='Greens')
                fig2.update_xaxes(tickangle=45)
                st.plotly_chart(fig2, use_container_width=True)
            
            with col3:
                st.subheader("리더 수")
                fig3 = px.bar(region_leader_counts, x='지역', y='리더 수',
                             color='리더 수', color_continuous_scale='Oranges')
                fig3.update_xaxes(tickangle=45)
                st.plotly_chart(fig3, use_container_width=True)
            
            # 지역별 종합 데이터 테이블
            st.subheader("지역별 종합 현황")
            region_summary = pd.merge(region_group_counts, region_participant_counts, on='지역', how='outer')
            region_summary = pd.merge(region_summary, region_leader_counts, on='지역', how='outer')
            region_summary = region_summary.fillna(0)
            region_summary['참여자당 공구방'] = (region_summary['공구방 수'] / region_summary['참여자 수']).round(2)
            region_summary = region_summary.replace([np.inf, -np.inf], 0)
            st.dataframe(region_summary, use_container_width=True)
        else:
            st.info("결합된 데이터가 없습니다.")
    else:
        st.info("표시할 데이터가 없습니다.")

# 탭 6: 카테고리별 인기도 분석
with tab6:
    st.header("카테고리별 인기도 분석")
    
    if safe_len(products_df) > 0 and safe_len(group_product_df) > 0:
        # 데이터 결합
        merged_df = pd.merge(products_df, group_product_df, on='category_id', how='inner')
        
        if len(merged_df) > 0 and 'rating' in merged_df.columns:
            st.subheader("평점 분포")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # 평점 히스토그램
                fig_rating = px.histogram(
                    merged_df, 
                    x='rating',
                    nbins=20,
                    title="전체 평점 분포",
                    labels={'rating': '평점', 'count': '빈도'}
                )
                st.plotly_chart(fig_rating, use_container_width=True)
            
            with col2:
                # 평점 박스플롯
                fig_box = px.box(
                    merged_df, 
                    y='rating',
                    title="평점 박스플롯",
                    labels={'rating': '평점'}
                )
                st.plotly_chart(fig_box, use_container_width=True)
            
            # 평점 통계
            st.subheader("평점 통계")
            rating_stats = merged_df['rating'].describe()
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("평균 평점", f"{rating_stats['mean']:.2f}")
            with col2:
                st.metric("중앙값", f"{rating_stats['50%']:.2f}")
            with col3:
                st.metric("최고 평점", f"{rating_stats['max']:.2f}")
            with col4:
                st.metric("최저 평점", f"{rating_stats['min']:.2f}")
            
            # 카테고리별 평점
            if 'category_id' in merged_df.columns and safe_len(category_df) > 0:
                # 카테고리 이름 추가
                category_ratings = merged_df.groupby('category_id')['rating'].agg(['mean', 'count']).reset_index()
                category_ratings = pd.merge(category_ratings, category_df[['category_id', 'name']], on='category_id', how='left')
                category_ratings = category_ratings[category_ratings['count'] >= 3]  # 최소 3개 이상
                category_ratings = category_ratings.sort_values('mean', ascending=False).head(10)
                
                if len(category_ratings) > 0:
                    st.subheader("카테고리별 평균 평점 (상위 10개)")
                    fig_cat_rating = px.bar(
                        category_ratings,
                        x='name',
                        y='mean',
                        title="카테고리별 평균 평점",
                        labels={'name': '카테고리', 'mean': '평균 평점'}
                    )
                    fig_cat_rating.update_xaxes(tickangle=45)
                    st.plotly_chart(fig_cat_rating, use_container_width=True)
        else:
            st.info("평점 데이터가 없거나 데이터 결합에 실패했습니다.")
    else:
        st.info("표시할 데이터가 없습니다.")

# 디버깅 정보 (사이드바에 유지)
st.sidebar.title("디버깅 정보")
if st.sidebar.checkbox("디버깅 정보 표시"):
    st.sidebar.markdown("### 데이터 정보")
    st.sidebar.write(f"공구방: {safe_len(group_boards_df)}개")
    st.sidebar.write(f"참여자: {safe_len(participants_df)}명")
    st.sidebar.write(f"상품: {safe_len(products_df)}개")
    st.sidebar.write(f"카테고리: {safe_len(category_df)}개")

# 푸터
st.markdown("---")
st.markdown("**공동구매 플랫폼 분석 대시보드** | 데이터 기반 의사결정 지원")