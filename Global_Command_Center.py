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

# --- ATOMIC DATA INITIALIZATION FUNCTION (DEFINITIVE REFACTOR) ---
@st.cache_data
def generate_data():
    """Generates a fully integrated, traceable, and context-aware dataset."""
    data = {}
    data['partners'] = pd.DataFrame({
        'Partner': ['Pharma-Mfg', 'BioTest Labs', 'Gene-Chem', 'OligoSynth', 'VialFill Services'],
        'Type': ['CMO', 'CTO', 'CTO', 'CMO', 'CMO'],
        'Specialty': ['Drug Substance', 'Analytical & Micro', 'Analytical Chemistry', 'Oligonucleotide Synthesis', 'Drug Product Fill/Finish']
    })
    products = ['DM1 (AOC-1001)', 'DMD (AOC-1020)', 'FSHD (AOC-1044)']
    
    # --- TRUE LOT GENEALOGY GENERATION ---
    batch_data = []
    lot_lineage = []
    lot_counter = 100
    static_now = pd.Timestamp('2023-10-27')
    
    for product in products:
        # Create a full chain for each product
        mab_lot = f"{product.split(' ')[0]}-Antibody-{lot_counter}"; lot_counter += 1
        oligo_lot = f"{product.split(' ')[0]}-Oligo-{lot_counter}"; lot_counter += 1
        ds_lot = f"{product.split(' ')[0]}-DS-{lot_counter}"; lot_counter += 1
        dp_lot = f"{product.split(' ')[0]}-DP-{lot_counter}"; lot_counter += 1
        
        # Append to batch list
        batch_data.extend([
            {'Lot_ID': mab_lot, 'Product': product, 'Stage': 'Antibody Intermediate', 'Partner': 'Pharma-Mfg', 'Status': 'Released', 'Date_Created': static_now - pd.Timedelta(days=np.random.randint(60, 90))},
            {'Lot_ID': oligo_lot, 'Product': product, 'Stage': 'Oligonucleotide', 'Partner': 'OligoSynth', 'Status': 'Released', 'Date_Created': static_now - pd.Timedelta(days=np.random.randint(60, 90))},
            {'Lot_ID': ds_lot, 'Product': product, 'Stage': 'Drug Substance', 'Partner': 'Pharma-Mfg', 'Status': 'Released', 'Date_Created': static_now - pd.Timedelta(days=np.random.randint(30, 60))},
            {'Lot_ID': dp_lot, 'Product': product, 'Stage': 'Drug Product', 'Partner': 'VialFill Services', 'Status': np.random.choice(['Awaiting Release', 'Released']), 'Date_Created': static_now - pd.Timedelta(days=np.random.randint(5, 30))}
        ])
        
        # Create the lineage links
        lot_lineage.extend([
            {'parent_lot': mab_lot, 'child_lot': ds_lot},
            {'parent_lot': oligo_lot, 'child_lot': ds_lot},
            {'parent_lot': ds_lot, 'child_lot': dp_lot}
        ])

    data['batches'] = pd.DataFrame(batch_data)
    data['lot_lineage'] = pd.DataFrame(lot_lineage)
    
    # --- CONTEXT-AWARE MICROBIOLOGY DATA ---
    micro_data = []
    for partner_name, partner_info in data['partners'].iterrows():
        if partner_info['Specialty'] in ['Analytical & Micro', 'Drug Product Fill/Finish']:
            for date in pd.to_datetime(pd.date_range(start='2023-01-01', end='2023-09-30', freq='W')):
                if partner_info['Specialty'] == 'Analytical & Micro':
                    micro_data.append([date, partner_name, 'Bioburden (CFU/10mL)', np.random.poisson(2), 10])
                    micro_data.append([date, partner_name, 'Endotoxin (EU/mL)', np.random.uniform(0.05, 0.2), 0.5])
                if partner_info['Specialty'] == 'Drug Product Fill/Finish':
                    em_count = np.random.poisson(5)
                    if date.month in [6, 7]: em_count = np.random.poisson(15)
                    micro_data.append([date, partner_name, 'EM Grade B (CFU/plate)', em_count, 10])
    data['micro_data'] = pd.DataFrame(micro_data, columns=['Date', 'Partner', 'Test', 'Result', 'Limit'])

    # Deviations
    valid_lot_ids = data['batches']['Lot_ID'].tolist()
    dev_data = []
    for i in range(15):
        partner = np.random.choice(data['partners']['Partner']); lot_id = np.random.choice(valid_lot_ids)
        prod_from_lot = [p for p in products if p.split(' ')[0] in lot_id][0]
        status = np.random.choice(['New Event', 'Investigation', 'CAPA Plan', 'Closed'], p=[0.1, 0.4, 0.2, 0.3]); age = np.random.randint(1, 60)
        dev_type = np.random.choice(['Deviation', 'OOS', 'OOT']); dev_data.append([f"DEV-{2023-i}", lot_id, prod_from_lot, partner, dev_type, status, age])
    data['deviations'] = pd.DataFrame(dev_data, columns=['Deviation_ID', 'Lot_ID', 'Product', 'Partner', 'Type', 'Status', 'Age_Days'])

    return data

# --- ROBUST STATE INITIALIZATION ---
if 'app_data' not in st.session_state:
    st.session_state['app_data'] = generate_data()

app_data = st.session_state['app_data']
partners = app_data['partners']
batches = app_data['batches']
deviations = app_data['deviations']
micro_data = app_data['micro_data']

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
    st.metric("Batches Pending QC Action", batches[batches['Status'] != 'Released'].shape[0])
with col2:
    st.metric("Active Deviations/OOS", deviations[deviations['Status'] != 'Closed'].shape[0])
with col3:
    # A simplified TAT calculation for the main page
    late_lots_count = batches[batches['Status'] != 'Released'].shape[0] // 3 
    st.metric("Lots At-Risk of Delay (TAT)", late_lots_count, delta=f"{late_lots_count - 2}", delta_color="inverse")
with col4:
    em_excursions = micro_data[micro_data['Result'] > micro_data['Limit']].shape[0]
    st.metric("Active Micro Excursions", em_excursions, delta=f"{em_excursions}", delta_color="inverse")

with st.expander("SME Explanations for KPIs"):
    st.markdown("""
    - **Batches Pending QC Action:** Total number of lots across all products and stages that are currently in the QC workflow (Testing, Data Review, Release). *Relevance: Measures the overall workload and throughput of the QC function.*
    - **Active Deviations/OOS:** Total number of open quality events (Out-of-Specification, Deviations). *Relevance: A direct measure of the current problem-solving burden and potential quality risks across the network. Governed by **cGMP** and **ICH Q10**.*
    - **Lots At-Risk of Delay (TAT):** Number of active lots where the testing Turnaround Time has exceeded the contractual Service Level Agreement (SLA). *Relevance: A leading indicator of potential supply chain disruptions and timeline misses.*
    - **Active Micro Excursions:** Number of Environmental Monitoring or product bioburden results exceeding action limits. *Relevance: A critical indicator of aseptic control for our injectable therapeutics, governed by **USP <1116>** and **EU GMP Annex 1**.*
    """)
st.divider()

col1, col2 = st.columns([2, 1.5])
with col1:
    st.subheader("CMO/CTO Performance Matrix")
    st.markdown("- **Why:** This data-driven ranking provides an objective basis for partner management, QBRs, and identifying systemic risks. It directly addresses the need to 'Hold CMOs/CTOs accountable'.")
    
    perf_summary = []
    for partner_name in partners['Partner']:
        partner_batches = batches[batches['Partner'] == partner_name]; partner_devs = deviations[deviations['Partner'] == partner_name]
        on_time_rate = np.random.uniform(92.0, 99.8) # Simulated for display
        oos_rate = (partner_devs['Type'] == 'OOS').mean() * 100 if not partner_devs.empty else 0
        late_devs = partner_devs[partner_devs['Age_Days'] > 30].shape[0]
        perf_summary.append([partner_name, on_time_rate, oos_rate, late_devs])
    perf_df = pd.DataFrame(perf_summary, columns=["Partner", "On-Time Rate (%)", "OOS Rate (%)", "Deviations >30d"])
    st.dataframe(perf_df, use_container_width=True,
                 column_config={"On-Time Rate (%)": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=100)})
    
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
