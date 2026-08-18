import os
import json
import random
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

# Load environment variables
load_dotenv()

# Helper to load config
def load_config():
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except Exception:
        return {
            "llm_provider": "gemini",
            "model_name": "gemini-2.5-flash",
            "churn_score_threshold": 10,
            "max_sms_limit": 2,
            "max_discount_limit": 2,
            "base_price_fluctuation_rate": 0.04
        }

# LLM initializations
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

def get_llm(provider="gemini"):
    if provider == "openai":
        return ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.2,
            api_key=os.getenv("OPENAI_API_KEY")
        )
    else:
        return ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.2,
            google_api_key=os.getenv("GOOGLE_API_KEY") or os.getenv("OPENAI_API_KEY") # fallback for mocked testing
        )

# 1. BEHAVIOR ANALYSIS AGENT (Deterministic Logic)
def behavior_analysis_agent(customer):
    """Analyzes raw history to create a 'Vibe Check' for the LLM."""
    last_3_events = customer['history'][-3:]
    score_change = customer['engagement_score']
    
    status = "Healthy"
    if "Inactive" in last_3_events:
        status = "At Risk"
    if "Visited Pricing Page" in last_3_events:
        status = "Upsell Opportunity"
        
    return {
        "customer_id": customer['id'],
        "status": status,
        "summary": f"User is {status} with a score of {score_change}."
    }

# 2. DECISION AGENT (Tying together Subagents and Group B fallback)
ACTIONS = [
    "SEND_SMS_DISCOUNT", 
    "SEND_SMS_TUTORIAL", 
    "SEND_EMAIL_DISCOUNT", 
    "SEND_EMAIL_TUTORIAL", 
    "SEND_IN_APP_MESSAGE", 
    "SEND_PUSH_NOTIFICATION", 
    "DO_NOTHING"
]

def decision_agent(customer, memory, llm_provider="gemini"):
    """
    Strategic Decision Agent with A/B testing:
    - Group A: Coordinates a Google ADK-inspired Subagent Mesh
    - Group B: Standard Rule-based control group
    """

    # ─────────────────────────────
    # HARD RULES (NO LLM / CHURN)
    # ─────────────────────────────
    if customer["status"] == "Churned":
        return {
            "thought": "Customer already churned. No further investment.",
            "action": "DO_NOTHING",
            "content": "No message."
        }

    # Load parameters from config
    config = load_config()
    max_discounts = config.get("max_discount_limit", 2)
    max_sms = config.get("max_sms_limit", 2)

    forbidden = memory.get_forbidden_actions(customer)

    # HARD BUSINESS CONSTRAINT: Discount cap
    if customer.get("discount_count", 0) >= max_discounts:
        if "SEND_SMS_DISCOUNT" not in forbidden:
            forbidden.append("SEND_SMS_DISCOUNT")
        if "SEND_EMAIL_DISCOUNT" not in forbidden:
            forbidden.append("SEND_EMAIL_DISCOUNT")

    # HARD BUSINESS CONSTRAINT: SMS cap
    if customer.get("sms_count", 0) >= max_sms:
        if "SEND_SMS_DISCOUNT" not in forbidden:
            forbidden.append("SEND_SMS_DISCOUNT")
        if "SEND_SMS_TUTORIAL" not in forbidden:
            forbidden.append("SEND_SMS_TUTORIAL")

    # Force action when inactive
    if customer.get("time_since_last_event", 0) >= 2:
        if "DO_NOTHING" not in forbidden:
            forbidden.append("DO_NOTHING")

    # Business policy: High-Value customers don't receive discounts
    if customer.get("segment") == "High-Value":
        if "SEND_SMS_DISCOUNT" not in forbidden:
            forbidden.append("SEND_SMS_DISCOUNT")
        if "SEND_EMAIL_DISCOUNT" not in forbidden:
            forbidden.append("SEND_EMAIL_DISCOUNT")

    allowed_actions = [a for a in ACTIONS if a not in forbidden]

    # Absolute fallback
    if not allowed_actions:
        return {
            "thought": "All actions are constrained. Defaulting to safe inaction.",
            "action": "DO_NOTHING",
            "content": "No message."
        }

    # ─────────────────────────────
    # A/B TESTING: GROUP B RULE-BASED FALLBACK
    # ─────────────────────────────
    if customer.get("test_group") == "Group B (Standard Rules)":
        # Rule-based static outreach matching
        if customer.get("time_since_last_event", 0) >= 3:
            if customer.get("segment") == "Price-Sensitive" and "SEND_EMAIL_DISCOUNT" in allowed_actions:
                action = "SEND_EMAIL_DISCOUNT"
            elif "SEND_EMAIL_TUTORIAL" in allowed_actions:
                action = "SEND_EMAIL_TUTORIAL"
            else:
                action = allowed_actions[0]
        else:
            action = "DO_NOTHING" if "DO_NOTHING" in allowed_actions else allowed_actions[0]
            
        return {
            "thought": "Rule-based control group (Group B). Static rule applied without LLM.",
            "action": action,
            "content": "Template outreach messaging."
        }

    # ─────────────────────────────
    # GROUP A: DELEGATING TO RootOrchestratorAgent (Subagent Mesh)
    # ─────────────────────────────
    try:
        llm = get_llm(llm_provider)
        from src.agents.orchestrator import RootOrchestratorAgent
        orchestrator = RootOrchestratorAgent(llm)
        
        result = orchestrator.run(customer, allowed_actions)
        return result
    except Exception as e:
        print("Orchestrator Loop Error:", e)
        return {
            "thought": f"Orchestrator mesh execution failed: {e}. Falling back to default.",
            "action": allowed_actions[0],
            "content": "Hello! How can we assist you today?"
        }
