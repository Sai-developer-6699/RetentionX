import os
import random
import time
import json
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Streamlit App Config
st.set_page_config(
    page_title="RetentionX | Autonomous CLM & Retention Agent",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Products and Customer imports
from data.customer import personas
from data.products import products
from src.agents import behavior_analysis_agent, decision_agent, load_config
from src.simulation import simulate_user_behavior, evaluate_agent_action
from src.memory_store import StrategyMemory

# ─────────────────────────────────────────────
# PREMIUM DARK GLASSMORPHIC DESIGN SYSTEM
# ─────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    
    /* App background & typography */
    .stApp {
        background: radial-gradient(circle at 15% 15%, #111827 0%, #080c14 100%);
        color: #f1f5f9;
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Glassmorphic Bento Cards */
    .premium-card {
        background: rgba(17, 24, 39, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 1.4rem;
        margin-bottom: 1.1rem;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .premium-card:hover {
        transform: translateY(-2px);
        border-color: rgba(99, 102, 241, 0.35);
        box-shadow: 0 14px 40px rgba(99, 102, 241, 0.12);
    }
    
    /* Live Log Card styles */
    .log-card {
        border-left: 4px solid #6366f1;
    }
    .log-card-success {
        border-left: 4px solid #10b981;
        background: rgba(16, 185, 129, 0.08);
    }
    .log-card-failed {
        border-left: 4px solid #ef4444;
        background: rgba(239, 68, 68, 0.08);
    }
    .log-card-neutral {
        border-left: 4px solid #64748b;
        background: rgba(100, 116, 139, 0.08);
    }
    
    /* Custom Pill Badges */
    .channel-badge {
        display: inline-flex;
        align-items: center;
        padding: 0.2rem 0.65rem;
        border-radius: 9999px;
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .badge-sms {
        background: rgba(168, 85, 247, 0.18);
        color: #d8b4fe;
        border: 1px solid rgba(168, 85, 247, 0.35);
    }
    .badge-email {
        background: rgba(59, 130, 246, 0.18);
        color: #93c5fd;
        border: 1px solid rgba(59, 130, 246, 0.35);
    }
    .badge-inapp {
        background: rgba(16, 185, 129, 0.18);
        color: #6ee7b7;
        border: 1px solid rgba(16, 185, 129, 0.35);
    }
    .badge-push {
        background: rgba(245, 158, 11, 0.18);
        color: #fde68a;
        border: 1px solid rgba(245, 158, 11, 0.35);
    }
    .badge-nothing {
        background: rgba(100, 116, 139, 0.18);
        color: #cbd5e1;
        border: 1px solid rgba(100, 116, 139, 0.35);
    }
    
    /* Metric Stat Box */
    .stat-container {
        background: rgba(17, 24, 39, 0.65);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 1.1rem;
        text-align: center;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
    }
    .stat-value {
        font-size: 1.85rem;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: -0.02em;
    }
    .stat-label {
        font-size: 0.72rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-top: 0.25rem;
    }
    .stat-sub {
        font-size: 0.78rem;
        color: #38bdf8;
        font-weight: 600;
        margin-top: 0.2rem;
    }
    
    /* Header Gradient Text */
    .logo-text {
        font-size: 2.1rem;
        font-weight: 800;
        background: linear-gradient(135deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.03em;
    }
    
    /* Streamlit Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: rgba(17, 24, 39, 0.6);
        padding: 6px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }
    .stTabs [data-baseweb="tab"] {
        height: 44px;
        border-radius: 8px;
        color: #94a3b8;
        font-weight: 600;
        padding: 0 16px;
        border: none;
        background-color: transparent;
    }
    .stTabs [aria-selected="true"] {
        background-color: rgba(99, 102, 241, 0.25) !important;
        color: #ffffff !important;
        border: 1px solid rgba(99, 102, 241, 0.4) !important;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SESSION STATE INITIALIZATION
# ─────────────────────────────────────────────
if "customers" not in st.session_state:
    st.session_state.customers = personas

if "memory" not in st.session_state:
    st.session_state.memory = StrategyMemory()

if "story_log" not in st.session_state:
    st.session_state.story_log = []

if "day_count" not in st.session_state:
    st.session_state.day_count = 0

if "pending_approvals" not in st.session_state:
    st.session_state.pending_approvals = []

if "price_history" not in st.session_state:
    st.session_state.price_history = {
        "Pro Subscription": [29.0],
        "Enterprise Plan": [99.0],
        "API Add-on": [15.0],
        "Pro + API Bundle": [39.0]
    }

if "base_prices" not in st.session_state:
    st.session_state.base_prices = {
        "P001": 29.0,
        "P002": 99.0,
        "P003": 15.0,
        "P004": 39.0
    }

def save_state_to_json(llm_provider="gemini"):
    state = {
        "day_count": st.session_state.day_count,
        "price_history": st.session_state.price_history,
        "customers": st.session_state.customers,
        "memory_registry": st.session_state.memory.registry,
        "story_log": st.session_state.story_log,
        "llm_provider": llm_provider,
        "pending_approvals": st.session_state.get("pending_approvals", [])
    }
    frontend_dir = os.path.join(os.getcwd(), "frontend", "public")
    if not os.path.exists(frontend_dir):
        os.makedirs(frontend_dir, exist_ok=True)
    state_file = os.path.join(frontend_dir, "state.json")
    try:
        with open(state_file, "w") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        pass

if "initial_saved" not in st.session_state:
    save_state_to_json("gemini")
    st.session_state.initial_saved = True

# ─────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────
def get_action_details(action):
    details = {
        "SEND_SMS_DISCOUNT": ("💬 SMS Promo", "badge-sms"),
        "SEND_SMS_TUTORIAL": ("💬 SMS Guide", "badge-sms"),
        "SEND_EMAIL_DISCOUNT": ("✉️ Email Promo", "badge-email"),
        "SEND_EMAIL_TUTORIAL": ("✉️ Email Guide", "badge-email"),
        "SEND_IN_APP_MESSAGE": ("💻 In-App Nudge", "badge-inapp"),
        "SEND_PUSH_NOTIFICATION": ("🔔 Push Alert", "badge-push"),
        "CUSTOM_BUNDLE": ("🎁 Value Bundle", "badge-inapp"),
        "DO_NOTHING": ("😴 Inaction", "badge-nothing")
    }
    return details.get(action, ("⚡ Action", "badge-nothing"))

def get_message_content(action, customer_name):
    if action == "SEND_SMS_DISCOUNT":
        return f"SMS: 'Hey {customer_name}! Don't lose access. Apply code SAVEMORE30 for 30% off! Reply STOP to opt out.'"
    elif action == "SEND_SMS_TUTORIAL":
        return f"SMS: 'Hi {customer_name}, check our setup guides: bit.ly/pro-onboarding. Reply STOP to opt out.'"
    elif action == "SEND_EMAIL_DISCOUNT":
        return f"Email: 'Subject: Personal discount on your plan | Hi {customer_name}, here is an exclusive 25% discount valid for 3 days...'"
    elif action == "SEND_EMAIL_TUTORIAL":
        return f"Email: 'Subject: Developer setup & integration guide | Hello {customer_name}, here is a tutorial for webhook setups...'"
    elif action == "SEND_IN_APP_MESSAGE":
        return f"In-App: 'Need assistance setting up your workspace? Chat with our experts!'"
    elif action == "SEND_PUSH_NOTIFICATION":
        return f"Push: 'Alert: Custom API limits warning - Tap to optimize your endpoints.'"
    elif action == "CUSTOM_BUNDLE":
        return f"Bundle: 'Offer: Get 50,000 extra queries added to your plan for $5/mo!'"
    return "No message dispatched."

def get_channel_metrics():
    metrics = {
        "SMS": {"sent": 0, "success": 0},
        "Email": {"sent": 0, "success": 0},
        "In-App": {"sent": 0, "success": 0},
        "Push": {"sent": 0, "success": 0}
    }
    registry = st.session_state.memory.registry
    for key, strategies in registry.items():
        for action, stats in strategies.items():
            successes = stats.get("SUCCESS", 0)
            failures = stats.get("FAILED", 0)
            total = successes + failures
            if "SMS" in action:
                metrics["SMS"]["sent"] += total
                metrics["SMS"]["success"] += successes
            elif "EMAIL" in action:
                metrics["Email"]["sent"] += total
                metrics["Email"]["success"] += successes
            elif "IN_APP" in action:
                metrics["In-App"]["sent"] += total
                metrics["In-App"]["success"] += successes
            elif "PUSH" in action:
                metrics["Push"]["sent"] += total
                metrics["Push"]["success"] += successes
    return metrics

# ─────────────────────────────────────────────
# SIDEBAR CONTROLS
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("<div style='text-align: center; margin-bottom: 1.2rem;'><span class='logo-text'>RetentionX</span><br><small style='color: #94a3b8; font-weight: 500;'>Autonomous CLM & Retention Agent</small></div>", unsafe_allow_html=True)
    st.markdown("---")
    
    st.metric("📅 Current Simulation Day", f"Day {st.session_state.day_count}")
    
    st.markdown("### ⚙️ Engine Settings")
    llm_provider = st.selectbox(
        "Active LLM Provider", 
        ["gemini", "openai"], 
        index=0, 
        help="Primary LLM driving the 4-agent orchestration mesh (Google Gemini 2.5 Flash vs OpenAI GPT-4o-mini)."
    )
    
    auto_pricing = st.toggle("Dynamic SaaS Price Fluctuation", value=True, help="Simulate random market pricing changes (+-4%) daily to test price elasticity.")
    
    if not auto_pricing:
        st.markdown("##### Manual Base Prices")
        st.session_state.base_prices["P001"] = st.slider("Pro Subscription ($)", 10.0, 50.0, float(st.session_state.base_prices["P001"]), 1.0)
        st.session_state.base_prices["P002"] = st.slider("Enterprise Plan ($)", 50.0, 200.0, float(st.session_state.base_prices["P002"]), 5.0)
        st.session_state.base_prices["P003"] = st.slider("API Add-on ($)", 5.0, 30.0, float(st.session_state.base_prices["P003"]), 1.0)
    
    st.markdown("---")
    st.markdown("### 🌐 Dual Workspace Info")
    st.info("💡 **Client Portal App** is available in `frontend/`.\nRun `npm run dev` in that folder to view the customer's live perspective at `http://localhost:5173`.")
    
    if st.session_state.story_log:
        story_df = pd.DataFrame([{
            "Day": s["day"],
            "Customer": s["customer"]["name"],
            "Action": s["action"],
            "Impact": s["impact"],
            "Thought": s["thought"]
        } for s in st.session_state.story_log])
        st.download_button(
            label="📥 Export Retention Stories (CSV)",
            data=story_df.to_csv(index=False),
            file_name="retention_stories.csv",
            mime="text/csv"
        )

# ─────────────────────────────────────────────
# HEADER SUMMARY BAR
# ─────────────────────────────────────────────
st.markdown("""
<div style='margin-bottom: 1.5rem;'>
    <div style='display: flex; justify-content: space-between; align-items: flex-end;'>
        <div>
            <h1 style='margin: 0; font-size: 2.2rem; font-weight: 800; color: #ffffff;'>⚡ Autonomous CLM Command Center</h1>
            <p style='margin: 0.3rem 0 0 0; color: #94a3b8; font-size: 1.05rem;'>Real-time AI agent loop orchestrating customer retention, dynamic pricing, and human compliance auditing.</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# TABBED INFORMATION ARCHITECTURE
# ─────────────────────────────────────────────
tab_sim, tab_customers, tab_analytics, tab_memory = st.tabs([
    "🕹️ Simulation & Approvals",
    "👥 Customer 360",
    "📊 Market & Channel Analytics",
    "🧠 Agent Brain & Memory"
])

# ═════════════════════════════════════════════
# TAB 1: SIMULATION & HITL APPROVAL DESK
# ═════════════════════════════════════════════
with tab_sim:
    col_ctrl1, col_ctrl2 = st.columns([2, 1])
    
    with col_ctrl1:
        st.markdown("### ⏯️ Loop Control")
        st.write("Advance the customer lifecycle by 1 day. The multi-agent mesh will inspect behavior signals, compute pricing elasticity, draft personalized interventions, and pass them to the audit queue.")
    
    with col_ctrl2:
        if st.session_state.pending_approvals:
            st.warning(f"⚠️ **{len(st.session_state.pending_approvals)} Campaign(s) Awaiting Review**")
            st.button("▶️ Advance Next Day (Blocked)", disabled=True)
        else:
            if st.button("▶️ **Simulate Next Day Outreach**", type="primary"):
                st.session_state.day_count += 1
                daily_stories = []
                
                # 1. Update prices if auto pricing is toggled
                if auto_pricing:
                    for prod_id, prod_data in products.items():
                        prod_name = prod_data["name"]
                        last_price = st.session_state.price_history[prod_name][-1]
                        change = random.uniform(-0.04, 0.04)
                        new_price = round(max(5.0, last_price * (1 + change)), 2)
                        st.session_state.price_history[prod_name].append(new_price)
                        st.session_state.base_prices[prod_id] = new_price
                else:
                    for prod_id, prod_data in products.items():
                        prod_name = prod_data["name"]
                        st.session_state.price_history[prod_name].append(st.session_state.base_prices[prod_id])

                st.session_state.memory.day_count = st.session_state.day_count

                with st.spinner("🧠 Agent mesh is observing vibes, checking memory, and drafting retention campaigns..."):
                    for customer in st.session_state.customers:
                        if customer.get("status") == "Churned":
                            continue
                        
                        prod_id = customer.get("product_id", "P001")
                        base_price = st.session_state.base_prices[prod_id]
                        
                        behavior_log = simulate_user_behavior(customer)
                        _ = behavior_analysis_agent(customer)
                        
                        decision = decision_agent(customer, st.session_state.memory, llm_provider=llm_provider)
                        action = decision.get("action")
                        thought = decision.get("thought", "No reasoning provided.")
                        content = decision.get("content", "No message.")
                        
                        if action == "DO_NOTHING":
                            impact = evaluate_agent_action(customer, action, st.session_state.memory, content=content)
                            daily_stories.append({
                                "day": st.session_state.day_count,
                                "customer": customer.copy(),
                                "base_price": base_price,
                                "thought": thought,
                                "action": action,
                                "impact": impact,
                                "behavior": behavior_log
                            })
                        else:
                            st.session_state.pending_approvals.append({
                                "customer_id": customer["id"],
                                "customer_name": customer["name"],
                                "action": action,
                                "content": content,
                                "thought": thought,
                                "base_price": base_price,
                                "behavior_log": behavior_log
                            })
                
                st.session_state.story_log.extend(daily_stories)
                save_state_to_json(llm_provider)
                st.success(f"Day {st.session_state.day_count} initialized! Review proposed campaigns below.")
                st.rerun()

    # ─────────────────────────────────────────
    # HUMAN-IN-THE-LOOP (HITL) AUDIT DESK
    # ─────────────────────────────────────────
    if st.session_state.pending_approvals:
        st.markdown("---")
        st.markdown("### 📥 Human-in-the-Loop Audit Desk")
        st.info("The agent generated the following personalized campaigns. You may review the reasoning, modify the proposed copy, and Approve or Reject before delivery.")
        
        pending_list = list(st.session_state.pending_approvals)
        for idx, approval in enumerate(pending_list):
            cust_id = approval["customer_id"]
            cust_name = approval["customer_name"]
            action = approval["action"]
            thought = approval["thought"]
            draft_copy = approval["content"]
            
            customer = next((c for c in st.session_state.customers if c["id"] == cust_id), None)
            if not customer:
                continue
                
            with st.container(border=True):
                col_ap1, col_ap2 = st.columns([3, 1])
                with col_ap1:
                    channel_name, badge_class = get_action_details(action)
                    st.markdown(f"<span class='channel-badge {badge_class}'>{channel_name}</span> &nbsp; **{cust_name}** ({customer.get('segment')})", unsafe_allow_html=True)
                    st.markdown(f"**🧠 Strategic Thought:** `{thought}`")
                    edited_copy = st.text_area(f"Edit Message Copy for {cust_name}", value=draft_copy, key=f"edit_copy_{cust_id}_{idx}", height=90)
                
                with col_ap2:
                    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
                    if st.button("✅ Approve & Dispatch", key=f"approve_{cust_id}_{idx}"):
                        impact = evaluate_agent_action(customer, action, st.session_state.memory, content=edited_copy)
                        st.session_state.story_log.append({
                            "day": st.session_state.day_count,
                            "customer": customer.copy(),
                            "base_price": approval["base_price"],
                            "thought": f"Approved by CSM. Thought: {thought}",
                            "action": action,
                            "impact": impact,
                            "behavior": approval["behavior_log"]
                        })
                        st.session_state.pending_approvals.pop(idx)
                        save_state_to_json(llm_provider)
                        st.rerun()
                        
                    if st.button("❌ Reject Campaign", key=f"reject_{cust_id}_{idx}"):
                        impact = evaluate_agent_action(customer, "DO_NOTHING", st.session_state.memory)
                        st.session_state.story_log.append({
                            "day": st.session_state.day_count,
                            "customer": customer.copy(),
                            "base_price": approval["base_price"],
                            "thought": f"Rejected by CSM. Fallback to DO_NOTHING. Original thought: {thought}",
                            "action": "DO_NOTHING",
                            "impact": impact,
                            "behavior": "Campaign rejected by operator."
                        })
                        st.session_state.pending_approvals.pop(idx)
                        save_state_to_json(llm_provider)
                        st.rerun()

    # ─────────────────────────────────────────
    # LIVE RETENTION NARRATIVE STREAM
    # ─────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 💬 Live Execution Feed (Observe → Decide → Act → Impact)")
    
    if st.session_state.story_log:
        recent_stories = st.session_state.story_log[-6:]
        recent_stories.reverse()
        
        for story in recent_stories:
            cust = story["customer"]
            action = story["action"]
            thought = story["thought"]
            impact = story["impact"]
            day = story["day"]
            behavior = story["behavior"]
            base_p = story["base_price"]
            
            if cust["status"] == "Churned":
                card_style = "log-card-failed"
                status_icon = "💀"
            elif impact > 0:
                card_style = "log-card-success"
                status_icon = "✅"
            elif impact < 0:
                card_style = "log-card-failed"
                status_icon = "⚠️"
            else:
                card_style = "log-card-neutral"
                status_icon = "ℹ️"
                
            channel_name, badge_class = get_action_details(action)
            message_text = get_message_content(action, cust["name"])
            price_multiplier = 0.7 if "DISCOUNT" in action and impact > 0 else 1.0
            actual_price = round(base_p * price_multiplier, 2)
            
            st.markdown(f"""
            <div class="premium-card {card_style}">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <div>
                        <span class="channel-badge {badge_class}">{channel_name}</span>
                        <strong style="font-size: 1.15rem; margin-left: 0.5rem; color: #fff;">{status_icon} {cust['name']}</strong>
                        <span style="color: #94a3b8; font-size: 0.8rem; margin-left: 0.5rem;">Day {day} • {cust['persona']}</span>
                    </div>
                    <div>
                        <span style="color: #38bdf8; font-weight: 700; font-size: 1.1rem;">${actual_price}/mo</span>
                        {f'<span style="text-decoration: line-through; color: #64748b; font-size: 0.85rem; margin-left: 0.3rem;">${base_p}</span>' if price_multiplier < 1.0 else ''}
                    </div>
                </div>
                <div style="font-size: 0.88rem; line-height: 1.5; color: #cbd5e1;">
                    <div style="margin-bottom: 0.25rem;">🔍 <strong>Telemetry Check:</strong> {behavior}</div>
                    <div style="margin-bottom: 0.25rem;">🧠 <strong>Agent Thought:</strong> <i>{thought}</i></div>
                    <div style="margin-bottom: 0.35rem; background: rgba(0,0,0,0.25); padding: 0.5rem; border-radius: 8px;">📱 <strong>Sent Copy:</strong> <code>{message_text}</code></div>
                    <div style="display: flex; justify-content: space-between; margin-top: 0.3rem; font-size: 0.85rem;">
                        <span>Impact: <strong style="color: {'#10b981' if impact > 0 else ('#ef4444' if impact < 0 else '#94a3b8')};">{'🏼' if impact == 0 else ('+' if impact > 0 else '')}{impact} Score</strong></span>
                        <span>Current Score: <strong>{cust['engagement_score']}/100</strong></span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Simulation log is empty. Advance Day 1 above to trigger the autonomous agent loop.")

# ═════════════════════════════════════════════
# TAB 2: CUSTOMER 360 & COHORT DIRECTORY
# ═════════════════════════════════════════════
with tab_customers:
    st.markdown("### 👥 Customer Cohorts Overview")
    
    cols = st.columns(5)
    for idx, customer in enumerate(st.session_state.customers):
        prod_id = customer.get("product_id", "P001")
        prod_name = products[prod_id]["name"]
        
        with cols[idx]:
            is_churned = customer["status"] == "Churned"
            status_style = "border-top: 4px solid #ef4444; background: rgba(239, 68, 68, 0.05);" if is_churned else "border-top: 4px solid #10b981;"
            status_badge = "💀 CHURNED" if is_churned else "✅ ACTIVE"
            
            st.markdown(f"""
            <div class="premium-card" style="{status_style} padding: 1.1rem;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <strong style="color: #fff; font-size: 1.05rem;">{customer['name']}</strong>
                    <span style="font-size: 0.68rem; font-weight: 700; color: {'#ef4444' if is_churned else '#10b981'};">{status_badge}</span>
                </div>
                <div style="font-size: 0.75rem; color: #94a3b8; margin: 0.2rem 0 0.6rem 0;">{customer['persona']}</div>
                <div style="font-size: 0.78rem; display: grid; gap: 0.2rem;">
                    <div>🏷️ <strong>Stage:</strong> {customer['lifecycle_stage']}</div>
                    <div>💼 <strong>Plan:</strong> {prod_name}</div>
                    <div>💬 <strong>SMS Sent:</strong> {customer.get('sms_count', 0)}/2</div>
                    <div>🎁 <strong>Discounts:</strong> {customer.get('discount_count', 0)}/2</div>
                    <div>💵 <strong>CLV:</strong> ${(customer.get('clv', 0.0)):.2f}</div>
                </div>
                <div style="margin-top: 0.8rem;">
                    <div style="display: flex; justify-content: space-between; font-size: 0.75rem; margin-bottom: 0.2rem;">
                        <span>Health</span>
                        <strong>{customer['engagement_score']}/100</strong>
                    </div>
                    <div style="width: 100%; height: 6px; background: rgba(255,255,255,0.08); border-radius: 3px; overflow: hidden;">
                        <div style="width: {customer['engagement_score']}%; height: 100%; background: {'#ef4444' if customer['engagement_score'] < 30 else ('#fbbf24' if customer['engagement_score'] < 70 else '#10b981')};"></div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🔍 Customer Deep Dive Inspector")
    selected_customer_name = st.selectbox("Inspect Customer Profile", [c["name"] for c in st.session_state.customers])
    selected_c = next((c for c in st.session_state.customers if c["name"] == selected_customer_name), None)
    
    if selected_c:
        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1:
            st.markdown("##### Behavioral Sensitivities")
            st.json(selected_c.get("sensitivity", {}))
        with col_c2:
            st.markdown("##### Lifecycle & Segment")
            st.write(f"**Segment:** {selected_c.get('segment')}")
            st.write(f"**Lifecycle Stage:** {selected_c.get('lifecycle_stage')}")
            st.write(f"**Test Group:** {selected_c.get('test_group')}")
            st.write(f"**Days Inactive:** {selected_c.get('time_since_last_event')} days")
        with col_c3:
            st.markdown("##### Telemetry History")
            st.write(selected_c.get("history", []))

# ═════════════════════════════════════════════
# TAB 3: MARKET & CHANNEL ANALYTICS
# ═════════════════════════════════════════════
with tab_analytics:
    # A/B TESTING BASELINE LIFT
    group_a_scores = [c["engagement_score"] for c in st.session_state.customers if c.get("test_group") == "Group A (AI-driven CLM)"]
    group_b_scores = [c["engagement_score"] for c in st.session_state.customers if c.get("test_group") == "Group B (Standard Rules)"]
    avg_a = sum(group_a_scores) / len(group_a_scores) if group_a_scores else 0.0
    avg_b = sum(group_b_scores) / len(group_b_scores) if group_b_scores else 0.0
    ab_lift = ((avg_a - avg_b) / avg_b * 100) if avg_b > 0 else 0.0

    st.markdown("### 🧪 A/B Testing Baseline Performance Lift")
    col_ab1, col_ab2, col_ab3 = st.columns(3)
    with col_ab1:
        st.metric(
            label="Group A: AI-Led OODA Mesh", 
            value=f"{avg_a:.1f}/100", 
            delta=f"{avg_a - avg_b:+.1f} vs Control",
            help="Average engagement score of customers managed by autonomous AI agents."
        )
    with col_ab2:
        st.metric(
            label="Group B: Static Rule Engine", 
            value=f"{avg_b:.1f}/100",
            help="Average engagement score of customers managed by fixed marketing rules."
        )
    with col_ab3:
        st.metric(
            label="AI Retention Performance Lift", 
            value=f"{ab_lift:+.1f}%",
            help="Percentage lift in customer retention achieved by the LLM OODA loop over standard rules."
        )

    st.markdown("---")
    st.markdown("### 📊 Outreach Delivery & Channel Conversion")
    ch_metrics = get_channel_metrics()
    col_sms, col_email, col_inapp, col_push = st.columns(4)
    
    with col_sms:
        sms_sent = ch_metrics["SMS"]["sent"]
        sms_success = ch_metrics["SMS"]["success"]
        sms_rate = (sms_success / sms_sent * 100) if sms_sent > 0 else 0.0
        st.markdown(f"""
        <div class="stat-container">
            <div class="stat-value">💬 {sms_sent}</div>
            <div class="stat-label">SMS Alerts Sent</div>
            <div class="stat-sub">{sms_rate:.1f}% Conversion Rate</div>
        </div>
        """, unsafe_allow_html=True)
    with col_email:
        email_sent = ch_metrics["Email"]["sent"]
        email_success = ch_metrics["Email"]["success"]
        email_rate = (email_success / email_sent * 100) if email_sent > 0 else 0.0
        st.markdown(f"""
        <div class="stat-container">
            <div class="stat-value">✉️ {email_sent}</div>
            <div class="stat-label">Emails Dispatched</div>
            <div class="stat-sub">{email_rate:.1f}% Conversion Rate</div>
        </div>
        """, unsafe_allow_html=True)
    with col_inapp:
        inapp_sent = ch_metrics["In-App"]["sent"]
        inapp_success = ch_metrics["In-App"]["success"]
        inapp_rate = (inapp_success / inapp_sent * 100) if inapp_sent > 0 else 0.0
        st.markdown(f"""
        <div class="stat-container">
            <div class="stat-value">💻 {inapp_sent}</div>
            <div class="stat-label">In-App Modals</div>
            <div class="stat-sub">{inapp_rate:.1f}% Conversion Rate</div>
        </div>
        """, unsafe_allow_html=True)
    with col_push:
        push_sent = ch_metrics["Push"]["sent"]
        push_success = ch_metrics["Push"]["success"]
        push_rate = (push_success / push_sent * 100) if push_sent > 0 else 0.0
        st.markdown(f"""
        <div class="stat-container">
            <div class="stat-value">🔔 {push_sent}</div>
            <div class="stat-label">Push Notifications</div>
            <div class="stat-sub">{push_rate:.1f}% Conversion Rate</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📈 SaaS Product Pricing History")
    df_prices = pd.DataFrame(st.session_state.price_history)
    df_prices.index.name = "Day"
    st.line_chart(df_prices)

# ═════════════════════════════════════════════
# TAB 4: AGENT BRAIN & MEMORY REGISTRY
# ═════════════════════════════════════════════
with tab_memory:
    st.markdown("### 🧠 Multi-Agent Architecture Mesh")
    st.markdown("""
    The retention decision loop executes through a coordinated subagent mesh:
    - **Adoption Analyst (`adoption.py`)**: Detects usage decay and friction points.
    - **Dynamic Pricing Agent (`pricing.py`)**: Protects margins while optimizing retention offers.
    - **Outreach Copywriter (`outreach.py`)**: Crafts tailored multi-channel messaging.
    - **Compliance Auditor (`auditor.py`)**: Enforces fatigue caps, adds opt-out legal disclaimers, and defends against prompt injections.
    """)
    
    st.markdown("---")
    st.markdown("### 📚 Strategy Memory Registry (Learned Patterns)")
    
    if st.session_state.memory.registry:
        for key, strategies in st.session_state.memory.registry.items():
            parts = key.split('_', 1)
            persona_name = parts[1] if len(parts) == 2 else key
            stage = parts[0] if len(parts) == 2 else ""
            
            with st.expander(f"👤 {persona_name} — Stage: {stage}"):
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    st.markdown("**Action Success / Failure Counts:**")
                    for action, stats in strategies.items():
                        s_count = stats.get("SUCCESS", 0)
                        f_count = stats.get("FAILED", 0)
                        status_color = "#10b981" if s_count > f_count else ("#ef4444" if f_count > 0 else "#94a3b8")
                        st.write(f"- `{action}`: **{s_count} Success** / **{f_count} Failed**")
                with col_m2:
                    st.markdown("**Self-Correcting Guardrails:**")
                    forbidden = [action for action, stats in strategies.items() if stats.get("FAILED", 0) >= 1]
                    if forbidden:
                        st.error(f"🚫 Blocked Actions (Never repeated): {', '.join(forbidden)}")
                    else:
                        st.success("✨ No actions blocked yet.")
    else:
        st.info("Strategy registry is currently empty. Run simulation steps to accumulate learned outcomes.")
