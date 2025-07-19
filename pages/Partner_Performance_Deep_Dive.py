import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import plotly.figure_factory as ff
from sklearn.ensemble import IsolationForest

if 'app_data' not in st.session_state:
    st.error("Application data not loaded. Please return to the 'Global Command Center' home page to initialize the app.")
    st.stop()

app_data = st.session_state['app_data']
partners = app_data['partners']
batches = app_data['batches']
deviations = app_data['deviations']

st.markdown("# 📈 Partner Performance Deep Dive")
st.markdown("This module provides a detailed analytical view of a single CMO/CTO's performance, ideal for troubleshooting issues or preparing for a Quarterly Business Review (QBR).")

selected_partner = st.selectbox("Select a Partner to Analyze", partners['Partner'].unique())
partner_batches = batches[batches['Partner'] == selected_partner]
partner_devs = deviations[deviations['Partner'] == selected_partner]

st.header(f"Performance Analysis for: {selected_partner}")

tab_perf, tab_ml, tab_transfers = st.tabs(["Performance Analytics (SPC/Cpk)", "ML Anomaly Detection", "Technology Transfers"])
with tab_perf:
    st.subheader("Key Performance & Quality Metrics")
    col1, col2, col3 = st.columns(3)
    with col1:
        on_time_rate = (partner_batches['Actual_TAT'] <= partner_batches['TAT_SLA']).mean() * 100 if not partner_batches.empty else 100
        st.metric("On-Time Release Rate", f"{on_time_rate:.1f}%")
    with col2:
        oos_rate = (partner_devs['Type'] == 'OOS').mean() * 100 if not partner_devs.empty else 0
        st.metric("Out-of-Specification (OOS) Rate", f"{oos_rate:.1f}%")
    with col3:
        open_capas = partner_devs[(partner_devs['Status'] == 'CAPA Plan')].shape[0]
        st.metric("Open CAPAs", open_capas)
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Process Capability (Cpk)")
        st.markdown("- **What:** A histogram of a **Critical Quality Attribute (CQA)** measured by this partner, plotted against engineering specifications. \n- **Why (Actionability):** This core **Six Sigma** metric proves if a partner's process is *capable* of reliably meeting our requirements. A **Cpk < 1.33** is a data-driven trigger to demand process improvement per **AS9145 (APQP)** principles.")
        usl, lsl = 99.8, 98.0; mu, sigma = 99.1, 0.3; process_data = np.random.normal(mu, sigma, 200)
        cpu = (usl - mu) / (3 * sigma); cpl = (mu - lsl) / (3 * sigma); cpk = min(cpu, cpl)
        fig_cpk = ff.create_distplot([process_data], ['Purity Data'], show_hist=True, show_rug=False)
        fig_cpk.add_vline(x=usl, line=dict(dash="dash", color="red"), name="USL"); fig_cpk.add_vline(x=lsl, line=dict(dash="dash", color="red"), name="LSL")
        fig_cpk.update_layout(title=f"Process Capability: Purity by HPLC (Cpk = {cpk:.2f})")
        st.plotly_chart(fig_cpk, use_container_width=True)
    with col2:
        st.subheader("Turnaround Time (TAT) Performance")
        st.caption("This histogram shows the distribution of actual testing TATs against the contractual SLA (red line). This provides objective evidence to hold partners accountable for their performance commitments.")
        if not partner_batches.empty:
            sla = partner_batches['TAT_SLA'].iloc[0]
            fig_hist = px.histogram(partner_batches, x="Actual_TAT", nbins=15, title=f"Testing TAT Distribution (SLA: {sla} days)")
            fig_hist.add_vline(x=sla, line_dash="dash", line_color="red", annotation_text="SLA")
            st.plotly_chart(fig_hist, use_container_width=True)
with tab_ml:
    st.header("Machine Learning: Assay Anomaly Detection")
    st.markdown("- **Why (Actionability):** This is a powerful tool for **proactive risk identification**. An anomalous result, even if in-spec, can be a leading indicator of method drift, instrument issues, or subtle changes in product quality. It provides a data-driven reason to place a batch on \"for-information\" stability or perform additional characterization, aligning with the principles of **ICH Q10 (Lifecycle Management)**.")
    np.random.seed(0)
    hist_data = pd.DataFrame(np.random.multivariate_normal([99.0, 1.5], [[0.1, 0.05], [0.05, 0.08]], 100), columns=['Purity', 'Main_Impurity'])
    model = IsolationForest(contamination=0.05, random_state=42).fit(hist_data)
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("Analyze New Batch Data")
        purity_val = st.slider("Purity by HPLC (%)", 98.0, 100.0, 99.1, 0.01)
        impurity_val = st.slider("Main Impurity Peak (%)", 0.1, 3.0, 1.45, 0.01)
        new_batch = pd.DataFrame([[purity_val, impurity_val]], columns=['Purity', 'Main_Impurity'])
        prediction = model.predict(new_batch)[0]
        decision = "Anomaly Detected" if prediction == -1 else "Statistically Normal (Inlier)"
        if decision == "Anomaly Detected": st.error(f"**Result:** {decision}", icon="🚨")
        else: st.success(f"**Result:** {decision}", icon="✅")
    with col2:
        st.subheader("Historical Assay Performance")
        fig_anomaly = px.scatter(hist_data, x="Purity", y="Main_Impurity", title="Historical Data Distribution")
        fig_anomaly.add_trace(go.Scatter(x=new_batch['Purity'], y=new_batch['Main_Impurity'], mode='markers', name='New Batch', marker=dict(color='red', size=15, symbol='star')))
        st.plotly_chart(fig_anomaly, use_container_width=True)
with tab_transfers:
    st.header("Analytical Technology Transfer Status")
    st.markdown("This tracker monitors the progress of all active analytical method transfers to this partner, ensuring clear communication and preventing delays in bringing new testing capabilities online.")
    tt_data = [{'Method': 'DMD Bioassay (EC50)', 'From': 'Avidity AD', 'Status': 'Protocol Execution', 'Target Date': '2024-09-15'}, {'Method': 'FSHD Purity by CE-SDS', 'From': 'Avidity AD', 'Status': 'Method Familiarization', 'Target Date': '2024-10-01'}, {'Method': 'DM1 Oligo Purity by IPRP-HPLC', 'From': 'Gene-Chem', 'Status': 'Completed', 'Target Date': '2024-07-30'}]
    st.dataframe(tt_data, use_container_width=True)
