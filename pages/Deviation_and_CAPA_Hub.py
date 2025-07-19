# ==============================================================================
# 🧬 Page 1: Deviation & CAPA Management Hub
#
# ==============================================================================

import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Deviation & CAPA Hub",
    page_icon="🗂️",
    layout="wide"
)

# --- 1. ROBUST STATE CHECK ---
if 'app_data' not in st.session_state:
    st.error("🚨 Application data not loaded. Please return to the 'Global Command Center' home page to initialize the app.")
    st.stop()

# --- 2. DATA UNPACKING ---
app_data = st.session_state['app_data']
deviations_df = app_data['deviations']
batches_df = app_data['batches']

# --- 3. UI RENDER ---
st.markdown("# 🗂️ Deviation & CAPA Management Hub")
st.markdown("This module provides a central workspace for managing quality events across the entire CMO/CTO network and for identifying systemic opportunities for improvement.")

st.header("Deviation Workflow (Kanban Board)")
st.caption("This board provides a visual representation of all active investigations, helping to manage workload, identify bottlenecks, and ensure timely closure of quality events.")

stages = ['New Event', 'Investigation', 'CAPA Plan', 'Effectiveness Check', 'Closed']
cols = st.columns(len(stages))

grouped_devs = {status: group for status, group in deviations_df.groupby('Status')}

for i, stage in enumerate(stages):
    with cols[i]:
        count = len(grouped_devs.get(stage, []))
        st.subheader(f"{stage} ({count})")
        
        devs_in_stage = grouped_devs.get(stage, pd.DataFrame())

        for dev in devs_in_stage.to_dict('records'):
            age = dev['Age_Days']
            
            # ======================================================================
            # DEFINITIVE TypeError FIX: st.error() and st.warning() are not
            # context managers and cannot be used with a 'with' statement. They
            # are direct functions that take the message body as an argument.
            # This corrected logic passes the formatted string directly to them,
            # which is the correct usage and resolves the crash.
            # ======================================================================
            if age > 60:
                card_body = f"""
                **{dev['Deviation_ID']}** 🚨\n
                {dev['Partner']}\n
                `{age} days old`
                """
                st.error(card_body)
            elif age > 30:
                card_body = f"""
                **{dev['Deviation_ID']}** ⚠️\n
                {dev['Partner']}\n
                `{age} days old`
                """
                st.warning(card_body)
            else:
                # st.container is a context manager and is used correctly here.
                with st.container(border=True):
                    st.markdown(f"**{dev['Deviation_ID']}**")
                    st.caption(f"{dev['Partner']}")
                    st.caption(f"`{age} days old`")
st.divider()

# --- ANALYTICS SECTION ---
col1, col2 = st.columns(2)
with col1:
    st.header("Actionable Analytics")
    st.subheader("OOS Root Cause Pareto Chart")
    st.markdown("- **Why (Actionability):** This Pareto chart is a powerful tool for continuous improvement per **ICH Q10**. By identifying the most frequent root causes, we can focus our systemic improvement efforts for the greatest impact.")

    oos_devs = deviations_df[deviations_df['Type'] == 'OOS']
    if not oos_devs.empty:
        rc_counts = oos_devs['Root_Cause'].value_counts().reset_index()
        rc_counts.columns = ['Root Cause', 'Count']
        
        fig_rc = px.bar(
            rc_counts, x="Count", y="Root Cause", orientation='h',
            title="OOS Investigations by Root Cause", color="Count",
            color_continuous_scale=px.colors.sequential.Reds
        )
        fig_rc.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_rc, use_container_width=True)
    else:
        st.info("No OOS deviations recorded to generate a root cause analysis.")

with col2:
    st.header("Process Efficiency")
    st.subheader("Deviation Closure Cycle Time")
    st.markdown("- **Why (Actionability):** This histogram tracks efficiency in closing quality events. A long tail indicates bottlenecks, justifying process improvements or additional resources to protect timelines.")
    
    closed_devs = deviations_df[deviations_df['Status'] == 'Closed']
    if not closed_devs.empty:
        fig_cycle = px.histogram(
            closed_devs, x="Age_Days", nbins=10,
            title="Cycle Time for Closed Deviations", color_discrete_sequence=['#dd5182']
        )
        fig_cycle.add_vline(x=30, line_dash="dash", line_color="red", annotation_text="30-Day Target")
        st.plotly_chart(fig_cycle, use_container_width=True)
    else:
        st.info("No closed deviations to analyze cycle time.")

st.divider()

# --- REGULATORY SUPPORT TOOL SECTION ---
st.header("CMC Regulatory Support")
st.markdown("""
- **What:** A tool to collate all relevant QC data for a specific product over a defined period.
- **Why (Actionability):** This directly supports the **"Assist in the preparation of CMC regulatory submissions"** responsibility. It automates the tedious process of gathering data for annual reports or filings, ensuring data integrity and saving significant time.
""")
reg_col1, reg_col2 = st.columns([1, 3])
with reg_col1:
    product_select_reg = st.selectbox("Select Product for Report", batches_df['Product'].unique())
    
    min_date = batches_df['Date_Created'].min().date()
    max_date = batches_df['Date_Created'].max().date()
    date_range_reg = st.date_input("Select Date Range", [min_date, max_date])

with reg_col2:
    if st.button("Generate Regulatory Data Summary"):
        if len(date_range_reg) == 2:
            start_date, end_date = date_range_reg
            
            start_ts = pd.to_datetime(start_date)
            end_ts = pd.to_datetime(end_date) + pd.Timedelta(days=1)

            filtered_batches = batches_df[
                (batches_df['Product'] == product_select_reg) &
                (batches_df['Date_Created'] >= start_ts) &
                (batches_df['Date_Created'] < end_ts)
            ]
            
            if not filtered_batches.empty:
                relevant_lot_ids = filtered_batches['Lot_ID'].unique()
                filtered_devs = deviations_df[deviations_df['Lot_ID'].isin(relevant_lot_ids)]

                st.subheader(f"Data Summary for {product_select_reg}")
                st.markdown(f"**Lots within Date Range:** `{filtered_batches.shape[0]}`")
                st.markdown(f"**Lots Released:** `{filtered_batches[filtered_batches['Status'] == 'Released'].shape[0]}`")
                st.markdown(f"**Associated Deviations/OOS:** `{filtered_devs.shape[0]}`")
                
                st.markdown("##### Batches in Period:")
                st.dataframe(filtered_batches[['Lot_ID', 'Stage', 'Partner', 'Status', 'Date_Created']], use_container_width=True, hide_index=True)

                if not filtered_devs.empty:
                    st.markdown("##### Associated Deviations in Period:")
                    st.dataframe(filtered_devs[['Deviation_ID', 'Lot_ID', 'Partner', 'Type', 'Status']], use_container_width=True, hide_index=True)
            else:
                st.info("No batches found for the selected product and date range.")
        else:
            st.warning("Please select a valid date range.")
