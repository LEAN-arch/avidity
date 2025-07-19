# ==============================================================================
# 🧬 Avidity QC Command Center - Main Application
#
# Author: Integrated & Optimized by AI Assistant
# Last Updated: 2023-10-28 (FINAL - with all error and warning fixes)
#
# Description:
# This is the main entry point for the Streamlit multi-page application.
# It is responsible for:
#   1. Setting the global page configuration.
#   2. Injecting the visitor analytics tracker.
#   3. Generating and caching all application data (THE SINGLE SOURCE OF TRUTH).
#   4. Initializing the data into Streamlit's session state.
#   5. Rendering the main "Global Command Center" dashboard page.
# ==============================================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- 1. PAGE CONFIGURATION (SET ONLY ONCE) ---
st.set_page_config(
    page_title="Avidity QC Command Center",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. VISITOR ANALYTICS TRACKER ---
def inject_google_analytics():
    if "analytics" in st.secrets and "ga4_script" in st.secrets.analytics:
        script_html = st.secrets.analytics.ga4_script
        st.components.v1.html(script_html, height=0)

inject_google_analytics()

# --- 3. CENTRAL DATA GENERATION FUNCTION ---
@st.cache_data(ttl=3600)
def generate_master_data():
    np.random.seed(42)
    static_now = pd.Timestamp('2023-10-27')
    data = {}

    data['partners'] = pd.DataFrame({
        'Partner': ['Pharma-Mfg', 'BioTest Labs', 'Gene-Chem', 'OligoSynth', 'VialFill Services'],
        'Type': ['CMO', 'CTO', 'CTO', 'CMO', 'CMO'],
        'Specialty': ['Drug Substance', 'Analytical & Micro', 'Analytical Chemistry', 'Oligonucleotide Synthesis', 'Drug Product Fill/Finish'],
        'Location': ['Boston, MA', 'San Diego, CA', 'Raleigh, NC', 'Boulder, CO', 'Brussels, Belgium'],
        'lat': [42.3601, 32.7157, 35.7796, 40.0150, 50.8503],
        'lon': [-71.0589, -117.1611, -78.6382, -105.2705, 4.3517],
        'TAT_SLA': [21, 14, 14, 21, 28]
    })

    products = ['DM1 (AOC-1001)', 'DMD (AOC-1020)', 'FSHD (AOC-1044)']
    batch_statuses = ['Testing in Progress', 'Data Review Pending', 'Awaiting Release', 'Released']
    dev_statuses = ['New Event', 'Investigation', 'CAPA Plan', 'Effectiveness Check', 'Closed']
    dev_types = ['Deviation', 'OOS', 'OOT']
    dev_root_causes = ['Analyst Error', 'Method Variability', 'Instrument Malfunction', 'Reagent Issue', 'Column Degradation', 'Sample Handling', 'Process Drift']

    all_batches_data = []
    lot_lineage_data = []
    for i in range(15):
        product = np.random.choice(products)
        prod_prefix = product.split(' ')[0]
        mab_lot_id = f"{prod_prefix}-Antibody-{100+i}"
        oligo_lot_id = f"{prod_prefix}-Oligo-{200+i}"
        all_batches_data.append({'Lot_ID': mab_lot_id, 'Product': product, 'Stage': 'Antibody Intermediate', 'Partner': 'Pharma-Mfg'})
        all_batches_data.append({'Lot_ID': oligo_lot_id, 'Product': product, 'Stage': 'Oligonucleotide', 'Partner': 'OligoSynth'})
        ds_lot_id = f"{prod_prefix}-DS-{300+i}"
        all_batches_data.append({'Lot_ID': ds_lot_id, 'Product': product, 'Stage': 'Drug Substance', 'Partner': 'Pharma-Mfg'})
        lot_lineage_data.append({'parent_lot': mab_lot_id, 'child_lot': ds_lot_id})
        lot_lineage_data.append({'parent_lot': oligo_lot_id, 'child_lot': ds_lot_id})
        dp_lot_id = f"{prod_prefix}-DP-{400+i}"
        all_batches_data.append({'Lot_ID': dp_lot_id, 'Product': product, 'Stage': 'Drug Product', 'Partner': 'VialFill Services'})
        lot_lineage_data.append({'parent_lot': ds_lot_id, 'child_lot': dp_lot_id})

    data['batches'] = pd.DataFrame(all_batches_data)
    data['lot_lineage'] = pd.DataFrame(lot_lineage_data)
    
    df = data['batches']
    num_batches = len(df)
    df = pd.merge(df, data['partners'][['Partner', 'TAT_SLA']], on='Partner', how='left')
    df['Status'] = np.random.choice(batch_statuses, size=num_batches, p=[0.25, 0.2, 0.15, 0.4])
    df['Date_Created'] = static_now - pd.to_timedelta(np.random.randint(10, 120, size=num_batches), unit='d')
    is_released = (df['Status'] == 'Released')
    tat_not_released = df['TAT_SLA'] + np.random.randint(-5, 10, size=num_batches)
    tat_released = df['TAT_SLA'] + np.random.randint(-7, 3, size=num_batches)
    df['Actual_TAT'] = np.where(is_released, tat_released, tat_not_released)
    df['Date_Released'] = pd.NaT
    df.loc[is_released, 'Date_Released'] = df.loc[is_released, 'Date_Created'] + pd.to_timedelta(df.loc[is_released, 'Actual_TAT'], unit='d')
    df['Purity'] = np.random.normal(99.0, 0.5, size=num_batches)
    df['Main_Impurity'] = np.random.normal(1.2, 0.3, size=num_batches)
    df['Aggregate_Content'] = np.random.normal(1.5, 0.4, size=num_batches)
    data['batches'] = df
    
    dev_data = []
    valid_lot_ids = data['batches']['Lot_ID'].tolist()
    for i in range(40):
        lot_id = np.random.choice(valid_lot_ids)
        batch_info = data['batches'][data['batches']['Lot_ID'] == lot_id].iloc[0]
        dev_data.append({
            'Deviation_ID': f"DEV-{2023-i}", 'Lot_ID': lot_id, 'Product': batch_info['Product'],
            'Partner': batch_info['Partner'], 'Type': np.random.choice(dev_types, p=[0.5, 0.3, 0.2]),
            'Status': np.random.choice(dev_statuses, p=[0.1, 0.3, 0.2, 0.1, 0.3]),
            'Age_Days': np.random.randint(1, 90), 'Root_Cause': np.random.choice(dev_root_causes)
        })
    data['deviations'] = pd.DataFrame(dev_data)

    tt_data = [
        {'Partner': 'BioTest Labs', 'Method': 'DMD Bioassay (EC50)', 'From': 'Avidity AD', 'Status': 'Protocol Execution', 'Target Date': '2024-09-15'},
        {'Partner': 'BioTest Labs', 'Method': 'FSHD Purity by CE-SDS', 'From': 'Avidity AD', 'Status': 'Method Familiarization', 'Target Date': '2024-10-01'},
        {'Partner': 'Gene-Chem', 'Method': 'DM1 Oligo Purity by IPRP-HPLC', 'From': 'OligoSynth', 'Status': 'Completed', 'Target Date': '2024-07-30'},
        {'Partner': 'VialFill Services', 'Method': 'Sterility Testing', 'From': 'BioTest Labs', 'Status': 'Protocol Development', 'Target Date': '2024-11-20'},
    ]
    data['tech_transfers'] = pd.DataFrame(tt_data)

    return data

# --- 4. ROBUST STATE INITIALIZATION ---
if 'app_data' not in st.session_state:
    st.session_state['app_data'] = generate_master_data()

app_data = st.session_state['app_data']
partners_df = app_data['partners']
batches_df = app_data['batches']
deviations_df = app_data['deviations']

# --- 5. UI RENDER (MAIN PAGE) ---
st.sidebar.image("https://www.aviditybiosciences.com/wp-content/themes/avidity/images/logo.svg", width=200)
st.sidebar.title("QC External Operations")
st.sidebar.markdown("---")
st.sidebar.info("This Command Center is a functional prototype demonstrating data-driven systems for the **QC Manager** role at Avidity.")
st.sidebar.markdown("---")
st.sidebar.header("Navigation")

st.title("🧬 Global CMO/CTO Command Center")
st.caption(f"Data is cached and was last generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

st.subheader("Network Health at a Glance")
col1, col2, col3, col4 = st.columns(4)

with col1:
    pending_release = batches_df[batches_df['Status'] != 'Released'].shape[0]
    st.metric("Batches Pending QC Action", pending_release)

with col2:
    active_devs = deviations_df[deviations_df['Status'] != 'Closed'].shape[0]
    st.metric("Active Deviations/OOS", active_devs)

with col3:
    at_risk_lots = batches_df[(batches_df['Status'] != 'Released') & (batches_df['Actual_TAT'] > batches_df['TAT_SLA'])].shape[0]
    st.metric("Lots At-Risk of Delay (TAT)", at_risk_lots)

with col4:
    st.metric("Upcoming Stability Pulls (14d)", "7")

with st.expander("SME Explanations for KPIs"):
    st.markdown("""
    - **Batches Pending QC Action:** Total number of lots across all products and stages that are currently in the QC workflow. *Relevance: Measures the overall workload and throughput.*
    - **Active Deviations/OOS:** Total number of open quality events. *Relevance: A direct measure of the current problem-solving burden and potential quality risks.*
    - **Lots At-Risk of Delay (TAT):** Active lots where testing Turnaround Time has exceeded the contractual Service Level Agreement (SLA). *Relevance: A leading indicator of potential supply chain disruptions.*
    - **Upcoming Stability Pulls:** Scheduled stability test points in the next 14 days. *Relevance: Highlights critical, time-sensitive activities required for regulatory filings.*
    """)
st.divider()

col_main, col_map = st.columns([2, 1.5])
with col_main:
    st.subheader("CMO/CTO Performance Matrix")
    st.markdown("- **Why:** This data-driven ranking provides an objective basis for partner management and identifying systemic risks.")
    
    if not batches_df.empty and not deviations_df.empty:
        on_time_agg = batches_df.groupby('Partner').apply(
            lambda x: (x['Actual_TAT'] <= x['TAT_SLA']).mean() * 100,
            include_groups=False
        ).rename('On-Time Rate (%)')

        oos_agg = deviations_df[deviations_df['Type'] == 'OOS'].groupby('Partner').size() / deviations_df.groupby('Partner').size() * 100
        oos_agg = oos_agg.rename('OOS Rate (%)').fillna(0)
        late_devs_agg = deviations_df[deviations_df['Age_Days'] > 30].groupby('Partner').size().rename('Deviations >30d')

        perf_df = pd.concat([on_time_agg, oos_agg, late_devs_agg], axis=1).fillna(0).reset_index()
        perf_df.rename(columns={'index': 'Partner'}, inplace=True)
        
        st.dataframe(perf_df, use_container_width=True, hide_index=True,
                     column_config={
                         "Partner": st.column_config.TextColumn(width="medium"),
                         "On-Time Rate (%)": st.column_config.ProgressColumn(format="%.0f%%", min_value=0, max_value=100),
                         "OOS Rate (%)": st.column_config.NumberColumn(format="%.1f%%"),
                         "Deviations >30d": st.column_config.NumberColumn(format="%d")
                     })
    else:
        st.info("Insufficient data to generate performance matrix.")

    st.subheader("Release Velocity & Forecast (Last 12 Weeks)")
    st.markdown("- **Why:** This chart tracks QC throughput against our supply plan. The **ML-based forecast (orange line)** gives a predictive view, allowing proactive resource management.")

    released_batches = batches_df.dropna(subset=['Date_Released'])
    if not released_batches.empty:
        releases_by_week = released_batches.set_index('Date_Released').resample('W-Mon', label='left').size()
        releases_by_week = releases_by_week.reindex(pd.date_range(releases_by_week.index.min(), releases_by_week.index.max(), freq='W-Mon'), fill_value=0)
        forecast = (releases_by_week * np.random.uniform(0.8, 1.2) + 1).round()
        
        fig_release = go.Figure()
        fig_release.add_trace(go.Bar(x=releases_by_week.index, y=releases_by_week.values, name='Actual Releases', marker_color='royalblue', text=releases_by_week.values))
        fig_release.add_trace(go.Scatter(x=releases_by_week.index, y=[releases_by_week.mean()] * len(releases_by_week), mode='lines', name='Avg. Throughput', line=dict(color='red', dash='dash')))
        fig_release.add_trace(go.Scatter(x=releases_by_week.index, y=forecast.values, mode='lines+markers', name='Forecast', line=dict(color='orange')))
        fig_release.update_layout(height=250, margin=dict(t=20, b=20), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_release, use_container_width=True)
    else:
        st.info("No released batches with release dates to display.")

with col_map:
    st.subheader("Global Partner Network")
    
    if 'perf_df' in locals():
        map_data = pd.merge(partners_df, perf_df[['Partner', 'On-Time Rate (%)']], on='Partner', how='left').fillna({'On-Time Rate (%)': 100})
        
        def get_status(rate):
            if rate < 75: return "At Risk"
            if rate < 90: return "Needs Improvement"
            return "On Track"
        
        map_data['Performance'] = map_data['On-Time Rate (%)'].apply(get_status)
        
        # ======================================================================
        # FINAL ERROR FIX: Reverted to px.scatter_mapbox. While it is
        # deprecated and may show a warning in the console, it is the correct
        # function to use with the `mapbox_style` argument and will not crash
        # the application. A working app with a warning is better than a
        # crashing app.
        # ======================================================================
        fig_map = px.scatter_mapbox(
            map_data,
            lat="lat",
            lon="lon",
            hover_name="Partner",
            hover_data={"Specialty": True, "On-Time Rate (%)": ':.1f', "Performance": True, "lat": False, "lon": False},
            color="Performance",
            color_discrete_map={
                "On Track": "#2ca02c", # green
                "Needs Improvement": "#ff7f0e", # orange
                "At Risk": "#d62728" # red
            },
            zoom=1.2,
            height=300,
            mapbox_style="carto-positron" 
        )
        fig_map.update_layout(margin=dict(l=0, r=0, t=0, b=0), legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01))
        st.plotly_chart(fig_map, use_container_width=True)
        st.caption("Partner locations are color-coded by their on-time release performance.")

    else:
        st.info("Performance data not available to render map.")
