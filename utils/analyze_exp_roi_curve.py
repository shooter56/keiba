import pandas as pd
import matplotlib.pyplot as plt

# --- 設定 ---
RESULTS_CSV = r"C:\TFJV\TXT\keiba_data\merged_results.csv"  # 過去の単勝・複勝など全券種結果
OUT_CSV = "exp_roi_curve.csv"
KENSYU_LIST = ["単勝", "複勝", "馬連", "ワイド"]

df = pd.read_csv(RESULTS_CSV)

def calc_roi_curve(df, target_col="exp_roi", result_col="hit", payout_col="payout", kensyu="単勝"):
    results = []
    for thresh in [round(x, 2) for x in list(frange(0.7, 1.4, 0.01))]:
        sel = df[(df["券種"] == kensyu) & (df[target_col] >= thresh)]
        if len(sel) == 0:
            continue
        total_bet = len(sel)
        total_payout = sel[payout_col].sum()  # 払い戻し金額（的中時のみ）
        roi = total_payout / total_bet if total_bet > 0 else 0
        hit_rate = sel[result_col].mean() if len(sel) > 0 else 0
        results.append({
            "券種": kensyu,
            "閾値": thresh,
            "件数": total_bet,
            "回収率": roi,
            "的中率": hit_rate
        })
    return pd.DataFrame(results)

def frange(start, stop, step):
    while start < stop:
        yield start
        start += step

# 全券種まとめて解析
curve_list = []
for k in KENSYU_LIST:
    curve = calc_roi_curve(df, kensyu=k)
    curve_list.append(curve)
    curve.plot(x="閾値", y="回収率", title=f"{k} 期待値カーブ")
    plt.axhline(1.0, color="r", linestyle="--")
    plt.savefig(f"exp_roi_curve_{k}.png")
    plt.close()

df_curve = pd.concat(curve_list)
df_curve.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
print(f"保存しました: {OUT_CSV}")
