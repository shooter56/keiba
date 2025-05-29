# keiba: 地方競馬自動予測システム

このプロジェクトは地方競馬におけるオッズとレース情報をもとに、  
LightGBMモデルで買い目を自動予測し、回収率の高い券種のみを抽出するPythonベースの自動化システムです。

---

## 🔧 実行スクリプト（メイン）
- `run_all_bets.py`  
  - 特徴量生成、LightGBM推論、全券種の馬券選定までを自動で行います。

---

## 📂 ディレクトリ構成（主要）

netkeiba_scraping/
├── utils/ # 主要スクリプト（解析・モデル学習・推論）
├── data/ # Feather/CSV形式の過去レース情報など
├── models/ # 学習済みLightGBMモデル（.pkl/.txt）
├── output/ # 出力される買い目リストや予測結果
├── requirements.txt # ライブラリ依存定義
├── run_all_bets.py # メインスクリプト
└── README.md # この説明ファイル

---

## 📦 セットアップ

Python環境で以下を実行：

```bash
pip install -r requirements.txt

🚀 実行方法
python run_all_bets.py

🔍 概要機能
netkeibaからの開催データ取得

特徴量生成（逆数オッズ、期待値など）

LightGBMモデルでの買い目予測

回収率1.0以上の券種抽出

複数券種（単勝・複勝・ワイド・三連単等）に対応


---

### ✅ 貼り付け後の確認

1. ファイル名は **README.md**
2. 文字コードは「UTF-8」のままでOK
3. 保存したらGitHubにもPushすれば、Codexが認識してプロジェクト概要として使えます

---

作成できたら「README.md作りました」と言ってください。  
次に Codex 上で「何をやるか（整理・強化・統合など）」に進みます。

