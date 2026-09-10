---
name: streamlit-dashboard-design
description: |
  Best practices, design patterns, and glassmorphic UI architecture for building
  world-class, high-aesthetic Streamlit dashboards and AI agent control centers.
  Use when designing or refactoring Streamlit apps, structuring multi-tab operational
  consoles, and eliminating visual clutter.
---

# Streamlit Modern Dashboard Design System

This skill guides the design and implementation of modern, production-grade Streamlit dashboards that avoid visual clutter and provide seamless agentic workflows.

## 1. Information Architecture: The Tabbed Pattern

Never dump simulation controls, detailed tables, time-series charts, and memory trees into a single scrolling page. Partition applications into clear, functional zones using `st.tabs()`:

```python
tab_sim, tab_customers, tab_analytics, tab_memory = st.tabs([
    "🕹️ Simulation & Approvals",
    "👥 Customer 360",
    "📊 Market & Channel Analytics",
    "🧠 Agent Brain & Memory"
])
```

- **Zone 1: Active Operations**: Controls for the loop, pending approvals (HITL), and real-time narrative story stream.
- **Zone 2: Entity Deep Dive**: Deep inspection cards for individual actors/personas with state metrics.
- **Zone 3: Retrospective BI**: Aggregate charts, A/B test lift comparisons, and conversion funnels.
- **Zone 4: Agent Transparency**: Inner reasoning, prompt logs, compliance audits, and strategy memory registry.

## 2. Design Tokens & Glassmorphic Styling

Inject a curated CSS design system via `st.markdown(..., unsafe_allow_html=True)` at the top of the app:

```css
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

.stApp {
    background: radial-gradient(circle at top right, #111827 0%, #090d16 100%);
    color: #f1f5f9;
    font-family: 'Plus Jakarta Sans', sans-serif;
}

/* Glassmorphic Bento Cards */
.glass-card {
    background: rgba(17, 24, 39, 0.65);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 1.5rem;
    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.35);
    backdrop-filter: blur(12px);
    transition: transform 0.2s ease, border-color 0.2s ease;
}

.glass-card:hover {
    border-color: rgba(99, 102, 241, 0.35);
    transform: translateY(-2px);
}
```

## 3. Human-In-The-Loop (HITL) Staging Desk

When agents propose actions, display them in an actionable approval queue:
1. Show **Agent Strategic Thought** (why the action was chosen).
2. Show **Proposed Copy** (with highlighted compliance disclaimers).
3. Provide one-click **Approve** and **Reject** buttons to keep human operators in control.

## 4. Modern Streamlit Syntax Compliance

- Replace deprecated `use_container_width=True` on buttons/plots with modern container-width syntax or styled columns.
- Keep session state cleanly encapsulated (`st.session_state`).
- Group sidebar controls strictly into configuration parameters vs system status.
