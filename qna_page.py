# qna_page.py
import streamlit as st
import pandas as pd
from datetime import datetime

def render_qna_page(conn):
    st.title("✉️ 1:1 문의 게시판")
    st.markdown("---")

    # --- [공통] 공지사항 불러오기 섹션 ---
    try:
        notice_df = conn.read(worksheet="Notice", ttl=0)
        if not notice_df.empty:
            st.subheader("📢 공지사항")
            for _, n_row in notice_df.sort_values(by="created_at", ascending=False).iterrows():
                with st.expander(f"📌 {n_row['title']} ({n_row['created_at']})"):
                    st.write(n_row['content'])
            st.markdown("---")
    except:
        pass

    # 기본 컬럼 정의
    required_columns = ['username', 'question', 'answer', 'status', 'created_at', 'replied_at']

    # QnA 데이터 불러오기
    try:
        df = conn.read(worksheet="QnA", ttl=0)

        # 만약 시트가 비어있거나 헤더가 없어서 데이터프레임이 제대로 안 만들어졌을 경우
        if df.empty or 'username' not in df.columns:
            df = pd.DataFrame(columns=required_columns)
    except:
        # 시트 자체를 못 읽어올 경우
        df = pd.DataFrame(columns=required_columns)

    # 현재 접속 유저 정보
    curr_user = st.session_state.username
    is_admin = st.session_state.is_admin

    if not is_admin:
        # --- [일반 유저 화면] ---
        st.subheader("새 질문 작성하기")
        with st.form("qna_form", clear_on_submit=True):
            user_question = st.text_area("문의하실 내용을 입력해주세요.")
            if st.form_submit_button("질문 등록"):
                if user_question.strip():
                    new_q = pd.DataFrame([{
                        "username": curr_user,
                        "question": user_question,
                        "answer": "",
                        "status": "답변대기",
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "replied_at": ""
                    }])
                    updated_df = pd.concat([df, new_q], ignore_index=True)
                    conn.update(worksheet="QnA", data=updated_df)
                    st.success("질문이 등록되었습니다. 관리자가 확인 후 답변드립니다.")
                    st.rerun()
                else:
                    st.warning("내용을 입력해주세요.")

        st.markdown("---")
        st.subheader("내 문의 내역")
        my_qna = df[df['username'] == curr_user].sort_values(by="created_at", ascending=False)

        if my_qna.empty:
            st.info("등록된 문의가 없습니다.")
        else:
            for _, row in my_qna.iterrows():
                with st.expander(f"Q: {row['question'][:30]}... ({row['status']})"):
                    st.write(f"**질문 일시:** {row['created_at']}")
                    st.write(f"**질문 내용:** {row['question']}")
                    st.markdown("---")
                    if row['status'] == "답변완료":
                        st.info(f"**A (관리자 답변):** {row['answer']}")
                        st.caption(f"답변 일시: {row['replied_at']}")
                    else:
                        st.warning("아직 답변이 등록되지 않았습니다.")

    else:
        # --- [어드민 화면] ---
        st.subheader("📥 들어온 문의 목록")
        pending_qna = df[df['status'] == "답변대기"]

        if pending_qna.empty:
            st.success("새로운 문의가 없습니다!")
        else:
            for idx, row in pending_qna.iterrows():
                with st.container():
                    st.write(f"**작성자:** {row['username']} | **작성일:** {row['created_at']}")
                    st.write(f"**질문:** {row['question']}")

                    with st.expander("답변 달기"):
                        admin_answer = st.text_area("답변 내용을 입력하세요", key=f"ans_{idx}")
                        if st.button("답변 저장", key=f"btn_{idx}"):
                            if admin_answer.strip():
                                # 원본 데이터프레임 인덱스 찾아서 수정
                                df.loc[idx, 'answer'] = admin_answer
                                df.loc[idx, 'status'] = "답변완료"
                                df.loc[idx, 'replied_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                conn.update(worksheet="QnA", data=df)
                                st.success("답변이 등록되었습니다.")
                                st.rerun()
                    st.markdown("---")

        if st.checkbox("답변 완료된 내역 보기"):
            completed_qna = df[df['status'] == "답변완료"]
            st.table(completed_qna[['username', 'question', 'answer', 'replied_at']])