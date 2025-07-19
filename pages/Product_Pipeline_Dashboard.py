import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- ROBUST STATE CHECK ---
if 'app_data' not in st.session_state:
    st.error("Application data not loaded. Please return to the 'Global Command Center' home page to initialize the app.")
    st.stop()

# Unpack data
app_data = st.session_state['app_data']
batches = app_data['batches']

# --- UI RENDER ---
st.markdown("# 🧬 Lot Genealogy & CQA Dashboard")
st.markdown("This dashboard provides a holistic, lot-centric view of the manufacturing process, tracking the propagation of **Critical Quality Attributes (CQAs)** from intermediates to final Drug Product. This is a key tool for CMC team reviews and regulatory submissions.")

product_list = batches['Product'].unique()
selected_product = st.selectbox("Select a Product Program to View", product_list, index=0)

# --- CORRECTED LOGIC FOR IndexError ---
filtered_lots = batches[(batches['Product'] == selected_product) & (batches['Stage'] == 'Drug Product')]
if filtered_lots.empty:
    st.warning(f"No Drug Product lots found for the {selected_product} program in the current dataset.")
    st.stop()  # Gracefully exit if no data to show

latest_dp_lot = filtered_lots.sort_values('Date_Created', ascending=False).iloc[0]

st.header(f"Genealogy for Drug Product Lot: `{latest_dp_lot['Lot_ID']}`")

st.subheader("Manufacturing & Testing Flow")
st.caption("This Sankey diagram visualizes the flow of materials through the external network for this specific lot, highlighting the partners involved at each critical stage.")
fig = go.Figure(data=[go.Sankey(
    node = dict(
        pad=15, thickness=20, line=dict(color="black", width=0.5),
        label=['Antibody Intermediate (Pharma-Mfg)', 'Oligonucleotide (OligoSynth)', 'Drug Substance (Pharma-Mfg)', 'Drug Product (VialFill)', 'QC Testing (BioTest Labs)', 'QC Testing (Gene-Chem)'],
        color=['#003f5c', '#003f5c', '#444e86', '#955196', '#dd5182', '#ff6e54']
    ),
    link = dict(
        source=[0, 1, 2, 2, 3], 
        target=[2, 2, 4, 5, 4], 
        value=[10, 10, 6, 4, 10]
    ))])
fig.update_layout(height=300, margin=dict(l=0, r=0, t=25, b=25))
st.plotly_chart(fig, use_container_width=True)

st.subheader("Critical Quality Attribute (CQA) Cascade")
st.markdown("""
- **What:** A summary of key CQAs for this batch, showing results at each stage of manufacturing. CQAs are physical, chemical, biological, or microbiological attributes that must be within an appropriate limit to ensure product quality.
- **Why (Actionability):** This is the core of a data-driven QC and CMC strategy. By tracking CQAs through the process, we can understand the impact of **Critical Process Parameters (CPPs)** at each CMO on the final product quality. The 'Trending High' status for Aggregates is a clear, data-driven action item for the process development team.
- **Regulatory:** This table is a simplified version of what would be included in the **CMC section of an IND or BLA filing**, as per **ICH Q8 (Pharmaceutical Development)**.
""")

# --- CORRECTED LOGIC FOR ArrowInvalid Error ---
# Data is now stored with numeric types. Display formatting is handled by Streamlit.
cqa_data = [
    {'CQA': 'Purity by RP-HPLC (%)', 'Intermediate Spec': '≥ 98.0', 'DS Spec': '≥ 97.0', 'DP Spec': '≥ 97.0', 'DS Result': 98.1, 'DP Result': 97.8, 'Status': '✅ In Trend'},
    {'CQA': 'Conjugation Efficiency (%)', 'Intermediate Spec': 'N/A', 'DS Spec': 'Report', 'DP Spec': 'Report', 'DS Result': 92.5, 'DP Result': 92.3, 'Status': '✅ In Trend'},
    {'CQA': 'Aggregate Content (%)', 'Intermediate Spec': '≤ 1.0', 'DS Spec': '≤ 2.0', 'DP Spec': '≤ 2.5', 'DS Result': 1.5, 'DP Result': 2.2, 'Status': '⚠️ Trending High'},
    {'CQA': 'Bioactivity (EC50, nM)', 'Intermediate Spec': 'N/A', 'DS Spec': 'Report', 'DP Spec': '≤ 10.0', 'DS Result': 4.5, 'DP Result': 4.8, 'Status': '✅ In Trend'},
    {'CQA': 'Endotoxin (EU/mL)', 'Intermediate Spec': 'N/A', 'DS Spec': '≤ 5.0', 'DP Spec': '≤ 2.5', 'DS Result': 0.4, 'DP Result': 0.3, 'Status': '✅ In Trend'}
]
cqa_df = pd.DataFrame(cqa_data)

st.dataframe(
    cqa_df,
    use_container_width=True,
    column_config={
        "DS Result": st.column_config.NumberColumn(
            "Drug Substance Result",
            format="%.1f",
        ),
        "DP Result": st.column_config.NumberColumn(
            "Drug Product Result",
            help="Final Drug Product release result",
            format="%.1f",
        ),
        "Status": st.column_config.TextColumn(
            "Trend Status",
            width="medium"
        )
    }
)
