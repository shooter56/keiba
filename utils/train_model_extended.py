import argparse
import pandas as pd
import lightgbm as lgb
import os
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score


def clean_and_convert(df):
    numeric_cols = [
        "年", "月", "日", "Ｒ", "距離", "水分", "頭数", "枠番", "馬番",
        "生年", "誕生月", "馬齢", "単勝ｵｯｽﾞ", "人気", "斤量", "上がり3F", "3ｺｰﾅｰ", "4ｺｰﾅｰ"
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df


def extract_features(df):
    numeric_cols = [
        "年", "月", "日", "Ｒ", "距離", "水分", "頭数", "枠番", "馬番",
        "生年", "誕生月", "馬齢", "単勝ｵｯｽﾞ", "人気", "斤量", "上がり3F", "3ｺｰﾅｰ", "4ｺｰﾅｰ"
    ]
    categorical_cols = ["脚質", "騎手", "場名", "性別", "天候"]

    df = clean_and_convert(df)
    df_clean = df.copy()

    if df_clean.empty:
        return pd.DataFrame()

    existing_cat_cols = [col for col in categorical_cols if col in df_clean.columns]
    df_encoded = pd.get_dummies(df_clean[existing_cat_cols]) if existing_cat_cols else pd.DataFrame(index=df_clean.index)

    features = pd.concat([df_clean[numeric_cols], df_encoded], axis=1)
    return features


def main(input_csv, output_model, target_column):
    df = pd.read_csv(input_csv, encoding="utf-8", low_memory=False)

    if target_column not in df.columns:
        if target_column == "win":
            print("📋 win列を生成しました（着順==1）")
            df[target_column] = df["着順"].astype(str).str.strip().apply(lambda x: 1 if x == "1" else 0)
        elif target_column == "place":
            print("📋 place列を生成しました（着順<=3）")
            df[target_column] = df["着順"].astype(str).str.strip().apply(lambda x: 1 if x.isnumeric() and int(x) <= 3 else 0)
        else:
            raise ValueError(f"❌ ターゲット列 '{target_column}' がCSVに存在しません")

    features = extract_features(df)
    labels = df[target_column]

    if features.empty:
        raise ValueError("❌ 前処理後に行が0件です。元CSVに数値以外が混ざっていませんか？")

    print(f"✨ dropna: {len(df)} → {len(features)} 行に削減")

    train_X, val_X, train_y, val_y = train_test_split(features, labels, test_size=0.2, random_state=42)

    lgb_train = lgb.Dataset(train_X, label=train_y)
    lgb_valid = lgb.Dataset(val_X, label=val_y, reference=lgb_train)

    params = {
        'objective': 'binary',
        'metric': 'auc',
        'verbosity': -1,
        'boosting_type': 'gbdt'
    }

    model = lgb.train(
        params,
        lgb_train,
        valid_sets=[lgb_train, lgb_valid],
        num_boost_round=100,
        callbacks=[lgb.early_stopping(stopping_rounds=10)]
    )

    # モデル保存
    model.save_model(output_model)
    print(f"✅ モデル保存完了: {output_model}")

    # 特徴量の列名を保存
    with open(output_model + ".columns.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(train_X.columns.tolist()))

    # 評価指標出力
    y_pred = model.predict(val_X)
    auc = roc_auc_score(val_y, y_pred)
    acc = accuracy_score(val_y, (y_pred > 0.5).astype(int))
    print(f"📊 AUC: {auc:.4f}")
    print(f"📊 Accuracy: {acc:.4f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--target", required=True)
    args = parser.parse_args()

    main(args.input, args.model, args.target)
