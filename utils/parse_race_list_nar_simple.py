import argparse
import re
import chardet
import pandas as pd

def detect_encoding(path):
    with open(path, "rb") as f:
        raw = f.read()
        return chardet.detect(raw)["encoding"]

def extract_nar_race_ids(html_path):
    enc = detect_encoding(html_path)
    with open(html_path, encoding=enc) as f:
        html = f.read()
    # NAR/JRA共通：12桁連続の数字パターン
    race_ids = re.findall(r"\b\d{12}\b", html)
    race_ids = sorted(set(race_ids))
    return race_ids

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--html", required=True)
    parser.add_argument("--csv", required=True)
    args = parser.parse_args()
    race_ids = extract_nar_race_ids(args.html)
    print(f"race_id件数: {len(race_ids)}")
    pd.DataFrame({"race_id": race_ids}).to_csv(args.csv, index=False)
    print(f"→ {args.csv} を出力しました")

if __name__ == "__main__":
    main()
