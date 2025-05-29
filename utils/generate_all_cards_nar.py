import os
import re
import pandas as pd
from bs4 import BeautifulSoup
import glob

def parse_race_info(html):
    soup = BeautifulSoup(html, "lxml")
    kyori = None
    race_data01 = soup.find("div", class_="RaceData01")
    if race_data01:
        m = re.search(r"([芝ダ])(\d+)m", race_data01.text)
        if m:
            kyori = int(m.group(2))
    tousu = None
    race_data02 = soup.find("div", class_="RaceData02")
    if race_data02:
        m = re.search(r"(\d+)頭", race_data02.text)
        if m:
            tousu = int(m.group(1))
    return kyori, tousu

def parse_card_table(html, kyori, tousu):
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table", class_="Shutuba_Table")
    records = []
    if not table:
        return records
    for tr in table.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) < 10:
            continue
        try:
            waku = tds[0].get_text(strip=True)
            num = tds[1].get_text(strip=True)
            horse_name = tds[3].get_text(strip=True)
            sex_age = tds[4].get_text(strip=True)
            m = re.match(r"[牡牝セ](\d+)", sex_age)
            umarei = int(m.group(1)) if m else None
            kinryo = tds[5].get_text(strip=True)
            records.append({
                "枠番": waku,
                "馬番": num,
                "馬名": horse_name,
                "馬齢": umarei,
                "斤量": kinryo,
                "距離": kyori,
                "頭数": tousu,
            })
        except Exception:
            continue
    return records

def parse_odds_table(html):
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table", class_="RaceOdds_HorseList_Table")
    odds_dict = {}
    if not table:
        return odds_dict
    for tr in table.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) < 5:
            continue
        num = tds[1].get_text(strip=True)
        ninki = tds[0].get_text(strip=True)
        odds = tds[4].get_text(strip=True)
        odds_dict[num] = {"人気": ninki, "単勝ｵｯｽﾞ": odds}
    return odds_dict

def get_html(path):
    with open(path, encoding="utf-8") as f:
        return f.read()

def build_card(race_id, shutuba_html, odds_html):
    kyori, tousu = parse_race_info(shutuba_html)
    card_list = parse_card_table(shutuba_html, kyori, tousu)
    odds_dict = parse_odds_table(odds_html)
    for row in card_list:
        num = row["馬番"]
        if num in odds_dict:
            row["人気"] = odds_dict[num]["人気"]
            row["単勝ｵｯｽﾞ"] = odds_dict[num]["単勝ｵｯｽﾞ"]
        else:
            row["人気"] = None
            row["単勝ｵｯｽﾞ"] = None
        row["レースID"] = race_id
    return card_list

def main():
    # html格納ディレクトリとrace_idリスト自動検出
    import glob

    html_dir = r"C:\Users\ashit\Documents\PythonScripts\netkeiba_scraping\utils\html\shutuba_20250522_NAR"
    odds_dir = html_dir.replace("shutuba", "odds")  # 必要なら同一ディレクトリでもOK

    # レースidをshutuba_XXXXXXXXXXXX.htmlから自動取得
    html_files = sorted(glob.glob(os.path.join(html_dir, "shutuba_*.html")))
    all_rows = []
    for fpath in html_files:
        race_id = os.path.basename(fpath).replace("shutuba_", "").replace(".html", "")
        shutuba_html = get_html(fpath)
        # オッズHTMLの保存先・命名規則に応じてパスを修正
        odds_path = fpath.replace("shutuba_", "odds_")
        if not os.path.exists(odds_path):
            print(f"[WARN] {odds_path} not found, skip.")
            continue
        odds_html = get_html(odds_path)
        card_list = build_card(race_id, shutuba_html, odds_html)
        all_rows.extend(card_list)
        print(f"✔ {race_id}: {len(card_list)}頭")
    df = pd.DataFrame(all_rows)
    # 出力パスは1日ごとに固定
    out_path = r"C:\Users\ashit\Documents\PythonScripts\netkeiba_scraping\utils\data\all_cards_20250522_NAR.xlsx"
    df.to_excel(out_path, index=False)
    print(f"✔ カードExcel出力: {out_path} ({len(df)}行)")

if __name__ == "__main__":
    main()
