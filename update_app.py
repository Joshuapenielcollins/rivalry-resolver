import re

with open("app.py", "r") as f:
    content = f.read()

replacement = """# ==========================================================
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
if "event_idx" not in st.session_state:
    st.session_state.event_idx = 0
if "match_started" not in st.session_state:
    st.session_state.match_started = False
if "feed_events" not in st.session_state:
    st.session_state.feed_events = []
if "pending_prediction" not in st.session_state:
    st.session_state.pending_prediction = None
if "referee_messages" not in st.session_state:
    st.session_state.referee_messages = []
if "action_messages" not in st.session_state:
    st.session_state.action_messages = []

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
        st.divider()
        st.markdown("### 🏆 Tier System")
        for t in TIERS:
            marker = "👉 " if t["name"] == tier["name"] else "   "
            st.markdown(f"{marker}{t['emoji']} **{t['name']}** ({t['min_pts']}+)")
        st.divider()
        if st.button("🔄 Reset Rivalry"):
            for k in ["rivalry", "score_a", "score_b", "streak", "history", "dispute_idx", "event_idx", "match_started", "feed_events", "pending_prediction", "referee_messages", "action_messages"]:
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

    # Render History
    with feed_box:
        for event in st.session_state.feed_events:
            if event["type"] in ("wicket", "clutch_moment", "match_end"):
                st.error(f"**Min {event['min']}** 🔥 {event['desc']}")
            elif event["type"] == "scoring_event":
                st.success(f"**Min {event['min']}** 🏏 {event['desc']}")
            elif event["type"] == "prediction_prompt":
                st.warning(f"**Min {event['min']}** 🎯 Prediction time: _{event['spice']}_")
            elif event["type"] == "dispute_trigger":
                st.warning(f"**Min {event['min']}** ⚔️ Disagreement:\\n\\n**{r['name_a']}:** {event['claim_a']}\\n\\n**{r['name_b']}:** {event['claim_b']}")
            else:
                st.info(f"**Min {event['min']}** · {event['desc']}")
                
    with ref_box:
        for msg in st.session_state.referee_messages:
            st.markdown(msg, unsafe_allow_html=True)
            st.divider()
            
    with action_box:
        for msg in st.session_state.action_messages:
            st.markdown(msg, unsafe_allow_html=True)
            st.divider()

    if not st.session_state.match_started:
        if st.button("▶ START THE FINAL", type="primary", use_container_width=True):
            st.session_state.match_started = True
            st.rerun()
    else:
        # Check if match is over
        if st.session_state.event_idx >= len(MATCH_EVENTS) and not st.session_state.pending_prediction:
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
                st.error(f"💀 **{loser_name}**, your forfeit awaits:\\n\\n_{r['forfeit']}_")
            else:
                st.info("🤝 Dead heat. Rivalry continues. No forfeit today, but pride is wounded.")

            new_tier = get_tier(max(st.session_state.score_a, st.session_state.score_b))
            if new_tier["name"] != tier["name"]:
                st.success(f"📈 **TIER UP!** You've reached **{new_tier['emoji']} {new_tier['name']}**")
                
        elif st.session_state.pending_prediction:
            # We are waiting for users to make a choice
            decision = st.session_state.pending_prediction['decision']
            event = st.session_state.pending_prediction['event']
            opts = decision.get('options', ["Yes", "No"])
            
            with action_box:
                st.info("Make your choices below:")
                
                if demo_mode:
                    st.write("Demo Mode active: Auto-selecting...")
                    if st.button("Resolve Prediction"):
                        choice_a = random.choice(opts)
                        choice_b = random.choice(opts)
                        
                        winner_side = random.choice(["A", "B"])
                        if winner_side == "A":
                            st.session_state.score_a += 1
                        else:
                            st.session_state.score_b += 1
                            
                        res_msg = f"🎯 **Prediction locked**<br><br>**{r['name_a']}:** {choice_a}<br>**{r['name_b']}:** {choice_b}<br><br>✅ {r['name_a' if winner_side=='A' else 'name_b']} called it. +1 pt."
                        st.session_state.action_messages.append(res_msg)
                        
                        st.session_state.pending_prediction = None
                        st.session_state.event_idx += 1
                        st.rerun()
                else:
                    with st.form("prediction_form"):
                        choice_a = st.radio(f"{r['name_a']}'s call:", opts, key="choice_a")
                        choice_b = st.radio(f"{r['name_b']}'s call:", opts, key="choice_b")
                        submitted = st.form_submit_button("Lock It In 🔒")
                        
                        if submitted:
                            # For simplicity we randomly decide who was actually correct in reality
                            winner_side = random.choice(["A", "B", "NEITHER"])
                            
                            res_msg = f"🎯 **Prediction locked**<br><br>**{r['name_a']}:** {choice_a}<br>**{r['name_b']}:** {choice_b}<br><br>"
                            if winner_side == "A":
                                st.session_state.score_a += 1
                                res_msg += f"✅ {r['name_a']} was right. +1 pt."
                            elif winner_side == "B":
                                st.session_state.score_b += 1
                                res_msg += f"✅ {r['name_b']} was right. +1 pt."
                            else:
                                res_msg += "❌ Both missed it."
                                
                            st.session_state.action_messages.append(res_msg)
                            st.session_state.pending_prediction = None
                            st.session_state.event_idx += 1
                            st.rerun()
                            
        else:
            # Match is ongoing, ready for next event
            if st.button("Next Event ⏩", type="primary", use_container_width=True):
                model = None
                if not demo_mode:
                    try:
                        model = genai.GenerativeModel("gemini-2.5-flash", system_instruction=SYSTEM_PROMPT)
                    except Exception as e:
                        demo_mode = True

                event = MATCH_EVENTS[st.session_state.event_idx]
                st.session_state.feed_events.append(event)
                
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

                        # Handle decision
                        if decision.get("type") == "prediction":
                            ref_msg = f"**Min {event['min']}** · 🎯 _{decision['question']}_<br>Options: {' / '.join(decision.get('options', []))}"
                            st.session_state.referee_messages.append(ref_msg)
                            
                            st.session_state.pending_prediction = {
                                "decision": decision,
                                "event": event
                            }
                            st.rerun() # Will display form
                            
                        elif decision.get("type") == "verdict":
                            winner = decision.get("winner", "SPLIT")
                            pa = int(decision.get("points_a", 0))
                            pb = int(decision.get("points_b", 0))
                            st.session_state.score_a += pa
                            st.session_state.score_b += pb
                            st.session_state.streak += 1

                            ref_msg = f"**Min {event['min']}** · ⚖️ **Verdict:**<br>"
                            if winner == "A":
                                ref_msg += f"🏆 **{r['name_a']} wins this round** (+{pa} pts)<br>"
                            elif winner == "B":
                                ref_msg += f"🏆 **{r['name_b']} wins this round** (+{pb} pts)<br>"
                            else:
                                ref_msg += f"🤝 **Split decision** (+{pa}/+{pb})<br>"
                            ref_msg += f"_{decision.get('reasoning', '')}_<br>"
                            if decision.get("tone_note"):
                                ref_msg += f"💬 {decision['tone_note']}"
                                
                            st.session_state.referee_messages.append(ref_msg)
                            
                            act_msg = f"⚔️ Round closed<br><br>**Score:** {r['name_a']} {st.session_state.score_a} — {st.session_state.score_b} {r['name_b']}"
                            st.session_state.action_messages.append(act_msg)
                            
                            st.session_state.event_idx += 1
                            st.rerun()

                    except Exception as e:
                        st.session_state.referee_messages.append(f"Min {event['min']} ref error: {str(e)[:150]}")
                        st.session_state.event_idx += 1
                        st.rerun()
                else:
                    st.session_state.event_idx += 1
                    st.rerun()
"""

new_content = content[:content.find("# ==========================================================\n# SESSION STATE")] + replacement
with open("app.py", "w") as f:
    f.write(new_content)
