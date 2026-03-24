import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="LDCMID + RequestID Extractor", layout="wide")

st.title("🔗 LDCMID + RequestID Matcher (Clean)")

# Regex
DATETIME_ID_REGEX = r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} ([a-f0-9\-]{36})'
LDCMID_REGEX = r'LDCMID=([A-Za-z0-9\-]+)'
REQUEST_ID_REGEX = r'Request ID:\s*([a-f0-9\-]{36})'

def extract_correlation_id(text):
    match = re.search(DATETIME_ID_REGEX, text)
    return match.group(1) if match else None

def extract_ldcmid(text):
    match = re.search(LDCMID_REGEX, text)
    return match.group(1) if match else None

def extract_request_id(text):
    match = re.search(REQUEST_ID_REGEX, text)
    return match.group(1) if match else None

uploaded_file = st.file_uploader("📥 Upload Excel / CSV", type=["xlsx", "csv"])

if uploaded_file:
    # Read file
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.write("📊 Preview", df.head())

    log_map = {}

    # Loop ทุก cell
    for col in df.columns:
        for val in df[col]:
            if pd.isna(val):
                continue

            text = str(val)

            corr_id = extract_correlation_id(text)
            if not corr_id:
                continue

            if corr_id not in log_map:
                log_map[corr_id] = {"deviceid": None, "request_id": None}

            ldcmid = extract_ldcmid(text)
            if ldcmid:
                log_map[corr_id]["deviceid"] = ldcmid

            req_id = extract_request_id(text)
            if req_id:
                log_map[corr_id]["request_id"] = req_id

    # 🔥 เอาเฉพาะค่าที่ match แล้ว
    result = [
        {
            "deviceid": v["deviceid"],
            "request_id": v["request_id"]
        }
        for v in log_map.values()
        if v["deviceid"] and v["request_id"]
    ]

    result_df = pd.DataFrame(result)

    # sort ให้ดู clean
    result_df = result_df.sort_values(by="deviceid")

    st.success(f"✅ Match ได้ {len(result_df)} records")

    st.dataframe(result_df)

    # Download
    output = BytesIO()
    result_df.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)

    st.download_button(
        label="📥 Download Excel",
        data=output,
        file_name="ldcmid_requestid_clean.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
