import argparse
import pandas as pd
import lightgbm as lgb
import os
import sys

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
    if not os.path.exists(columns_txt):
        raise FileNotFoundError(f"カラムリストファイルが見つかりません: {columns_txt}")
    with open(columns_txt, encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def predict_and_filter(df, model, features, min_exp_roi=1.0, min_prob=None):
    # ▼ カラム存在チェック＋NaN埋め
    print("[DEBUG] モデル要求特徴量:", features)
    missing = [col for col in features if col not in df.columns]
    if missing:
        print(f"[ERROR] カードに存在しないカラム: {missing}")
        print("[DEBUG] 実際のカードカラム:", df.columns.tolist())
        raise Exception("特徴量カラム不一致。columns.txtを確認し、カードのカラム名をそろえてください。")
    for col in features:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    X = df[features]
    print("[DEBUG] X.head():\n", X.head())
    if X.isnull().all().all():
        print("[ERROR] Xが全てNaNです。カードとcolumns.txtの型や値を再確認してください。")
        sys.exit(1)
    probs = model.predict(X)
    print("[DEBUG] probs[:10]:", probs[:10])
    df["prob"] = probs
    if "odds" in df.columns:
        df["odds"] = pd.to_numeric(df["odds"], errors="coerce")
        df["exp_roi"] = df["odds"] * df["prob"]
        print("[DEBUG] exp_roi describe:", df["exp_roi"].describe())
        if min_prob is not None:
            buy_df = df[(df["exp_roi"] >= min_exp_roi) | (df["prob"] >= min_prob)]
        else:
            buy_df = df[df["exp_roi"] >= min_exp_roi]
    else:
        print("[WARN] oddsカラムが見つかりません。exp_roi判定をスキップします。")
        buy_df = df
    print(f"[DEBUG] buy_df件数={len(buy_df)} / 全体={len(df)}")
    return buy_df

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--card-xlsx", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--out-csv", required=True)
    parser.add_argument("--min-roi", type=float, default=1.0)
    parser.add_argument("--min-prob", type=float, default=None)
    args = parser.parse_args()

    print("[INFO] カード読み込み:", args.card_xlsx)
    df = load_card(args.card_xlsx)
    print("[INFO] モデル特徴量読み込み:", args.model + ".columns.txt")
    features = load_feature_columns(args.model)
    print("[INFO] モデル本体読み込み:", args.model)
    model = load_model(args.model)
    buy_df = predict_and_filter(df, model, features, min_exp_roi=args.min_roi, min_prob=args.min_prob)
    buy_df.to_csv(args.out_csv, index=False, encoding="utf-8-sig")
    print(f"✅ 買い目出力: {args.out_csv}（{len(buy_df)}件）")

if __name__ == "__main__":
    main()
