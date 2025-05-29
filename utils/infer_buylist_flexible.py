import argparse
import pandas as pd
import lightgbm as lgb

KENSHU_THRESHOLDS = {
    "単勝": {"min_exp_roi": 0.95, "min_prob": 0.09},
    "複勝": {"min_exp_roi": 0.85, "min_prob": 0.14},
    "馬連": {"min_exp_roi": 1.10, "min_prob": 0.03},
    "ワイド": {"min_exp_roi": 1.00, "min_prob": 0.08}
    # ← analyze_exp_roi_curve.pyの結果から自動生成可
}

def load_card(path):
    if path.endswith(".xlsx"):
        df = pd.read_excel(path)
    elif path.endswith(".csv"):
        df = pd.read_csv(path)
    else:
        raise Exception("未対応のファイル形式: " + path)
    return df

def load_model(model_path):
    return lgb.Booster(model_file=str(model_path))

def load_feature_columns(model_path):
    columns_txt = model_path + ".columns.txt"
    with open(columns_txt, encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def infer_one_kenshu(df, model, features, kenshu):
    th = KENSHU_THRESHOLDS.get(kenshu, {"min_exp_roi": 1.0, "min_prob": 0.0})
    for col in features:
        if col not in df.columns:
            df[col] = float('nan')
    X = df[features]
    probs = model.predict(X)
    df["prob"] = probs
    if "odds" in df.columns:
        df["exp_roi"] = pd.to_numeric(df["odds"], errors="coerce") * df["prob"]
        buy_df = df[
            (df["exp_roi"] >= th["min_exp_roi"]) | 
            (df["prob"] >= th["min_prob"])
        ].copy()
        buy_df["券種"] = kenshu
    else:
        buy_df = pd.DataFrame()
    return buy_df

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--card-xlsx", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--kenshu", required=True, choices=KENSHU_THRESHOLDS.keys())
    parser.add_argument("--out-csv", required=True)
    args = parser.parse_args()

    df = load_card(args.card_xlsx)
    features = load_feature_columns(args.model)
    model = load_model(args.model)
    buy_df = infer_one_kenshu(df, model, features, args.kenshu)
    buy_df.to_csv(args.out_csv, index=False, encoding="utf-8-sig")
    print(f"✅ 買い目出力: {args.out_csv}（{len(buy_df)}件）")

if __name__ == "__main__":
    main()
