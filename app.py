import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="LDCMID Full Extractor", layout="wide")

st.title("🚀 LDCMID Full Extractor (Carrier + ProStatus + Latest Date)")

# Regex
DATETIME_ID_REGEX = r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} ([a-f0-9\-]{36})'
LDCMID_REGEX = r'LDCMID=([A-Za-z0-9\-]+)'
REQUEST_ID_REGEX = r'Request ID:\s*([a-f0-9\-]{36})'
PROSTATUS_REGEX = r'ProStatus=([A-Za-z0-9_]+)'
PRODATE_REGEX = r'ProDate=([\d\-:\s]+)'

def extract_corr_id(text):
    m = re.search(DATETIME_ID_REGEX, text)
    return m.group(1) if m else None

def extract_ldcmids(text):
    return re.findall(LDCMID_REGEX, text)

def extract_request_id(text):
    m = re.search(REQUEST_ID_REGEX, text)
    return m.group(1) if m else None

def extract_prostatus(text):
    m = re.search(PROSTATUS_REGEX, text)
    return m.group(1) if m else None

def extract_prodate(text):
    m = re.search(PRODATE_REGEX, text)
    return m.group(1) if m else None

def get_carrier(deviceid):
    if deviceid.startswith(("A", "Z")):
        return "AIS"
    elif deviceid == "" or pd.isna(deviceid):
        return "-"
    else:
        return "TRUE"

uploaded_file = st.file_uploader("📥 Upload Excel / CSV", type=["xlsx", "csv"])

if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.write("📊 Preview", df.head())

    log_map = {}

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
                    "request_id": None,
                    "prostatus": None,
                    "prodate": None
                }

            # Device
            ldcmids = extract_ldcmids(text)
            if ldcmids:
                log_map[corr_id]["deviceids"].extend(ldcmids)

            # Request ID
            req_id = extract_request_id(text)
            if req_id:
                log_map[corr_id]["request_id"] = req_id

            # ProStatus
            ps = extract_prostatus(text)
            if ps:
                log_map[corr_id]["prostatus"] = ps

            # ProDate
            pd_val = extract_prodate(text)
            if pd_val:
                log_map[corr_id]["prodate"] = pd_val

    # 🔥 flatten
    rows = []
    for v in log_map.values():
        if v["deviceids"] and v["request_id"]:
            for d in v["deviceids"]:
                rows.append({
                    "deviceid": d,
                    "request_id": v["request_id"],
                    "ProStatus": v["prostatus"],
                    "ProDate": v["prodate"]
                })

    result_df = pd.DataFrame(rows)

    # clean
    result_df = result_df.drop_duplicates()

    # 🔥 Carrier
    result_df["Carrier"] = result_df["deviceid"].apply(get_carrier)

    # 🔥 convert date + sort ใหม่สุดบน
    result_df["ProDate"] = pd.to_datetime(result_df["ProDate"], errors="coerce")
    result_df = result_df.sort_values(by="ProDate", ascending=False)

    # 🔥 reset + No.
    result_df = result_df.reset_index(drop=True)
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
        file_name="ldcmid_full_output.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
