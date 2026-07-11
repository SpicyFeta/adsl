import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="ADSL | Contested Logistics Decision Support",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional Header
st.title("ADSL — Agent-Based Decision Support for Logistics")
st.markdown("### Enterprise Demo | Designed for Defense & High-Risk Operations")

st.caption("This is a professional-grade demonstration of the ADSL platform. The full system includes advanced agent simulation, real-time analytics, decision traceability, and Palantir Foundry integration capabilities.")

# Sidebar Configuration
with st.sidebar:
    st.header("Scenario Configuration")
    
    scenario = st.selectbox(
        "Select Operating Environment",
        ["Baseline (Stable Logistics)", "Contested Logistics Scenario"],
        index=1
    )
    
    st.markdown("---")
    st.subheader("Simulation Parameters")
    disruption_level = st.slider("Adversarial Disruption Level", 0, 100, 65 if "Contested" in scenario else 15)
    
    run_analysis = st.button("Run ADSL Analysis", type="primary", use_container_width=True)

if run_analysis:
    with st.spinner("ADSL agents analyzing contested logistics network..."):
        
        if "Contested" in scenario:
            risk_score = 78 + (disruption_level - 65) // 5
            bottlenecks = 6 + disruption_level // 20
            focus_areas = 3 + disruption_level // 25
            avg_delay = round(8.5 + (disruption_level - 65) / 10, 1)
            recommendation = "**High Priority Actions:**\n- Reroute 40% of volume through Northern Corridor\n- Reduce exposure in Sector 4 immediately\n- Activate secondary suppliers in Region B"
            status = "Elevated Risk"
            color = "orange"
        else:
            risk_score = 38
            bottlenecks = 2
            focus_areas = 1
            avg_delay = 3.4
            recommendation = "**Recommended Actions:**\n- Minor optimization possible in Sector 2\n- Current network is stable under baseline conditions"
            status = "Stable"
            color = "green"

        # Key Metrics Row
        st.subheader("Key Decision Metrics")
        col1, col2, col3, col4 = st.columns(4)
        
        col1.metric("Overall Risk Score", f"{risk_score}", delta=f"+{risk_score - 42}" if risk_score > 42 else None)
        col2.metric("Critical Bottlenecks", bottlenecks)
        col3.metric("Focus Areas Identified", focus_areas)
        col4.metric("Average Delay (hrs)", avg_delay)

        st.markdown("---")

        # Scenario Comparison
        st.subheader("Scenario Comparison")
        
        comparison_data = {
            "Metric": ["Risk Score", "Bottlenecks", "Focus Areas", "Avg Delay (hrs)"],
            "Baseline": [42, 2, 1, 3.4],
            "Current Scenario": [risk_score, bottlenecks, focus_areas, avg_delay]
        }
        df = pd.DataFrame(comparison_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Recommendation Box
        st.subheader("ADSL Recommendation")
        if color == "orange":
            st.warning(recommendation)
        else:
            st.success(recommendation)

        st.caption("Note: Full ADSL platform provides agent-level decision traces, real-time updates, and direct integration with Palantir Foundry.")

else:
    st.markdown("""
    ### How to Use This Demo
    
    1. Select your operating environment (Baseline or Contested)
    2. Adjust the disruption level if desired
    3. Click **Run ADSL Analysis**
    4. Review risk metrics, bottlenecks, and recommended actions
    
    This demo illustrates how ADSL rapidly surfaces risk and provides actionable decision support under different conditions.
    """)

st.markdown("---")
st.caption("ADSL Enterprise Demo v2.0 | Built for contested logistics and high-stakes decision support | Palantir integration ready")