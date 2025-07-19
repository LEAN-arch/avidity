# ==============================================================================
# 🧬 Page 3: Lot Genealogy & CQA Dashboard
#
# ==============================================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

st.set_page_config(
    page_title="Lot Genealogy & CQA",
    page_icon="🧬",
    layout="wide"
)

# --- 1. ROBUST STATE CHECK ---
if 'app_data' not in st.session_state:
    st.error("🚨 Application data not loaded. Please return to the 'Global Command Center' home page to initialize the app.")
    st.stop()

# --- 2. DATA UNPACKING ---
app_data = st.session_state['app_data']
batches_df = app_data['batches']
lot_lineage_df = app_data['lot_lineage']

# --- 3. DYNAMIC CQA TABLE FUNCTION ---
# This function creates the CQA table by pulling data for the specific lots
# involved in the genealogy, rather than generating fake data on the fly.
def create_cqa_cascade_table(dp_lot_id, ds_lot_id):
    """
    Constructs a DataFrame comparing CQAs between a Drug Substance lot and its
    corresponding Drug Product lot.
    """
    try:
        ds_results = batches_df[batches_df['Lot_ID'] == ds_lot_id].iloc[0]
        dp_results = batches_df[batches_df['Lot_ID'] == dp_lot_id].iloc[0]
    except IndexError:
        # If for some reason a lot isn't found, return an empty frame.
        return pd.DataFrame()

    # Define the structure and specifications for the CQA table
    cqa_data = [
        {'CQA': 'Purity by RP-HPLC (%)', 'DS Spec': '≥ 97.0', 'DP Spec': '≥ 97.0', 'DS Result': ds_results['Purity'], 'DP Result': dp_results['Purity']},
        {'CQA': 'Aggregate Content (%)', 'DS Spec': '≤ 2.0', 'DP Spec': '≤ 2.5', 'DS Result': ds_results['Aggregate_Content'], 'DP Result': dp_results['Aggregate_Content']},
        {'CQA': 'Main Impurity Peak (%)', 'DS Spec': 'Report', 'DP Spec': '≤ 1.5', 'DS Result': ds_results['Main_Impurity'], 'DP Result': dp_results['Main_Impurity']},
    ]
    cqa_df = pd.DataFrame(cqa_data)

    # Add a status column based on a simple trend rule
    def get_trend_status(row):
        if row['CQA'] == 'Aggregate Content (%)' and row['DP Result'] > row['DS Result'] + 0.2:
            return "⚠️ Trending High"
        elif row['CQA'] == 'Purity by RP-HPLC (%)' and row['DP Result'] < row['DS Result'] - 0.2:
            return "⚠️ Trending Low"
        return "✅ In Trend"
    
    cqa_df['Status'] = cqa_df.apply(get_trend_status, axis=1)
    
    return cqa_df

# --- 4. UI RENDER ---
st.markdown("# 🧬 Lot Genealogy & CQA Dashboard")
st.markdown("This dashboard provides a holistic, lot-centric view of the manufacturing process, tracking the propagation of **Critical Quality Attributes (CQAs)** from intermediates to final Drug Product. This is a key tool for CMC team reviews and regulatory submissions.")

product_list = sorted(batches_df['Product'].unique())
selected_product = st.selectbox("Select a Product Program to View", product_list)

# Filter for final Drug Product lots of the selected program
filtered_dp_lots = batches_df[(batches_df['Product'] == selected_product) & (batches_df['Stage'] == 'Drug Product')]

if filtered_dp_lots.empty:
    st.warning(f"No Drug Product lots found for the {selected_product} program in the current dataset.")
    st.stop()

# Let user select a specific DP lot to view
selected_dp_lot_id = st.selectbox("Select a Drug Product Lot to Analyze", filtered_dp_lots['Lot_ID'].unique())
selected_dp_lot = filtered_dp_lots[filtered_dp_lots['Lot_ID'] == selected_dp_lot_id].iloc[0]

st.header(f"Genealogy for Drug Product Lot: `{selected_dp_lot_id}`")

# --- SANKEY DIAGRAM VISUALIZATION (NOW FUNCTIONAL) ---
st.subheader("Manufacturing & Testing Flow")
st.caption("This Sankey diagram visualizes the flow of materials through the external network for this specific lot, highlighting the partners involved at each critical stage.")

try:
    # Trace the lineage using the now-available lot_lineage_df
    ds_lot_id = lot_lineage_df[lot_lineage_df['child_lot'] == selected_dp_lot_id]['parent_lot'].iloc[0]
    
    # Find the parents of the Drug Substance lot
    ds_parents = lot_lineage_df[lot_lineage_df['child_lot'] == ds_lot_id]['parent_lot'].tolist()
    mab_lot_id = next((lot for lot in ds_parents if 'Antibody' in lot), "N/A")
    oligo_lot_id = next((lot for lot in ds_parents if 'Oligo' in lot), "N/A")

    # Define the nodes (stages) and links (flow) for the diagram
    labels = [
        f'Antibody Lot ({mab_lot_id.split("-")[-1]})',
        f'Oligo Lot ({oligo_lot_id.split("-")[-1]})',
        f'Drug Substance ({ds_lot_id.split("-")[-1]})',
        f'Drug Product ({selected_dp_lot_id.split("-")[-1]})',
        'Final QC Release'
    ]
    colors = ['#003f5c', '#003f5c', '#444e86', '#955196', '#dd5182']
    
    fig = go.Figure(data=[go.Sankey(
        node=dict(pad=20, thickness=25, line=dict(color="black", width=0.5), label=labels, color=colors),
        link=dict(
            source=[0, 1, 2, 3],  # From: Antibody, Oligo, DS, DP
            target=[2, 2, 3, 4],  # To:   DS, DS, DP, QC
            value=[10, 10, 10, 10] # Dummy values for thickness
        )
    )])
    fig.update_layout(height=300, margin=dict(l=10, r=10, t=25, b=25))
    st.plotly_chart(fig, use_container_width=True)

    # --- CQA CASCADE TABLE (NOW FUNCTIONAL) ---
    st.subheader("Critical Quality Attribute (CQA) Cascade")
    st.markdown("- **Why (Actionability):** By tracking CQAs through the process, we can understand the impact of manufacturing on final product quality. The 'Trending' status is a clear, data-driven action item. \n- **Regulatory:** This table is a simplified version of what would be included in the **CMC section of an IND or BLA filing**, as per **ICH Q8**.")
    
    # We now call our new helper function that uses real data.
    cqa_cascade_df = create_cqa_cascade_table(selected_dp_lot_id, ds_lot_id)

    if not cqa_cascade_df.empty:
        st.dataframe(
            cqa_cascade_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "CQA": st.column_config.TextColumn("Critical Quality Attribute", width="large"),
                "DS Spec": st.column_config.TextColumn("DS Spec"),
                "DP Spec": st.column_config.TextColumn("DP Spec"),
                "DS Result": st.column_config.NumberColumn("Drug Substance Result", format="%.2f"),
                "DP Result": st.column_config.NumberColumn("Drug Product Result", help="Final Drug Product release result", format="%.2f"),
                "Status": st.column_config.TextColumn("Trend Status", width="medium")
            }
        )
    else:
        st.error("Could not retrieve CQA data for the linked lots.")

except (IndexError, KeyError, StopIteration):
    # This block will now only catch genuine cases of incomplete data in the model.
    st.error(f"Could not construct the full lineage for lot `{selected_dp_lot_id}`. Data may be incomplete in the source system.", icon="🕸️")
