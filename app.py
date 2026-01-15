import streamlit as st
import pandas as pd
import datetime
import uuid
import time

# ==========================================
# 1. 시스템 설정
# ==========================================
st.set_page_config(page_title="밥상매치 MVP", layout="wide", page_icon="🍚")

if 'requests' not in st.session_state:
    st.session_state.requests = []
if 'bids' not in st.session_state:
    st.session_state.bids = []
if 'matches' not in st.session_state:
    st.session_state.matches = []

# ==========================================
# 2. 핵심 로직
# ==========================================
def generate_auto_bid(req_id, owner_name, vacancy_rate):
    now_hour = datetime.datetime.now().hour
    if vacancy_rate >= 0.7 or (14 <= now_hour <= 17):
        offer = "20% 할인 + 특수부위 서비스"
        tag = "🔥파격제안"
    elif vacancy_rate >= 0.3:
        offer = "10% 할인 + 음료수"
        tag = "⚡추천제안"
    else:
        offer = "음료수 1병 서비스"
        tag = "일반제안"
        
    return {
        "bid_id": str(uuid.uuid4())[:8],
        "req_id": req_id,
        "owner_name": owner_name,
        "offer": offer,
        "tag": tag,
        "timestamp": datetime.datetime.now().strftime("%H:%M:%S")
    }

# ==========================================
# 3. 사이드바 (역할 선택)
# ==========================================
with st.sidebar:
    st.header("🍚 밥상매치 시뮬레이터")
    role = st.radio("역할 선택", ["👨‍👩‍👧‍👦 손님 (User)", "👨‍🍳 사장님 (Owner)", "📊 관리자 (Admin)"])
    st.divider()
    st.info("💡 팁: 역할을 바꿔가며 [새로고침] 버튼을 눌러야 상대방의 반응이 보입니다!")

# ------------------------------------------
# A. 손님 화면 (User View)
# ------------------------------------------
if role == "👨‍👩‍👧‍👦 손님 (User)":
    st.title("👨‍👩‍👧‍👦 오늘 뭐 드시나요?")

    # [입력 섹션]
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        with c1: location = st.text_input("📍 위치", value="광안리")
        with c2: people = st.number_input("인원", 1, 10, 4)
        with c3: menu = st.selectbox("메뉴", ["회/해산물", "고기", "한식"])
        
        if st.button("📢 사장님 호출하기", type="primary", use_container_width=True):
            req_id = str(uuid.uuid4())[:8]
            new_req = {
                "id": req_id,
                "location": location,
                "people": people,
                "menu": menu,
                "status": "입찰대기",
                "time": datetime.datetime.now().strftime("%H:%M:%S")
            }
            st.session_state.requests.append(new_req)
            
            with st.spinner('주변 사장님들에게 신호를 보내는 중...'):
                time.sleep(0.5)
            st.toast(f"📡 전송 완료! {location} 주변 식당에 알림이 갔습니다!", icon="✅")
            st.rerun()

    # [내 요청 현황]
    st.subheader("📡 내 호출 현황")
    
    if st.session_state.requests:
        my_req = st.session_state.requests[-1]
        
        # 상태 표시
        status_color = "gray"
        if my_req['status'] == "제안도착": status_color = "green"
        elif my_req['status'] == "매칭완료": status_color = "blue"
        st.markdown(f"#### 상태: :{status_color}[{my_req['status']}]")
        
        if st.button("🔄 도착한 제안 확인하기 (새로고침)"):
            st.rerun()

        # 도착한 입찰 및 매칭 로직
        my_bids = [b for b in st.session_state.bids if b['req_id'] == my_req['id']]
        
        if my_req['status'] == "매칭완료":
            st.success("✅ 예약이 확정되었습니다! 식당으로 이동해주세요.")
            # 어떤 식당이랑 됐는지 찾기
            confirmed_bid = next((m for m in st.session_state.matches if m['req_id'] == my_req['id']), None)
            if confirmed_bid:
                 st.info(f"🏪 식당: {confirmed_bid['owner_name']} | 🎁 혜택: {confirmed_bid['offer']}")

        elif my_bids:
            st.write(f"🎁 **{len(my_bids)}개의 제안**이 도착했습니다!")
            for bid in my_bids:
                with st.container(border=True):
                    bc1, bc2, bc3 = st.columns([2,3,1])
                    with bc1: 
                        st.write(f"**{bid['owner_name']}**")
                        st.caption(f"🕒 {bid['timestamp']}")
                    with bc2: 
                        st.success(f"{bid['offer']}")
                    with bc3:
                        if st.button("수락", key=bid['bid_id']):
                            st.session_state.matches.append(bid)
                            # 요청 상태 변경
                            for r in st.session_state.requests:
                                if r['id'] == bid['req_id']:
                                    r['status'] = "매칭완료"
                            st.toast("🎉 매칭 성공! 예약이 확정되었습니다.", icon="😍")
                            st.rerun()
        else:
            st.info("사장님들의 제안을 기다리고 있습니다...")

# ------------------------------------------
# B. 사장님 화면 (Owner View)
# ------------------------------------------
elif role == "👨‍🍳 사장님 (Owner)":
    st.title("👨‍🍳 사장님 전용 알림판")
    
    with st.expander("⚙️ 내 가게 설정", expanded=True):
        shop_name = st.text_input("가게 이름", "A.대박횟집")
        vacancy = st.slider("현재 빈자리", 0.0, 1.0, 0.8)

    st.divider()
    
    if st.button("🔄 알림 및 예약 확인 (새로고침)", type="primary"):
        st.rerun()

    # [1] 예약 확정 알림 (여기가 추가된 부분!)
    # 내 가게 이름으로 성사된 매칭 찾기
    my_matches = [m for m in st.session_state.matches if m['owner_name'] == shop_name]
    
    if my_matches:
        st.success(f"🎉 축하합니다! 총 {len(my_matches)}건의 예약이 확정되었습니다!")
        # 가장 최근 매칭에 대해 효과 주기
        latest_match = my_matches[-1]
        
        for match in my_matches:
            # 매칭된 요청 정보 찾기 (인원, 메뉴 등 표시 위해)
            original_req = next((r for r in st.session_state.requests if r['id'] == match['req_id']), None)
            
            with st.container(border=True):
                mc1, mc2 = st.columns([4, 1])
                with mc1:
                    st.markdown(f"### ✅ **예약 확정!** ({match['timestamp']})")
                    if original_req:
                        st.write(f"**손님:** {original_req['menu']} / {original_req['people']}명 ({original_req['location']})")
                    st.write(f"**제공 혜택:** {match['offer']}")
                with mc2:
                    st.write("🟢 방문 예정")
    
    st.divider()

    # [2] 대기 중인 호출
    st.subheader("🔔 새로운 호출")
    pending_reqs = [r for r in st.session_state.requests if r['status'] in ["입찰대기", "제안도착"]]
    
    if pending_reqs:
        for req in pending_reqs:
            # 이미 매칭된 건(다른 가게랑 된 거) 제외
            if req['status'] == "매칭완료": continue

            with st.container(border=True):
                st.markdown(f"### 🔔 **{req['menu']} {req['people']}명** 호출!")
                st.caption(f"위치: {req['location']} | ID: {req['id']}")
                
                already_bid = any(b['req_id'] == req['id'] and b['owner_name'] == shop_name for b in st.session_state.bids)
                
                if already_bid:
                    st.info("✅ 제안 발송 완료. 손님의 응답 대기 중...")
                else:
                    if st.button("⚡ 빈자리 채우기 (제안 발송)", key=f"bid_{req['id']}"):
                        bid = generate_auto_bid(req['id'], shop_name, vacancy)
                        st.session_state.bids.append(bid)
                        
                        for r in st.session_state.requests:
                            if r['id'] == req['id']:
                                r['status'] = "제안도착"
                        
                        st.toast(f"📨 '{bid['offer']}' 제안을 보냈습니다!", icon="🚀")
                        time.sleep(0.5)
                        st.rerun()
    else:
        st.write("새로운 호출이 없습니다.")

# ------------------------------------------
# C. 관리자 화면
# ------------------------------------------
elif role == "📊 관리자 (Admin)":
    st.title("📊 통합 대시보드")
    m1, m2, m3 = st.columns(3)
    m1.metric("총 호출 수", len(st.session_state.requests))
    m2.metric("총 입찰 수", len(st.session_state.bids))
    m3.metric("성사된 거래", len(st.session_state.matches))
    
    st.write("### 매칭 데이터 로그")
    if st.session_state.matches:
        st.dataframe(pd.DataFrame(st.session_state.matches))
