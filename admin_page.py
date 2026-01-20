# admin_page.py
import streamlit as st
import pandas as pd

def render_admin_page(conn, load_user_data_func):
    st.title("🛠️ 시스템 관리자 패널")
    st.markdown("---")

    # 최신 데이터 불러오기
    df = load_user_data_func()

    # 1. 요약 통계 (Metric)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("총 가입자 수", len(df))
    with col2:
        admin_count = len(df[df['role'] == 'admin'])
        st.metric("관리자 수", admin_count)
    with col3:
        # 최근 24시간 내 가입자 등 추가 통계 가능
        st.metric("활성 세션(추정)", len(df[df['session_token'] != ""]))

    st.markdown("### 📋 사용자 데이터베이스 관리")
    st.info("💡 테이블 내의 값을 직접 수정하고 하단의 '변경사항 저장' 버튼을 누르면 구글 시트에 즉시 반영됩니다.")

    # 2. 데이터 에디터 (st.data_editor 활용)
    # 보안을 위해 비밀번호 해시는 수정 불가능하게 설정하거나 숨길 수 있습니다.
    edited_df = st.data_editor(
        df,
        column_config={
            "hashed_password": st.column_config.TextColumn("비밀번호 해시", disabled=True),
            "created_at": st.column_config.DatetimeColumn("가입 일시", disabled=True),
            "role": st.column_config.SelectboxColumn(
                "권한",
                help="사용자의 권한을 설정합니다.",
                options=["user", "admin"],
                required=True,
            )
        },
        num_rows="dynamic", # 행 삭제/추가 가능
        use_container_width=True,
        key="admin_editor"
    )

    # 3. 저장 버튼
    if st.button("💾 변경사항 저장", key="save_admin_changes"):
        try:
            with st.spinner("구글 시트 업데이트 중..."):
                conn.update(worksheet="Users", data=edited_df)
                st.cache_data.clear() # 캐시 초기화하여 즉시 반영
                st.success("✅ 데이터가 성공적으로 저장되었습니다!")
                st.rerun()
        except Exception as e:
            st.error(f"❌ 저장 중 오류 발생: {e}")

#     st.markdown("---")
#     st.markdown("### ⚙️ 시스템 도구")
#     if st.button("🧹 전체 시스템 캐시 초기화"):
#         st.cache_data.clear()
#         st.success("캐시가 초기화되었습니다.")