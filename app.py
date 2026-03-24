import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="LDCMID Multi Extractor", layout="wide")

st.title("📱 LDCMID Multi + RequestID Matcher")

# Regex
DATETIME_ID_REGEX = r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} ([a-f0-9\-]{36})'
LDCMID_REGEX = r'LDCMID=([A-Za-z0-9\-]+)'
REQUEST_ID_REGEX = r'Request ID:\s*([a-f0-9\-]{36})'

def extract_corr_id(text):
    m = re.search(DATETIME_ID_REGEX, text)
    return m.group(1) if m else None

def extract_ldcmids(text):
    return re.findall(LDCMID_REGEX, text)

def extract_request_id(text):
    m = re.search(REQUEST_ID_REGEX, text)
    return m.group(1) if m else None

uploaded_file = st.file_uploader("📥 Upload Excel / CSV", type=["xlsx", "csv"])

if uploaded_file:
    # Read file
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.write("📊 Preview", df.head())

    log_map = {}

    # 🔥 Loop ทุก cell
    for col in df.columns:
        for val in df[col]:
            if pd.isna(val):
                continue

            text = str(val)
            corr_id = extract_corr_id(text)

            if not corr_id:
                continue

            if corr_id not in log_map:
                log_map[corr_id] = {
                    "deviceids": [],
                    "request_id": None
                }

            # ดึงหลาย device
            ldcmids = extract_ldcmids(text)
            if ldcmids:
                log_map[corr_id]["deviceids"].extend(ldcmids)

            # ดึง request id
            req_id = extract_request_id(text)
            if req_id:
                log_map[corr_id]["request_id"] = req_id

    # 🔥 flatten + match
    rows = []
    for v in log_map.values():
        if v["deviceids"] and v["request_id"]:
            for d in v["deviceids"]:
                rows.append({
                    "deviceid": d,
                    "request_id": v["request_id"]
                })

    result_df = pd.DataFrame(rows)

    # ลบซ้ำ
    result_df = result_df.drop_duplicates()

    # sort
    result_df = result_df.sort_values(by="deviceid").reset_index(drop=True)

    # 🔥 ใส่ No.
    result_df.insert(0, "No.", result_df.index + 1)

    st.success(f"✅ ได้ทั้งหมด {len(result_df)} rows")

    st.dataframe(result_df)

    # Download
    output = BytesIO()
    result_df.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)

    st.download_button(
        label="📥 Download Excel",
        data=output,
        file_name="ldcmid_multi_matched.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
