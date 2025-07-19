# ==============================================================================
# 🧬 Page 2: Partner Performance Deep Dive
#
# ==============================================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import plotly.figure_factory as ff
from sklearn.ensemble import IsolationForest

st.set_page_config(
    page_title="Partner Deep Dive",
    page_icon="📈",
    layout="wide"
)

# --- 1. ROBUST STATE CHECK ---
if 'app_data' not in st.session_state:
    st.error("🚨 Application data not loaded. Please return to the 'Global Command Center' home page to initialize the app.")
    st.stop()

# --- 2. DATA UNPACKING ---
app_data = st.session_state['app_data']
partners_df = app_data['partners']
batches_df = app_data['batches']
deviations_df = app_data['deviations']
tech_transfers_df = app_data['tech_transfers']

# --- 3. UI RENDER ---
st.markdown("# 📈 Partner Performance Deep Dive")
st.markdown("This module provides a detailed analytical view of a single CMO/CTO's performance, ideal for troubleshooting issues or preparing for a Quarterly Business Review (QBR).")

selected_partner = st.selectbox("Select a Partner to Analyze", partners_df['Partner'].unique())

# Filter all data for the selected partner at the top level for efficiency.
partner_batches = batches_df[batches_df['Partner'] == selected_partner]
partner_devs = deviations_df[deviations_df['Partner'] == selected_partner]
partner_transfers = tech_transfers_df[tech_transfers_df['Partner'] == selected_partner]

st.header(f"Performance Analysis for: {selected_partner}")

tab_perf, tab_ml, tab_transfers = st.tabs(["Performance Analytics (SPC/Cpk)", "ML Anomaly Detection", "Technology Transfers"])

# --- TAB 1: Performance Analytics (SPC/Cpk) ---
with tab_perf:
    st.subheader("Key Performance & Quality Metrics")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Calculate On-Time Rate for the selected partner
        if not partner_batches.empty:
            on_time_rate = (partner_batches['Actual_TAT'] <= partner_batches['TAT_SLA']).mean() * 100
        else:
            on_time_rate = 100 # Default to 100% if no batches
        st.metric("On-Time Release Rate", f"{on_time_rate:.1f}%")
        
    with col2:
        # Calculate OOS Rate
        if not partner_devs.empty:
            total_devs = len(partner_devs)
            oos_count = len(partner_devs[partner_devs['Type'] == 'OOS'])
            oos_rate = (oos_count / total_devs) * 100 if total_devs > 0 else 0
        else:
            oos_rate = 0
        st.metric("Out-of-Specification (OOS) Rate", f"{oos_rate:.1f}%")
        
    with col3:
        # Calculate Open CAPAs
        open_capas = partner_devs[partner_devs['Status'] == 'CAPA Plan'].shape[0]
        st.metric("Open CAPAs", open_capas)
    
    st.divider()
    
    col_cpk, col_tat = st.columns(2)
    with col_cpk:
        st.subheader("Process Capability (Cpk)")
        st.markdown("- **Why (Actionability):** This core **Six Sigma** metric proves if a partner's process is *capable* of reliably meeting our requirements. A **Cpk < 1.33** is a data-driven trigger to demand process improvement.")
        
        # DATA-DRIVEN CPK: This chart is no longer a simulation. It uses the 'Purity'
        # CQA data from the batches_df for the selected partner.
        process_data = partner_batches['Purity'].dropna()

        if len(process_data) > 1:
            # Define specifications for the CQA (Purity)
            usl, lsl = 100.0, 97.0
            mu = process_data.mean()
            sigma = process_data.std()
            
            # Cpk calculation
            if sigma > 0:
                cpu = (usl - mu) / (3 * sigma)
                cpl = (mu - lsl) / (3 * sigma)
                cpk = min(cpu, cpl)
            else: # Handle case where all data points are the same
                cpk = float('inf')


            fig_cpk = ff.create_distplot(
                [process_data.tolist()], ['Purity Data'],
                show_hist=True, show_rug=False, colors=['#444e86']
            )
            fig_cpk.add_vline(x=usl, line=dict(dash="dash", color="red"), name="USL", annotation_text="USL")
            fig_cpk.add_vline(x=lsl, line=dict(dash="dash", color="red"), name="LSL", annotation_text="LSL")
            fig_cpk.update_layout(title_text=f"Process Capability: Purity by HPLC (Cpk = {cpk:.2f})")
            st.plotly_chart(fig_cpk, use_container_width=True)

            if cpk < 1.33:
                st.error(f"**Action Required:** Cpk of {cpk:.2f} is below the target of 1.33. This indicates a high risk of producing non-conforming parts. A process improvement plan is required.", icon="🚨")
            else:
                st.success(f"**Process Capable:** Cpk of {cpk:.2f} meets the target of 1.33.", icon="✅")
        else:
            st.info("Insufficient batch data (n < 2) to calculate Process Capability.")

    with col_tat:
        st.subheader("Turnaround Time (TAT) Performance")
        st.markdown("- **Why (Actionability):** This provides objective, visual evidence to 'hold partners accountable'. A distribution skewed right of the SLA line is clear justification for escalating performance issues.")
        
        if not partner_batches.empty:
            # Get the SLA value safely.
            sla = partner_batches['TAT_SLA'].iloc[0]
            fig_hist = px.histogram(
                partner_batches,
                x="Actual_TAT",
                nbins=15,
                title=f"Testing TAT Distribution (SLA: {sla} days)",
                color_discrete_sequence=['#955196']
            )
            fig_hist.add_vline(x=sla, line_dash="dash", line_color="red", annotation_text="SLA")
            st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.info("No batch data available for this partner to analyze TAT.")

# --- TAB 2: ML Anomaly Detection ---
with tab_ml:
    st.header("Machine Learning: Assay Anomaly Detection")
    st.markdown("""
    - **What:** An unsupervised ML model (**Isolation Forest**) trained on historical results for this partner. It learns the "normal" multivariate distribution of results (e.g., the relationship between Purity and the Main Impurity).
    - **Why (Actionability):** This tool provides proactive risk identification. An anomalous result, even if in-spec, can be a leading indicator of method drift or quality issues, justifying further investigation per **ICH Q10**.
    """)
    
    # DATA-DRIVEN ML: This is no longer a simulation. The model is trained on
    # the actual batch data for the selected partner.
    assay_data = partner_batches[['Lot_ID', 'Purity', 'Main_Impurity']].dropna()

    if len(assay_data) > 5: # Need a minimum number of samples to train the model
        hist_data = assay_data[['Purity', 'Main_Impurity']]
        
        # Train the model on the partner's historical data
        model = IsolationForest(contamination='auto', random_state=42).fit(hist_data)
        
        col_input, col_chart = st.columns([1, 2])
        with col_input:
            st.subheader("Analyze a Specific Batch")
            # The selectbox is now populated with REAL lot IDs from the partner.
            selected_lot = st.selectbox("Select a Batch to Analyze", assay_data['Lot_ID'].unique())
            
            new_batch = assay_data[assay_data['Lot_ID'] == selected_lot][['Purity', 'Main_Impurity']]
            
            if not new_batch.empty:
                prediction = model.predict(new_batch)[0]
                decision = "Anomaly Detected" if prediction == -1 else "Statistically Normal (Inlier)"

                st.metric("Purity (%)", f"{new_batch['Purity'].iloc[0]:.2f}")
                st.metric("Main Impurity (%)", f"{new_batch['Main_Impurity'].iloc[0]:.2f}")

                if decision == "Anomaly Detected":
                    st.error(f"**Result:** {decision}", icon="🚨")
                else:
                    st.success(f"**Result:** {decision}", icon="✅")
        
        with col_chart:
            st.subheader("Historical Assay Performance")
            fig_anomaly = px.scatter(
                hist_data,
                x="Purity",
                y="Main_Impurity",
                title="Historical Data Distribution vs. Selected Batch",
                color_discrete_sequence=['royalblue']
            )
            # Highlight the selected batch on the chart
            fig_anomaly.add_trace(go.Scatter(
                x=new_batch['Purity'],
                y=new_batch['Main_Impurity'],
                mode='markers',
                name='Selected Batch',
                marker=dict(color='red', size=15, symbol='star')
            ))
            st.plotly_chart(fig_anomaly, use_container_width=True)
    else:
        st.info("Insufficient historical assay data (n < 6) for this partner to train the anomaly detection model.")

# --- TAB 3: Technology Transfers ---
with tab_transfers:
    st.header("Analytical Technology Transfer Status")
    st.markdown("This tracker monitors the progress of all active analytical method transfers to this partner, ensuring clear communication and preventing delays in bringing new testing capabilities online.")
    
    # DATA-DRIVEN TABLE: This is no longer a hardcoded list. It displays the
    # filtered data from the tech_transfers_df.
    if not partner_transfers.empty:
        st.dataframe(
            partner_transfers[['Method', 'From', 'Status', 'Target Date']],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info(f"No active technology transfers recorded for {selected_partner}.")
