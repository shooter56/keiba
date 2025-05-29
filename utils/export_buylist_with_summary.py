import pandas as pd
import argparse
import matplotlib.pyplot as plt
import io
from openpyxl import load_workbook
from openpyxl.drawing.image import Image as ExcelImage

def make_odds_hist(df, odds_col="odds"):
    fig, ax = plt.subplots(figsize=(7, 3))
    df[odds_col].dropna().astype(float).hist(bins=30, ax=ax)
    ax.set_title("オッズ分布（買い目）")
    ax.set_xlabel("オッズ")
    ax.set_ylabel("件数")
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    return buf

def calc_summary(df):
    # 的中率・回収率（実測）仮：target列が1=的中, 0=ハズレを仮定
    total_bet = len(df)
    total_hit = df['target'].sum() if 'target' in df.columns else 0
    payout = (df[df['target']==1]['odds']).sum() if 'target' in df.columns else 0
    hit_rate = (total_hit / total_bet * 100) if total_bet else 0
    return_rate = (payout / total_bet * 100) if total_bet else 0
    return {
        "件数": total_bet,
        "的中数": total_hit,
        "的中率": f"{hit_rate:.2f}%",
        "回収率": f"{return_rate:.2f}%"
    }

def export_with_graph(input_csv, output_xlsx):
    df = pd.read_csv(input_csv)
    # Excel書き込み
    with pd.ExcelWriter(output_xlsx, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="buylist")
        # サマリー
        summary = calc_summary(df)
        pd.DataFrame([summary]).to_excel(writer, index=False, sheet_name="summary")
    # グラフ貼付
    wb = load_workbook(output_xlsx)
    ws = wb["summary"]
    img_data = make_odds_hist(df)
    img = ExcelImage(img_data)
    img.anchor = "A5"
    ws.add_image(img)
    wb.save(output_xlsx)
    print(f"✔ Excel出力: {output_xlsx}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", required=True)
    parser.add_argument("--dst", required=True)
    args = parser.parse_args()
    export_with_graph(args.src, args.dst)
