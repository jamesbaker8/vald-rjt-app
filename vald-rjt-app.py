import streamlit as st
import pandas as pd
import re

st.title("Jump Test Data Restructuring")
st.write("Upload your Excel file with horizontal-format jump trial data. Row 8: headers, Row 9: trial labels.")

uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx"])

if uploaded_file:
    # Read metadata separately to preserve Test Date accurately
    meta_cols = ['Athlete', 'Athlete Id', 'ExtId', 'Test Type', 'Test Date', 'Body Weight [kg]']
    raw_meta = pd.read_excel(uploaded_file, header=7, usecols=meta_cols)
    
    # Read full sheet with two-level header for metrics
    df = pd.read_excel(uploaded_file, header=[7, 8])
    # Clean up multi-index
    df.columns = pd.MultiIndex.from_tuples([
        (lvl0.strip(), lvl1.strip()) for lvl0, lvl1 in df.columns
    ])
    
    # Separate metric columns (exclude metadata)
    metric_cols = [col for col in df.columns if col[0] not in meta_cols]
    metrics_df = df[metric_cols]
    
    # Melt metrics into long format
    long = metrics_df.stack(level=[0, 1]).reset_index()
    long.columns = ['row_idx', 'Metric', 'Trial_Rep', 'Value']
    
    # Align metadata rows with metrics
    meta = raw_meta.loc[long['row_idx']].reset_index(drop=True)
    
    # Combine into one DataFrame
    data = pd.concat([meta, long[['Metric', 'Trial_Rep', 'Value']]], axis=1)
    
    # Extract numeric Trial and Rep
    data[['Trial', 'Rep']] = data['Trial_Rep'].str.extract(r'Trial (\d+)\.(\d+)').astype(float)
    data = data.dropna(subset=['Trial', 'Rep'])
    
    # Pivot metrics so each becomes a column
    tidy = data.pivot_table(
        index=['Athlete', 'Athlete Id', 'ExtId', 'Test Type', 'Test Date', 'Body Weight [kg]', 'Trial', 'Rep'],
        columns='Metric',
        values='Value'
    ).reset_index()
    
    # Ensure Test Date is parsed as datetime
    tidy['Test Date'] = pd.to_datetime(tidy['Test Date'])
    
    # Display and export
    st.write("### Tidy Data Preview")
    st.dataframe(tidy)
    csv = tidy.to_csv(index=False)
    st.download_button(
        label="Download Tidy CSV",
        data=csv,
        file_name="tidy_jump_data.csv",
        mime="text/csv"
    )
