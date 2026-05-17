import html
import re
import zipfile
from datetime import timedelta
from pathlib import Path
from urllib.parse import quote

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Post-Close Market Reset",
    layout="wide",
    initial_sidebar_state="collapsed",
)

OUTPUT_DIR = Path("outputs")
ARCHIVE_DIRNAME = "interesting20_archive"
BUILD_ID = "v30-summary-icons-buttons"
FEEDBACK_EMAIL = "investingwithstrategy@gmail.com"

st.markdown(
    """
<style>
:root {
  --page-bg-1: #edf7ff;
  --page-bg-2: #f8fbf4;
  --page-bg-3: #fff3df;
  --card-bg: rgba(255,255,255,0.86);
  --card-bg-strong: rgba(255,255,255,0.96);
  --ink: #122033;
  --ink-soft: #46586f;
  --ink-faint: #718095;
  --border: rgba(35,72,108,0.15);
  --blue: #1d5fd1;
  --teal: #008f8c;
  --amber: #c47a00;
  --green: #168253;
  --red: #bd3c3c;
  --violet: #7058c9;
}
html, body, .stApp, [data-testid="stAppViewContainer"] {
  background:
    radial-gradient(circle at 15% 0%, rgba(74,144,226,0.18) 0, rgba(74,144,226,0.00) 32%),
    radial-gradient(circle at 90% 10%, rgba(255,185,80,0.24) 0, rgba(255,185,80,0.00) 30%),
    linear-gradient(135deg, var(--page-bg-1) 0%, var(--page-bg-2) 50%, var(--page-bg-3) 100%) !important;
  color: var(--ink) !important;
}
.block-container {
  padding-top: 0.55rem;
  padding-bottom: 2rem;
  padding-left: 0.72rem;
  padding-right: 0.72rem;
  max-width: 980px;
}
[data-testid="stSidebar"], section[data-testid="stSidebar"], [data-testid="collapsedControl"] {display:none;}
#MainMenu, footer, header {visibility: hidden;}
.reset-shell {max-width: 920px; margin: 0 auto;}
.top-card, .metric-card, .info-card, .stock-card, .summary-card, .disclaimer-card, .stage-section-card {
  border: 1px solid var(--border);
  background: var(--card-bg);
  color: var(--ink);
  border-radius: 24px;
  padding: 0.95rem 1rem;
  box-shadow: 0 18px 45px rgba(31,56,88,0.10);
  backdrop-filter: blur(12px);
}
.top-card {padding: 1.12rem 1.05rem; margin-bottom: 0.75rem; background: var(--card-bg-strong);}
.title {font-size: 1.78rem; line-height: 1.04; font-weight: 950; letter-spacing: -0.045em; margin: 0 0 0.35rem 0; color: var(--ink);}
.subtitle {font-size: 0.96rem; color: var(--ink-soft); line-height: 1.38;}
.kicker {font-size: 0.71rem; text-transform: uppercase; letter-spacing: 0.08em; color: var(--ink-faint); font-weight: 900; margin-bottom: 0.16rem;}
.metric-value {font-size: 1.13rem; font-weight: 950; line-height: 1.15; color: var(--ink);}
.metric-sub {font-size: 0.82rem; color: var(--ink-soft); line-height: 1.25; margin-top: 0.15rem;}
.build-pill, .safe-pill, .leader-pill, .stage-pill, .fresh-pill, .summary-pill {
  display:inline-flex; align-items:center; gap:0.25rem; border-radius:999px; padding: 0.27rem 0.58rem;
  font-size: 0.76rem; font-weight: 900; border: 1px solid var(--border); background: rgba(255,255,255,0.72); color: var(--ink);
}
.safe-pill {border-color: rgba(22,130,83,0.25); color: var(--green); background: rgba(22,130,83,0.08);}
.build-pill {border-color: rgba(29,95,209,0.20); color: var(--blue); background: rgba(29,95,209,0.08);}
.stage-pill {color: var(--blue);}
.fresh-pill.new {color: var(--green); background: rgba(22,130,83,0.09); border-color: rgba(22,130,83,0.24);}
.fresh-pill.repeat {color: var(--blue); background: rgba(29,95,209,0.08); border-color: rgba(29,95,209,0.22);}
.fresh-pill.drop {color: var(--red); background: rgba(189,60,60,0.08); border-color: rgba(189,60,60,0.22);}
.fresh-pill.stage2 {color: var(--violet); background: rgba(112,88,201,0.08); border-color: rgba(112,88,201,0.22);}
.fresh-pill.fo {color:#7c3aed; background: rgba(124,58,237,0.08); border-color: rgba(124,58,237,0.24);}
.fresh-pill.support {color: var(--green); background: rgba(22,130,83,0.09); border-color: rgba(22,130,83,0.24);}
.fresh-pill.weak {color: var(--red); background: rgba(189,60,60,0.08); border-color: rgba(189,60,60,0.24);}
.fresh-pill.rank {color: var(--blue); background: rgba(29,95,209,0.08); border-color: rgba(29,95,209,0.22);}
.mover-up {font-weight:950; color: var(--green);}
.mover-down {font-weight:950; color: var(--red);}
.reset-summary-lines {font-size:1.03rem; font-weight:950; color:var(--ink); line-height:1.46;}
.reset-summary-lines div {margin:0.1rem 0;}
.leader-strip, .badge-strip, .summary-strip {display:flex; gap:0.45rem; flex-wrap:wrap; margin-top: 0.46rem;}
.section-title {font-size: 1.18rem; font-weight: 950; margin: 1.18rem 0 0.45rem 0; letter-spacing: -0.025em; color: var(--ink);}
.section-note {font-size:0.86rem; color: var(--ink-soft); margin-top:-0.2rem; margin-bottom:0.58rem; line-height:1.38;}
.summary-card {margin-top:0.72rem; background: rgba(255,255,255,0.91);}
.summary-main {font-size:1.03rem; font-weight:950; color:var(--ink); line-height:1.28;}
.summary-sub {font-size:0.86rem; color:var(--ink-soft); line-height:1.35; margin-top:0.28rem;}
.unlock-line {font-size:0.84rem; color:var(--amber); font-weight:900; margin-top:0.52rem;}
.stock-card {margin: 0.78rem 0 1.08rem 0; padding: 0.9rem 0.82rem 0.82rem 0.82rem; background: var(--card-bg-strong); scroll-snap-align: start;}
.stock-head {display:flex; justify-content:space-between; gap:0.6rem; align-items:flex-start; margin-bottom:0.36rem;}
.stock-name {font-size: 1.08rem; line-height: 1.18; font-weight: 950; letter-spacing:-0.024em; color: var(--ink);}
.stock-meta {font-size:0.9rem; color:var(--ink-soft); line-height:1.25; margin-top:0.2rem;}
.stage-variant {font-size:0.88rem; color:#000000; font-weight:850; line-height:1.25; margin-top:0.18rem;}
.signal-line {font-size:0.88rem; color:var(--ink-soft); line-height:1.32; margin-top:0.36rem;}
.chart-wrap {border:1px solid var(--border); border-radius:18px; overflow:hidden; margin-top:0.58rem; background: #ffffff; box-shadow: inset 0 1px 0 rgba(255,255,255,0.8);}
.chart-missing {border:1px dashed var(--border); border-radius:18px; padding:1.2rem; color:var(--ink-soft); text-align:center; font-size:0.9rem; margin-top:0.58rem; background: rgba(255,255,255,0.58);}
.disclaimer-card {border-left:4px solid rgba(22,130,83,0.45); font-size:0.84rem; color:var(--ink-soft); line-height:1.38; margin-top:0.85rem; background: rgba(255,255,255,0.90);}
.liked-note {font-size:0.8rem; color:var(--ink-soft); margin-top:0.25rem;}
.stage-section-card {margin:0.7rem 0 0.5rem 0; padding:0.72rem 0.85rem; background: rgba(255,255,255,0.72);}
.stage-section-title {font-size:1rem; font-weight:950; color:var(--ink);}
[data-testid="stDataFrame"] {border-radius: 18px; overflow: hidden; border: 1px solid var(--border); background:#fff;}
button[kind="secondary"] {border-radius: 999px !important; font-weight: 900 !important; border-color: rgba(35,72,108,0.22) !important; color: var(--ink) !important; background: rgba(255,255,255,0.72) !important;}
div[role="radiogroup"] label {background: rgba(255,255,255,0.72); border:1px solid var(--border); padding:0.25rem 0.55rem; border-radius:999px;}

/* v16: force card/subtext readability on Streamlit light backgrounds */
.top-card, .metric-card, .info-card, .stock-card, .summary-card, .disclaimer-card, .stage-section-card,
.subtitle, .metric-sub, .section-note, .summary-sub, .stock-meta, .signal-line, .liked-note, .kicker, .stock-name, .metric-value, .stage-section-title {
  color: #111827 !important;
}
.fresh-pill, .summary-pill, .leader-pill, .stage-pill {
  color: #111827 !important;
}


.feedback-card {
  border: 1px solid rgba(29,95,209,0.18);
  background: rgba(255,255,255,0.92);
  color: #111827;
  border-radius: 24px;
  padding: 1.05rem 1rem;
  margin-top: 1rem;
  box-shadow: 0 18px 45px rgba(31,56,88,0.10);
}
.feedback-title {font-size:1.12rem; font-weight:950; color:#111827; margin-bottom:0.25rem;}
.feedback-sub {font-size:0.88rem; color:#111827; line-height:1.4; margin-bottom:0.55rem;}
.feedback-mail-link {
  display:inline-flex; align-items:center; justify-content:center;
  border-radius:999px; padding:0.58rem 0.9rem; margin-top:0.45rem;
  color:#ffffff !important; text-decoration:none !important; font-weight:950;
  background: linear-gradient(90deg, #1d5fd1 0%, #008f8c 100%);
  box-shadow: 0 10px 24px rgba(29,95,209,0.20);
}

@media (max-width: 768px) {
  html {scroll-snap-type: y proximity;}
  .block-container {padding-left:0.42rem; padding-right:0.42rem; padding-top:0.35rem;}
  .title {font-size: 1.43rem;}
  .subtitle {font-size: 0.89rem;}
  .metric-card {padding:0.72rem 0.75rem;}
  .metric-value {font-size:1rem;}
  .stock-card {border-radius:24px; padding:0.76rem 0.66rem; min-height: calc(100vh - 26px); display:flex; flex-direction:column; justify-content:flex-start;}
  .stock-name {font-size:1.01rem;}
  .stock-meta, .signal-line {font-size:0.84rem;}
  .chart-wrap img {width:100% !important;}
}
</style>
""",
    unsafe_allow_html=True,
)

# v15 hard override: Streamlit sometimes paints inner white containers over body/app background.
# This block forces the visible app surface to keep the designed pastel market-reset background.
st.markdown(
    """
<style>
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
section.main,
.main,
[data-testid="stAppViewContainer"] > .main {
  background:
    radial-gradient(circle at 8% 8%, rgba(29,95,209,0.22) 0, rgba(29,95,209,0.00) 30%),
    radial-gradient(circle at 92% 4%, rgba(0,143,140,0.18) 0, rgba(0,143,140,0.00) 28%),
    radial-gradient(circle at 82% 78%, rgba(196,122,0,0.18) 0, rgba(196,122,0,0.00) 34%),
    linear-gradient(135deg, #e6f2ff 0%, #f8fbff 42%, #fff0d9 100%) !important;
  background-attachment: fixed !important;
}
.block-container,
[data-testid="stMainBlockContainer"],
[data-testid="stVerticalBlock"],
[data-testid="stElementContainer"] {
  background: transparent !important;
}
[data-testid="stHeader"] {
  background: rgba(230,242,255,0.35) !important;
  backdrop-filter: blur(10px) !important;
}
.v15-visible-banner {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  margin: 0.15rem 0 0.55rem 0;
  padding: 0.36rem 0.68rem;
  border-radius: 999px;
  color: #ffffff;
  font-weight: 950;
  font-size: 0.78rem;
  letter-spacing: 0.01em;
  background: linear-gradient(90deg, #1d5fd1 0%, #008f8c 100%);
  box-shadow: 0 10px 24px rgba(29,95,209,0.20);
}
.reset-summary-lines {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.44rem;
  margin-top: 0.45rem;
}
.reset-summary-lines div {
  color: #122033;
  font-weight: 950;
  font-size: 1.04rem;
  line-height: 1.18;
  padding: 0.48rem 0.62rem;
  border-radius: 14px;
  border-left: 5px solid #1d5fd1;
  background: rgba(255,255,255,0.78);
}
.top-card, .metric-card, .info-card, .stock-card, .summary-card, .disclaimer-card, .stage-section-card {
  background: rgba(255,255,255,0.88) !important;
}
.stock-card {
  box-shadow: 0 22px 55px rgba(31,56,88,0.12) !important;
}
.chart-wrap {
  background: linear-gradient(135deg, #f6fbff 0%, #ffffff 100%) !important;
}
</style>
""",
    unsafe_allow_html=True,
)



# v29: real card/container + button readability overrides.
st.markdown(
    """
<style>
/* Let long stock text wrap instead of clipping. */
.stock-card,
.stock-card * {
  box-sizing: border-box !important;
}
.stock-card {
  overflow: visible !important;
  height: auto !important;
  min-height: auto !important;
}
.stock-head {
  flex-wrap: wrap !important;
  align-items: flex-start !important;
}
.stock-head > div:first-child {
  min-width: 0 !important;
  flex: 1 1 280px !important;
}
.stock-name,
.stock-meta,
.stage-variant,
.signal-line,
.liked-note,
.fresh-pill,
.stage-pill {
  white-space: normal !important;
  overflow-wrap: anywhere !important;
  word-break: normal !important;
}
.stock-meta,
.stage-variant,
.signal-line,
.liked-note {
  color: #000000 !important;
}

/* Style the real Streamlit bordered container used for each stock card. */
[data-testid="stVerticalBlockBorderWrapper"] {
  border-radius: 24px !important;
  border: 1px solid rgba(35,72,108,0.16) !important;
  background: rgba(255,255,255,0.96) !important;
  box-shadow: 0 22px 55px rgba(31,56,88,0.12) !important;
  overflow: visible !important;
}
[data-testid="stVerticalBlockBorderWrapper"] > div {
  overflow: visible !important;
}

/* Better Like / Daily / Weekly button surface. */
.stButton > button {
  border-radius: 999px !important;
  min-height: 2.65rem !important;
  font-weight: 950 !important;
  letter-spacing: 0.01em !important;
  border: 1px solid rgba(29,95,209,0.26) !important;
  color: #0f172a !important;
  background: linear-gradient(180deg, #ffffff 0%, #e9f3ff 100%) !important;
  box-shadow: 0 9px 20px rgba(29,95,209,0.12) !important;
}
.stButton > button:hover {
  border-color: rgba(29,95,209,0.62) !important;
  background: linear-gradient(180deg, #f8fbff 0%, #dbeafe 100%) !important;
  transform: translateY(-1px);
}
.stButton > button:active {
  transform: translateY(0px);
  box-shadow: inset 0 2px 5px rgba(15,23,42,0.14) !important;
}
.stButton > button[kind="primary"] {
  color: #ffffff !important;
  border-color: rgba(15,118,110,0.42) !important;
  background: linear-gradient(135deg, #1d5fd1 0%, #0f766e 100%) !important;
  box-shadow: 0 10px 24px rgba(15,118,110,0.25) !important;
}
.stButton > button[kind="primary"] p,
.stButton > button[kind="primary"] span {
  color: #ffffff !important;
}
.stButton > button[kind="secondary"] p,
.stButton > button[kind="secondary"] span {
  color: #0f172a !important;
}
.today-summary-card {
  margin-top: 0.72rem;
  border: 1px solid rgba(35,72,108,0.14);
  background: rgba(255,255,255,0.92);
  border-radius: 24px;
  padding: 1rem 1.05rem;
  box-shadow: 0 18px 45px rgba(31,56,88,0.10);
}
.today-summary-title {
  font-size: 1.05rem;
  font-weight: 950;
  color: #111827;
  letter-spacing: -0.02em;
  margin-bottom: 0.55rem;
}
.today-summary-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.48rem;
}
.today-summary-row {
  display: grid;
  grid-template-columns: 125px 1fr;
  gap: 0.55rem;
  align-items: start;
  color: #111827;
  font-size: 0.96rem;
  line-height: 1.35;
  padding: 0.5rem 0.6rem;
  border-radius: 14px;
  background: rgba(248,251,255,0.88);
  border: 1px solid rgba(35,72,108,0.09);
}
.today-summary-label {
  font-weight: 950;
  color: #344256;
}
.today-summary-value {
  font-weight: 900;
  color: #111827;
}
.today-summary-title-small {
  margin-top: 0.82rem;
  margin-bottom: 0.42rem;
  font-size: 0.94rem;
  color: #344256;
}
.market-story-box {
  display: grid;
  gap: 0.44rem;
  margin-bottom: 0.72rem;
}
.market-story-line {
  color: #111827;
  font-weight: 950;
  font-size: 1.02rem;
  line-height: 1.32;
  padding: 0.55rem 0.68rem;
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(29,95,209,0.08) 0%, rgba(0,143,140,0.08) 100%);
  border: 1px solid rgba(35,72,108,0.10);
}

.feedback-card {
  border: 1px solid rgba(29,95,209,0.18);
  background: rgba(255,255,255,0.92);
  color: #111827;
  border-radius: 24px;
  padding: 1.05rem 1rem;
  margin-top: 1rem;
  box-shadow: 0 18px 45px rgba(31,56,88,0.10);
}
.feedback-title {font-size:1.12rem; font-weight:950; color:#111827; margin-bottom:0.25rem;}
.feedback-sub {font-size:0.88rem; color:#111827; line-height:1.4; margin-bottom:0.55rem;}
.feedback-mail-link {
  display:inline-flex; align-items:center; justify-content:center;
  border-radius:999px; padding:0.58rem 0.9rem; margin-top:0.45rem;
  color:#ffffff !important; text-decoration:none !important; font-weight:950;
  background: linear-gradient(90deg, #1d5fd1 0%, #008f8c 100%);
  box-shadow: 0 10px 24px rgba(29,95,209,0.20);
}



/* Compact stock-card action buttons: keep Like / Daily / Weekly on one row on mobile. */
.stock-actions-marker + div [data-testid="stHorizontalBlock"] {
  display: flex !important;
  flex-direction: row !important;
  flex-wrap: nowrap !important;
  gap: 0.32rem !important;
}
.stock-actions-marker + div [data-testid="column"] {
  flex: 1 1 0 !important;
  min-width: 0 !important;
  width: 33.33% !important;
}
.stock-actions-marker + div .stButton > button {
  min-height: 2.22rem !important;
  padding: 0.32rem 0.22rem !important;
  font-size: 0.82rem !important;
  white-space: nowrap !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
}
.stock-actions-marker + div .stButton > button p,
.stock-actions-marker + div .stButton > button span {
  white-space: nowrap !important;
  font-size: 0.82rem !important;
}
@media (max-width: 768px) {
  .stock-actions-marker + div [data-testid="stHorizontalBlock"] {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    gap: 0.24rem !important;
  }
  .stock-actions-marker + div [data-testid="column"] {
    flex: 1 1 0 !important;
    min-width: 0 !important;
    width: 33.33% !important;
  }
  .stock-actions-marker + div .stButton > button {
    min-height: 2.05rem !important;
    padding: 0.26rem 0.12rem !important;
    font-size: 0.76rem !important;
    letter-spacing: 0 !important;
  }
  .stock-actions-marker + div .stButton > button p,
  .stock-actions-marker + div .stButton > button span {
    font-size: 0.76rem !important;
  }
}

@media (max-width: 768px) {
  .today-summary-row { grid-template-columns: 1fr; gap: 0.15rem; }
}

/* Mobile: do not force one-card viewport height when text is long. */

.feedback-card {
  border: 1px solid rgba(29,95,209,0.18);
  background: rgba(255,255,255,0.92);
  color: #111827;
  border-radius: 24px;
  padding: 1.05rem 1rem;
  margin-top: 1rem;
  box-shadow: 0 18px 45px rgba(31,56,88,0.10);
}
.feedback-title {font-size:1.12rem; font-weight:950; color:#111827; margin-bottom:0.25rem;}
.feedback-sub {font-size:0.88rem; color:#111827; line-height:1.4; margin-bottom:0.55rem;}
.feedback-mail-link {
  display:inline-flex; align-items:center; justify-content:center;
  border-radius:999px; padding:0.58rem 0.9rem; margin-top:0.45rem;
  color:#ffffff !important; text-decoration:none !important; font-weight:950;
  background: linear-gradient(90deg, #1d5fd1 0%, #008f8c 100%);
  box-shadow: 0 10px 24px rgba(29,95,209,0.20);
}

@media (max-width: 768px) {
  .stock-card {
    min-height: auto !important;
    height: auto !important;
    display: block !important;
    overflow: visible !important;
  }
  [data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 22px !important;
  }
}

/* v31 prevent F&O/rank badges from occupying removed Daily/Weekly top-right slot */
.stock-head {
  display: block !important;
}
.stock-head > div {
  width: 100% !important;
}
.stock-head > div:nth-child(2):empty {
  display: none !important;
}
.badge-strip {
  margin-top: 0.42rem !important;
}


/* v31 mobile stock action buttons: force Like / Daily / Weekly into one row */
@media (max-width: 768px) {
  div[data-testid="stHorizontalBlock"]:has(.stButton) {
    display: grid !important;
    grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
    gap: 0.28rem !important;
    align-items: stretch !important;
  }
  div[data-testid="stHorizontalBlock"]:has(.stButton) > div[data-testid="column"] {
    width: 100% !important;
    min-width: 0 !important;
    flex: 1 1 0 !important;
  }
  .stButton > button {
    min-height: 2.05rem !important;
    height: 2.05rem !important;
    padding: 0.18rem 0.18rem !important;
    font-size: 0.70rem !important;
    line-height: 1 !important;
    white-space: nowrap !important;
    width: 100% !important;
  }
  .stButton > button p,
  .stButton > button span {
    font-size: 0.70rem !important;
    line-height: 1 !important;
    white-space: nowrap !important;
  }
}

</style>
""",
    unsafe_allow_html=True,
)


def h(value) -> str:
    try:
        if pd.isna(value):
            return "-"
    except Exception:
        pass
    return html.escape(str(value))


@st.cache_data(show_spinner=False)
def read_csv_cached(path: str, mtime_ns: int) -> pd.DataFrame:
    return pd.read_csv(path)


def safe_read(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return read_csv_cached(str(path), path.stat().st_mtime_ns)
    except Exception:
        return pd.DataFrame()


def boolish(value) -> bool:
    if isinstance(value, bool):
        return value
    try:
        if pd.isna(value):
            return False
    except Exception:
        pass
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in {"1", "true", "yes", "y", "t"}


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    if "Company Name" not in out.columns:
        for col in ["Company Name_x", "Company Name_y", "company", "company_name", "name"]:
            if col in out.columns:
                out["Company Name"] = out[col]
                break
    if "Industry" not in out.columns:
        for col in ["Industry_x", "Industry_y", "industry", "sector", "Sector"]:
            if col in out.columns:
                out["Industry"] = out[col]
                break
    if "ticker" not in out.columns:
        for col in ["Ticker", "symbol", "Symbol", "SYMBOL"]:
            if col in out.columns:
                out["ticker"] = out[col].astype(str)
                break
    if "ticker" in out.columns:
        out["ticker"] = out["ticker"].astype(str).str.strip()
    return out


def numeric(df: pd.DataFrame, cols) -> pd.DataFrame:
    out = df.copy()
    for col in cols:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


def filter_include_signal(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only the universe rows explicitly marked Include == 1 when the column exists."""
    if df.empty:
        return df
    out = df.copy()
    include_col = next((c for c in ["Include", "include", "include_signal", "include signal"] if c in out.columns), None)
    if include_col is None:
        return out
    mask = out[include_col].apply(boolish)
    return out[mask].copy()


def is_fo_row(row: pd.Series) -> bool:
    if boolish(row.get("is_fo_stock", False)):
        return True
    raw = str(row.get("fo_category", row.get("f&o", row.get("F&O", ""))) or "").strip().lower()
    return raw in {"f&o", "fo", "fno", "yes", "true", "1"}


def ensure_current_rank(df: pd.DataFrame, score_col: str = "final_combined_score") -> pd.DataFrame:
    if df.empty:
        return df
    out = normalize_columns(df).copy()
    rank_candidates = ["current_rank", "rank", "rs_rank", "daily_rank", "weekly_rank", "final_rank", "combined_rank", "stock_rank"]
    existing = next((c for c in rank_candidates if c in out.columns), None)
    if existing:
        out["current_rank"] = pd.to_numeric(out[existing], errors="coerce")
    else:
        fallback_cols = [score_col, "combined_score", "final_daily_score", "daily_score", "avg_combined_score"]
        sort_col = next((c for c in fallback_cols if c in out.columns), None)
        if sort_col:
            out = out.sort_values(sort_col, ascending=False, na_position="last").reset_index(drop=True)
        out["current_rank"] = range(1, len(out) + 1)
    return out


def load_outputs(outdir: Path):
    combined = ensure_current_rank(safe_read(outdir / "vcp_combined_ranked.csv"))
    daily = ensure_current_rank(safe_read(outdir / "vcp_daily_ranked.csv"), "final_daily_score")
    weekly = ensure_current_rank(safe_read(outdir / "vcp_weekly_ranked.csv"), "final_weekly_score")
    industry = ensure_current_rank(safe_read(outdir / "industry_strength.csv"), "avg_combined_score")
    changes = ensure_current_rank(safe_read(outdir / "stock_changes.csv"))
    industry_changes = ensure_current_rank(safe_read(outdir / "industry_changes.csv"), "avg_combined_score")
    moves = normalize_columns(safe_read(outdir / "stock_price_moves.csv"))
    regime = safe_read(outdir / "market_regime.csv")
    history = normalize_columns(safe_read(outdir / "stage_action_history.csv"))

    num_cols = [
        "current_rank", "prev_rank", "rank_change", "final_combined_score", "combined_score",
        "daily_breakout_distance_pct", "weekly_breakout_distance_pct", "rs_3m_pct", "rs_6m_pct",
        "volume_dryup_ratio", "breakout_volume_ratio", "avg_turnover_inr", "avg_combined_score",
        "change_1d_pct", "day_change_pct", "move_1d_pct", "pct_change_1d", "return_1d_pct",
        "daily_return_pct", "change_pct", "pct_change", "1d_change_pct", "daily_move_pct",
    ]
    combined = numeric(combined, num_cols)
    daily = numeric(daily, num_cols)
    weekly = numeric(weekly, num_cols)
    industry = numeric(industry, num_cols)
    changes = numeric(changes, num_cols)
    industry_changes = numeric(industry_changes, num_cols)
    moves = numeric(moves, num_cols)
    history = numeric(history, num_cols)
    # Dashboard safety filter: the engine should already apply Include == 1,
    # but keep this here so old output files do not leak excluded stocks into the UI.
    combined = filter_include_signal(combined)
    daily = filter_include_signal(daily)
    weekly = filter_include_signal(weekly)
    changes = filter_include_signal(changes)
    moves = filter_include_signal(moves)
    history = filter_include_signal(history)
    return combined, daily, weekly, industry, changes, industry_changes, moves, regime, history


def latest_output_timestamp(outdir: Path, history: pd.DataFrame) -> pd.Timestamp | None:
    files = [
        outdir / "vcp_combined_ranked.csv",
        outdir / "industry_strength.csv",
        outdir / "market_regime.csv",
        outdir / "stock_changes.csv",
        outdir / "interesting20_latest.csv",
    ]
    mtimes = [p.stat().st_mtime for p in files if p.exists()]
    if mtimes:
        return pd.Timestamp.fromtimestamp(max(mtimes), tz="Asia/Kolkata")
    if not history.empty and "snapshot_date" in history.columns:
        dates = pd.to_datetime(history["snapshot_date"], errors="coerce")
        if dates.notna().any():
            return pd.Timestamp(dates.max()).tz_localize("Asia/Kolkata") if pd.Timestamp(dates.max()).tzinfo is None else pd.Timestamp(dates.max()).tz_convert("Asia/Kolkata")
    return None


def latest_update_date(outdir: Path, history: pd.DataFrame) -> str:
    ts = latest_output_timestamp(outdir, history)
    if ts is None:
        return "Not available"
    return ts.date().isoformat()


def generated_at_text(outdir: Path, history: pd.DataFrame) -> str:
    ts = latest_output_timestamp(outdir, history)
    if ts is None:
        return "Updated time not available yet · Latest date: Not available"
    time_text = ts.strftime("%I:%M %p").lstrip("0")
    date_text = ts.strftime("%d-%b-%y")
    return f"· Updated on {date_text} {time_text} IST · "


def market_mode_text(regime: pd.DataFrame, combined: pd.DataFrame) -> str:
    if not regime.empty and "regime_label" in regime.columns:
        raw = str(regime.iloc[0].get("regime_label", "")).strip()
        return {
            "strong_risk_on": "Strong Risk On",
            "risk_on": "Risk On",
            "mixed": "Mixed",
            "risk_off": "Risk Off",
            "strong_risk_off": "Strong Risk Off",
        }.get(raw, raw.replace("_", " ").title() if raw else "Mixed")
    if combined.empty or "stage" not in combined.columns:
        return "Mixed"
    stage2_pct = (combined["stage"].astype(str).eq("Stage 2").mean() * 100) if len(combined) else 0
    if stage2_pct >= 35:
        return "Risk On"
    if stage2_pct <= 12:
        return "Risk Off"
    return "Mixed"


def industry_icon(industry: str) -> str:
    ind = str(industry or "").lower()
    mapping = [
        (["bank", "nbfc", "credit services", "finance", "financial", "insurance", "capital markets","asset management"], "🏦"),
        (["software", "information technology", "technology", "internet", "semiconductor", "electronic"], "💻"),
        (["drug", "pharma", "biotech", "life sciences", "diagnostic", "healthcare plans"], "💊"),
        (["medical care", "hospital", "health", "clinic", "facilities"], "🏥"),
        (["auto", "automobile", "vehicle", "two wheel", "tyre", "tire", "auto parts"], "🚗"),
        (["steel", "metal", "mining", "aluminium", "aluminum", "copper", "coal"], "⛓️"),
        (["oil", "gas", "refining", "energy", "power", "utilities", "renewable", "solar"], "⚡"),
        (["fmcg", "consumer defensive", "household", "personal products", "packaged foods", "beverages", "food"], "🛒"),
        (["retail", "apparel", "luxury", "consumer cyclical", "footwear"], "🛍️"),
        (["realty", "real estate", "construction", "cement", "infra", "building materials"], "🏗️"),
        (["telecom", "communication", "media", "entertainment"], "📡"),
        (["chemical", "fertilizer", "paint", "specialty chemicals", "agro chemicals"], "🧪"),
        (["electrical", "equipment", "parts", "machinery", "capital goods", "engineering", "industrial", "tools"], "⚙️"),
        (["aerospace", "defense", "defence", "aviation"], "✈️"),
        (["textile", "fabric", "garment"], "🧵"),
        (["hotel", "tourism", "travel", "restaurant", "leisure","Furnishings"], "🏨"),
        (["marine", "shipping", "logistics", "transport", "rail"], "🚢"),
        (["paper", "packaging", "containers"], "📦"),
        (["agriculture", "farm", "crop", "seeds"], "🌾"),
    ]
    for keys, icon in mapping:
        if any(k in ind for k in keys):
            return icon
    return "▫️"


def stage_counts_by_industry(combined: pd.DataFrame) -> pd.DataFrame:
    if combined.empty or "Industry" not in combined.columns or "stage" not in combined.columns:
        return pd.DataFrame(columns=["Industry", "Stage 2 Stocks", "Stage 4 Stocks", "Total Stocks"])
    temp = combined.copy()
    temp["Industry"] = temp["Industry"].fillna("Unknown").astype(str).str.strip()
    pivot = temp.groupby("Industry")["stage"].agg(
        **{
            "Stage 2 Stocks": lambda s: int(s.astype(str).eq("Stage 2").sum()),
            "Stage 4 Stocks": lambda s: int(s.astype(str).eq("Stage 4").sum()),
            "Total Stocks": "count",
        }
    ).reset_index()
    return pivot


def build_industry_table(industry: pd.DataFrame, industry_changes: pd.DataFrame, combined: pd.DataFrame) -> pd.DataFrame:
    base = industry_changes if not industry_changes.empty else industry
    counts = stage_counts_by_industry(combined)
    if base.empty:
        if counts.empty:
            return pd.DataFrame(columns=["Industry Raw", "Industry", "Current Rank", "Stage 2 Stocks", "Stage 4 Stocks", "Total Stocks"])
        out = counts.copy()
        out["current_rank"] = out["Stage 2 Stocks"].rank(ascending=False, method="dense")
        out["prev_rank"] = pd.NA
    else:
        base = ensure_current_rank(normalize_columns(base), "avg_combined_score").copy()
        if "prev_rank" not in base.columns:
            base["prev_rank"] = pd.NA
        keep = [c for c in ["Industry", "current_rank", "prev_rank", "avg_combined_score", "rs_rank", "rank_change"] if c in base.columns]
        out = base[keep].drop_duplicates("Industry")
        out = out.merge(counts, on="Industry", how="left")
    for col in ["Stage 2 Stocks", "Stage 4 Stocks", "Total Stocks"]:
        out[col] = pd.to_numeric(out.get(col, 0), errors="coerce").fillna(0).astype(int)
    out = out[out["Total Stocks"] >= 7].copy()
    # Sort by the raw engine/database industry rank, but display a compact visible rank
    # for the filtered Top-8 table. This avoids confusing rows like 12, 17, 23 after
    # industries with fewer than 10 stocks have been removed.
    out = out.sort_values(["current_rank", "Stage 2 Stocks"], ascending=[True, False], na_position="last").head(8).reset_index(drop=True)
    out["Raw Dataset Rank"] = pd.to_numeric(out.get("current_rank"), errors="coerce").round(0).astype("Int64")
    out["Current Rank"] = range(1, len(out) + 1)
    out["Industry Raw"] = out["Industry"].astype(str)
    out["Industry"] = out["Industry Raw"].apply(lambda x: f"{industry_icon(x)} {x}")
    if "prev_rank" in out.columns:
        out["_Previous Rank Internal"] = pd.to_numeric(out["prev_rank"], errors="coerce").round(0).astype("Int64")
    return out[["Industry Raw", "Industry", "Current Rank", "Stage 2 Stocks", "Stage 4 Stocks", "Total Stocks"]].reset_index(drop=True)


def leader_sector_names(industry_table: pd.DataFrame, n: int = 3) -> list[str]:
    if industry_table.empty:
        return []
    top = industry_table.sort_values(["Current Rank", "Stage 2 Stocks"], ascending=[True, False], na_position="last").head(n)
    return top["Industry"].dropna().astype(str).tolist()


def clean_leader_sector_text(leaders: list[str]) -> str:
    if not leaders:
        return "Not available"
    cleaned = []
    for name in leaders[:3]:
        text = str(name).strip()
        text = re.sub(r"^[^A-Za-z0-9]+\s*", "", text).strip()
        cleaned.append(text)
    return ", ".join(cleaned) if cleaned else "Not available"


def _pct_from_first_row(df: pd.DataFrame, *cols: str) -> float | None:
    if df.empty:
        return None
    for col in cols:
        if col in df.columns:
            value = pd.to_numeric(pd.Series([df.iloc[0].get(col)]), errors="coerce").iloc[0]
            if pd.notna(value):
                return float(value)
    return None


def _tone_from_mode(mode_text: str) -> str:
    mode = str(mode_text or "").lower()
    if "strong risk on" in mode:
        return "broad risk appetite is strong"
    if "risk on" in mode:
        return "risk appetite is constructive"
    if "strong risk off" in mode:
        return "risk appetite is weak"
    if "risk off" in mode:
        return "risk appetite is defensive"
    return "market structure is mixed"


def build_market_story(mode_text: str, stage2_count: int, leaders: list[str], reset_summary: dict, regime: pd.DataFrame, industry_table: pd.DataFrame) -> list[str]:
    """Create a SEBI-safe, data-only daily narrative.

    This intentionally avoids buy/sell language, targets, conviction calls, and stock-specific
    recommendations. It only describes market breadth, sector/industry leadership, and
    changes in the rule-based scan.
    """
    story: list[str] = []
    leader_text = clean_leader_sector_text(leaders)
    b20 = _pct_from_first_row(regime, "breadth_above_20_pct")
    b50 = _pct_from_first_row(regime, "breadth_above_50_pct")

    if leader_text != "Not available":
        story.append(f"{leader_text} are currently leading the industry structure table.")
    else:
        story.append(f"{_tone_from_mode(mode_text).capitalize()} based on the latest rule-based scan.")

    if b20 is not None and b50 is not None:
        if b20 >= b50 + 8:
            story.append(f"Short-term breadth is improving: {b20:.0f}% of tracked stocks are above the 20-DMA versus {b50:.0f}% above the 50-DMA.")
        elif b20 <= b50 - 8:
            story.append(f"Short-term breadth is cooling: {b20:.0f}% of tracked stocks are above the 20-DMA versus {b50:.0f}% above the 50-DMA.")
        else:
            story.append(f"Breadth is balanced: {b20:.0f}% are above the 20-DMA and {b50:.0f}% are above the 50-DMA.")
    elif stage2_count > 0:
        story.append(f"Stage 2 participation stands at {stage2_count} stocks in the current universe.")

    new_stage2 = int(reset_summary.get("new_stage2", 0) or 0)
    repeated = int(reset_summary.get("repeated", 0) or 0)
    if new_stage2 > 0:
        story.append(f"Fresh Stage 2 additions are visible today with {new_stage2} new names from the scan.")
    elif repeated > 0:
        story.append(f"Leadership is stable: {repeated} Interesting 20 names repeated from the previous snapshot.")
    elif not industry_table.empty:
        story.append("Leadership remains selective across the top-ranked industries.")

    return story[:3]


def build_today_summary_html(mode_text: str, stage2_count: int, leaders: list[str], reset_summary: dict, regime: pd.DataFrame | None = None, industry_table: pd.DataFrame | None = None) -> str:
    regime = regime if regime is not None else pd.DataFrame()
    industry_table = industry_table if industry_table is not None else pd.DataFrame()
    rows = [
        ("Market Mood", mode_text or "Mixed"),
        ("Stage 2 Stocks", str(stage2_count)),
        ("Leader Industries", clean_leader_sector_text(leaders)),
    ]
    repeated = int(reset_summary.get("repeated", 0) or 0)
    new_stage2 = int(reset_summary.get("new_stage2", 0) or 0)
    if new_stage2 > 0:
        rows.append(("Fresh Stage 2", f"{new_stage2} names"))
    if repeated > 0:
        rows.append(("Interesting 20", f"{repeated} repeated from yesterday"))
    body = "".join(
        f'<div class="today-summary-row"><div class="today-summary-label">{h(label)}</div><div class="today-summary-value">{h(value)}</div></div>'
        for label, value in rows
    )
    story_lines = "".join(
        f'<div class="market-story-line">{h(line)}</div>'
        for line in build_market_story(mode_text, stage2_count, leaders, reset_summary, regime, industry_table)
    )
    return f"""
<div class="today-summary-card">
  <div class="today-summary-title">Today's Market Story</div>
  <div class="market-story-box">{story_lines}</div>
  <div class="today-summary-title today-summary-title-small">Scan Snapshot</div>
  <div class="today-summary-grid">{body}</div>
</div>
"""


def top_ranked_industries(industry_table: pd.DataFrame, n: int = 6) -> list[str]:
    if industry_table.empty or "Industry Raw" not in industry_table.columns:
        return []
    top = industry_table.sort_values(["Current Rank", "Stage 2 Stocks"], ascending=[True, False], na_position="last").head(n)
    return top["Industry Raw"].dropna().astype(str).tolist()


def industry_key(value) -> str:
    """Stable key for industry matching across output files and stock rows."""
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass
    s = str(value).strip()
    # Remove common leading emoji/symbol prefix if an already-display-formatted industry leaks in.
    s = re.sub(r"^[^A-Za-z0-9]+\s*", "", s)
    s = re.sub(r"\s+", " ", s)
    return s.lower()


def build_industry_rank_context(industry: pd.DataFrame, industry_changes: pd.DataFrame, combined: pd.DataFrame) -> tuple[dict[str, int], dict[str, int], dict[str, int]]:
    """Return (all_industry_position_map, top_support_position_map, weak_bottom_position_map).

    The visible badge now says only "Industry Rank: X".
    Styling still quietly highlights top-6 industries and bottom-8 industries.
    Industries with fewer than 10 stocks are excluded from ranking context.
    """
    counts = stage_counts_by_industry(combined)
    base = industry_changes if not industry_changes.empty else industry
    if base.empty:
        if counts.empty:
            return {}, {}, {}
        out = counts.copy()
        out["current_rank"] = out["Stage 2 Stocks"].rank(ascending=False, method="first")
    else:
        base = ensure_current_rank(normalize_columns(base), "avg_combined_score").copy()
        keep = [c for c in ["Industry", "current_rank", "avg_combined_score", "rs_rank", "rank_change"] if c in base.columns]
        out = base[keep].drop_duplicates("Industry").merge(counts, on="Industry", how="left")

    for col in ["Stage 2 Stocks", "Stage 4 Stocks", "Total Stocks"]:
        out[col] = pd.to_numeric(out.get(col, 0), errors="coerce").fillna(0).astype(int)

    out["Industry"] = out.get("Industry", pd.Series(dtype=str)).astype(str).str.strip()
    out["current_rank"] = pd.to_numeric(out.get("current_rank"), errors="coerce")
    out = out[(out["Total Stocks"] >= 7) & out["Industry"].ne("")].copy()
    if out.empty:
        return {}, {}, {}

    out = out.sort_values(["current_rank", "Stage 2 Stocks", "Industry"], ascending=[True, False, True], na_position="last").reset_index(drop=True)
    out["rank_position"] = range(1, len(out) + 1)

    all_map = {industry_key(r["Industry"]): int(r["rank_position"]) for _, r in out.iterrows()}
    top = out.head(6).copy()
    support_map = {industry_key(r["Industry"]): int(r["rank_position"]) for _, r in top.iterrows()}

    bottom = out.tail(8).copy().sort_values(["current_rank", "Stage 2 Stocks", "Industry"], ascending=[False, True, True], na_position="last").reset_index(drop=True)
    weak_map = {industry_key(r["Industry"]): i for i, (_, r) in enumerate(bottom.iterrows(), start=1)}
    return all_map, support_map, weak_map


def interesting_priority(row: pd.Series) -> float:
    priority = 0.0
    stage = str(row.get("stage", ""))
    combined_bucket = str(row.get("combined_bucket", ""))
    daily_bucket = str(row.get("daily_setup_bucket", ""))
    weekly_bucket = str(row.get("weekly_setup_bucket", ""))
    priority += {"Stage 2": 30, "Stage 1": 12, "Stage 3": 6, "Stage 4": 0}.get(stage, 4)
    priority += {"high_conviction_breakout": 70, "high_conviction_near_pivot": 62, "building_setup": 30, "watchlist": 8}.get(combined_bucket, 0)
    priority += {"breakout_today": 54, "near_pivot": 46, "building_setup": 25, "watchlist": 4}.get(daily_bucket, 0)
    priority += {"weekly_breakout": 42, "weekly_near_pivot": 36, "weekly_watchlist": 4}.get(weekly_bucket, 0)
    if boolish(row.get("volume_is_drying_up", False)):
        priority += 9
    if boolish(row.get("weekly_volume_is_drying_up", False)):
        priority += 7
    for col, points in [("daily_breakout_distance_pct", 14), ("weekly_breakout_distance_pct", 10)]:
        dist = pd.to_numeric(row.get(col), errors="coerce")
        if pd.notna(dist):
            if -5 <= float(dist) <= 1.5:
                priority += points
            elif 1.5 < float(dist) <= 4:
                priority += points * 0.45
    score = pd.to_numeric(row.get("final_combined_score", row.get("combined_score")), errors="coerce")
    if pd.notna(score):
        priority += min(float(score), 100) * 0.20
    rank = pd.to_numeric(row.get("current_rank"), errors="coerce")
    if pd.notna(rank):
        priority += max(0.0, 30.0 - min(float(rank), 30.0)) * 0.25
    return round(priority, 4)


def build_interesting20(combined: pd.DataFrame) -> pd.DataFrame:
    if combined.empty:
        return pd.DataFrame()
    df = ensure_current_rank(combined).copy()
    df = numeric(df, ["current_rank", "final_combined_score", "combined_score", "daily_breakout_distance_pct", "weekly_breakout_distance_pct"])
    pool = df[df["current_rank"].le(30)].copy()
    if pool.empty:
        pool = df.sort_values("current_rank", ascending=True, na_position="last").head(30).copy()
    pool["interesting_priority"] = pool.apply(interesting_priority, axis=1)
    sort_cols = ["interesting_priority", "current_rank"]
    ascending = [False, True]
    if "final_combined_score" in pool.columns:
        sort_cols.append("final_combined_score")
        ascending.append(False)
    return pool.sort_values(sort_cols, ascending=ascending, na_position="last").head(20).reset_index(drop=True)


def archive_date_from_path(path: Path):
    match = re.match(r"(\d{4}-\d{2}-\d{2})_interesting20\.csv$", path.name)
    if not match:
        return None
    try:
        return pd.to_datetime(match.group(1)).date()
    except Exception:
        return None


def archive_files(outdir: Path) -> list[tuple[object, Path]]:
    archive_dir = outdir / ARCHIVE_DIRNAME
    if not archive_dir.exists():
        return []
    files = []
    for path in archive_dir.glob("*_interesting20.csv"):
        dt = archive_date_from_path(path)
        if dt:
            files.append((dt, path))
    return sorted(files, key=lambda x: x[0])


def read_archive(path: Path) -> pd.DataFrame:
    return normalize_columns(safe_read(path))


def load_previous_interesting(outdir: Path, latest_date: str) -> pd.DataFrame:
    files = archive_files(outdir)
    if not files:
        return pd.DataFrame()
    try:
        latest_dt = pd.to_datetime(latest_date).date()
    except Exception:
        latest_dt = files[-1][0]
    eligible = [(dt, p) for dt, p in files if dt < latest_dt]
    if not eligible:
        return pd.DataFrame()
    return read_archive(eligible[-1][1])


def persist_interesting_snapshot(outdir: Path, interesting: pd.DataFrame, latest_date: str) -> None:
    if interesting.empty or latest_date == "Not available":
        return
    archive_dir = outdir / ARCHIVE_DIRNAME
    archive_dir.mkdir(parents=True, exist_ok=True)
    today_file = archive_dir / f"{latest_date}_interesting20.csv"
    latest_file = outdir / "interesting20_latest.csv"
    snapshot = interesting.copy()
    if "snapshot_date" not in snapshot.columns:
        snapshot.insert(0, "snapshot_date", latest_date)
    keep = [c for c in [
        "snapshot_date", "ticker", "Company Name", "Industry", "stage", "current_rank", "interesting_priority",
        "daily_setup_bucket", "weekly_setup_bucket", "combined_bucket", "final_combined_score", "rs_3m_pct", "rs_6m_pct",
        "volume_dryup_ratio", "breakout_volume_ratio", "volume_is_drying_up", "weekly_volume_is_drying_up",
    ] if c in snapshot.columns]
    snapshot = snapshot[keep]
    try:
        snapshot.to_csv(latest_file, index=False)
        snapshot.to_csv(today_file, index=False)
    except Exception:
        pass


def load_last_week_interesting(outdir: Path, latest_date: str, combined: pd.DataFrame) -> pd.DataFrame:
    files = archive_files(outdir)
    if not files:
        return pd.DataFrame()
    try:
        latest_dt = pd.to_datetime(latest_date).date()
    except Exception:
        latest_dt = files[-1][0]
    target = latest_dt - timedelta(days=7)
    eligible = [(dt, p) for dt, p in files if dt <= target]
    if not eligible:
        eligible = [(dt, p) for dt, p in files if dt < latest_dt]
    if not eligible:
        return pd.DataFrame()
    archived = read_archive(eligible[-1][1])
    if archived.empty:
        return pd.DataFrame()
    if "ticker" in archived.columns and not combined.empty and "ticker" in combined.columns:
        current = combined.drop_duplicates("ticker")
        merged = archived[["ticker"]].merge(current, on="ticker", how="left")
        fallback = archived.drop_duplicates("ticker").set_index("ticker", drop=False)
        for col in archived.columns:
            if col not in merged.columns:
                merged[col] = merged["ticker"].map(fallback[col])
        return ensure_current_rank(merged)
    return ensure_current_rank(archived)


def interesting_streaks(outdir: Path, latest_date: str, current_tickers: set[str]) -> dict[str, int]:
    files = archive_files(outdir)
    if not files:
        return {t: 1 for t in current_tickers}
    try:
        latest_dt = pd.to_datetime(latest_date).date()
    except Exception:
        latest_dt = files[-1][0]
    relevant = [(dt, p) for dt, p in files if dt <= latest_dt]
    relevant = sorted(relevant, key=lambda x: x[0], reverse=True)
    streaks = {}
    for ticker in current_tickers:
        streak = 0
        for _, path in relevant:
            df = read_archive(path)
            tickers = set(df.get("ticker", pd.Series(dtype=str)).dropna().astype(str))
            if ticker in tickers:
                streak += 1
            else:
                break
        streaks[ticker] = max(streak, 1)
    return streaks


def build_misc20(combined: pd.DataFrame, exclude_tickers: set[str], top_industries: list[str]) -> pd.DataFrame:
    if combined.empty:
        return pd.DataFrame()
    df = ensure_current_rank(combined).copy()
    if "ticker" in df.columns:
        df = df[~df["ticker"].astype(str).isin(exclude_tickers)].copy()
    if "Industry" in df.columns and top_industries:
        preferred = df[df["Industry"].astype(str).isin(top_industries)].copy()
    else:
        preferred = df.copy()
    frames = []
    stage_order = [("Stage 1", 5), ("Stage 2", 5), ("Stage 3", 5), ("Stage 4", 5)]
    for stage, limit in stage_order:
        part = preferred[preferred["stage"].astype(str).eq(stage)].sort_values("current_rank", ascending=True, na_position="last").head(limit).copy()
        if len(part) < limit:
            already = set(part.get("ticker", pd.Series(dtype=str)).astype(str)) if not part.empty and "ticker" in part.columns else set()
            fallback = df[(df["stage"].astype(str).eq(stage)) & (~df["ticker"].astype(str).isin(already))].sort_values("current_rank", ascending=True, na_position="last").head(limit - len(part))
            part = pd.concat([part, fallback], ignore_index=True)
        part["misc_stage_group"] = stage
        frames.append(part)
    out = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    return out.head(20).reset_index(drop=True)




def normalize_ticker_for_match(value) -> str:
    """Normalize ticker from trending_stocks.csv and output files for matching."""
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass
    text = str(value).strip().upper()
    if not text or text in {"NAN", "NONE"}:
        return ""
    if text.startswith("^") or text.endswith(".NS"):
        return text
    return f"{text}.NS"


def sort_stock_cards_alpha(df: pd.DataFrame) -> pd.DataFrame:
    """Sort stock-card views alphabetically by company/display name."""
    if df is None or df.empty:
        return pd.DataFrame() if df is None else df
    out = normalize_columns(df).copy()
    if "Company Name" in out.columns:
        key = out["Company Name"].fillna(out.get("ticker", "")).astype(str).str.lower()
    elif "ticker" in out.columns:
        key = out["ticker"].fillna("").astype(str).str.replace(".NS", "", regex=False).str.lower()
    else:
        return out.reset_index(drop=True)
    out["_alpha_sort_key"] = key
    out = out.sort_values(["_alpha_sort_key"], ascending=True, na_position="last").drop(columns=["_alpha_sort_key"], errors="ignore")
    return out.reset_index(drop=True)


def _read_trending_file(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        if path.suffix.lower() in {".xlsx", ".xls"}:
            return pd.read_excel(path)
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def load_trending_stocks(combined: pd.DataFrame, outdir: Path, limit: int = 20) -> pd.DataFrame:
    """Load manually curated Trending Stocks from CSV/XLSX and return matched stock rows.

    Supported locations, in priority order:
    - outputs/trending_stocks.csv
    - trending_stocks.csv beside this Streamlit file
    - outputs/trending_stocks.xlsx
    - trending_stocks.xlsx beside this Streamlit file

    The dashboard takes the first `limit` tickers from the manual file, matches them
    against vcp_combined_ranked.csv, then displays the matched cards alphabetically.
    """
    if combined.empty or "ticker" not in combined.columns:
        return pd.DataFrame()

    candidates = [
        outdir / "trending_stocks.csv",
        Path("trending_stocks.csv"),
        outdir / "trending_stocks.xlsx",
        Path("trending_stocks.xlsx"),
    ]
    raw = pd.DataFrame()
    for path in candidates:
        raw = _read_trending_file(path)
        if not raw.empty:
            break
    if raw.empty:
        return pd.DataFrame()

    ticker_col = None
    normalized_cols = {str(c).strip().lower().replace(" ", "_"): c for c in raw.columns}
    for cand in ["ticker", "symbol", "stock", "stock_symbol", "nse_symbol"]:
        if cand in normalized_cols:
            ticker_col = normalized_cols[cand]
            break
    if ticker_col is None:
        ticker_col = raw.columns[0]

    tickers = []
    seen = set()
    for value in raw[ticker_col].dropna().tolist():
        t = normalize_ticker_for_match(value)
        if t and t not in seen:
            seen.add(t)
            tickers.append(t)
        if len(tickers) >= limit:
            break
    if not tickers:
        return pd.DataFrame()

    combined_work = normalize_columns(combined).copy()
    combined_work["_ticker_key"] = combined_work["ticker"].apply(normalize_ticker_for_match)
    combined_work["_ticker_key_raw"] = combined_work["ticker"].astype(str).str.strip().str.upper()

    frames = []
    for order, ticker in enumerate(tickers, start=1):
        match = combined_work[combined_work["_ticker_key"].eq(ticker)]
        if match.empty:
            raw_key = ticker.replace(".NS", "")
            match = combined_work[combined_work["_ticker_key_raw"].str.replace(".NS", "", regex=False).eq(raw_key)]
        if not match.empty:
            row = match.head(1).copy()
            row["trending_order"] = order
            frames.append(row)
    if not frames:
        return pd.DataFrame()
    out = pd.concat(frames, ignore_index=True).drop(columns=["_ticker_key", "_ticker_key_raw"], errors="ignore")
    return sort_stock_cards_alpha(out)

def build_new_stage2(combined: pd.DataFrame, changes: pd.DataFrame, history: pd.DataFrame, latest_date: str) -> pd.DataFrame:
    if combined.empty:
        return pd.DataFrame()
    base = ensure_current_rank(combined).copy()
    entered = set()
    if not history.empty and "snapshot_date" in history.columns and "ticker" in history.columns and "stage" in history.columns:
        hist = history.copy()
        hist["snapshot_date"] = pd.to_datetime(hist["snapshot_date"], errors="coerce")
        hist = hist.dropna(subset=["snapshot_date"])
        if not hist.empty:
            try:
                latest_dt = pd.to_datetime(latest_date).normalize()
            except Exception:
                latest_dt = hist["snapshot_date"].max().normalize()
            window_start = latest_dt - pd.Timedelta(days=21)
            current_stage2 = set(base[base["stage"].astype(str).eq("Stage 2")]["ticker"].astype(str))
            for ticker in current_stage2:
                rows = hist[(hist["ticker"].astype(str) == ticker) & (hist["snapshot_date"] >= window_start)].sort_values("snapshot_date")
                if not rows.empty and rows["stage"].astype(str).ne("Stage 2").any():
                    entered.add(ticker)
    if not entered and not changes.empty and "entered_stage_2" in changes.columns and "ticker" in changes.columns:
        entered.update(changes[changes["entered_stage_2"].apply(boolish)]["ticker"].dropna().astype(str).tolist())
    if not entered:
        return pd.DataFrame()
    out = base[base["ticker"].astype(str).isin(entered)].sort_values("current_rank", ascending=True, na_position="last").head(9).reset_index(drop=True)
    return out


def sectors_improved_count(industry_changes: pd.DataFrame, industry_table: pd.DataFrame) -> int:
    df = industry_changes.copy() if not industry_changes.empty else pd.DataFrame()
    if not df.empty:
        df = normalize_columns(df)
        improved = pd.Series(False, index=df.index)
        if "rank_change" in df.columns:
            improved = improved | (pd.to_numeric(df["rank_change"], errors="coerce") > 0)
        if "current_rank" in df.columns and "prev_rank" in df.columns:
            improved = improved | (pd.to_numeric(df["current_rank"], errors="coerce") < pd.to_numeric(df["prev_rank"], errors="coerce"))
        if "Industry" in df.columns:
            return int(df.loc[improved, "Industry"].dropna().astype(str).nunique())
        return int(improved.sum())
    if not industry_table.empty and "_Previous Rank Internal" in industry_table.columns:
        improved = pd.to_numeric(industry_table["Current Rank"], errors="coerce") < pd.to_numeric(industry_table["_Previous Rank Internal"], errors="coerce")
        return int(improved.fillna(False).sum())
    return 0


def build_reset_summary(new_stage2: pd.DataFrame, industry_changes: pd.DataFrame, industry_table: pd.DataFrame, interesting20: pd.DataFrame, previous_interesting: pd.DataFrame) -> dict:
    current = set(interesting20.get("ticker", pd.Series(dtype=str)).dropna().astype(str))
    previous = set(previous_interesting.get("ticker", pd.Series(dtype=str)).dropna().astype(str))
    repeated = len(current & previous) if previous else 0
    dropped = len(previous - current) if previous else 0
    improved = sectors_improved_count(industry_changes, industry_table)
    return {
        "new_stage2": int(len(new_stage2)),
        "sectors_improved": int(improved),
        "repeated": int(repeated),
        "dropped": int(dropped),
    }


def resolve_chart_path(chart_dir: Path, ticker: str, suffix: str):
    if not chart_dir.exists():
        return None
    ticker = str(ticker).strip()
    raw = ticker.replace(".NS", "")
    candidates = []
    for candidate in {
        ticker, raw,
        ticker.replace(".", "_"), raw.replace(".", "_"),
        ticker.replace("&", "_"), raw.replace("&", "_"),
        ticker.replace("&", "AND"), raw.replace("&", "AND"),
        re.sub(r"[^A-Za-z0-9]+", "_", ticker),
        re.sub(r"[^A-Za-z0-9]+", "_", raw),
        re.sub(r"[^A-Za-z0-9]+", "", ticker),
        re.sub(r"[^A-Za-z0-9]+", "", raw),
    }:
        if candidate:
            candidates.append(candidate + suffix)
    for name in candidates:
        path = chart_dir / name
        if path.exists():
            return path
    raw_key = re.sub(r"[^A-Za-z0-9]+", "", raw).lower()
    for path in chart_dir.glob(f"*{suffix}"):
        stem_key = re.sub(r"[^A-Za-z0-9]+", "", path.stem).lower()
        if raw_key and raw_key in stem_key:
            return path
    return None


def _chart_lookup_key(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "", str(value or "")).lower()


def build_chart_index(chart_dir: Path, suffix: str) -> dict[str, str]:
    """Index chart filenames once so every stock card does not scan the chart folder."""
    if not chart_dir.exists():
        return {}
    index: dict[str, str] = {}
    for path in chart_dir.glob(f"*{suffix}"):
        stem = path.name[:-len(suffix)] if path.name.endswith(suffix) else path.stem
        keys = {
            path.name.lower(),
            stem.lower(),
            _chart_lookup_key(stem),
            _chart_lookup_key(stem.replace("_", ".")),
        }
        for key in keys:
            if key:
                index.setdefault(key, str(path))
    return index


def resolve_chart_path_fast(ticker: str, suffix: str) -> Path | None:
    ticker = str(ticker or "").strip()
    raw = ticker.replace(".NS", "")
    index = DAILY_CHART_INDEX if suffix == "_daily.png" else WEEKLY_CHART_INDEX
    candidates = {
        ticker, raw,
        ticker.replace(".", "_"), raw.replace(".", "_"),
        ticker.replace("&", "_"), raw.replace("&", "_"),
        ticker.replace("&", "AND"), raw.replace("&", "AND"),
        re.sub(r"[^A-Za-z0-9]+", "_", ticker),
        re.sub(r"[^A-Za-z0-9]+", "_", raw),
        re.sub(r"[^A-Za-z0-9]+", "", ticker),
        re.sub(r"[^A-Za-z0-9]+", "", raw),
    }
    for candidate in candidates:
        if not candidate:
            continue
        for key in [candidate.lower(), _chart_lookup_key(candidate)]:
            path_str = index.get(key)
            if path_str:
                return Path(path_str)
    raw_key = _chart_lookup_key(raw)
    if raw_key:
        for key, path_str in index.items():
            if raw_key in key:
                return Path(path_str)
    return None


@st.cache_data(show_spinner=False)
def image_bytes(path: str, mtime_ns: int) -> bytes:
    return Path(path).read_bytes()


def get_chart_bytes(chart_dir: Path, ticker: str, suffix: str):
    path = resolve_chart_path_fast(ticker, suffix)
    if not path:
        return None
    try:
        return image_bytes(str(path), path.stat().st_mtime_ns)
    except Exception:
        return None



def _first_existing_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    if df is None or df.empty:
        return None
    lower_map = {str(c).lower(): c for c in df.columns}
    for candidate in candidates:
        if candidate in df.columns:
            return candidate
        if candidate.lower() in lower_map:
            return lower_map[candidate.lower()]
    return None


def build_top_movers(moves: pd.DataFrame, combined: pd.DataFrame, limit: int = 10) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build top/bottom daily movers from stock_price_moves.csv, with a combined-output fallback."""
    base = normalize_columns(moves.copy()) if moves is not None and not moves.empty else normalize_columns(combined.copy())
    if base.empty:
        return pd.DataFrame(), pd.DataFrame()

    move_col = _first_existing_column(base, [
        "change_1d_pct", "daily_move_pct", "day_change_pct", "move_1d_pct", "pct_change_1d",
        "return_1d_pct", "daily_return_pct", "change_pct", "pct_change", "1d_change_pct",
        "change_1d", "daily_change", "move_pct",
    ])
    if move_col is None:
        return pd.DataFrame(), pd.DataFrame()

    base["move_pct"] = pd.to_numeric(base[move_col], errors="coerce")
    base = base.dropna(subset=["move_pct"]).copy()
    if base.empty:
        return pd.DataFrame(), pd.DataFrame()

    # Enrich movers with the full combined output so mover cards look like the other stock cards.
    if not combined.empty and "ticker" in base.columns and "ticker" in combined.columns:
        enrich = normalize_columns(combined.drop_duplicates("ticker").copy())
        if not enrich.empty:
            base = base.merge(enrich, on="ticker", how="left", suffixes=("", "_combined"))
            for col in enrich.columns:
                if col == "ticker":
                    continue
                alt = f"{col}_combined"
                if alt in base.columns:
                    if col not in base.columns:
                        base[col] = base[alt]
                    else:
                        base[col] = base[col].where(base[col].notna() & (base[col].astype(str).str.strip() != ""), base[alt])

    base = base.drop_duplicates("ticker") if "ticker" in base.columns else base
    top = base.sort_values("move_pct", ascending=False).head(limit).copy()
    bottom = base.sort_values("move_pct", ascending=True).head(limit).copy()
    return top.reset_index(drop=True), bottom.reset_index(drop=True)


def format_move_pct(value) -> str:
    val = pd.to_numeric(value, errors="coerce")
    if pd.isna(val):
        return "-"
    return f"{float(val):+.2f}%"


def render_movers_table(df: pd.DataFrame, title: str):
    st.markdown(f'<div class="kicker">{h(title)}</div>', unsafe_allow_html=True)
    if df.empty:
        st.info("Top mover data is not available from the current output yet.")
        return
    display = df.copy()
    display["Stock"] = display.apply(stock_display_name, axis=1)
    if "Industry" in display.columns:
        display["Industry"] = display["Industry"].apply(lambda x: f"{industry_icon(str(x))} {x}" if str(x).strip() else "-")
    else:
        display["Industry"] = "-"
    display["Move"] = display["move_pct"].apply(format_move_pct)
    cols = ["Stock", "Industry", "Move"]
    st.dataframe(display[cols], use_container_width=True, hide_index=True, height=385)

def stock_display_name(row: pd.Series) -> str:
    company = str(row.get("Company Name", "") or "").strip()
    ticker = str(row.get("ticker", "") or "").replace(".NS", "").strip()
    if company and ticker:
        return f"{company} ({ticker})"
    return company or ticker or "Stock"


def volume_text(row: pd.Series) -> str:
    ratio = pd.to_numeric(row.get("breakout_volume_ratio"), errors="coerce")
    if pd.isna(ratio):
        ratio = pd.to_numeric(row.get("volume_dryup_ratio"), errors="coerce")
    if pd.isna(ratio):
        return "Volume: not available"
    direction = "More Than" if float(ratio) >= 1 else "Less Than"
    return f"Volume: {float(ratio):.1f}x {direction} Daily Average"


def rs_text(value, months: str) -> str:
    val = pd.to_numeric(value, errors="coerce")
    label_map = {"3m": "3 Months", "6m": "6 Months", "1m": "1 Month", "12m": "12 Months"}
    label = label_map.get(str(months).strip().lower(), str(months))
    if pd.isna(val):
        return f"Nifty Relative: not available for {label}"
    arrow = "↑" if float(val) >= 0 else "↓"
    verb = "Outperformed" if float(val) >= 0 else "Underperformed"
    return f"{verb} {arrow} Nifty : {abs(float(val)):.1f}% in {label}"


def safe_key(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]+", "_", str(text))[:80]


def rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    if hasattr(st, "experimental_rerun"):
        st.experimental_rerun()


def render_metric(title: str, value: str, subtitle: str = ""):
    st.markdown(
        f"""
<div class="metric-card">
  <div class="kicker">{h(title)}</div>
  <div class="metric-value">{h(value)}</div>
  <div class="metric-sub">{h(subtitle)}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def badge_html(label: str, css_class: str) -> str:
    return f'<span class="fresh-pill {css_class}">{h(label)}</span>'


def render_stock_card(row: pd.Series, idx: int, daily_dir: Path, weekly_dir: Path, freshness_badges: list[tuple[str, str]] | None = None, streak: int | None = None):
    ticker = str(row.get("ticker", "") or "").strip()
    key = safe_key(ticker or f"row_{idx}")
    mode_key = f"chart_mode_{key}"
    if mode_key not in st.session_state:
        st.session_state[mode_key] = "Daily"

    liked = st.session_state.setdefault("liked_tickers", [])
    is_liked = ticker in liked

    stage = str(row.get("stage", "-") or "-")
    stage_variant = str(row.get("stage_variant", "") or "").strip()
    stage_confidence = pd.to_numeric(row.get("stage_confidence"), errors="coerce")

    variant_line = ""
    if stage_variant and stage_variant not in {"nan", "None", stage}:
        if pd.notna(stage_confidence):
            variant_line = f"<div class=\"stage-variant\">Variant: {h(stage_variant)} · Confidence: {float(stage_confidence) * 100:.0f}%</div>"
        else:
            variant_line = f"<div class=\"stage-variant\">Variant: {h(stage_variant)}</div>"
    elif stage_variant and stage_variant == stage and pd.notna(stage_confidence):
        variant_line = f"<div class=\"stage-variant\">Confidence: {float(stage_confidence) * 100:.0f}%</div>"

    industry_raw = str(row.get("Industry", row.get("industry", "-")) or "-")
    sector_raw = str(row.get("sector", row.get("Sector", "")) or "").strip()
    group_raw = str(row.get("industry_group", row.get("Industry Group", row.get("industry group", ""))) or "").strip()

    industry = f"{industry_icon(industry_raw)} {industry_raw}" if industry_raw and industry_raw != "-" else "-"
    name = stock_display_name(row)
    chart_mode = st.session_state.get(mode_key, "Daily")
    chart_dir = daily_dir if chart_mode == "Daily" else weekly_dir
    suffix = "_daily.png" if chart_mode == "Daily" else "_weekly.png"
    chart = get_chart_bytes(chart_dir, ticker, suffix) if ticker else None

    badges = list(freshness_badges or [])
    if is_fo_row(row):
        badges.insert(0, ("F&O", "fo"))
    industry_match_key = industry_key(industry_raw)
    industry_rank = INDUSTRY_POSITION_MAP.get(industry_match_key)
    top_position = INDUSTRY_RANK_MAP.get(industry_match_key)
    weak_position = WEAK_INDUSTRY_POSITION_MAP.get(industry_match_key)
    if industry_rank:
        badge_style = "support" if top_position else "weak" if weak_position else "rank"
        badges.append((f"Industry Rank: {industry_rank}", badge_style))
    if streak and streak >= 2:
        badges.append((f"Seen in Interesting 20 for {streak} days", "repeat"))
    if is_liked:
        badges.insert(0, ("Liked", "support"))
    badge_line = "".join([badge_html(label, css_class) for label, css_class in badges])

    extra_meta = []

    extra_meta_line = ""
    if extra_meta:
        extra_meta_line = f"<div class=\"stock-meta\">{' · '.join(extra_meta)}</div>"

    # Use a real Streamlit container so the text, chart, and buttons are inside one card.
    with st.container(border=True):
        st.markdown(
            f"""
<div class="stock-card">
  <div class="stock-head">
    <div>
      <div class="stock-name">{h(name)} — {h(stage)}</div>
      {variant_line}
      <div class="stock-meta">Industry: {h(industry)}</div>
      {extra_meta_line}
    </div>
  </div>
  <div class="badge-strip">{badge_line}</div>
  <div class="signal-line">{h(volume_text(row))}</div>
  <div class="signal-line">{h(rs_text(row.get('rs_3m_pct'), '3m'))}</div>
</div>
""",
            unsafe_allow_html=True,
        )

        if chart:
            st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
            st.image(chart, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="chart-missing">Chart not available for this stock yet.</div>', unsafe_allow_html=True)

        st.markdown('<div class="stock-actions-marker"></div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            like_label = "♥ Liked" if is_liked else "♡ Like"
            if st.button(like_label, key=f"like_{key}_{idx}", use_container_width=True, type=("primary" if is_liked else "secondary")):
                liked = st.session_state.setdefault("liked_tickers", [])
                if ticker and ticker not in liked:
                    liked.append(ticker)
                rerun()
        with c2:
            daily_label = "Daily"
            if st.button(daily_label, key=f"daily_{key}_{idx}", use_container_width=True, type=("primary" if chart_mode == "Daily" else "secondary")):
                st.session_state[mode_key] = "Daily"
                rerun()
        with c3:
            weekly_label = "Weekly"
            if st.button(weekly_label, key=f"weekly_{key}_{idx}", use_container_width=True, type=("primary" if chart_mode == "Weekly" else "secondary")):
                st.session_state[mode_key] = "Weekly"
                rerun()

        if is_liked:
            st.markdown('<div class="liked-note">Saved to your liked list for this session.</div>', unsafe_allow_html=True)


DAILY_CHART_INDEX: dict[str, str] = {}
WEEKLY_CHART_INDEX: dict[str, str] = {}
INDUSTRY_POSITION_MAP: dict[str, int] = {}
INDUSTRY_RANK_MAP: dict[str, int] = {}
WEAK_INDUSTRY_POSITION_MAP: dict[str, int] = {}



def render_connect_feedback_section():
    st.markdown(
        """
<div class="feedback-card">
  <div class="feedback-title">Connect & Feedback</div>
  <div class="feedback-sub">Share your view on this market-structure page, what felt useful, what was confusing, and your email ID if you want a reply.</div>
</div>
""",
        unsafe_allow_html=True,
    )
    with st.form("connect_feedback_form", clear_on_submit=False):
        visitor_email = st.text_input("Your email ID", placeholder="name@example.com")
        feedback_text = st.text_area(
            "Your view / feedback",
            placeholder="What should be improved? Which section was useful? What would make you come back daily?",
            height=130,
        )
        submitted = st.form_submit_button("Prepare feedback email", use_container_width=True)

    if submitted:
        subject = "Feedback for Market Structure Daily"
        body = (
            "Hi,\n\n"
            "Here is my feedback for the Market Structure Daily page.\n\n"
            f"My email ID: {visitor_email or 'Not provided'}\n\n"
            "Feedback / view:\n"
            f"{feedback_text or 'Not provided'}\n\n"
            "Regards"
        )
        mailto = f"mailto:{FEEDBACK_EMAIL}?subject={quote(subject)}&body={quote(body)}"
        st.markdown(
            f'<a class="feedback-mail-link" href="{mailto}">Open email to send feedback</a>',
            unsafe_allow_html=True,
        )
        st.caption(f"This opens your email app addressed to {FEEDBACK_EMAIL}. Please press Send in your email app.")


combined, daily_df, weekly_df, industry, changes, industry_changes, moves, regime, history = load_outputs(OUTPUT_DIR)

if combined.empty:
    st.error("No VCP output found. Put the generated CSV files inside an outputs folder beside this Streamlit file.")
    st.stop()

industry_table = build_industry_table(industry, industry_changes, combined)
interesting20 = sort_stock_cards_alpha(build_interesting20(combined))
trending20 = load_trending_stocks(combined, OUTPUT_DIR, limit=20)
latest_date = latest_update_date(OUTPUT_DIR, history)
previous_interesting = load_previous_interesting(OUTPUT_DIR, latest_date)
new_stage2 = sort_stock_cards_alpha(build_new_stage2(combined, changes, history, latest_date))
persist_interesting_snapshot(OUTPUT_DIR, interesting20, latest_date)
last_week_interesting = load_last_week_interesting(OUTPUT_DIR, latest_date, combined)
interesting_tickers = set(interesting20.get("ticker", pd.Series(dtype=str)).dropna().astype(str))
previous_tickers = set(previous_interesting.get("ticker", pd.Series(dtype=str)).dropna().astype(str))
top6_industries = top_ranked_industries(industry_table, 6)
leaders = leader_sector_names(industry_table, 3)
stage2_count = int(combined["stage"].astype(str).eq("Stage 2").sum()) if "stage" in combined.columns else 0
mode_text = market_mode_text(regime, combined)
daily_dir = OUTPUT_DIR / "charts" / "daily"
weekly_dir = OUTPUT_DIR / "charts" / "weekly"
DAILY_CHART_INDEX = build_chart_index(daily_dir, "_daily.png")
WEEKLY_CHART_INDEX = build_chart_index(weekly_dir, "_weekly.png")
INDUSTRY_POSITION_MAP, INDUSTRY_RANK_MAP, WEAK_INDUSTRY_POSITION_MAP = build_industry_rank_context(industry, industry_changes, combined)
streak_map = interesting_streaks(OUTPUT_DIR, latest_date, interesting_tickers)
reset_summary = build_reset_summary(new_stage2, industry_changes, industry_table, interesting20, previous_interesting)
top_movers, bottom_movers = build_top_movers(moves, combined, 10)
generated_line = generated_at_text(OUTPUT_DIR, history)
dropped_tickers = previous_tickers - interesting_tickers

st.markdown('<div class="reset-shell">', unsafe_allow_html=True)
st.markdown(
    f"""
<div class="top-card">
  <div class="title">Daily Market Scan (After Close)</div>
  <div class="subtitle">A Holy-Grail for serious market participants who believe in long term structures over short term volatility. Not Investment Advice</div>

  <div class="unlock-line">{h(generated_line)}</div>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    build_today_summary_html(mode_text, stage2_count, leaders, reset_summary, regime, industry_table),
    unsafe_allow_html=True,
)

st.markdown('<div class="section-title">Industry Structure Table</div>', unsafe_allow_html=True)
st.markdown('<div class="section-note">Top Industries that Scores Well.</div>', unsafe_allow_html=True)
if industry_table.empty:
    st.info("Industry table is not available yet.")
else:
    display_table = industry_table.drop(columns=["Industry Raw"], errors="ignore")
    st.dataframe(display_table, use_container_width=True, hide_index=True, height=340)

st.markdown('<div class="section-title">Interesting Stock charts</div>', unsafe_allow_html=True)
st.markdown('<div class="section-note">Switch each card between daily and weekly chart. No buy, sell, target, stop-loss, or position-sizing advice.</div>', unsafe_allow_html=True)

list_choice = st.radio(
    "Stock list",
    ["Trending Stocks", "Interesting 20 Stocks", "Top Movers", "New Stage 2", "Last week Interesting 20 Stock"],
    horizontal=True,
    label_visibility="collapsed",
)

views = {
    "Trending Stocks": trending20,
    "Interesting 20 Stocks": interesting20,
    "New Stage 2": new_stage2,
    "Last week Interesting 20 Stock": last_week_interesting,
}

if list_choice == "Top Movers":
    st.markdown('<div class="section-note">Top 10 movers and bottom 10 movers from the latest daily move output.</div>', unsafe_allow_html=True)
    if top_movers.empty and bottom_movers.empty:
        st.info("Top mover data is not available from the current output yet.")
    else:
        if not top_movers.empty:
            st.markdown('<div class="stage-section-card"><div class="stage-section-title">Top 10 movers</div></div>', unsafe_allow_html=True)
            for i, (_, row) in enumerate(top_movers.head(10).iterrows(), start=1):
                render_stock_card(row, i, daily_dir, weekly_dir, [(f"Move: {format_move_pct(row.get('move_pct'))}", "new")])
        if not bottom_movers.empty:
            st.markdown('<div class="stage-section-card"><div class="stage-section-title">Bottom 10 movers</div></div>', unsafe_allow_html=True)
            for i, (_, row) in enumerate(bottom_movers.head(10).iterrows(), start=1):
                render_stock_card(row, i + 100, daily_dir, weekly_dir, [(f"Move: {format_move_pct(row.get('move_pct'))}", "drop")])
else:
    view_df = views.get(list_choice, pd.DataFrame())
    if view_df.empty:
        if list_choice == "Trending Stocks":
            st.info("No trending stocks found. Add a trending_stocks.csv file beside this dashboard or inside the outputs folder with a ticker column.")
        elif list_choice == "Last week Interesting 20 Stock":
            st.info("Last week Interesting 20 snapshot is not available yet. It will appear after archived daily snapshots exist for at least one prior week.")
        elif list_choice == "New Stage 2":
            st.info("None — no stocks entered Stage 2 in the available last 1–3 week history.")
        else:
            st.info("No stocks available for this view.")
    else:
        for i, (_, row) in enumerate(view_df.head(20).iterrows(), start=1):
            ticker = str(row.get("ticker", "") or "").strip()
            badges = []
            streak = None
            if list_choice == "Interesting 20 Stocks":
                # No repeated badge. Keep the useful streak memory only.
                streak = streak_map.get(ticker, 1)
            elif list_choice == "New Stage 2":
                badges.append(("Entered Stage 2 recently", "stage2"))
            elif list_choice == "Last week Interesting 20 Stock":
                pass
            render_stock_card(row, i, daily_dir, weekly_dir, badges, streak)

liked_count = len(st.session_state.get("liked_tickers", []))
st.markdown(
    f"""
<div class="disclaimer-card">
<b>Public-data disclaimer:</b> This page shows rule-based structure, stage, sector and chart data only. It is not investment advice, research advice, portfolio advice, a recommendation, or a solicitation to buy/sell securities. Any mention of “interesting”, “leader”, “stage”, “outperformed”, or “underperformed” is a descriptive label from the dataset only. Liked stocks in this session: {liked_count}. Liked-watchlist memory is intentionally kept for the next update.
</div>
""",
    unsafe_allow_html=True,
)
render_connect_feedback_section()
st.markdown('</div>', unsafe_allow_html=True)
