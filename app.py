import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time
import secrets  # 보안 토큰 생성용
from streamlit_gsheets import GSheetsConnection
import bcrypt
from dotenv import load_dotenv
from admin_page import render_admin_page
from qna_page import render_qna_page
from mypage import render_mypage
from notice_page import render_notice_manager

# [중요] 방금 만든 파일에서 함수 불러오기
from news_dashboard import render_news_section

def local_css(file_name):
    with open(file_name, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# 페이지 설정 직후 호출
st.set_page_config(page_title="증시 핵심 요약", layout="wide")
local_css("style_global.css")

load_dotenv()

# --- 데이터 연결 --- #
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=2)
def load_user_data():
    try:
        return conn.read(worksheet="Users", ttl=0)
        if 'role' not in df.columns:
            df['role'] = 'user'
        return df
    except:
        return pd.DataFrame(columns=['username', 'hashed_password', 'openai_api_key', 'gemini_api_key', 'session_token', 'created_at'])

# --- 세션 초기화 --- #
if 'logged_in' not in st.session_state:
    st.session_state.update({
        'logged_in': False,
        'username': None,
        'is_admin': False,
        'user_keys': {'GEMINI': None, 'OPENAI': None}
    })

# ---------------------------------------------------------
# [수정 핵심] URL 파라미터를 이용한 자동 로그인 로직
# ---------------------------------------------------------
# 주소창에 ?token=... 이 있는지 확인
query_params = st.query_params
url_token = query_params.get("token")

if url_token and not st.session_state.logged_in:
    df = load_user_data()
    # 시트에서 해당 토큰을 가진 유저 검색
    user_match = df[df['session_token'] == url_token]

    if not user_match.empty:
        user = user_match.iloc[0]
        st.session_state.update({
            'logged_in': True,
            'username': user['username'],
            'is_admin': str(user.get('role')).lower() == 'admin',
            'user_keys': {'GEMINI': user.get('gemini_api_key'), 'OPENAI': user.get('openai_api_key')}
        })
        # 자동 로그인 성공 후 화면 유지

# --- 사이드바 (로그인/회원가입) --- #
with st.sidebar:
    st.title("👤 멤버십")
    if not st.session_state.logged_in:
        menu = st.radio("메뉴 선택", ["로그인", "회원가입"])
        if menu == "로그인":
            with st.form("login"):
                uid = st.text_input("아이디")
                upw = st.text_input("비밀번호", type="password")
                if st.form_submit_button("로그인"):
                    df = load_user_data()
                    if uid in df['username'].values:
                        user = df[df['username'] == uid].iloc[0]
                        if bcrypt.checkpw(upw.encode('utf-8'), str(user['hashed_password']).encode('utf-8')):
                            # 1. 고유 세션 토큰 생성 (보안 강화)
                            new_token = secrets.token_urlsafe(32)

                            # 2. [핵심 수정] 한국 시간(KST) 계산
                            # 서버 시간(UTC)에 9시간을 더해 한국 시간으로 맞춥니다.
                            kst_now = datetime.now() + timedelta(hours=9)
                            kst_now_str = kst_now.strftime("%Y-%m-%d %H:%M:%S")

                            # 2. [DB 업데이트] 토큰과 마지막 로그인 시간 저장
                            df.loc[df['username'] == uid, 'session_token'] = new_token
                            df.loc[df['username'] == uid, 'last_login'] = kst_now_str
                            conn.update(worksheet="Users", data=df)

                            # 3. 세션 업데이트
                            st.session_state.update({
                                'logged_in': True,
                                'username': uid,
                                'is_admin': str(user.get('role')).lower() == 'admin', # 권한 확인
                                'user_keys': {'GEMINI': user.get('gemini_api_key'), 'OPENAI': user.get('openai_api_key')}
                            })

                            # 4. 주소창에 토큰 심기 및 강제 새로고침
                            st.query_params.token = new_token
                            st.success("로그인 성공!")
                            st.rerun()
                        else: st.error("비밀번호 불일치")
                    else: st.error("아이디 없음")
        else:
            with st.form("signup"):
                nid = st.text_input("아이디")
                npw = st.text_input("비밀번호", type="password")
                nge = st.text_input("Gemini API Key (선택)")
                noa = st.text_input("GPT API Key (선택)")
                if st.form_submit_button("가입하기"):
                    df = load_user_data()
                    if nid in df['username'].values: st.error("중복 아이디 입니다.")
                    else:
                        hashed = bcrypt.hashpw(npw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                        new_row = pd.DataFrame([{
                            "username": nid,
                            "hashed_password": hashed,
                            "gemini_api_key": nge,
                            "openai_api_key": noa,
                            "session_token": "", # 초기 토큰은 비어있음
                            "created_at": datetime.now().isoformat(),
                            "role": "user"
                        }])
                        conn.update(worksheet="Users", data=pd.concat([df, new_row], ignore_index=True))
                        st.success("가입 완료!")
    else:
        st.success(f"반가워요, {st.session_state.username}님!")

        main_menu = ["뉴스 대시보드", "1:1 질문", "마이페이지"]
        if st.session_state.is_admin:
            main_menu.append("📢 공지사항 관리")
            main_menu.append("🛠️ 어드민 설정")

        selected_page = st.radio("이동", main_menu)

        if st.button("로그아웃"):
            # 로그아웃 시 시트의 토큰 무효화 (보안)
            df = load_user_data()
            df.loc[df['username'] == st.session_state.username, 'session_token'] = ""
            conn.update(worksheet="Users", data=df)

            # 세션 및 URL 파라미터 초기화
            st.session_state.update({'logged_in': False, 'username': None, 'user_keys': {'GEMINI': None, 'OPENAI': None}})
            st.query_params.clear()
            st.rerun()

# --- 메인 컨텐츠 제어 --- #
if st.session_state.logged_in:
    if selected_page == "뉴스 대시보드":
        # --- [추가] 최상단 공지사항 노출 로직 ---
        try:
            # Notice 워크시트에서 데이터 로드 (가장 최신 것이 첫 번째로 오게 정렬됨)
            notice_df = conn.read(worksheet="Notice", ttl=0)
            if not notice_df.empty:
                # 최신순으로 정렬 후 첫 번째 행 가져오기
                latest_notice = notice_df.sort_values(by="created_at", ascending=False).iloc[0]

                # 메인 컨텐츠 최상단에 강조된 박스로 표시
                st.info(f"📢 **최신 공지**: {latest_notice['title']} ({latest_notice['created_at']})")
                with st.expander("공지 내용 상세보기"):
                    st.write(latest_notice['content'])
                st.markdown("<br>", unsafe_allow_html=True) # 약간의 여백
        except Exception as e:
            # 시트가 없거나 읽기 오류 시 무시 (사용자 경험 방해 금지)
            pass
        render_news_section()
    elif selected_page == "1:1 질문":
        render_qna_page(conn) # QnA 페이지 호출
    elif selected_page == "마이페이지":
        render_mypage(conn)
    elif selected_page == "📢 공지사항 관리": # 새로 만든 페이지 연결
        render_notice_manager(conn)
    elif selected_page == "🛠️ 어드민 설정":
        render_admin_page(conn, load_user_data)
else:
    # 비로그인 시 기본 화면
    render_news_section()