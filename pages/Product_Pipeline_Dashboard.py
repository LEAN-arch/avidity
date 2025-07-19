import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# --- ROBUST STATE CHECK ---
if 'app_data' not in st.session_state:
    st.error("Application data not loaded. Please return to the 'Global Command Center' home page to initialize the app.")
    st.stop()

# Unpack data from the central session state
app_data = st.session_state['app_data']
batches = app_data['batches']
lot_lineage = app_data['lot_lineage']

# --- SME ENHANCEMENT: Dynamic CQA Data Generation ---
@st.cache_data
def generate_cqa_data(product_name, lot_id):
    """Generates realistic and unique CQA data for a specific lot."""
    # Use the lot_id to seed the random number generator for consistency
    seed = int(sum(ord(c) for c in lot_id))
    np.random.seed(seed)
    
    # Base values
    purity_ds = np.random.uniform(97.5, 99.0)
    conjugation_ds = np.random.uniform(91.0, 94.0)
    aggregate_ds = np.random.uniform(1.0, 1.8)
    bioactivity_ds = np.random.uniform(4.0, 6.0)
    endotoxin_ds = np.random.uniform(0.1, 0.5)
    bioburden_ds = np.random.randint(0, 3)

    # Simulate slight changes from Drug Substance (DS) to Drug Product (DP)
    purity_dp = purity_ds - np.random.uniform(0.1, 0.3)
    aggregate_dp = aggregate_ds + np.random.uniform(0.2, 0.4)
    
    cqa_data = [
        {'CQA': 'Purity by RP-HPLC (%)', 'DS Spec': '≥ 97.0', 'DP Spec': '≥ 97.0', 'DS Result': purity_ds, 'DP Result': purity_dp, 'Status': '✅ In Trend'},
        {'CQA': 'Conjugation Efficiency (%)', 'DS Spec': 'Report', 'DP Spec': 'Report', 'DS Result': conjugation_ds, 'DP Result': conjugation_ds - 0.2, 'Status': '✅ In Trend'},
        {'CQA': 'Aggregate Content (%)', 'DS Spec': '≤ 2.0', 'DP Spec': '≤ 2.5', 'DS Result': aggregate_ds, 'DP Result': aggregate_dp, 'Status': '⚠️ Trending High' if aggregate_dp > 2.0 else '✅ In Trend'},
        {'CQA': 'Bioactivity (EC50, nM)', 'DS Spec': 'Report', 'DP Spec': '≤ 10.0', 'DS Result': bioactivity_ds, 'DP Result': bioactivity_ds + 0.3, 'Status': '✅ In Trend'},
        {'CQA': 'Endotoxin (EU/mL)', 'DS Spec': '≤ 5.0', 'DP Spec': '≤ 2.5', 'DS Result': endotoxin_ds, 'DP Result': endotoxin_ds - 0.1, 'Status': '✅ In Trend'},
        {'CQA': 'Bioburden (CFU/10mL)', 'DS Spec': '≤ 10', 'DP Spec': 'N/A (Sterile)', 'DS Result': float(bioburden_ds), 'DP Result': 0.0, 'Status': '✅ In Trend'}
    ]
    return pd.DataFrame(cqa_data)

# --- UI RENDER ---
st.markdown("# 🧬 Lot Genealogy & CQA Dashboard")
st.markdown("This dashboard provides a holistic, lot-centric view of the manufacturing process, tracking the propagation of **Critical Quality Attributes (CQAs)** from intermediates to final Drug Product. This is a key tool for CMC team reviews and regulatory submissions.")

product_list = sorted(batches['Product'].unique())
selected_product = st.selectbox("Select a Product Program to View", product_list, index=0)

# --- CORRECTED LOGIC FOR IndexError ---
filtered_lots = batches[(batches['Product'] == selected_product) & (batches['Stage'] == 'Drug Product')]
if filtered_lots.empty:
    st.warning(f"No Drug Product lots found for the {selected_product} program in the current dataset."); st.stop()

latest_dp_lot = filtered_lots.sort_values('Date_Created', ascending=False).iloc[0]
st.header(f"Genealogy for Drug Product Lot: `{latest_dp_lot['Lot_ID']}`")

# --- DYNAMIC GENEALOGY VISUALIZATION ---
st.subheader("Manufacturing & Testing Flow")
st.caption("This Sankey diagram visualizes the flow of materials through the external network for this specific lot, highlighting the partners involved at each critical stage.")
try:
    ds_lot_id = lot_lineage[lot_lineage['child_lot'] == latest_dp_lot['Lot_ID']]['parent_lot'].iloc[0]
    mab_lot_id = lot_lineage[(lot_lineage['child_lot'] == ds_lot_id) & (lot_lineage['parent_lot'].str.contains('Antibody'))]['parent_lot'].iloc[0]
    oligo_lot_id = lot_lineage[(lot_lineage['child_lot'] == ds_lot_id) & (lot_lineage['parent_lot'].str.contains('Oligo'))]['parent_lot'].iloc[0]
    
    fig = go.Figure(data=[go.Sankey(
        node = dict(pad=15, thickness=20, line=dict(color="black", width=0.5),
            label=[f'Antibody Lot ({mab_lot_id.split("-")[-1]})', f'Oligo Lot ({oligo_lot_id.split("-")[-1]})', f'Drug Substance ({ds_lot_id.split("-")[-1]})', f'Drug Product ({latest_dp_lot["Lot_ID"].split("-")[-1]})', 'QC Testing'],
            color=['#003f5c', '#003f5c', '#444e86', '#955196', '#dd5182']),
        link = dict(source=[0, 1, 2, 3], target=[2, 2, 3, 4], value=[10, 10, 10, 10])
    )])
    fig.update_layout(height=300, margin=dict(l=0, r=0, t=25, b=25))
    st.plotly_chart(fig, use_container_width=True)
except (IndexError, KeyError):
    st.error("Could not construct the full lineage for this lot. Data may be incomplete.")

st.subheader("Critical Quality Attribute (CQA) Cascade")
st.markdown("- **Why (Actionability):** By tracking CQAs through the process, we can understand the impact of **Critical Process Parameters (CPPs)** at each CMO on the final product quality. The 'Trending High' status for Aggregates is a clear, data-driven action item for the process development team. \n- **Regulatory:** This table is a simplified version of what would be included in the **CMC section of an IND or BLA filing**, as per **ICH Q8 (Pharmaceutical Development)**.")

# --- DYNAMIC CQA TABLE ---
cqa_df = generate_cqa_data(selected_product, latest_dp_lot['Lot_ID'])
st.dataframe(
    cqa_df, use_container_width=True,
    column_config={
        "CQA": st.column_config.TextColumn("Critical Quality Attribute", width="large"),
        "DS Result": st.column_config.NumberColumn("Drug Substance Result", format="%.2f"),
        "DP Result": st.column_config.NumberColumn("Drug Product Result", help="Final Drug Product release result", format="%.2f"),
        "Status": st.column_config.TextColumn("Trend Status", width="medium")
    }
)
