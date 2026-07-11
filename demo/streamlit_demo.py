import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="ADSL Demo | Contested Logistics",
    page_icon="🚢",
    layout="wide"
)

st.title("ADSL — Agent-based Decision Support for Logistics")
st.markdown("### Professional Demo for Enterprise & Defense Use Cases")

st.info("This is a **simplified interactive demo** of the full ADSL platform. The complete system includes advanced agent simulation, real-time analytics, and Palantir integration capabilities.")

# Sidebar
st.sidebar.header("Scenario Configuration")
scenario = st.sidebar.selectbox(
    "Select Scenario",
    ["Baseline (Stable Logistics)", "Contested Logistics Scenario"]
)

run_button = st.sidebar.button("Run Analysis", type="primary")

if run_button:
    with st.spinner("Running ADSL analysis..."):
        # Simulated realistic results
        if "Contested" in scenario:
            risk_score = 78
            bottlenecks = 7
            focus_areas = 4
            recommendation = "High priority: Reroute through northern corridor. Reduce exposure in Sector 4."
            df = pd.DataFrame({
                "Metric": ["Risk Score", "Bottlenecks Detected", "Focus Areas", "Avg Delay (hrs)"],
                "Baseline": [42, 2, 1, 3.2],
                "Contested": [78, 7, 4, 11.8]
            })
        else:
            risk_score = 42
            bottlenecks = 2
            focus_areas = 1
            recommendation = "Logistics network is stable. Minor optimization possible in Sector 2."
            df = pd.DataFrame({
                "Metric": ["Risk Score", "Bottlenecks Detected", "Focus Areas", "Avg Delay (hrs)"],
                "Baseline": [42, 2, 1, 3.2],
                "Contested": [78, 7, 4, 11.8]
            })

        # Metrics Row
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Risk Score", risk_score, delta="+36" if risk_score > 50 else None)
        col2.metric("Bottlenecks Detected", bottlenecks)
        col3.metric("Focus Areas", focus_areas)
        col4.metric("Avg Delay (hrs)", 11.8 if risk_score > 50 else 3.2)

        st.markdown("---")

        # Comparison Table
        st.subheader("Scenario Comparison")
        st.dataframe(df, use_container_width=True)

        # Recommendation
        st.subheader("Key Recommendation")
        st.success(recommendation)

        st.caption("Note: Full ADSL system provides agent-level decision traces, real-time updates, and direct Palantir Foundry integration.")

else:
    st.markdown("""
    ### How to use this demo
    
    1. Select a scenario from the sidebar
    2. Click **Run Analysis**
    3. Review the risk metrics and recommendations
    
    This demo showcases ADSL's ability to quickly surface risk and decision support under different conditions.
    """)

st.markdown("---")
st.caption("ADSL v2.0 | Built for contested logistics and enterprise decision support | Palantir integration ready")