import streamlit as st
from google import genai
from rss_collector import fetch_rss_feeds, fetch_naver_news, SOURCES

# CSS 파일을 불러오는 유틸리티 함수
def local_css(file_name):
    with open(file_name, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# --- Gemini 요약 함수 ---
def analyze_news_gemini(api_key, title, summary):
    try:
        client = genai.Client(api_key=api_key.strip())
        prompt = f"투자 전문가로서 뉴스 분석: {title}\n내용: {summary}. 핵심요약, 시장영향, 투자포인트 작성."
        response = client.models.generate_content(model="gemini-3-flash-preview", contents=prompt)
        return response.text
    except Exception as e:
        return f"⚠️ 분석 실패: {str(e)}"

# --- 개별 뉴스 카드 렌더링 함수 ---
def display_news_cards(df, market_key):
    local_css("style_global.css")
    if df.empty:
        st.info("표시할 뉴스가 없습니다.")
        return

    for idx, row in df.head(10).iterrows():
        with st.container():
            pub_time = row["published"].strftime("%m/%d %H:%M")
            st.markdown(
                f'<div class="news-card">'
                f'<h3>{row["title"]}</h3>'
                f'<p style="color:#6B7280; font-size:0.9rem;">{row["published"].strftime("%Y-%m-%d %H:%M")} | '
                f'<a href="{row["link"]}" target="_blank" style="color:#3B82F6;">기사 원문</a></p>'
                f'</div>',
                unsafe_allow_html=True
            )

            if st.button(f"🤖 AI 분석 실행", key=f"ai_{market_key}_{idx}"):
                if st.session_state.logged_in:
                    if st.session_state.user_keys['GEMINI']:
                        with st.spinner("AI 분석 중..."):
                            res = analyze_news_gemini(st.session_state.user_keys['GEMINI'], row['title'], row['summary'])
                            st.markdown(f'<div class="ai-result">{res}</div>', unsafe_allow_html=True)
                    else:
                        st.error("API 키를 등록해주세요.")
                else:
                    st.warning("로그인이 필요합니다.")

# --- 메인 뉴스 화면 렌더링 함수 ---
def render_news_section():
    st.title("📈 증시 핵심 요약 대시보드")

    # 1단계 메인 탭: 국내장, 미국장
    tab_kor, tab_usa, tab_search = st.tabs(["🇰🇷 국내장", "🇺🇸 미국장", "🔍 뉴스 검색"])

    # --- 국내장 섹션 ---
    with tab_kor:
        kor_source_names = list(SOURCES["KOREA"].keys())
        # 2단계 하위 탭: 국내 언론사 6개
        sub_tabs_kor = st.tabs(kor_source_names)

        for i, name in enumerate(kor_source_names):
            with sub_tabs_kor[i]:
                st.subheader(f"🇰🇷 {name} 증시 뉴스")
                if st.button(f"🔄 {name} 새로고침", key=f"refresh_kor_{i}"):
                    st.cache_data.clear()
                    st.rerun()

                news_df = fetch_rss_feeds("KOREA", source_name=name)
                display_news_cards(news_df, f"KOR_{name}")

    # --- 미국장 섹션 ---
    with tab_usa:
        usa_source_names = list(SOURCES["USA"].keys())
        # 2단계 하위 탭: 미국 관련 소스 2개
        sub_tabs_usa = st.tabs(usa_source_names)

        for i, name in enumerate(usa_source_names):
            with sub_tabs_usa[i]:
                st.subheader(f"🇺🇸 {name} 뉴스")
                if st.button(f"🔄 {name} 새로고침", key=f"refresh_usa_{i}"):
                    st.cache_data.clear()
                    st.rerun()

                news_df = fetch_rss_feeds("USA", source_name=name)
                display_news_cards(news_df, f"USA_{name}")

    # --- [신규] 뉴스 검색 탭 ---
    with tab_search:
        st.subheader("🔎 키워드로 뉴스 찾기")
        # 검색 폼 사용 (엔터를 치거나 버튼을 누를 때만 실행)
        with st.form(key="search_form"):
            col1, col2 = st.columns([3, 1])
            with col1:
                query = st.text_input("검색어를 입력하세요", key="search_input_field")
            with col2:
                search_market = st.selectbox("시장", ["국내(Naver)"])

            submit_btn = st.form_submit_button("검색 실행")

        # 검색 버튼을 누르면 결과를 세션에 저장
        if submit_btn and query:
            with st.spinner(f"'{query}' 검색 중..."):
                if search_market == "국내(Naver)":
                    df_res = fetch_naver_news(query)

                # 검색 결과와 키워드를 세션에 저장 (핵심!)
                st.session_state['last_search_df'] = df_res
                st.session_state['last_query'] = query

        # 페이지가 새로고침되어도 세션에 결과가 있으면 출력
        if 'last_search_df' in st.session_state:
            st.write(f"### '{st.session_state.last_query}' 검색 결과")
            display_news_cards(st.session_state.last_search_df, "SEARCH_RESULT")