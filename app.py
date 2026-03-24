import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="LDCMID Extractor", layout="wide")

st.title("📱 LDCMID → DeviceID Extractor")

# Regex หา LDCMID
LDCMID_REGEX = r'LDCMID=([A-Za-z0-9\-]+)'

def extract_ldcmid(text):
    if pd.isna(text):
        return []
    return re.findall(LDCMID_REGEX, str(text))

# Upload file
uploaded_file = st.file_uploader("📥 Upload Excel / CSV", type=["xlsx", "csv"])

if uploaded_file:
    # อ่านไฟล์
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.write("📊 Preview Data", df.head())

    all_device_ids = []

    # Loop ทุก column ทุก row
    for col in df.columns:
        for val in df[col]:
            ids = extract_ldcmid(val)
            all_device_ids.extend(ids)

    # ลบค่าว่าง + ซ้ำ
    device_ids = list(set(all_device_ids))

    # เรียงค่า
    device_ids.sort()

    # แปลงเป็น DataFrame
    result_df = pd.DataFrame({"deviceid": device_ids})

    st.success(f"✅ เจอทั้งหมด {len(device_ids)} device IDs")

    st.dataframe(result_df)

    # Download
    output = BytesIO()
    result_df.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)

    st.download_button(
        label="📥 Download Excel",
        data=output,
        file_name="deviceid_output.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
