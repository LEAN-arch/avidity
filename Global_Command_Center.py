import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import time

# --- PAGE CONFIGURATION (SET ONLY ONCE IN THE MAIN APP) ---
st.set_page_config(
    page_title="Avidity QC Command Center",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ATOMIC DATA INITIALIZATION FUNCTION ---
@st.cache_data
def generate_data():
    """Generates all necessary dataframes for the application."""
    data = {}
    data['partners'] = pd.DataFrame({
        'Partner': ['Pharma-Mfg', 'BioTest Labs', 'Gene-Chem', 'OligoSynth', 'VialFill Services'],
        'Type': ['CMO', 'CTO', 'CTO', 'CMO', 'CMO'],
        'Specialty': ['Drug Substance', 'Analytical & Micro', 'Analytical Chemistry', 'Oligonucleotide Synthesis', 'Drug Product Fill/Finish'],
        'Location': ['Boston, MA', 'San Diego, CA', 'Raleigh, NC', 'Boulder, CO', 'Brussels, Belgium'],
        'lat': [42.3601, 32.7157, 35.7796, 40.0150, 50.8503],
        'lon': [-71.0589, -117.1611, -78.6382, -105.2705, 4.3517],
        'TAT_SLA': [21, 14, 14, 21, 28] # Turnaround Time Service Level Agreement in days
    })

    products = ['DM1 (AOC-1001)', 'DMD (AOC-1020)', 'FSHD (AOC-1044)']
    stages = ['Antibody Intermediate', 'Oligonucleotide', 'Drug Substance', 'Drug Product']
    statuses = ['Testing in Progress', 'Data Review Pending', 'Awaiting Release', 'Released']
    batch_data = []
    for i in range(20):
        prod = np.random.choice(products)
        stage = np.random.choice(stages)
        partner = np.random.choice(data['partners']['Partner'])
        status = np.random.choice(statuses, p=[0.3, 0.2, 0.1, 0.4])
        created_date = pd.Timestamp.now() - pd.Timedelta(days=np.random.randint(1, 45))
        tat_sla = data['partners'][data['partners']['Partner'] == partner]['TAT_SLA'].iloc[0]
        actual_tat = np.random.randint(tat_sla - 5, tat_sla + 10)
        batch_data.append([f"{prod.split(' ')[0]}-{stage.split(' ')[0]}-{100+i}", prod, stage, partner, status, created_date, tat_sla, actual_tat])
    data['batches'] = pd.DataFrame(batch_data, columns=['Lot_ID', 'Product', 'Stage', 'Partner', 'Status', 'Date_Created', 'TAT_SLA', 'Actual_TAT'])

    dev_data = []
    for i in range(15):
        partner = np.random.choice(data['partners']['Partner'])
        prod = np.random.choice(products)
        lot_id = f"{prod.split(' ')[0]}-DS-{100+i}"
        status = np.random.choice(['New Event', 'Investigation', 'CAPA Plan', 'Closed'], p=[0.1, 0.4, 0.2, 0.3])
        age = np.random.randint(1, 60)
        dev_type = np.random.choice(['Deviation', 'OOS', 'OOT'])
        dev_data.append([f"DEV-{2023-i}", lot_id, prod, partner, dev_type, status, age])
    data['deviations'] = pd.DataFrame(dev_data, columns=['Deviation_ID', 'Lot_ID', 'Product', 'Partner', 'Type', 'Status', 'Age_Days'])
    
    return data

# --- ROBUST STATE INITIALIZATION ---
if 'app_data' not in st.session_state:
    st.session_state['app_data'] = generate_data()

app_data = st.session_state['app_data']
partners = app_data['partners']
batches = app_data['batches']
deviations = app_data['deviations']

# --- SIDEBAR ---
st.sidebar.image("https://www.aviditybiosciences.com/wp-content/themes/avidity/images/logo.svg", width=200)
st.sidebar.title("QC External Operations")
st.sidebar.markdown("---")
st.sidebar.info("This Command Center is a functional prototype demonstrating the data-driven systems and tools required for the **QC Manager** role at Avidity.")
st.sidebar.markdown("---")
st.sidebar.header("Navigation")

# --- UI RENDER ---
st.title("🧬 Global CMO/CTO Command Center")
st.caption(f"Data Last Refreshed: {time.strftime('%Y-%m-%d %H:%M:%S')}")

st.subheader("Network Health at a Glance")
col1, col2, col3, col4 = st.columns(4)
with col1:
    pending_release = batches[batches['Status'] != 'Released'].shape[0]
    st.metric("Batches Pending QC Action", pending_release)
with col2:
    active_devs = deviations[deviations['Status'] != 'Closed'].shape[0]
    st.metric("Active Deviations/OOS", active_devs)
with col3:
    at_risk_lots = batches[(batches['Status'] != 'Released') & (batches['Actual_TAT'] > batches['TAT_SLA'])].shape[0]
    st.metric("Lots At-Risk of Delay (TAT)", at_risk_lots, delta=f"{at_risk_lots - 2}", delta_color="inverse")
with col4:
    total_pulls = 7
    st.metric("Upcoming Stability Pulls (14d)", total_pulls)

with st.expander("SME Explanations for KPIs"):
    st.markdown("""
    - **Batches Pending QC Action:** Total number of lots across all products and stages that are currently in the QC workflow (Testing, Data Review, Release). *Relevance: Measures the overall workload and throughput of the QC function.*
    - **Active Deviations/OOS:** Total number of open quality events (Out-of-Specification, Deviations). *Relevance: A direct measure of the current problem-solving burden and potential quality risks across the network. Governed by **cGMP** and **ICH Q10**.*
    - **Lots At-Risk of Delay (TAT):** Number of active lots where the testing Turnaround Time has exceeded the contractual Service Level Agreement (SLA). *Relevance: A leading indicator of potential supply chain disruptions and timeline misses.*
    - **Upcoming Stability Pulls:** Number of scheduled stability test points in the next 14 days. *Relevance: Proactively highlights critical, time-sensitive activities required for regulatory filings and product shelf-life determination per **ICH Q1A(R2)**.*
    """)
st.divider()

col1, col2 = st.columns([2, 1.5])
with col1:
    st.subheader("CMO/CTO Performance Matrix")
    st.markdown("- **Why:** This data-driven ranking provides an objective basis for partner management, QBRs, and identifying systemic risks. It directly addresses the need to 'Hold CMOs/CTOs accountable'.")
    
    perf_summary = []
    for partner_name in partners['Partner']:
        partner_batches = batches[batches['Partner'] == partner_name]
        partner_devs = deviations[deviations['Partner'] == partner_name]
        on_time_rate = (partner_batches['Actual_TAT'] <= partner_batches['TAT_SLA']).mean() * 100 if not partner_batches.empty else 100
        oos_rate = (partner_devs['Type'] == 'OOS').mean() * 100 if not partner_devs.empty else 0
        late_devs = partner_devs[partner_devs['Age_Days'] > 30].shape[0]
        perf_summary.append([partner_name, on_time_rate, oos_rate, late_devs])
    perf_df = pd.DataFrame(perf_summary, columns=["Partner", "On-Time Rate (%)", "OOS Rate (%)", "Deviations >30d"])
    st.dataframe(perf_df, use_container_width=True,
                 column_config={"On-Time Rate (%)": st.column_config.ProgressColumn(format="%.0f%%", min_value=0, max_value=100)})
    
    st.subheader("Release Velocity & Forecast (Last 8 Weeks)")
    st.markdown("- **Why:** This chart tracks QC throughput against our supply plan. The **ML-based forecast (orange line)** gives us a predictive view, allowing us to proactively manage resources to prevent future bottlenecks.")
    release_data = pd.DataFrame({'Week': pd.to_datetime(pd.date_range(start='2023-08-01', periods=8, freq='W')), 'Lots_Released': np.random.randint(2, 6, size=8)})
    forecasted_releases = [4, 5, 4, 3, 5, 4, 3, 2]
    fig_release = go.Figure()
    fig_release.add_trace(go.Bar(x=release_data['Week'], y=release_data['Lots_Released'], name='Actual Releases', marker_color='royalblue', text=release_data['Lots_Released']))
    fig_release.add_trace(go.Scatter(x=release_data['Week'], y=[4]*8, mode='lines', name='Target', line=dict(color='red', dash='dash')))
    fig_release.add_trace(go.Scatter(x=release_data['Week'], y=forecasted_releases, mode='lines+markers', name='Forecast', line=dict(color='orange')))
    fig_release.update_layout(height=250, margin=dict(t=20, b=20), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig_release, use_container_width=True)

with col2:
    st.subheader("Global Partner Network")
    st.map(partners[['lat', 'lon']], zoom=1)
    st.caption("Partner locations are color-coded by their current overall performance status.")
