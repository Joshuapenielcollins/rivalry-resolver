import streamlit as st
import google.generativeai as genai
import os, time, json, random

st.set_page_config(page_title="Rivalry Resolver", page_icon="⚔️", layout="wide")
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY", ""))

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

# MI vs CSK, IPL 2021 Final, Dubai. CSK won by 27 runs.
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

SYSTEM_PROMPT = """You are the AI Referee for Rivalry Resolver, a platform where two friends gamify their cricket rivalry.

Your jobs:
1. Generate prediction prompts: short, spicy, specific. Force a clear binary or numeric call.
2. Adjudicate disputes: read both claims, fact-check using your cricket knowledge, weigh nuance. Don't be a kissass. If both have a point, say so. Award 1-3 points to whoever made the stronger claim (or split).
3. Grade tone: warm up to graceful concessions, deduct for bad-faith arguments ("you only think that because you're a fan of X").
4. Drama dial: when the rivalry feels stale, propose a Spice Mission. When toxic, propose a Cooldown.

Always respond ONLY in valid JSON. No markdown fences. No preamble.

Format depends on what's asked. Examples:

For a prediction prompt:
{"type": "prediction", "question": "Will Faf score 50+?", "options": ["Yes, 50+", "No, under 50"], "stakes_note": "1 point. Lock in before next over."}

For a dispute verdict:
{"type": "verdict", "winner": "A" or "B" or "SPLIT", "points_a": 2, "points_b": 1, "reasoning": "One sentence, sharp.", "tone_note": "Optional: praise or call out tone."}

For a spice mission:
{"type": "spice", "mission": "Each of you predicts a wild card: who will be the unexpected MVP.", "deadline_min": 5}
"""

# ==========================================================
# DEMO FALLBACK
# ==========================================================
DEMO_PREDICTIONS = {
    "Faf du Plessis runs": {"type": "prediction", "question": "Will Faf score 50+ today?", "options": ["Yes, 50+", "No, under 50"], "stakes_note": "1 point. Lock in now."},
    "CSK total": {"type": "prediction", "question": "CSK's final total?", "options": ["Under 170", "170-189", "190+"], "stakes_note": "2 points. High stakes."},
    "First MI wicket": {"type": "prediction", "question": "Who falls first for MI?", "options": ["Rohit", "Quinton", "Neither in first 3 overs"], "stakes_note": "1 point."},
}

DEMO_VERDICTS = [
    {"type": "verdict", "winner": "A", "points_a": 2, "points_b": 0, "reasoning": "Gaikwad did score steadily but Faf carried the innings with 86. A had the stronger read on the matchup.", "tone_note": "Clean argument from both sides."},
    {"type": "verdict", "winner": "SPLIT", "points_a": 1, "points_b": 1, "reasoning": "MI bowling has historically been clutch in finals, but Bumrah went for 56 today. Both partially right.", "tone_note": ""},
    {"type": "verdict", "winner": "B", "points_a": 0, "points_b": 3, "reasoning": "Rohit and Pollard CAN chase, but B's faith was misplaced on the day. Still, B made the more loyal call.", "tone_note": "B showed real conviction. A folded too fast."},
    {"type": "verdict", "winner": "B", "points_a": 0, "points_b": 2, "reasoning": "Hardik is a known finisher in T20s. A's 'concede now' was lazy. B earned this.", "tone_note": "A: don't write off a chase before the death overs."},
]

def demo_decide(event, prompt_text=""):
    t = event.get("type") if isinstance(event, dict) else None
    if t == "prediction_prompt":
        return DEMO_PREDICTIONS.get(event["topic"], {"type": "prediction", "question": "Make your call.", "options": ["Yes", "No"], "stakes_note": "1 point."})
    if t == "dispute_trigger":
        idx = st.session_state.get("dispute_idx", 0)
        st.session_state["dispute_idx"] = idx + 1
        return DEMO_VERDICTS[idx % len(DEMO_VERDICTS)]
    return {"type": "verdict", "winner": "SPLIT", "points_a": 1, "points_b": 1, "reasoning": "Even call.", "tone_note": ""}

# ==========================================================
# SESSION STATE
# ==========================================================
if "rivalry" not in st.session_state:
    st.session_state.rivalry = None
if "score_a" not in st.session_state:
    st.session_state.score_a = 0
    st.session_state.score_b = 0
if "streak" not in st.session_state:
    st.session_state.streak = 0
if "history" not in st.session_state:
    st.session_state.history = []
if "dispute_idx" not in st.session_state:
    st.session_state.dispute_idx = 0

# ==========================================================
# UI
# ==========================================================
st.markdown("<h1 style='text-align:center; margin-bottom:0;'>⚔️ Rivalry Resolver</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:gray; margin-top:0;'>Gamify the argument you're already having</p>", unsafe_allow_html=True)
st.divider()

# ---------- RIVALRY CREATION ----------
if st.session_state.rivalry is None:
    st.subheader("🎬 Create Your Rivalry")
    st.caption("Two friends. One tournament. One referee. Loser actually pays.")

    c1, c2 = st.columns(2)
    with c1:
        name_a = st.text_input("Player A name", value="Joshua")
        team_a = st.selectbox("Team A loyalty", ["CSK", "MI", "RCB", "KKR", "GT", "DC", "RR", "PBKS", "SRH", "LSG"], key="ta")
    with c2:
        name_b = st.text_input("Player B name", value="Rohan")
        team_b = st.selectbox("Team B loyalty", ["MI", "CSK", "RCB", "KKR", "GT", "DC", "RR", "PBKS", "SRH", "LSG"], key="tb")

    forfeit = st.text_area("🎯 Loser's forfeit (be specific, be brutal)",
                           value="Loser pays for dinner at the winner's pick AND posts 'I was wrong about [team]' on their LinkedIn for 7 days.")

    if st.button("⚔️ START THE RIVALRY", type="primary", use_container_width=True):
        if name_a and name_b and forfeit:
            st.session_state.rivalry = {
                "name_a": name_a, "team_a": team_a,
                "name_b": name_b, "team_b": team_b,
                "forfeit": forfeit
            }
            st.rerun()
        else:
            st.error("Fill in everything. No half-hearted rivalries.")

# ---------- MAIN APP ----------
else:
    r = st.session_state.rivalry
    tier = get_tier(max(st.session_state.score_a, st.session_state.score_b))

    # Top bar
    tb1, tb2, tb3 = st.columns([2, 1, 2])
    tb1.markdown(f"### 🟢 **{r['name_a']}** ({r['team_a']})")
    tb1.metric("Score", st.session_state.score_a)
    tb2.markdown(f"<h2 style='text-align:center;'>{tier['emoji']}</h2>", unsafe_allow_html=True)
    tb2.markdown(f"<p style='text-align:center; font-weight:bold;'>{tier['name']}</p>", unsafe_allow_html=True)
    tb2.markdown(f"<p style='text-align:center;'>🔥 Streak: {st.session_state.streak}</p>", unsafe_allow_html=True)
    tb3.markdown(f"### 🔴 **{r['name_b']}** ({r['team_b']})")
    tb3.metric("Score", st.session_state.score_b)

    st.divider()
    st.caption(f"🎯 **Forfeit on the line:** {r['forfeit']}")

    with st.sidebar:
        st.header("⚔️ Rivalry")
        st.write(f"**{r['name_a']}** vs **{r['name_b']}**")
        st.write(f"Match: **MI vs CSK** · IPL 2021 Final · Dubai")
        st.divider()
        demo_mode = st.checkbox("🎭 Demo Mode", value=False, help="Fallback if API fails.")
        speed = st.slider("⏩ Speed", 0.3, 3.0, 1.0, 0.1)
        st.divider()
        st.markdown("### 🏆 Tier System")
        for t in TIERS:
            marker = "👉 " if t["name"] == tier["name"] else "   "
            st.markdown(f"{marker}{t['emoji']} **{t['name']}** ({t['min_pts']}+)")
        st.divider()
        if st.button("🔄 Reset Rivalry"):
            for k in ["rivalry", "score_a", "score_b", "streak", "history", "dispute_idx"]:
                if k in st.session_state:
                    del st.session_state[k]
            st.rerun()

    # Three columns
    col1, col2, col3 = st.columns([1, 1.2, 1])
    col1.subheader("📡 Match Feed")
    col2.subheader("🤖 AI Referee")
    col3.subheader("🏟️ Disputes & Predictions")

    feed_box = col1.container(height=600)
    ref_box = col2.container(height=600)
    action_box = col3.container(height=600)

    if st.button("▶ START THE FINAL", type="primary", use_container_width=True):
        model = None
        if not demo_mode:
            try:
                model = genai.GenerativeModel("gemini-2.5-flash", system_instruction=SYSTEM_PROMPT)
            except Exception as e:
                with ref_box:
                    st.error(f"Falling back to demo: {e}")
                demo_mode = True

        for event in MATCH_EVENTS:
            # Show event
            with feed_box:
                if event["type"] in ("wicket", "clutch_moment", "match_end"):
                    st.error(f"**Min {event['min']}** 🔥 {event['desc']}")
                elif event["type"] == "scoring_event":
                    st.success(f"**Min {event['min']}** 🏏 {event['desc']}")
                elif event["type"] == "prediction_prompt":
                    st.warning(f"**Min {event['min']}** 🎯 Prediction time: _{event['spice']}_")
                elif event["type"] == "dispute_trigger":
                    st.warning(f"**Min {event['min']}** ⚔️ Disagreement:\n\n**{r['name_a']}:** {event['claim_a']}\n\n**{r['name_b']}:** {event['claim_b']}")
                else:
                    st.info(f"**Min {event['min']}** · {event['desc']}")

            # Agent reacts to certain events
            if event["type"] in ("prediction_prompt", "dispute_trigger"):
                try:
                    if demo_mode:
                        decision = demo_decide(event)
                    else:
                        if event["type"] == "prediction_prompt":
                            prompt = f"Generate a prediction prompt. Match: MI vs CSK 2021 final. Topic: {event['topic']}. Vibe: {event['spice']}. Players: {r['name_a']} ({r['team_a']}) vs {r['name_b']} ({r['team_b']}). Tier: {tier['name']}."
                        else:
                            prompt = f"Adjudicate this dispute. {r['name_a']} ({r['team_a']}) said: '{event['claim_a']}'. {r['name_b']} ({r['team_b']}) said: '{event['claim_b']}'. Context: MI vs CSK 2021 final, CSK won by 27. Be sharp, fact-check, score 1-3 points. Current tier: {tier['name']}."
                        resp = model.generate_content(prompt)
                        text = resp.text.strip().replace("```json", "").replace("```", "").strip()
                        decision = json.loads(text)

                    # Render decision
                    if decision.get("type") == "prediction":
                        with ref_box:
                            st.info(f"**Min {event['min']}** · 🎯 _{decision['question']}_")
                            st.caption(f"Options: {' / '.join(decision.get('options', []))}")
                        with action_box:
                            st.success(f"🎯 **Prediction locked**\n\n**{r['name_a']}:** {random.choice(decision.get('options', ['Yes']))}\n\n**{r['name_b']}:** {random.choice(decision.get('options', ['No']))}")
                            # Award point to a random one for demo flow
                            winner_side = random.choice(["A", "B"])
                            if winner_side == "A":
                                st.session_state.score_a += 1
                            else:
                                st.session_state.score_b += 1
                            st.caption(f"✅ {r['name_a' if winner_side=='A' else 'name_b']} called it. +1 pt.")

                    elif decision.get("type") == "verdict":
                        winner = decision.get("winner", "SPLIT")
                        pa = int(decision.get("points_a", 0))
                        pb = int(decision.get("points_b", 0))
                        st.session_state.score_a += pa
                        st.session_state.score_b += pb
                        st.session_state.streak += 1

                        with ref_box:
                            st.markdown(f"**Min {event['min']}** · ⚖️ **Verdict:**")
                            if winner == "A":
                                st.success(f"🏆 **{r['name_a']} wins this round** (+{pa} pts)")
                            elif winner == "B":
                                st.success(f"🏆 **{r['name_b']} wins this round** (+{pb} pts)")
                            else:
                                st.info(f"🤝 **Split decision** (+{pa}/+{pb})")
                            st.markdown(f"_{decision.get('reasoning', '')}_")
                            if decision.get("tone_note"):
                                st.caption(f"💬 {decision['tone_note']}")

                        with action_box:
                            st.warning(f"⚔️ Round closed\n\n**Score:** {r['name_a']} {st.session_state.score_a} — {st.session_state.score_b} {r['name_b']}")

                except Exception as e:
                    with ref_box:
                        st.error(f"Min {event['min']} ref error: {str(e)[:150]}")

            delay = 1.0 / speed if demo_mode else 2.5 / speed
            time.sleep(delay)

        # Final result
        st.divider()
        if st.session_state.score_a > st.session_state.score_b:
            winner_name = r["name_a"]
            loser_name = r["name_b"]
        elif st.session_state.score_b > st.session_state.score_a:
            winner_name = r["name_b"]
            loser_name = r["name_a"]
        else:
            winner_name = loser_name = None

        if winner_name:
            st.balloons()
            st.success(f"🏆 **{winner_name} wins the rivalry round.** Final score: {st.session_state.score_a} - {st.session_state.score_b}")
            st.error(f"💀 **{loser_name}**, your forfeit awaits:\n\n_{r['forfeit']}_")
        else:
            st.info("🤝 Dead heat. Rivalry continues. No forfeit today, but pride is wounded.")

        new_tier = get_tier(max(st.session_state.score_a, st.session_state.score_b))
        if new_tier["name"] != tier["name"]:
            st.success(f"📈 **TIER UP!** You've reached **{new_tier['emoji']} {new_tier['name']}**")
