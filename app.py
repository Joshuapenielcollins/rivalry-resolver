import streamlit as st
import google.generativeai as genai
import os, time, json, random

st.set_page_config(page_title="Rivalry Resolver", page_icon="⚔️", layout="wide")
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY", ""))

# ==========================================================
# CUSTOM CSS FOR PREMIUM SAAS UI
# ==========================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #0d1117;
        color: #c9d1d9;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .st-emotion-cache-1wmy9hl, .st-emotion-cache-1y4p8pa {
        background: rgba(22, 27, 34, 0.6) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        padding: 1.5rem !important;
        backdrop-filter: blur(10px) !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3) !important;
    }
    
    div[data-testid="column"] {
        background: rgba(22, 27, 34, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
    }

    div[data-testid="stButton"] > button {
        background: linear-gradient(135deg, #6e45e2 0%, #88d3ce 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.2rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(110, 69, 226, 0.4) !important;
        width: 100%;
    }
    div[data-testid="stButton"] > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(110, 69, 226, 0.6) !important;
    }

    h1, h2, h3 {
        color: #ffffff !important;
        font-weight: 800 !important;
        letter-spacing: -0.5px;
    }
    
    div[data-testid="stMetricValue"] {
        font-size: 3rem !important;
        font-weight: 800 !important;
        background: -webkit-linear-gradient(45deg, #ff6b6b, #feca57);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    div[data-testid="stAlert"] {
        border-radius: 10px !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1) !important;
    }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: #0d1117; }
    ::-webkit-scrollbar-thumb { background: #30363d; border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: #484f58; }
</style>
""", unsafe_allow_html=True)

# ==========================================================
# DATA
# ==========================================================
TIERS = [
    {"name": "Casual Banter", "emoji": "💬", "min_pts": 0},
    {"name": "Heated Debate", "emoji": "🔥", "min_pts": 15},
    {"name": "Sworn Rivals", "emoji": "⚔️", "min_pts": 35},
    {"name": "Hall of Flame", "emoji": "👑", "min_pts": 60},
]

def get_tier(points):
    current = TIERS[0]
    for t in TIERS:
        if points >= t["min_pts"]:
            current = t
    return current

MATCH_EVENTS = [
    {"min": 0, "type": "match_start", "desc": "IPL 2021 FINAL — MI vs CSK at Dubai. CSK won toss, chose to bat. Dhoni captains."},
    {"min": 1, "type": "prediction_prompt", "topic": "Faf du Plessis runs", "spice": "Faf has been quiet. Will he fire today?"},
    {"min": 8, "type": "scoring_event", "desc": "Gaikwad and Faf opening steadily. CSK 22/0 in 3."},
    {"min": 12, "type": "dispute_trigger", "claim_a": "Gaikwad will outscore Faf today.", "claim_b": "Faf carries the innings, watch."},
    {"min": 18, "type": "wicket", "desc": "Gaikwad gone for 32 to Chahar. CSK 61/1 in 8."},
    {"min": 22, "type": "prediction_prompt", "topic": "CSK total", "spice": "Lock in a number. Loser eats it."},
    {"min": 28, "type": "scoring_event", "desc": "Faf cruising. 50 in 38 balls. CSK 110/1 in 13."},
    {"min": 35, "type": "dispute_trigger", "claim_a": "MI's bowling is overrated in finals.", "claim_b": "Bumrah always delivers in finals. Wait for the death overs."},
    {"min": 42, "type": "clutch_moment", "desc": "Faf hits Bumrah for back-to-back boundaries. CSK 158/2 in 17."},
    {"min": 48, "type": "scoring_event", "desc": "CSK finish 192/3. Faf 86, Moeen 37*. Massive total."},
    {"min": 52, "type": "innings_break", "desc": "Innings break. MI need 193."},
    {"min": 55, "type": "prediction_prompt", "topic": "First MI wicket", "spice": "Who falls first — Rohit or Quinton?"},
    {"min": 60, "type": "wicket", "desc": "Quinton de Kock gone early to Chahar for 0. MI 1/1."},
    {"min": 65, "type": "dispute_trigger", "claim_a": "MI is done. No way back from this.", "claim_b": "Rohit + Pollard can chase anything. It's not over."},
    {"min": 72, "type": "scoring_event", "desc": "Rohit batting well. MI 67/2 in 8."},
    {"min": 80, "type": "wicket", "desc": "POLLARD GONE FOR ZERO! Caught Jadeja, bowled Hazlewood. MI 90/4 in 12."},
    {"min": 85, "type": "dispute_trigger", "claim_a": "Concede now, save your dignity.", "claim_b": "Hardik can still take it deep. 4 overs to go."},
    {"min": 92, "type": "clutch_moment", "desc": "MI 135/5 in 16. Need 58 off 24. Going down."},
    {"min": 100, "type": "scoring_event", "desc": "MI 158/8 in 19. Game over."},
    {"min": 105, "type": "match_end", "desc": "CSK WIN BY 27 RUNS. 4th IPL title. Dhoni lifts trophy."},
]

SYSTEM_PROMPT = """You are the AI Referee for Rivalry Resolver. Adjudicate disputes and generate predictions.
Always respond ONLY in valid JSON.
"""

DEMO_PREDICTIONS = {
    "Faf du Plessis runs": {"type": "prediction", "question": "Will Faf score 50+ today?", "options": ["Yes, 50+", "No, under 50"], "stakes_note": "1 point."},
    "CSK total": {"type": "prediction", "question": "CSK's final total?", "options": ["Under 170", "170-189", "190+"], "stakes_note": "2 points."},
    "First MI wicket": {"type": "prediction", "question": "Who falls first for MI?", "options": ["Rohit", "Quinton", "Neither"], "stakes_note": "1 point."},
}

DEMO_VERDICTS = [
    {"type": "verdict", "winner": "A", "points_a": 2, "points_b": 0, "reasoning": "Faf carried the innings with 86. A was right.", "tone_note": "Clean argument."},
    {"type": "verdict", "winner": "SPLIT", "points_a": 1, "points_b": 1, "reasoning": "Mixed results for Bumrah. Both had points.", "tone_note": ""},
    {"type": "verdict", "winner": "B", "points_a": 0, "points_b": 3, "reasoning": "B showed loyalty despite the score.", "tone_note": "B showed conviction."},
    {"type": "verdict", "winner": "B", "points_a": 0, "points_b": 2, "reasoning": "Hardik is a finisher, B's faith was logical.", "tone_note": "A was too pessimistic."},
]

def demo_decide(event):
    t = event.get("type")
    if t == "prediction_prompt":
        return DEMO_PREDICTIONS.get(event["topic"], {"type": "prediction", "question": "Make your call.", "options": ["Yes", "No"], "stakes_note": "1 point."})
    if t == "dispute_trigger":
        idx = st.session_state.get("dispute_idx", 0)
        st.session_state["dispute_idx"] = idx + 1
        return DEMO_VERDICTS[idx % len(DEMO_VERDICTS)]
    return {"type": "verdict", "winner": "SPLIT", "points_a": 1, "points_b": 1, "reasoning": "Even call."}

# ==========================================================
# SESSION STATE
# ==========================================================
if "rivalry" not in st.session_state: st.session_state.rivalry = None
if "score_a" not in st.session_state: st.session_state.score_a = 0
if "score_b" not in st.session_state: st.session_state.score_b = 0
if "streak" not in st.session_state: st.session_state.streak = 0
if "dispute_idx" not in st.session_state: st.session_state.dispute_idx = 0
if "event_idx" not in st.session_state: st.session_state.event_idx = 0
if "is_playing" not in st.session_state: st.session_state.is_playing = False
if "feed_events" not in st.session_state: st.session_state.feed_events = []
if "pending_prediction" not in st.session_state: st.session_state.pending_prediction = None
if "referee_messages" not in st.session_state: st.session_state.referee_messages = []
if "action_messages" not in st.session_state: st.session_state.action_messages = []

# ==========================================================
# UI
# ==========================================================
st.markdown("<h1 style='text-align:center; margin-bottom:0;'>⚔️ Rivalry Resolver</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#8b949e; margin-top:0;'>The ultimate referee for friend-vs-friend cricket rivalries</p>", unsafe_allow_html=True)
st.divider()

if st.session_state.rivalry is None:
    _, col_mid, _ = st.columns([1, 2, 1])
    with col_mid:
        st.subheader("🎬 Initialize Rivalry")
        c1, c2 = st.columns(2)
        with c1:
            name_a = st.text_input("Player A", value="Joshua")
            team_a = st.selectbox("Team A", ["CSK", "MI", "RCB", "KKR", "GT", "DC", "RR", "PBKS", "SRH", "LSG"], key="ta")
        with c2:
            name_b = st.text_input("Player B", value="Rohan")
            team_b = st.selectbox("Team B", ["MI", "CSK", "RCB", "KKR", "GT", "DC", "RR", "PBKS", "SRH", "LSG"], key="tb")
        forfeit = st.text_area("🎯 Forfeit", value="Loser pays for dinner at the winner's pick.")
        if st.button("⚔️ START RIVALRY", type="primary"):
            st.session_state.rivalry = {"name_a": name_a, "team_a": team_a, "name_b": name_b, "team_b": team_b, "forfeit": forfeit}
            st.rerun()
else:
    r = st.session_state.rivalry
    tier = get_tier(max(st.session_state.score_a, st.session_state.score_b))

    # Top Stats
    s1, s2, s3 = st.columns([2, 1, 2])
    s1.metric(f"🟢 {r['name_a']} ({r['team_a']})", st.session_state.score_a)
    s2.markdown(f"<h2 style='text-align:center; margin:0;'>{tier['emoji']}</h2><p style='text-align:center;'><b>{tier['name']}</b><br>🔥 {st.session_state.streak}</p>", unsafe_allow_html=True)
    s3.markdown(f"<div style='text-align:right;'>", unsafe_allow_html=True)
    with s3: st.metric(f"🔴 {r['name_b']} ({r['team_b']})", st.session_state.score_b)
    st.markdown("</div>", unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("## ⚔️ Rivalry Control")
        st.write(f"Match: **MI vs CSK** · 2021 Final")
        st.divider()
        demo_mode = st.checkbox("🎭 Demo Mode", value=True)
        speed = st.slider("⏩ Play Speed", 1, 5, 2)
        st.divider()
        if st.button("🔄 Reset"):
            for k in list(st.session_state.keys()): del st.session_state[k]
            st.rerun()

    col1, col2, col3 = st.columns([1, 1.2, 1])

    with col1:
        st.markdown("### 📡 Live Feed")
        for ev in reversed(st.session_state.feed_events):
            t = ev["type"]
            m = ev["min"]
            if t in ("wicket", "match_end"): st.error(f"**Min {m}** 🔥 {ev.get('desc', '')}")
            elif t == "scoring_event": st.success(f"**Min {m}** 🏏 {ev.get('desc', '')}")
            elif t == "prediction_prompt": st.warning(f"**Min {m}** 🎯 Prediction: {ev.get('topic', 'Next Play')}")
            elif t == "dispute_trigger": st.warning(f"**Min {m}** ⚔️ Dispute: {ev.get('claim_a', '')} vs {ev.get('claim_b', '')}")
            else: st.info(f"**Min {m}** · {ev.get('desc', 'Match Update')}")

    with col2:
        st.markdown("### 🤖 Referee")
        for msg in reversed(st.session_state.referee_messages):
            st.markdown(msg, unsafe_allow_html=True)
            st.divider()
            
    with col3:
        st.markdown("### 🏟️ Action Hub")
        if not st.session_state.is_playing and st.session_state.event_idx < len(MATCH_EVENTS) and not st.session_state.pending_prediction:
            if st.button("▶ RESUME MATCH", type="primary"):
                st.session_state.is_playing = True
                st.rerun()
        elif st.session_state.is_playing:
            if st.button("⏸ PAUSE"):
                st.session_state.is_playing = False
                st.rerun()
        
        if st.session_state.pending_prediction:
            p = st.session_state.pending_prediction
            opts = p['decision'].get('options', ["Yes", "No"])
            st.markdown(f"#### 🎯 Prediction: {p['event']['topic']}")
            if demo_mode:
                if st.button("Auto-Resolve (Demo)"):
                    ca, cb = random.choice(opts), random.choice(opts)
                    win = random.choice(["A", "B"])
                    if win == "A": st.session_state.score_a += 1
                    else: st.session_state.score_b += 1
                    st.session_state.action_messages.append(f"✅ **Resolved:** {r['name_a' if win=='A' else 'name_b']} won.")
                    st.session_state.pending_prediction = None
                    st.session_state.is_playing = True
                    st.rerun()
            else:
                with st.form("pred"):
                    ca = st.radio(f"{r['name_a']}'s call", opts)
                    cb = st.radio(f"{r['name_b']}'s call", opts)
                    if st.form_submit_button("Submit Calls"):
                        win = random.choice(["A", "B", "Neither"])
                        if win == "A": st.session_state.score_a += 1
                        elif win == "B": st.session_state.score_b += 1
                        st.session_state.action_messages.append(f"✅ **Resolved:** {win} won round.")
                        st.session_state.pending_prediction = None
                        st.session_state.is_playing = True
                        st.rerun()

        for msg in reversed(st.session_state.action_messages):
            st.markdown(f"<div style='background:rgba(255,255,255,0.05);padding:10px;border-radius:8px;'>{msg}</div>", unsafe_allow_html=True)

    # AUTO-PLAY LOGIC
    if st.session_state.is_playing and st.session_state.event_idx < len(MATCH_EVENTS):
        event = MATCH_EVENTS[st.session_state.event_idx]
        st.session_state.feed_events.append(event)
        
        if event["type"] in ("prediction_prompt", "dispute_trigger"):
            st.session_state.is_playing = False
            dec = demo_decide(event)
            if dec.get("type") == "prediction":
                st.session_state.referee_messages.append(f"🎯 **{dec['question']}**")
                st.session_state.pending_prediction = {"decision": dec, "event": event}
            elif dec.get("type") == "verdict":
                pa, pb = dec.get("points_a", 0), dec.get("points_b", 0)
                st.session_state.score_a += pa; st.session_state.score_b += pb
                st.session_state.referee_messages.append(f"⚖️ **Verdict:** {dec['reasoning']}")
                st.session_state.is_playing = True
        
        st.session_state.event_idx += 1
        time.sleep(2 / speed)
        st.rerun()

    if st.session_state.event_idx >= len(MATCH_EVENTS):
        st.balloons()
        st.success(f"🏆 Final: {st.session_state.score_a} - {st.session_state.score_b}")
        st.error(f"💀 Forfeit: {r['forfeit']}")
