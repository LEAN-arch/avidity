import streamlit as st
import pandas as pd
import plotly.express as px

# --- ROBUST STATE CHECK ---
if 'app_data' not in st.session_state:
    st.error("Application data not loaded. Please return to the 'Global Command Center' home page to initialize the app.")
    st.stop()

# Unpack data
app_data = st.session_state['app_data']
deviations = app_data['deviations']
batches = app_data['batches']

# --- UI RENDER ---
st.markdown("# 🗂️ Deviation & CAPA Management Hub")
st.markdown("This module provides a central workspace for managing quality events across the entire CMO/CTO network and for identifying systemic opportunities for improvement.")

st.header("Deviation Workflow (Kanban Board)")
st.caption("This board provides a visual representation of all active investigations, helping to manage workload, identify bottlenecks, and ensure timely closure of quality events.")
stages = ['New Event', 'Investigation', 'CAPA Plan', 'Effectiveness Check', 'Closed']
cols = st.columns(len(stages))
for i, stage in enumerate(stages):
    with cols[i]:
        st.subheader(stage)
        devs_in_stage = deviations[deviations['Status'] == stage]
        for index, dev in devs_in_stage.iterrows():
            age = dev['Age_Days']
            if age > 30:
                st.error(f"**{dev['Deviation_ID']}**\n{dev['Partner']}\n`{age} days`")
            elif age > 15:
                st.warning(f"**{dev['Deviation_ID']}**\n{dev['Partner']}\n`{age} days`")
            else:
                with st.container(border=True):
                    st.markdown(f"**{dev['Deviation_ID']}**")
                    st.caption(f"{dev['Partner']}")
                    st.caption(f"`{age} days`")
st.divider()

col1, col2 = st.columns(2)
with col1:
    st.header("Actionable Analytics")
    st.subheader("OOS Root Cause Pareto Chart")
    st.markdown("- **Why (Actionability):** This Pareto chart is a powerful tool for continuous improvement per **ICH Q10**. By identifying the most frequent root causes for OOS results (the 'vital few'), we can focus our systemic improvement efforts for the greatest impact across the entire network.")
    rc_data = pd.DataFrame({
        'Root Cause': ['Analyst Error', 'Method Variability', 'Instrument Malfunction', 'Reagent Issue', 'Column Degradation', 'Sample Handling'],
        'Count': [12, 8, 5, 3, 2, 1]
    })
    fig_rc = px.bar(rc_data, x="Count", y="Root Cause", orientation='h', title="OOS Investigations by Root Cause", color="Count", color_continuous_scale=px.colors.sequential.Reds)
    fig_rc.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_rc, use_container_width=True)
with col2:
    st.header("Process Efficiency")
    st.subheader("Deviation Closure Cycle Time")
    st.markdown("- **Why (Actionability):** This histogram tracks our team's and partners' efficiency in closing quality events. A long tail on this chart (many events > 30 days) indicates a bottleneck in our investigation process, which can delay lot release and put clinical supply timelines at risk.")
    fig_cycle = px.histogram(deviations[deviations['Status'] == 'Closed'], x="Age_Days", nbins=10, title="Cycle Time for Closed Deviations", color_discrete_sequence=['#dd5182'])
    fig_cycle.add_vline(x=30, line_dash="dash", line_color="red", annotation_text="30-Day Target")
    st.plotly_chart(fig_cycle, use_container_width=True)

st.divider()

st.header("CMC Regulatory Support")
st.markdown("""
- **What:** A tool to collate all relevant QC data for a specific product over a defined period.
- **Why (Actionability):** This directly supports the **"Assist in the preparation of CMC regulatory submissions"** responsibility. It automates the tedious process of gathering data for annual reports or for filings like an **IND or BLA**, ensuring data integrity and saving significant time.
""")
reg_col1, reg_col2 = st.columns([1, 3])
with reg_col1:
    product_select_reg = st.selectbox("Select Product for Report", batches['Product'].unique())
    date_range_reg = st.date_input("Select Date Range", [pd.Timestamp('2023-08-01'), pd.Timestamp.now()])
with reg_col2:
    if st.button("Generate Regulatory Data Summary"):
        # Filter data based on selection
        filtered_batches = batches[(batches['Product'] == product_select_reg) & (batches['Date_Created'].dt.date.between(date_range_reg[0], date_range_reg[1]))]
        filtered_devs = deviations[(deviations['Product'] == product_select_reg)]
        st.subheader(f"Data Summary for {product_select_reg}")
        st.markdown(f"**Lots Released:** {filtered_batches[filtered_batches['Status'] == 'Released'].shape[0]}")
        st.markdown(f"**Associated Deviations/OOS:** {filtered_devs.shape[0]}")
        st.dataframe(filtered_batches[['Lot_ID', 'Stage', 'Partner', 'Status']], use_container_width=True)
