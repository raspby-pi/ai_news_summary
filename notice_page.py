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

    # 2. 새 공지사항 작성 섹션
    st.subheader("🆕 새 공지사항 등록")
    with st.form("admin_notice_form", clear_on_submit=True):
        n_title = st.text_input("공지 제목", placeholder="제목을 입력하세요")
        n_content = st.text_area("공지 내용", placeholder="내용을 입력하세요", height=200)
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

    # 3. 기존 공지사항 목록 및 삭제 섹션
    st.subheader("🗑️ 공지사항 목록 및 삭제")
    if notice_df.empty:
        st.info("현재 등록된 공지사항이 없습니다.")
    else:
        # 최신순 정렬
        notice_df = notice_df.sort_values(by="created_at", ascending=False)
        for idx, row in notice_df.iterrows():
            # 각 공지사항별 컨테이너
            with st.container():
                col1, col2, col3 = st.columns([6, 1, 1])

                with col1:
                    st.markdown(f"**{row['title']}**")
                    st.caption(f"작성일: {row['created_at']}")

                with col2:
                    # 수정 버튼: 클릭 시 세션 상태에 수정 모드 활성화
                    edit_mode_key = f"edit_mode_{idx}"
                    if st.button("수정", key=f"btn_edit_{idx}"):
                        st.session_state[edit_mode_key] = True

                with col3:
                    # 삭제 버튼
                    if st.button("삭제", key=f"btn_del_{idx}"):
                        updated_df = notice_df.drop(idx)
                        conn.update(worksheet="Notice", data=updated_df)
                        st.toast("🗑️ 공지사항이 삭제되었습니다.")
                        st.rerun()

                # 수정 모드 활성화 시 입력 폼 등장
                if st.session_state.get(edit_mode_key, False):
                    with st.form(key=f"edit_form_{idx}"):
                        edit_title = st.text_input("제목 수정", value=row['title'])
                        edit_content = st.text_area("내용 수정", value=row['content'], height=150)

                        col_f1, col_f2 = st.columns([1, 1])
                        with col_f1:
                            if st.form_submit_button("💾 변경사항 저장"):
                                # 데이터 업데이트
                                notice_df.at[idx, 'title'] = edit_title
                                notice_df.at[idx, 'content'] = edit_content
                                # (선택사항) 수정 시간으로 업데이트하고 싶다면 아래 주석 해제
                                # notice_df.at[idx, 'created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                                conn.update(worksheet="Notice", data=notice_df)
                                st.session_state[edit_mode_key] = False
                                st.success("✅ 수정이 완료되었습니다.")
                                st.rerun()
                        with col_f2:
                            if st.form_submit_button("취소"):
                                st.session_state[edit_mode_key] = False
                                st.rerun()

                st.markdown("---")