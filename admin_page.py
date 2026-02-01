import streamlit as st
import pandas as pd

def render_admin_page(conn, load_user_data_func):
    st.title("🛠️ 시스템 관리자 패널")
    st.markdown("---")

    # 1. 사용자 데이터 불러오기 (변수명: df_users)
    try:
        df_users = load_user_data_func()
    except Exception as e:
        st.error(f"사용자 데이터를 불러오는 중 오류 발생: {e}")
        df_users = pd.DataFrame()

    # 2. 방문자 데이터 불러오기 (Visitors 시트)
    try:
        # ttl=0으로 최신 데이터 로드
        df_visitors = conn.read(worksheet="Visitors", ttl=0)

        # 데이터가 있고 날짜 컬럼이 있는지 확인
        if not df_visitors.empty and 'date' in df_visitors.columns and 'count' in df_visitors.columns:
            # 날짜 형식 변환 및 정렬
            df_visitors['date'] = pd.to_datetime(df_visitors['date'])
            df_visitors = df_visitors.sort_values(by='date')

            total_visits = df_visitors['count'].sum()
            # 마지막 행(오늘 날짜일 가능성이 높음)의 방문자 수
            last_row = df_visitors.iloc[-1]
            today_visits = last_row['count']
        else:
            total_visits = 0
            today_visits = 0
            df_visitors = pd.DataFrame()

    except Exception as e:
        # 시트가 없거나 읽기 오류 시 초기화
        df_visitors = pd.DataFrame()
        total_visits = 0
        today_visits = 0

    # 3. 대시보드 요약 통계 (Metric)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("총 가입자 수", f"{len(df_users)}명")
    with col2:
        st.metric("누적 방문자 수", f"{total_visits}회")
    with col3:
        st.metric("오늘 방문자 수(추정)", f"{today_visits}회")
    with col4:
        if not df_users.empty and 'role' in df_users.columns:
            admin_count = len(df_users[df_users['role'] == 'admin'])
        else:
            admin_count = 0
        st.metric("관리자 수", f"{admin_count}명")

    # 4. 방문자 추이 차트
    if not df_visitors.empty and 'date' in df_visitors.columns:
        st.markdown("### 📈 일별 방문자 추이")
        # 날짜를 인덱스로 설정하여 라인 차트 그리기
        chart_data = df_visitors.set_index('date')['count']
        st.line_chart(chart_data, color="#FF4B4B")

    st.markdown("---")
    st.markdown("### 📋 사용자 데이터베이스 관리")
    st.info("💡 테이블 내의 값을 직접 수정하고 하단의 '변경사항 저장' 버튼을 누르면 구글 시트에 즉시 반영됩니다.")

    # 5. 사용자 데이터 에디터
    if not df_users.empty:
        edited_df = st.data_editor(
            df_users,
            column_config={
                "hashed_password": st.column_config.TextColumn("비밀번호 해시", disabled=True),
                "created_at": st.column_config.DatetimeColumn("가입 일시", disabled=True),
                "last_login": st.column_config.TextColumn("마지막 로그인", disabled=True),
                "role": st.column_config.SelectboxColumn(
                    "권한",
                    help="사용자의 권한을 설정합니다.",
                    options=["user", "admin"],
                    required=True,
                )
            },
            num_rows="dynamic",
            use_container_width=True,
            key="admin_editor"
        )

        # 6. 저장 버튼
        if st.button("💾 변경사항 저장", key="save_admin_changes"):
            try:
                with st.spinner("구글 시트 업데이트 중..."):
                    conn.update(worksheet="Users", data=edited_df)
                    st.success("✅ 데이터가 성공적으로 저장되었습니다!")
                    # 1초 후 새로고침하여 변경사항 반영 확인
                    import time
                    time.sleep(1)
                    st.rerun()
            except Exception as e:
                st.error(f"저장 중 오류가 발생했습니다: {e}")
    else:
        st.warning("표시할 사용자 데이터가 없습니다.")