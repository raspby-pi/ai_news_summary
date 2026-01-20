import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import bcrypt
import os

# --- CSS 파일을 불러오는 함수 ---
def local_css(file_name):
    if os.path.exists(file_name):
        with open(file_name, encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.error(f"CSS 파일을 찾을 수 없습니다: {file_name}")

def render_mypage(conn):
    local_css("mypage.css") # 외부 파일 로드

    # --- 로그인 체크 ---
    if 'logged_in' not in st.session_state or not st.session_state.logged_in:
        st.warning("🔒 로그인이 필요한 페이지입니다. 메인 홈에서 로그인해 주세요.")
        st.stop()

    def update_info(field, value):
        try:
            df = conn.read(worksheet="Users")
            idx = df.index[df['username'] == st.session_state.username].tolist()[0]
            if field == 'password':
                df.at[idx, 'hashed_password'] = bcrypt.hashpw(value.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            elif field == 'gemini':
                df.at[idx, 'gemini_api_key'] = value
                st.session_state.user_keys['GEMINI'] = value
            elif field == 'gpt':
                df.at[idx, 'openai_api_key'] = value
                st.session_state.user_keys['OPENAI'] = value
            conn.update(worksheet="Users", data=df)
            st.cache_data.clear()
            return True
        except Exception as e:
            st.error(f"오류 발생: {e}")
            return False

    # --- 메인 레이아웃 ---
    st.title("⚙️ 계정 설정")

    # === 1. Gemini 섹션 ===
    st.markdown('<div class="gemini-box">', unsafe_allow_html=True)
    st.subheader("💎 Gemini API 설정")
    st.write("AI 분석 기능을 사용하기 위해 Google API 키가 필요합니다.")

    # 입력창
    new_gemini = st.text_input("Gemini API Key",
                               value=st.session_state.user_keys.get('GEMINI', ''),
                               type="password",
                               key="edit_gemini")

    if st.button("저장", key="btn_gemini"):
        if update_info('gemini', new_gemini):
            st.toast("✅ Gemini 키가 업데이트되었습니다!")

    # --- 가이드 (Expander로 깔끔하게 정리) ---
    with st.expander("💡 API 키 발급 방법이 궁금하신가요? (그림 가이드)"):
        st.markdown('<div class="guide-box">', unsafe_allow_html=True)

        # STEP 1
        col1, col2 = st.columns([1, 1.2])
        with col1: # expander 안쪽으로 들여쓰기가 정확해야 합니다.
            st.markdown("#### **STEP 1**")
            st.write("**Google AI Studio 접속**")
            st.write("[Google AI Studio](https://aistudio.google.com/app/apikey)에 접속하여 로그인하세요.")
            st.write("오른쪽 상단에 **'API 키 만들기'** 버튼을 클릭합니다.")
        with col2:
            try:
                st.image("img/1.png", caption="키 생성 버튼 위치", use_container_width=True)
            except:
                st.warning("⚠️ 'img/guide_step1.png' 없음")

        st.markdown("<br>", unsafe_allow_html=True)
        st.divider()

        # STEP 2
        col3, col4 = st.columns([1, 1.2])
        with col3:
            st.markdown("#### **STEP 2**")
            st.write("**키 생성**")
            st.write("**'키 만들기'** 버튼을 클릭합니다.")
        with col4:
            try:
                st.image("img/2.png", caption="키 만들기 버튼 위치", use_container_width=True)
            except:
                st.warning("⚠️ 'img/guide_step2.png' 없음")

        st.markdown("<br>", unsafe_allow_html=True)
        st.divider()

        # STEP 3
        col5, col6 = st.columns([1, 1.2])
        with col5:
            st.markdown("#### **STEP 3**")
            st.write("**생성된 키 선택**")
            st.write("생성된 키 를 선택합니다.")
        with col6:
            try:
                st.image("img/3.png", caption="키 선택", use_container_width=True)
            except:
                st.warning("⚠️ 'img/guide_step2.png' 없음")

        st.markdown("<br>", unsafe_allow_html=True)
        st.divider()

        # STEP 4
        col7, col8 = st.columns([1, 1.2])
        with col7:
            st.markdown("#### **STEP 4**")
            st.write("**키 복사**")
            st.write("**'키 복사'** 버튼을 클릭합니다.")
        with col8:
            try:
                st.image("img/4.png", caption="키 복사 버튼 위치", use_container_width=True)
            except:
                st.warning("⚠️ 'img/guide_step2.png' 없음")
        # STEP 5
        col9, col10 = st.columns([1, 1.2])
        with col9:
            st.markdown("#### **STEP 5**")
            st.write("**마이페이지 키 업데이트**")
            st.write("왼쪽 상단에 펼치기 버튼을 눌러 mypage 로 이동합니다.")
            st.write("**'Gemini API 설정'** 에 발급된 `AIza...` 키를 붙여넣습니다.")
            st.write("**'저장'** 버튼을 누르면 설정이 완료됩니다.")

        st.markdown('</div>', unsafe_allow_html=True)
    # expander가 닫히는 지점

    st.divider()

    # === 2. GPT 섹션 (투명 배경) ===
    # with st.container():
    #     st.markdown('<div class="gemini-container-marker"></div>', unsafe_allow_html=True)
    #     st.markdown('<h3>🤖 GPT API 설정</h3>', unsafe_allow_html=True)
    #     st.markdown('<p>OpenAI API 키를 입력하세요. (선택사항)</p>', unsafe_allow_html=True)
    #     st.markdown('<b>GPT API Key</b>', unsafe_allow_html=True)
    #     new_gpt = st.text_input("o_key", value=st.session_state.user_keys.get('OPENAI', ''), type="password", key="edit_gpt", label_visibility="collapsed")
    #     if st.button("수정", key="btn_gpt"):
    #         if update_info('gpt', new_gpt):
    #             st.toast("✅ GPT 키 업데이트 완료!")
    #
    # st.divider()

    # === 3. 비밀번호 섹션 (투명 배경) ===
    with st.container():
        st.markdown('<div class="gemini-container-marker"></div>', unsafe_allow_html=True)
        st.markdown('<h3>🔒 비밀번호 변경</h3>', unsafe_allow_html=True)
        st.markdown('<p>새로운 비밀번호를 입력하세요. (4자 이상)</p>', unsafe_allow_html=True)
        st.markdown('<b>New Password</b>', unsafe_allow_html=True)
        new_pw = st.text_input("p_key", type="password", key="edit_pw", label_visibility="collapsed")
        if st.button("저장", key="btn_pw"):
            if len(new_pw) >= 4:
                if update_info('password', new_pw):
                    st.toast("✅ 비밀번호 변경 완료!")
            else:
                st.error("비밀번호는 4자 이상이어야 합니다.")