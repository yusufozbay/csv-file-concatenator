import streamlit as st
import pandas as pd
import chardet
import csv
from io import StringIO, BytesIO

st.set_page_config(page_title="CSV Combiner", layout="centered")
st.title("CSV Combiner App")

def read_csv_with_encoding(file):
    file.seek(0)
    rawdata = file.read()
    # Detect encoding
    result = chardet.detect(rawdata)
    enc = result['encoding'] if result['encoding'] else 'utf-8'

    # Decode to string for delimiter sniffing
    try:
        decoded = rawdata.decode(enc)
    except Exception:
        try:
            decoded = rawdata.decode('utf-16')
        except Exception as e:
            raise Exception(f"Could not decode file: {e}")

    # Try to auto-detect delimiter
    try:
        sample = '\n'.join(decoded.splitlines()[:5])  # sample first 5 lines
        dialect = csv.Sniffer().sniff(sample)
        delimiter = dialect.delimiter
    except Exception:
        delimiter = ','  # fallback

    # Now read with pandas, skipping problematic rows
    try:
        df = pd.read_csv(StringIO(decoded), delimiter=delimiter, on_bad_lines='skip')  # pandas >= 1.3.0
        return df
    except Exception as e:
        raise Exception(f"Error reading CSV: {e}")

uploaded_files = st.file_uploader(
    "Upload one or more CSV files",
    type="csv",
    accept_multiple_files=True
)

if uploaded_files:
    dfs = []
    for file in uploaded_files:
        try:
            df = read_csv_with_encoding(file)
            dfs.append(df)
            st.success(f"Uploaded: {file.name} ({df.shape[0]} rows, {df.shape[1]} cols)")
        except Exception as e:
            st.error(f"Error reading {file.name}: {e}")

    if len(dfs) > 1:
        combined_df = pd.concat(dfs, ignore_index=True)
        st.write("### Combined Data Preview", combined_df.head())
        st.write(f"**Total rows:** {combined_df.shape[0]}  |  **Columns:** {combined_df.shape[1]}")
        # Download button
        csv_buffer = BytesIO()
        combined_df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)
        st.download_button(
            label="Download Combined CSV",
            data=csv_buffer,
            file_name="combined.csv",
            mime="text/csv"
        )
    elif len(dfs) == 1:
        st.info("You have uploaded only one file. Upload more to combine.")
else:
    st.info("Please upload your CSV files.")
