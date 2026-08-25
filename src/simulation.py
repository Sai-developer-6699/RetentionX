import time
import random
import streamlit as st
from src.agents import behavior_analysis_agent, decision_agent, load_config
from data.products import products

def run_simulation_step(customer, memory, llm_provider="gemini"):
    # STEP 1: OBSERVE
    analysis = behavior_analysis_agent(customer)

    # STEP 2: DECIDE
    decision = decision_agent(customer, memory, llm_provider)

    # STEP 3: ACT + EVALUATE
    impact = evaluate_outcome(customer, decision["action"], memory, content=decision.get("content"))

    return analysis, decision, impact

def simulate_time_step(customer):
    """Call this every loop to advance 'time' for the user."""
    customer["time_since_last_event"] += 1
    
    # Behavior logic: High engagement = likely event. High 'time_since' = likely churn.
    activity_threshold = customer["engagement_score"] / 100.0
    
    if random.random() < activity_threshold:
        event = random.choice(["Login", "Feature Use", "Search"])
        customer["history"].append(event)
        customer["time_since_last_event"] = 0 # Reset on activity
        return f"User performed: {event}"
    
    return "User was inactive."

def get_message_content(action, customer_name):
    """Generates the actual copy sent to the customer"""
    if action == "SEND_SMS_DISCOUNT":
        return f"Hey {customer_name}! Don't lose your access. Apply code SAVEMORE30 on your next renewal for 30% off!"
    elif action == "SEND_SMS_TUTORIAL":
        return f"Hi {customer_name}, we updated your setup instructions! View our quick guides here: bit.ly/pro-onboarding"
    elif action == "SEND_EMAIL_DISCOUNT":
        return f"Subject: Personal discount on your plan\n\nHi {customer_name},\n\nWe appreciate your subscription. Here is an exclusive 25% discount valid for the next 3 days..."
    elif action == "SEND_EMAIL_TUTORIAL":
        return f"Subject: Developer setup & integration guide\n\nHello {customer_name},\n\nHere is a detailed deep dive tutorial to help you get the most out of your webhooks and API rate limits..."
    elif action == "SEND_IN_APP_MESSAGE":
        return f"Modal Check-in: Need assistance setting up your developer workspace? Chat with our experts!"
    elif action == "SEND_PUSH_NOTIFICATION":
        return f"Alert: Custom API limits warning - Tap to optimize your endpoints."
    elif action == "CUSTOM_BUNDLE":
        return f"Add-on Offer: Get 50,000 extra API queries added to your plan for only $5/mo!"
    return "No message sent."

def evaluate_outcome(customer, action, memory=None, content=None):
    """
    Deterministic environment reaction.
    LLM decides WHAT to do (e.g. outreach channel).
    This function decides WHAT HAPPENS (impact on score, pricing, and CLV).
    """
    impact = 0
    history = customer["history"]
    
    # Initialize missing fields safely
    if "sms_count" not in customer:
        customer["sms_count"] = 0
    if "discount_count" not in customer:
        customer["discount_count"] = 0
    if "action_history" not in customer:
        customer["action_history"] = []
    if "messages" not in customer:
        customer["messages"] = []
    if "clv" not in customer:
        customer["clv"] = 0.0

    # Get Day Count
    day = getattr(memory, "day_count", 0) if memory else 0
    
    # Load config limits
    config = load_config()
    churn_threshold = config.get("churn_score_threshold", 10)

    # Use agent-generated copy if provided, otherwise fall back to templates
    message_content = content if content and content != "No message." else get_message_content(action, customer["name"])

    # ─────────────────────────────
    # ACTION: SEND_SMS_DISCOUNT
    # ─────────────────────────────
    if action == "SEND_SMS_DISCOUNT":
        customer["sms_count"] += 1
        customer["discount_count"] += 1
        msg = f"SMS Discount Sent: '{message_content}'"
        history.append(msg)
        
        if customer["sensitivity"]["discount"] > 0.6:
            if customer["sms_count"] <= 2:
                reaction = "SMS Discount Accepted: User clicked mobile link and applied code"
                impact = +10
            else:
                reaction = "SMS Discount Accepted but Annoyed: Applied code, but complained about text spam"
                impact = +2
        else:
            reaction = "SMS Discount Ignored: User swiped away text message"
            impact = -6
            
        customer["messages"].append({
            "day": day,
            "channel": "SMS",
            "content": message_content,
            "reaction": reaction,
            "impact": impact
        })

    # ─────────────────────────────
    # ACTION: SEND_SMS_TUTORIAL
    # ─────────────────────────────
    elif action == "SEND_SMS_TUTORIAL":
        customer["sms_count"] += 1
        msg = f"SMS Tutorial Sent: '{message_content}'"
        history.append(msg)
        
        if customer["sensitivity"]["content"] > 0.6:
            if customer["sms_count"] <= 2:
                reaction = "SMS Tutorial Link Visited: Watched quick video on mobile"
                impact = +7
            else:
                reaction = "SMS Tutorial Link Ignored: User is fatigued by SMS messages"
                impact = -3
        else:
            reaction = "SMS Tutorial Link Skipped: Message left unread"
            impact = -4
            
        customer["messages"].append({
            "day": day,
            "channel": "SMS",
            "content": message_content,
            "reaction": reaction,
            "impact": impact
        })

    # ─────────────────────────────
    # ACTION: SEND_EMAIL_DISCOUNT
    # ─────────────────────────────
    elif action == "SEND_EMAIL_DISCOUNT":
        customer["discount_count"] += 1
        msg = f"Email Discount Sent: '{message_content.splitlines()[0] if message_content else ''}'"
        history.append(msg)
        
        if customer["sensitivity"]["discount"] > 0.5:
            reaction = "Email Discount Claimed: User opened email and upgraded"
            impact = +8
        else:
            reaction = "Email Discount Ignored: Email remains unread in promotions folder"
            impact = -3
            
        customer["messages"].append({
            "day": day,
            "channel": "Email",
            "content": message_content,
            "reaction": reaction,
            "impact": impact
        })

    # ─────────────────────────────
    # ACTION: SEND_EMAIL_TUTORIAL
    # ─────────────────────────────
    elif action == "SEND_EMAIL_TUTORIAL":
        msg = f"Tutorial Email Sent: '{message_content.splitlines()[0] if message_content else ''}'"
        history.append(msg)
        
        if customer["sensitivity"]["content"] > 0.5:
            reaction = "Tutorial Email Completed: Read documentation and ran API commands"
            impact = +8
        else:
            reaction = "Tutorial Email Archived: Email opened but closed immediately"
            impact = -2
            
        customer["messages"].append({
            "day": day,
            "channel": "Email",
            "content": message_content,
            "reaction": reaction,
            "impact": impact
        })

    # ─────────────────────────────
    # ACTION: SEND_IN_APP_MESSAGE
    # ─────────────────────────────
    elif action == "SEND_IN_APP_MESSAGE":
        msg = f"In-App Message Rendered: '{message_content}'"
        history.append(msg)
        
        if customer["time_since_last_event"] <= 1:
            if customer["sensitivity"]["content"] > 0.4:
                reaction = "In-App Message Acknowledged: Clicked 'Got it' and rated setup 5-stars"
                impact = +5
            else:
                reaction = "In-App Message Closed: Clicked 'Dismiss' pop-up"
                impact = +2
        else:
            reaction = "In-App Message Missed: User did not log in today"
            impact = 0
            
        customer["messages"].append({
            "day": day,
            "channel": "In-App",
            "content": message_content,
            "reaction": reaction,
            "impact": impact
        })

    # ─────────────────────────────
    # ACTION: SEND_PUSH_NOTIFICATION
    # ─────────────────────────────
    elif action == "SEND_PUSH_NOTIFICATION":
        msg = f"Push Notification Triggered: '{message_content}'"
        history.append(msg)
        
        if customer["time_since_last_event"] <= 5:
            if customer["sensitivity"]["content"] > 0.5 or customer["sensitivity"]["discount"] > 0.5:
                reaction = "Push Notification Tapped: Opened the notification on phone"
                impact = +4
            else:
                reaction = "Push Notification Swiped Away: Cleared notification"
                impact = -1
        else:
            reaction = "Push Notification Missed: Mobile app notifications disabled/ignored"
            impact = -3
            
        customer["messages"].append({
            "day": day,
            "channel": "Push",
            "content": message_content,
            "reaction": reaction,
            "impact": impact
        })

    # ─────────────────────────────
    # ACTION: CUSTOM_BUNDLE
    # ─────────────────────────────
    elif action == "CUSTOM_BUNDLE":
        msg = f"Custom Value Bundle Offered: '{message_content}'"
        history.append(msg)
        
        if customer["sensitivity"]["content"] > 0.5:
            reaction = "Bundle Accepted: Added 50,000 extra API queries to current plan"
            impact = +12
            customer["product_id"] = "P004" # Upgrade subscription ID
        else:
            reaction = "Bundle Ignored: User closed bundling offer pop-up"
            impact = -2
            
        customer["messages"].append({
            "day": day,
            "channel": "In-App",
            "content": message_content,
            "reaction": reaction,
            "impact": impact
        })

    # ─────────────────────────────
    # ACTION: DO_NOTHING
    # ─────────────────────────────
    elif action == "DO_NOTHING":
        decay = -4 - customer["time_since_last_event"]
        impact = max(-15, decay)
        history.append("No Action Taken: System allowed customer to churn naturally")

    # ─────────────────────────────
    # APPLY IMPACT TO ENGAGEMENT
    # ─────────────────────────────
    customer["engagement_score"] = max(
        0, min(100, customer["engagement_score"] + impact)
    )

    # Time and Event tracking
    if action == "DO_NOTHING":
        customer["time_since_last_event"] += 1
    else:
        customer["time_since_last_event"] = 0

    # ─────────────────────────────
    # CHURN ELIMINATION (ROI CAP)
    # ─────────────────────────────
    if customer["engagement_score"] <= churn_threshold or customer["not_interested_count"] >= 3:
        customer["status"] = "Churned"
        customer["lifecycle_stage"] = "Churned"
        if "Agent stopped investing due to low ROI" not in history:
            history.append("Agent stopped investing due to low ROI")
        impact = 0

    # ─────────────────────────────
    # CUSTOMER LIFETIME VALUE (CLV) DYNAMIC UPDATE
    # ─────────────────────────────
    if customer["status"] != "Churned":
        prod_id = customer.get("product_id", "P001")
        if "base_prices" in st.session_state:
            base_price = st.session_state.base_prices.get(prod_id, 29.0)
        else:
            base_price = products.get(prod_id, {}).get("base_price", 29.0)
        
        price_multiplier = 0.7 if "DISCOUNT" in action and impact > 0 else 1.0
        cycle_revenue = base_price * price_multiplier
        
        # Add dynamic bundle billing cost if bundle accepted
        if action == "CUSTOM_BUNDLE" and impact > 0:
            cycle_revenue += 5.0 # Bundle costs $5
            
        customer["clv"] = round(customer.get("clv", 0.0) + cycle_revenue, 2)

    # ─────────────────────────────
    # LEARNING (Strategy Memory)
    # ─────────────────────────────
    if memory is not None and action != "DO_NOTHING":
        status = "SUCCESS" if impact > 0 else "FAILED"
        memory.update(customer, action, status)

    # ─────────────────────────────
    # STATE TRACKING
    # ─────────────────────────────
    customer["last_action"] = action
    customer["action_history"].append(action)

    return impact

# Aliases for app.py compatibility
simulate_user_behavior = simulate_time_step
evaluate_agent_action = evaluate_outcome