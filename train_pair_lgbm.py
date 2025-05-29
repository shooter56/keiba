# -*- coding: utf-8 -*-
"""
train_pair_lgbm.py  ― 2頭組（馬連／ワイド）LightGBM モデル学習   **v1.2.0**
===================================================================
* 2025‑04‑24  v1.2.0  — LightGBM 4.x 互換修正
  - `early_stopping_rounds` → callback API に置き換え
  - Windows PowerShell での改行バックスラッシュ混入を回避（Usage 例を 1 行コマンドに）

Usage examples (1‑line)
----------------------
```powershell
python netkeiba_scraping/train_pair_lgbm.py odds_features_all_years.csv --model C:/keiba/data/models/quinella_lgbm.pkl --topk 2 --skip-bad
python netkeiba_scraping/train_pair_lgbm.py odds_features_all_years.csv --model C:/keiba/data/models/wide_lgbm.pkl     --topk 3 --skip-bad
```
"""
import argparse, pickle, lightgbm as lgb
from pathlib import Path
from itertools import combinations
import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

FEATS = ["人気","単勝","odds_inv","頭数","枠番","馬番"]

# ----------------- utils -----------------

def read_csv_guess(path: Path, skip_bad: bool, engine: str):
    opts = dict(low_memory=False, engine=engine)
    if skip_bad:
        opts["on_bad_lines"] = "skip"
    for enc in ("utf-8-sig","utf-8","cp932"):
        try:
            return pd.read_csv(path, encoding=enc, **opts)
        except UnicodeDecodeError:
            continue
    raise RuntimeError("encoding detection failed")

def build_pair_df(df: pd.DataFrame, topk: int):
    rec = []
    for rid, g in df.groupby("race_id"):
        top = g[g["着順"] <= topk]
        idx = list(top.index)
        for i, j in combinations(idx, 2):
            rec.append({
                "race_id": rid,
                "馬番1": g.loc[i, "馬番"],
                "馬番2": g.loc[j, "馬番"],
                **{f"{c}1": g.loc[i, c] for c in FEATS},
                **{f"{c}2": g.loc[j, c] for c in FEATS},
                "y": 1,
            })
    return pd.DataFrame(rec)

# ----------------- main ------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", help="odds_features_all_years.csv など")
    ap.add_argument("--model", required=True, help="出力 pkl")
    ap.add_argument("--topk", type=int, default=2, help="positive とみなす着順上限 (2=馬連,3=ワイド)")
    ap.add_argument("--skip-bad", action="store_true", help="壊れ行をスキップして読み込む")
    ap.add_argument("--engine", choices=["c","python"], default="c", help="pandas CSV パーサ")
    args = ap.parse_args()

    df = read_csv_guess(Path(args.csv), args.skip_bad, args.engine)
    print(f"📊 loaded {len(df):,} rows (skip_bad={args.skip_bad})")

    df_pair = build_pair_df(df, args.topk)
    X = df_pair.drop(columns=["race_id","馬番1","馬番2","y"])
    y = df_pair["y"]

    X_tr,X_va,y_tr,y_va = train_test_split(X,y,test_size=0.2,stratify=y,random_state=42)
    dtr = lgb.Dataset(X_tr,y_tr); dva = lgb.Dataset(X_va,y_va,reference=dtr)
    params = {"objective":"binary","metric":"auc","learning_rate":0.05,"num_leaves":128,"seed":42}

    callbacks = [
        lgb.early_stopping(stopping_rounds=50, verbose=False),
        lgb.log_evaluation(period=50),
    ]
    booster = lgb.train(params, dtr, num_boost_round=400, valid_sets=[dva], callbacks=callbacks)

    print("AUC(valid)=", roc_auc_score(y_va, booster.predict(X_va, num_iteration=booster.best_iteration)))

    with open(args.model, "wb") as f:
        pickle.dump({"model": booster, "features": list(X.columns), "cat_idx": []}, f)
    print(f"✅ saved {args.model}")

if __name__ == "__main__":
    main()