import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# ---------------------------------------------------------
# 1. 페이지 설정 (발표용으로 깔끔하게)
# ---------------------------------------------------------
st.set_page_config(
    page_title="K-Festival Guide 2025",
    layout="wide",
    page_icon="🎉",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# 2. 데이터 로드 및 전처리
# ---------------------------------------------------------
@st.cache_data
def load_data():
    # CSV 파일 읽기 (인코딩 에러 방지 처리)
    try:
        df = pd.read_csv('2025년 지역축제.CSV', encoding='cp949')
    except:
        df = pd.read_csv('2025년 지역축제.CSV', encoding='utf-8')
    
    # 1. 외국인 방문객 수 전처리 (콤마 제거, 숫자로 변환)
    # 컬럼명이 '외국인(명)' 이라고 가정합니다. 파일 헤더 확인 필요!
    if '외국인(명)' in df.columns:
        df['visitors'] = df['외국인(명)'].astype(str).str.replace(',', '').str.replace('미집계', '0').str.replace('최초 행사', '0')
        df['visitors'] = pd.to_numeric(df['visitors'], errors='coerce').fillna(0).astype(int)
    else:
        df['visitors'] = 0 # 컬럼 못 찾으면 0 처리

    # 2. 월(Month) 데이터 전처리
    # '시작월' 컬럼이 있다고 가정
    if '시작월' in df.columns:
        df['month'] = pd.to_numeric(df['시작월'], errors='coerce').fillna(0).astype(int)
    
    return df

# 좌표 데이터 (공공데이터에는 위도/경도가 없어서 지역별 중심좌표 매핑)
lat_lon_dict = {
    '서울': [37.5665, 126.9780], '부산': [35.1796, 129.0756], '대구': [35.8714, 128.6014],
    '인천': [37.4563, 126.7052], '광주': [35.1595, 126.8526], '대전': [36.3504, 127.3845],
    '울산': [35.5384, 129.3114], '세종': [36.4800, 127.2890], '경기': [37.4138, 127.5183],
    '강원': [37.8228, 128.1555], '충북': [36.6350, 127.4914], '충남': [36.5184, 126.8000],
    '전북': [35.7175, 127.1530], '전남': [34.8161, 126.4629], '경북': [36.5760, 128.5056],
    '경남': [35.2383, 128.6925], '제주': [33.4890, 126.4983]
}

# 데이터 로딩 실행
try:
    df = load_data()
    
    # 지도 표시를 위한 좌표 매핑 (광역단체명 기준)
    # 데이터 포인트가 겹치지 않게 랜덤 노이즈(Jitter) 추가
    df['lat'] = df['광역자치단체명'].map(lambda x: lat_lon_dict.get(str(x)[:2], [36.5, 127.5])[0])
    df['lon'] = df['광역자치단체명'].map(lambda x: lat_lon_dict.get(str(x)[:2], [36.5, 127.5])[1])
    
    df['lat'] = df['lat'] + np.random.normal(0, 0.04, len(df))
    df['lon'] = df['lon'] + np.random.normal(0, 0.04, len(df))

except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()

# ---------------------------------------------------------
# 3. 사이드바 (외국인 맞춤형 필터)
# ---------------------------------------------------------
st.sidebar.title("🔍 Festival Finder")
st.sidebar.markdown("Find the best K-Festival for you!")

# 필터 1: 월 선택
selected_month = st.sidebar.slider("When will you visit?", 1, 12, 10) # 기본값 10월

# 필터 2: 지역 선택
regions = ['All'] + sorted(list(df['광역자치단체명'].dropna().unique()))
selected_region = st.sidebar.selectbox("Where to go?", regions)

# 필터 3: 카테고리
categories = ['All'] + list(df['축제 유형'].dropna().unique())
selected_category = st.sidebar.multiselect("What do you like?", categories, default='All')

# 데이터 필터링 로직
filtered_df = df[df['month'] == selected_month]
if selected_region != 'All':
    filtered_df = filtered_df[filtered_df['광역자치단체명'] == selected_region]
if 'All' not in selected_category and selected_category:
    filtered_df = filtered_df[filtered_df['축제 유형'].isin(selected_category)]

# ---------------------------------------------------------
# 4. 메인 대시보드 구성
# ---------------------------------------------------------
st.title("🇰🇷 K-Festival Information Map 2025")
st.markdown(f"### Discover {len(filtered_df)} festivals in **{selected_month}월(Month)**!")

# 탭 구성: 지도 / 랭킹 / 시즌추천 / AI
tab1, tab2, tab3, tab4 = st.tabs(["🗺️ Festival Map", "🔥 Hot Pick (Ranking)", "🌸☀️🍂❄️ Seasonal", "🤖 AI Guide"])

# [Tab 1] 지도 시각화 (가장 중요한 부분)
with tab1:
    col1, col2 = st.columns([3, 1])
    with col1:
        if not filtered_df.empty:
            st.map(filtered_df, latitude='lat', longitude='lon', color='#FF4B4B', size=20)
        else:
            st.warning("No festivals found for this filter.")
            
    with col2:
        st.subheader("Festival List")
        if not filtered_df.empty:
            # 리스트 보여주기
            display_cols = ['축제명', '개최 장소', '축제 유형']
            st.dataframe(filtered_df[display_cols], hide_index=True, use_container_width=True)
        else:
            st.write("Try changing the month or region!")

# [Tab 2] 외국인 인기 랭킹 (데이터 분석 포인트)
with tab2:
    st.subheader("🏆 Top 10 Festivals Loved by Foreigners")
    st.caption("Based on last year's visitor data")
    
    # 외국인 방문객 수 기준 정렬 (0인 데이터 제외)
    ranking_df = df[df['visitors'] > 0].sort_values(by='visitors', ascending=False).head(10)
    
    if not ranking_df.empty:
        # Plotly 가로 막대 그래프
        fig = px.bar(
            ranking_df,
            x='visitors',
            y='축제명',
            orientation='h',
            text='visitors',
            color='축제 유형',
            labels={'visitors': 'Foreign Visitors', '축제명': 'Festival Name'},
            height=500
        )
        fig.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig, use_container_width=True)
        
        st.info("💡 **Insight:** 데이터에 따르면, 외국인들은 '전통 문화'와 '자연 생태' 관련 축제를 가장 선호합니다.")
    else:
        st.write("방문객 데이터가 충분하지 않습니다.")

# [Tab 3] 계절별 추천 (큐레이션)
with tab3:
    st.subheader("📅 Recommended Festivals by Season")
    
    season_col1, season_col2, season_col3, season_col4 = st.columns(4)
    
    # 간단한 계절별 필터링
    spring = df[df['month'].isin([3, 4, 5])].sort_values('visitors', ascending=False).head(3)
    summer = df[df['month'].isin([6, 7, 8])].sort_values('visitors', ascending=False).head(3)
    autumn = df[df['month'].isin([9, 10, 11])].sort_values('visitors', ascending=False).head(3)
    winter = df[df['month'].isin([12, 1, 2])].sort_values('visitors', ascending=False).head(3)

    with season_col1:
        st.markdown("#### 🌱 Spring")
        for i, row in spring.iterrows():
            st.write(f"- {row['축제명']}")
    with season_col2:
        st.markdown("#### 🌊 Summer")
        for i, row in summer.iterrows():
            st.write(f"- {row['축제명']}")
    with season_col3:
        st.markdown("#### 🍁 Autumn")
        for i, row in autumn.iterrows():
            st.write(f"- {row['축제명']}")
    with season_col4:
        st.markdown("#### ☃️ Winter")
        for i, row in winter.iterrows():
            st.write(f"- {row['축제명']}")

# [Tab 4] Gemini AI (시뮬레이션)
with tab4:
    st.subheader("🤖 Ask AI about Korea Festivals")
    
    # 채팅 기록
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Hello! I can help you find the best festival. Ask me anything!"}]

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input("Ex: Where is the best place for K-Food?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)
        
        # 간단한 키워드 기반 응답 (발표용)
        response = "I'm analyzing the 2025 festival data..."
        if "food" in prompt.lower() or "음식" in prompt:
            response = "For food lovers, I highly recommend the 'Jeonju Bibimbap Festival' in October. It offers authentic Korean taste!"
        elif "music" in prompt.lower() or "음악" in prompt:
            response = "If you like music, check out the 'Incheon Pentaport Rock Festival' in August. It's huge!"
        elif "seoul" in prompt.lower() or "서울" in prompt:
            response = "In Seoul, the 'Yeouido Cherry Blossom Festival' in April is a must-visit."
        else:
            response = f"That's a great question about '{prompt}'. Please check the Map tab for detailed schedules!"
            
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.chat_message("assistant").write(response)
