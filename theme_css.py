"""استایل آبی/زردِ سوئدی برای کل اپ (تزریق با st.markdown). فقط ظاهر؛ منطق برنامه رو عوض نمی‌کنه."""
import streamlit as st

BLUE = "#006AA7"
YELLOW = "#FECC02"

_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;500;700&display=swap');
html, body, [class*="css"], .stMarkdown, .stButton button, input, textarea {{
  font-family: 'Vazirmatn', system-ui, -apple-system, 'Segoe UI', sans-serif;
}}
/* فاصله‌ی کمتر بالای صفحه + عنوان با نوار آبی/زرد */
.block-container {{ padding-top: 2.2rem; padding-bottom: 5rem; max-width: 1100px; }}
h1 {{
  color: {BLUE}; font-weight: 700; padding-bottom: .35rem; margin-bottom: .25rem;
  border-bottom: 5px solid {YELLOW}; display: inline-block;
}}
h1, h2, h3, h4, [data-testid="stHeading"] h2, [data-testid="stHeading"] h3,
.stMarkdown h2, .stMarkdown h3 {{ color: {BLUE} !important; }}
/* دکمه‌ها: گرد، بزرگ برای انگشت، آبی با لبه‌ی زرد در هاور */
.stButton > button, .stFormSubmitButton > button, .stDownloadButton > button {{
  border-radius: 14px; min-height: 2.9rem; font-weight: 500;
  border: 1.5px solid {BLUE}; color: {BLUE}; background: #fff;
  transition: all .15s ease; box-shadow: 0 1px 2px rgba(0,106,167,.12);
}}
.stButton > button:hover, .stFormSubmitButton > button:hover {{
  background: {BLUE}; color: #fff; border-color: {YELLOW}; box-shadow: 0 3px 8px rgba(0,106,167,.25);
}}
.stButton > button:active {{ transform: scale(.98); }}
/* ناوبری اصلی: قرص‌های گرد (radio افقی) — ساختار: radiogroup > div > label[stRadioOption] */
div[data-testid="stRadioGroup"] {{ flex-wrap: wrap; gap: .4rem; }}
label[data-testid="stRadioOption"] {{
  background: #EEF5FB; border: 1.5px solid #D5E6F3; border-radius: 999px;
  padding: .35rem .9rem; margin: 0; transition: all .15s ease; cursor: pointer;
}}
label[data-testid="stRadioOption"]:hover {{ border-color: {BLUE}; }}
label[data-testid="stRadioOption"]:has(input:checked) {{ background: {BLUE}; border-color: {YELLOW}; }}
label[data-testid="stRadioOption"]:has(input:checked) * {{ color: #fff !important; }}
/* دایره‌ی کوچک radio رو مخفی کن تا قرص تمیز بشه */
label[data-testid="stRadioOption"] > div > div:first-child {{ display: none; }}
label[data-testid="stRadioOption"] {{ padding: .3rem .75rem; }}
label[data-testid="stRadioOption"] p {{ font-size: .92rem; white-space: nowrap; }}
/* کارت‌ها: expander، فرم، پیام‌های چت */
div[data-testid="stExpander"] {{
  border: 1.5px solid #D5E6F3; border-radius: 14px; background: #fff;
  box-shadow: 0 1px 3px rgba(0,106,167,.08);
}}
div[data-testid="stForm"] {{ border: 1.5px solid #D5E6F3; border-radius: 14px; background: #F7FBFE; }}
div[data-testid="stChatMessage"] {{ border-radius: 16px; background: #F3F8FC; border: 1px solid #E1EDF6; }}
/* هشدارها گردتر */
div[data-testid="stAlert"] {{ border-radius: 12px; }}
/* ورودی‌ها و پلیر صدا */
input, textarea {{ border-radius: 10px !important; }}
audio {{ width: 100%; border-radius: 999px; }}
/* متریک‌ها مثل کارت */
div[data-testid="stMetric"] {{
  background: #fff; border: 1.5px solid #D5E6F3; border-radius: 14px; padding: .6rem .9rem;
  border-left: 5px solid {YELLOW};
}}
/* خط جداکننده نرم‌تر */
hr {{ border-color: #E1EDF6; }}
/* موبایل: فاصله‌ها کمتر */
@media (max-width: 640px) {{
  div[data-testid="stRadioGroup"] {{ gap: .3rem; }}
  label[data-testid="stRadioOption"] {{ padding: .25rem .55rem; }}
  label[data-testid="stRadioOption"] p {{ font-size: .82rem; }}
  .block-container {{ padding-left: .8rem; padding-right: .8rem; }}
  h1 {{ font-size: 1.7rem; }}
}}
</style>
"""


def inject():
    st.markdown(_CSS, unsafe_allow_html=True)
