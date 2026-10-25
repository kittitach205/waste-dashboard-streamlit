"""
Dashboard ปริมาณขยะมูลฝอย กรมอุทยานแห่งชาติ สัตว์ป่า และพันธุ์พืช
ข้อมูลจาก data.go.th : https://data.go.th/dataset/gdpublish-69-dnp01-11-01
(รวมข้อมูลปี 2568 และ 2569 ไว้ในไฟล์ waste_data.csv)

วิธีรันบนเครื่อง:
    pip install -r requirements.txt
    streamlit run app.py
"""

import altair as alt
import pandas as pd
import streamlit as st

DATA_FILE = "waste_data.csv"
SOURCE_URL = "https://data.go.th/dataset/gdpublish-69-dnp01-11-01"

MONTHS = [
    "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
    "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม",
]
MONTH_SHORT = {
    "มกราคม": "ม.ค.", "กุมภาพันธ์": "ก.พ.", "มีนาคม": "มี.ค.", "เมษายน": "เม.ย.",
    "พฤษภาคม": "พ.ค.", "มิถุนายน": "มิ.ย.", "กรกฎาคม": "ก.ค.", "สิงหาคม": "ส.ค.",
    "กันยายน": "ก.ย.", "ตุลาคม": "ต.ค.", "พฤศจิกายน": "พ.ย.", "ธันวาคม": "ธ.ค.",
}

GEN = "ขยะที่เกิดขึ้น (กก.)"
USED = "นำไปใช้ประโยชน์ (กก.)"
DISP = "ขยะที่ส่งกำจัด (กก.)"

COLOR = {GEN: "#2f6b4f", USED: "#7fb069", DISP: "#d1803a"}


@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_FILE)
    df["เดือนที่"] = df["เดือน"].map({m: i + 1 for i, m in enumerate(MONTHS)})
    df["เดือนย่อ"] = df["เดือน"].map(MONTH_SHORT)
    return df


# ---------------- หน้าเว็บ ----------------
st.set_page_config(page_title="Dashboard ปริมาณขยะมูลฝอย", page_icon="♻️", layout="wide")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@400;600;700&display=swap');
    html, body, [class*="css"], p, label, h1, h2, h3, button, input {
        font-family: 'Sarabun', sans-serif !important;
    }
    .block-container { padding-top: 2rem; }
    .hero h1 { font-size: 2.1rem; margin-bottom: 0.2rem; color: #1f4d38; }
    .hero p { color: #5b6b62; margin: 0; }
    div[data-testid="stMetric"] {
        background: #f3f7f2;
        border: 1px solid #dde8da;
        border-radius: 14px;
        padding: 14px 16px;
    }
    div[data-testid="stMetricValue"] { color: #1f4d38; font-size: 1.7rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

df = load_data()

st.markdown(
    f"""
    <div class="hero">
      <h1>♻️ Dashboard ปริมาณขยะมูลฝอย</h1>
      <p>กรมอุทยานแห่งชาติ สัตว์ป่า และพันธุ์พืช · ปีงบ 2568–2569 ·
      ข้อมูลจาก <a href="{SOURCE_URL}" target="_blank">data.go.th</a></p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.write("")

# ---------------- Interactive Widgets (Sidebar) ----------------
with st.sidebar:
    st.header("🔎 ตัวกรองข้อมูล")

    years = sorted(df["ปี"].unique())
    year = st.radio("ปี พ.ศ.", years, index=len(years) - 1, horizontal=True)

    df_year = df[df["ปี"] == year]
    months_in_year = [m for m in MONTHS if m in set(df_year["เดือน"])]
    if len(months_in_year) > 1:
        m_from, m_to = st.select_slider(
            "ช่วงเดือน",
            options=months_in_year,
            value=(months_in_year[0], months_in_year[-1]),
        )
    else:
        m_from = m_to = months_in_year[0]
    i_from, i_to = MONTHS.index(m_from) + 1, MONTHS.index(m_to) + 1

    groups = sorted(df_year["สังกัด"].unique())
    group_sel = st.multiselect("สังกัด", groups, default=groups)

    units_all = sorted(df_year[df_year["สังกัด"].isin(group_sel)]["หน่วยงาน"].unique())
    unit_sel = st.multiselect("หน่วยงาน (เว้นว่าง = ทุกหน่วยงาน)", units_all)

    top_n = st.slider("จำนวนหน่วยงานในกราฟจัดอันดับ", 5, 20, 10)

    st.caption(f"ข้อมูลทั้งหมด {len(df):,} แถว · {df['หน่วยงาน'].nunique()} หน่วยงาน")

# ---------------- กรองข้อมูล ----------------
f = df_year[
    df_year["สังกัด"].isin(group_sel)
    & df_year["เดือนที่"].between(i_from, i_to)
]
if unit_sel:
    f = f[f["หน่วยงาน"].isin(unit_sel)]

if f.empty:
    st.warning("ไม่มีข้อมูลตามตัวกรองที่เลือก ลองเลือกสังกัดหรือหน่วยงานเพิ่ม")
    st.stop()

# ---------------- สรุปตัวเลข (KPI) ----------------
total_gen = f[GEN].sum()
total_used = f[USED].sum()
total_disp = f[DISP].sum()
used_pct = total_used / total_gen * 100 if total_gen else 0
per_person = (f[GEN] / (f["คนเฉลี่ย"] * f["วันทำงาน"])).replace([float("inf")], pd.NA).mean()

st.subheader(f"สรุปปี {year} · {MONTH_SHORT[m_from]}–{MONTH_SHORT[m_to]}")
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("ขยะที่เกิดขึ้น (กก.)", f"{total_gen:,.0f}")
k2.metric("นำไปใช้ประโยชน์ (กก.)", f"{total_used:,.0f}")
k3.metric("ส่งกำจัด (กก.)", f"{total_disp:,.0f}")
k4.metric("สัดส่วนใช้ประโยชน์", f"{used_pct:.1f}%")
k5.metric("ขยะเฉลี่ย/คน/วัน (กรัม)", f"{per_person * 1000:,.0f}")

st.divider()

# ---------------- กราฟที่ 1: แนวโน้มรายเดือน ----------------
c1, c2 = st.columns([3, 2])

with c1:
    st.markdown("#### 📈 ปริมาณขยะรายเดือน")
    monthly = (
        f.groupby(["เดือนที่", "เดือนย่อ"], as_index=False)[[GEN, USED, DISP]].sum()
        .melt(id_vars=["เดือนที่", "เดือนย่อ"], var_name="ประเภท", value_name="กิโลกรัม")
    )
    order = [MONTH_SHORT[m] for m in MONTHS]
    line = (
        alt.Chart(monthly)
        .mark_line(point=alt.OverlayMarkDef(size=60), strokeWidth=3)
        .encode(
            x=alt.X("เดือนย่อ:N", sort=order, title="เดือน", axis=alt.Axis(labelAngle=0)),
            y=alt.Y("กิโลกรัม:Q", title="กิโลกรัม"),
            color=alt.Color(
                "ประเภท:N",
                scale=alt.Scale(domain=list(COLOR), range=list(COLOR.values())),
                legend=alt.Legend(orient="bottom", title=None),
            ),
            tooltip=["เดือนย่อ", "ประเภท", alt.Tooltip("กิโลกรัม:Q", format=",.2f")],
        )
        .properties(height=360)
    )
    st.altair_chart(line, use_container_width=True)

# ---------------- กราฟที่ 2: สัดส่วนการจัดการขยะ ----------------
with c2:
    st.markdown("#### 🍩 สัดส่วนใช้ประโยชน์ vs ส่งกำจัด")
    share = pd.DataFrame(
        {"ประเภท": [USED, DISP], "กิโลกรัม": [total_used, total_disp]}
    )
    share["ร้อยละ"] = share["กิโลกรัม"] / share["กิโลกรัม"].sum() * 100
    donut = (
        alt.Chart(share)
        .mark_arc(innerRadius=70, outerRadius=130)
        .encode(
            theta="กิโลกรัม:Q",
            color=alt.Color(
                "ประเภท:N",
                scale=alt.Scale(domain=[USED, DISP], range=[COLOR[USED], COLOR[DISP]]),
                legend=alt.Legend(orient="bottom", title=None),
            ),
            tooltip=["ประเภท", alt.Tooltip("กิโลกรัม:Q", format=",.2f"), alt.Tooltip("ร้อยละ:Q", format=".1f")],
        )
        .properties(height=360)
    )
    st.altair_chart(donut, use_container_width=True)

# ---------------- กราฟที่ 3: จัดอันดับหน่วยงาน ----------------
st.markdown(f"#### 🏢 {top_n} หน่วยงานที่มีขยะเกิดขึ้นมากที่สุด")
by_unit = (
    f.groupby(["หน่วยงาน", "สังกัด"], as_index=False)[[GEN, USED, DISP]].sum()
    .sort_values(GEN, ascending=False)
    .head(top_n)
    .rename(columns={GEN: "เกิดขึ้น", USED: "ใช้ประโยชน์", DISP: "ส่งกำจัด"})
)
bar = (
    alt.Chart(by_unit)
    .mark_bar(cornerRadiusEnd=4)
    .encode(
        x=alt.X("เกิดขึ้น:Q", title="ขยะที่เกิดขึ้น (กก.)"),
        y=alt.Y("หน่วยงาน:N", sort="-x", title=None, axis=alt.Axis(labelLimit=320, labelOverlap=False)),
        color=alt.Color(
            "สังกัด:N",
            scale=alt.Scale(domain=["ส่วนกลาง", "ส่วนภูมิภาค"], range=["#2f6b4f", "#9cc5a1"]),
            legend=alt.Legend(orient="bottom"),
        ),
        tooltip=[
            "หน่วยงาน", "สังกัด",
            alt.Tooltip("เกิดขึ้น:Q", title="ขยะที่เกิดขึ้น (กก.)", format=",.2f"),
            alt.Tooltip("ใช้ประโยชน์:Q", title="นำไปใช้ประโยชน์ (กก.)", format=",.2f"),
            alt.Tooltip("ส่งกำจัด:Q", title="ขยะที่ส่งกำจัด (กก.)", format=",.2f"),
        ],
    )
    .properties(height=alt.Step(30))
)
st.altair_chart(bar, use_container_width=True)

# ---------------- กราฟที่ 4: เทียบปี 2568 vs 2569 ----------------
st.markdown("#### 📊 เทียบปี 2568 กับ 2569 (เฉพาะเดือนที่มีข้อมูลทั้ง 2 ปี)")
common = sorted(
    set(df[df["ปี"] == 2568]["เดือนที่"]) & set(df[df["ปี"] == 2569]["เดือนที่"])
)
cmp_src = df[df["สังกัด"].isin(group_sel) & df["เดือนที่"].isin(common)]
if unit_sel:
    cmp_src = cmp_src[cmp_src["หน่วยงาน"].isin(unit_sel)]
cmp = (
    cmp_src.groupby(["ปี", "เดือนที่", "เดือนย่อ"], as_index=False)[GEN].sum()
    .rename(columns={GEN: "เกิดขึ้น"})
)
cmp["ปี"] = cmp["ปี"].astype(str)
grouped = (
    alt.Chart(cmp)
    .mark_bar()
    .encode(
        x=alt.X("เดือนย่อ:N", sort=order, title="เดือน", axis=alt.Axis(labelAngle=0)),
        xOffset="ปี:N",
        y=alt.Y("เกิดขึ้น:Q", title="ขยะที่เกิดขึ้น (กก.)"),
        color=alt.Color("ปี:N", scale=alt.Scale(range=["#b7c9bd", "#2f6b4f"]), legend=alt.Legend(orient="bottom")),
        tooltip=["ปี", "เดือนย่อ", alt.Tooltip("เกิดขึ้น:Q", title="ขยะที่เกิดขึ้น (กก.)", format=",.2f")],
    )
    .properties(height=320)
)
st.altair_chart(grouped, use_container_width=True)
st.caption("กราฟนี้ไม่ขึ้นกับตัวกรองปีและช่วงเดือน แต่ใช้ตัวกรองสังกัดและหน่วยงาน")

# ---------------- ตารางข้อมูล ----------------
with st.expander("📋 ดูข้อมูลตามตัวกรอง"):
    show = f.drop(columns=["เดือนที่", "เดือนย่อ"])
    st.dataframe(show, hide_index=True, width="stretch")
    st.download_button(
        "⬇️ ดาวน์โหลด CSV",
        show.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"waste_{year}.csv",
        mime="text/csv",
    )

st.caption(f"ที่มา: ชุดข้อมูล “ปริมาณขยะมูลฝอย” กรมอุทยานแห่งชาติ สัตว์ป่า และพันธุ์พืช — {SOURCE_URL}")
