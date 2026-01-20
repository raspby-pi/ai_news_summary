# notice_page.py
import streamlit as st
import pandas as pd
from datetime import datetime

def render_notice_manager(conn):
    st.title("📢 공지사항 관리 (Admin)")
    st.markdown("---")

    # 1. 데이터 불러오기
    try:
        notice_df = conn.read(worksheet="Notice", ttl=0)
    except:
        notice_df = pd.DataFrame(columns=['title', 'content', 'created_at'])

    # 2. 새 공지사항 등록 섹션
    st.subheader("🆕 새 공지사항 등록")
    with st.form("admin_notice_form", clear_on_submit=True):
        n_title = st.text_input("공지 제목", placeholder="제목을 입력하세요")
        n_content = st.text_area("공지 내용", placeholder="내용을 입력하세요 (엔터로 줄바꿈 가능)", height=200)
        submit = st.form_submit_button("공지사항 게시")

        if submit:
            if n_title and n_content:
                new_n = pd.DataFrame([{
                    "title": n_title,
                    "content": n_content,
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }])
                updated_df = pd.concat([notice_df, new_n], ignore_index=True)
                conn.update(worksheet="Notice", data=updated_df)
                st.success("✅ 공지사항이 성공적으로 등록되었습니다.")
                st.rerun()
            else:
                st.error("❌ 제목과 내용을 모두 입력해주세요.")

    st.markdown("---")

    # 3. 기존 공지사항 목록 관리 (펼치기 로직 유지)
    st.subheader("📋 공지사항 목록 관리")

    if notice_df.empty:
        st.info("현재 등록된 공지사항이 없습니다.")
    else:
        # 최신순 정렬
        notice_df = notice_df.sort_values(by="created_at", ascending=False)

        for idx, row in notice_df.iterrows():
            edit_mode_key = f"edit_mode_{idx}"

            # --- 수정 모드가 아닐 때 (일반 조회 화면) ---
            if not st.session_state.get(edit_mode_key, False):
                col_title, col_edit, col_del = st.columns([6, 1, 1])

                with col_title:
                    # 기존의 펼치기(Expander) 로직 유지
                    with st.expander(f"📌 {row['title']} ({row['created_at']})"):
                        # 엔터(줄바꿈) 보존을 위한 스타일 적용
                        st.markdown(
                            f"""<div style="white-space: pre-wrap; word-wrap: break-word;">{row['content']}</div>""",
                            unsafe_allow_html=True
                        )

                with col_edit:
                    if st.button("📝 수정", key=f"btn_edit_{idx}"):
                        st.session_state[edit_mode_key] = True
                        st.rerun()

                with col_del:
                    if st.button("🗑️ 삭제", key=f"btn_del_{idx}"):
                        updated_df = notice_df.drop(idx)
                        conn.update(worksheet="Notice", data=updated_df)
                        st.toast("🗑️ 삭제 완료")
                        st.rerun()

            # --- 수정 모드일 때 (폼 화면으로 전환) ---
            else:
                st.info(f"✏️ '{row['title']}' 공지 수정 중...")
                with st.form(key=f"edit_form_{idx}"):
                    new_title = st.text_input("제목 수정", value=row['title'])
                    new_content = st.text_area("내용 수정", value=row['content'], height=200)

                    btn_col1, btn_col2 = st.columns([1, 1])
                    with btn_col1:
                        if st.form_submit_button("💾 저장"):
                            # 인덱스를 사용하여 정확한 행 수정
                            notice_df.at[idx, 'title'] = new_title
                            notice_df.at[idx, 'content'] = new_content
                            conn.update(worksheet="Notice", data=notice_df)
                            st.session_state[edit_mode_key] = False
                            st.success("✅ 수정 완료")
                            st.rerun()
                    with btn_col2:
                        if st.form_submit_button("취소"):
                            st.session_state[edit_mode_key] = False
                            st.rerun()

            st.markdown("<div style='margin-bottom: 5px;'></div>", unsafe_allow_html=True)