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
            col1, col2 = st.columns([7, 1])
            with col1:
                with st.expander(f"📌 {row['title']} ({row['created_at']})"):
                    st.write(row['content'])
            with col2:
                if st.button("삭제", key=f"del_notice_{idx}"):
                    # 해당 인덱스 삭제 후 업데이트
                    updated_df = notice_df.drop(idx)
                    conn.update(worksheet="Notice", data=updated_df)
                    st.toast("🗑️ 공지사항이 삭제되었습니다.")
                    st.rerun()