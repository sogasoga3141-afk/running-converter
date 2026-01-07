# running_converter_fixed.py
import streamlit as st
import numpy as np

# =====================
# ユーティリティ
# =====================
def time_to_sec(t_str):
    m, s = map(int, t_str.split(":"))
    return m * 60 + s

def sec_to_time(sec):
    m = int(sec // 60)
    s = int(sec % 60)
    return f"{m}:{s:02d}"

# =====================
# Riegelベースモデル
# =====================
def estimate_k(distances, times):
    log_d = np.log(distances)
    log_t = np.log(times)
    k, _ = np.polyfit(log_d, log_t, 1)
    return np.clip(k, 1.05, 1.10)

def adjust_k(k, vo2max, mileage):
    k_adj = k
    k_adj -= 0.002 * (vo2max - 60)
    k_adj -= 0.001 * (mileage - 200) / 100
    return np.clip(k_adj, 1.04, 1.10)

def predict_time(t_ref, d_ref, d_target, k):
    return t_ref * (d_target / d_ref) ** k

# =====================
# Streamlit UI
# =====================
st.title("A Performance Conversion App 2026ver. -Long-Distance Chiba Univ. T&F-")
st.markdown(
    """
PB・VO₂max・走行距離から  
**実測換算表と乖離しにくい記録換算**を行います（Riegel 法則ベース）。
"""
)

# ---------------------
# PB入力
# ---------------------
st.header("① PB入力（2種目以上推奨）")

distance_list = [1500, 3000, 5000, 10000, 21097, 42195]
pb_data = {}

for d in distance_list:
    t = st.text_input(f"{d}m の PB（例 14:47）", "")
    if t:
        try:
            pb_data[d] = time_to_sec(t)
        except:
            st.warning(f"{d}m の入力形式が正しくありません")

# ---------------------
# 任意入力（必ず数値）
# ---------------------
st.header("② 任意入力（未入力でも可）")

vo2max = st.number_input(
    "VO₂max（GARMIN 等）",
    min_value=40.0,
    max_value=85.0,
    value=60.0,
    step=0.1
)

monthly_mileage = st.number_input(
    "月平均走行距離（km）",
    min_value=0.0,
    value=200.0,
    step=10.0
)

# ---------------------
# 計算・表示
# ---------------------
if st.button("換算記録を計算"):
    if len(pb_data) == 0:
        st.error("PBを1つ以上入力してください。")
    else:
        # --- 必ずここで定義 ---
        distances = np.array(list(pb_data.keys()))
        times = np.array(list(pb_data.values()))

        # 最長距離PBを基準（短距離に引っ張られない）
        d_ref = distances.max()
        t_ref = pb_data[d_ref]

        if len(pb_data) >= 2:
            k = estimate_k(distances, times)
            k = adjust_k(k, vo2max, monthly_mileage)
            st.success(f"推定疲労指数 k = {k:.3f}")
        else:
            k = 1.06
            st.info("PBが1つのため、一般的疲労指数 k = 1.06 を使用")

        st.header("③ 換算記録（分析結果）")

        targets = {
            "1500 m": 1500,
            "3000 m": 3000,
            "5000 m": 5000,
            "10000 m": 10000,
            "ハーフマラソン": 21097,
            "フルマラソン": 42195
        }

        # --- t_ref, d_ref, k はここでは必ず存在 ---
        for name, d in targets.items():
            pred = predict_time(t_ref, d_ref, d, k)
            st.write(f"{name}：**{sec_to_time(pred)}**")
