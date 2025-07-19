import streamlit as st
import pandas as pd
import plotly.express as px

# --- ROBUST STATE CHECK ---
if 'app_data' not in st.session_state:
    st.error("Application data not loaded. Please return to the 'Global Command Center' home page to initialize the app.")
    st.stop()

# Unpack data from the central session state
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
        # Filter deviations for the current stage from the session state data
        devs_in_stage = deviations[deviations['Status'] == stage]
        for index, dev in devs_in_stage.iterrows():
            age = dev['Age_Days']
            # Color-code cards by age to visually flag overdue items
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
    st.markdown("- **Why (Actionability):** This Pareto chart is a powerful tool for continuous improvement per **ICH Q10**. By identifying the most frequent root causes for Out-of-Specification results (the 'vital few,' like Analyst Error), we can focus our systemic improvement efforts (e.g., targeted training programs) for the greatest impact across the entire network.")
    
    # Simulate root cause data for demonstration
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
    st.markdown("- **Why (Actionability):** This histogram tracks our team's and partners' efficiency in closing quality events. A long tail on this chart (many events taking > 30 days) indicates a bottleneck in our investigation process. This data can be used to justify additional resources or process improvements to accelerate lot release and protect clinical supply timelines.")
    
    # Use the 'deviations' DataFrame from session state for the chart
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
    product_select_reg = st.selectbox("Select Product for Report", sorted(batches['Product'].unique()))
    # Default date range for demonstration
    start_date = batches['Date_Created'].min().date()
    end_date = batches['Date_Created'].max().date()
    date_range_reg = st.date_input("Select Date Range", [start_date, end_date])

with reg_col2:
    if st.button("Generate Regulatory Data Summary"):
        # Ensure the date range is valid
        if len(date_range_reg) == 2:
            # Filter data based on selection
            filtered_batches = batches[
                (batches['Product'] == product_select_reg) & 
                (batches['Date_Created'].dt.date >= date_range_reg[0]) & 
                (batches['Date_Created'].dt.date <= date_range_reg[1])
            ]
            
            # Filter deviations based on the lots found in the filtered batches
            relevant_lot_ids = filtered_batches['Lot_ID'].unique()
            filtered_devs = deviations[deviations['Lot_ID'].isin(relevant_lot_ids)]

            st.subheader(f"Data Summary for {product_select_reg}")
            st.markdown(f"**Lots within Date Range:** `{filtered_batches.shape[0]}`")
            st.markdown(f"**Lots Released:** `{filtered_batches[filtered_batches['Status'] == 'Released'].shape[0]}`")
            st.markdown(f"**Associated Deviations/OOS:** `{filtered_devs.shape[0]}`")
            
            st.markdown("##### Batches in Period:")
            st.dataframe(filtered_batches[['Lot_ID', 'Stage', 'Partner', 'Status']], use_container_width=True)

            if not filtered_devs.empty:
                st.markdown("##### Associated Deviations in Period:")
                st.dataframe(filtered_devs[['Deviation_ID', 'Lot_ID', 'Partner', 'Type', 'Status']], use_container_width=True)
        else:
            st.warning("Please select a valid date range.")
