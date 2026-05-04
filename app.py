import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import os

# 1. 페이지 설정 및 제목
st.set_page_config(page_title="서울시 공공자전거 분석 대시보드", layout="wide")
st.title("🚲 서울시 공공자전거 이용현황 대시보드")
st.markdown("데이터를 통해 자전거 이용 패턴과 기온의 상관관계를 확인해보세요.")

# 2. 데이터베이스 연결 함수
DB_NAME = 'bicycle.db'

def get_connection():
    if not os.path.exists(DB_NAME):
        return None
    return sqlite3.connect(DB_NAME)

conn = get_connection()

# 3. 데이터베이스 존재 여부 체크
if conn is None:
    st.error(f"⚠️ '{DB_NAME}' 파일을 찾을 수 없습니다. 데이터베이스 파일이 같은 폴더에 있는지 확인해 주세요.")
    st.stop()

# --- 차트 1: 월별 이용 패턴 ---
st.header("1. 월별 이용 패턴")
query1 = """
SELECT 대여일자, SUM(이용건수) as 총이용건수
FROM 이용정보
GROUP BY 대여일자
ORDER BY 대여일자
"""
df1 = pd.read_sql(query1, conn)
fig1 = px.line(df1, x='대여일자', y='총이용건수', markers=True, title="월별 총 이용건수 변화")
st.plotly_chart(fig1, use_container_width=True)

with st.expander("🔍 SQL 및 인사이트 보기"):
    st.code(query1, language='sql')
    st.write("- **인사이트:** 동절기(12월~2월)에는 이용량이 급격히 감소하다가 날씨가 풀리는 3월부터 이용량이 증가하는 경향을 보입니다.")
    st.write("- **데이터 설명:** 매월 이용건수의 합계를 구해 시계열 흐름을 시각화했습니다.")

# --- 차트 2: 기온별 평균 이용량 ---
st.header("2. 기온별 평균 이용량 (5도 단위)")
query2 = """
SELECT 
    (CAST(평균기온/5 AS INT) * 5) as 기온구간,
    AVG(이용건수) as 평균이용건수
FROM 이용정보 i
JOIN 기온 t ON i.대여일자 = t.년월
GROUP BY 기온구간
ORDER BY 기온구간
"""
df2 = pd.read_sql(query2, conn)
# 구간 이름을 예쁘게 포맷팅 (예: 5 ~ 10도)
df2['기온구간_명'] = df2['기온구간'].astype(str) + " ~ " + (df2['기온구간'] + 5).astype(str) + "도"

fig2 = px.bar(df2, x='기온구간_명', y='평균이용건수', color='평균이용건수',
             title="기온 구간별 평균 이용건수", color_continuous_scale='Viridis')
st.plotly_chart(fig2, use_container_width=True)

with st.expander("🔍 SQL 및 인사이트 보기"):
    st.code(query2, language='sql')
    st.write("- **인사이트:** 이용량은 20~25도 사이에서 가장 활발하며, 너무 덥거나(30도 이상) 추운 날씨에는 이용 건수가 줄어듭니다.")
    st.write("- **데이터 설명:** 기온 데이터를 5도 단위로 범주화(Binning)하여 날씨와 이용량의 상관관계를 분석했습니다.")

# --- 차트 3: 인기 대여소 TOP 10 ---
st.header("3. 가장 인기 있는 대여소 TOP 10")
query3 = """
SELECT s.보관소명, SUM(i.이용건수) as 총이용건수
FROM 이용정보 i
JOIN 대여소 s ON i.대여소번호 = s.대여소번호
GROUP BY s.보관소명
ORDER BY 총이용건수 DESC
LIMIT 10
"""
df3 = pd.read_sql(query3, conn)
fig3 = px.bar(df3, x='총이용건수', y='보관소명', orientation='h', 
             title="총 이용건수 상위 10개 대여소", color='총이용건수')
# Y축이 반대로 나오는 것을 방지 (높은 순서대로 위로)
fig3.update_layout(yaxis={'categoryorder':'total ascending'})
st.plotly_chart(fig3, use_container_width=True)

with st.expander("🔍 SQL 및 인사이트 보기"):
    st.code(query3, language='sql')
    st.write("- **인사이트:** 한강 공원 근처나 지하철 역세권 대여소가 상위권을 차지하고 있습니다.")
    st.write("- **데이터 설명:** 대여소 테이블과 조인하여 번호 대신 실제 위치 명칭을 사용해 가독성을 높였습니다.")

# 연결 종료
conn.close()