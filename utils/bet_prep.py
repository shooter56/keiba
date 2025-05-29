import re
import os
import requests
from bs4 import BeautifulSoup
import pandas as pd

def parse_race_info(html):
    """距離・頭数・馬場・レース名などを抽出"""
    soup = BeautifulSoup(html, "lxml")
    # 距離
    race_data01 = soup.find("div", class_="RaceData01")
    kyori = None
    if race_data01:
        m = re.search(r"([芝ダ])(\d+)m", race_data01.text)
        if m:
            kyori = int(m.group(2))
    # 頭数
    tousu = None
    race_data02 = soup.find("div", class_="RaceData02")
    if race_data02:
        m = re.search(r"(\d+)頭", race_data02.text)
        if m:
            tousu = int(m.group(1))
    return kyori, tousu

def parse_card_table(html, kyori, tousu):
    """出馬表テーブルから枠番・馬番・馬名・馬齢・斤量などを抽出"""
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table", class_="Shutuba_Table")
    records = []
    if not table:
        return records
    for tr in table.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) < 10:
            continue
        # 枠番, 馬番, 馬名, 性齢, 斤量, 騎手, 人気, 厩舎、他
        try:
            waku = tds[0].get_text(strip=True)
            num = tds[1].get_text(strip=True)
            horse_name = tds[3].get_text(strip=True)
            sex_age = tds[4].get_text(strip=True)
            # 性齢 → 馬齢
            m = re.match(r"[牡牝セ](\d+)", sex_age)
            umarei = int(m.group(1)) if m else None
            kinryo = tds[5].get_text(strip=True)
            # 人気（オッズページ側で取得）
            record = {
                "枠番": waku,
                "馬番": num,
                "馬名": horse_name,
                "馬齢": umarei,
                "斤量": kinryo,
                "距離": kyori,
                "頭数": tousu,
                # ここでは人気・単勝オッズはまだ埋めない
            }
            records.append(record)
        except Exception as e:
            continue
    return records

def parse_odds_table(html):
    """オッズテーブルから馬番・人気・単勝オッズを抽出"""
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table", class_="RaceOdds_HorseList_Table")
    odds_dict = {}
    if not table:
        return odds_dict
    for tr in table.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) < 5:
            continue
        num = tds[1].get_text(strip=True)        # 馬番
        ninki = tds[0].get_text(strip=True)      # 人気
        odds = tds[4].get_text(strip=True)       # オッズ
        odds_dict[num] = {"人気": ninki, "単勝ｵｯｽﾞ": odds}
    return odds_dict

def get_html(path_or_url):
    if os.path.exists(path_or_url):
        with open(path_or_url, encoding="utf-8") as f:
            return f.read()
    else:
        r = requests.get(path_or_url)
        r.raise_for_status()
        return r.text

def build_card(race_id, shutuba_html, odds_html):
    kyori, tousu = parse_race_info(shutuba_html)
    card_list = parse_card_table(shutuba_html, kyori, tousu)
    odds_dict = parse_odds_table(odds_html)
    for row in card_list:
        num = row["馬番"]
        # オッズ情報をマージ
        if num in odds_dict:
            row["人気"] = odds_dict[num]["人気"]
            row["単勝ｵｯｽﾞ"] = odds_dict[num]["単勝ｵｯｽﾞ"]
    return card_list

def main():
    race_id = "202530052201"
    shutuba_html_path = "DOたび賞 出馬表 _ 2025年5月22日 門別1R 地方競馬レース情報 - netkeiba.html"
    odds_html_path    = "DOたび賞 オッズ _ 2025年5月22日 門別1R 地方競馬レース情報 - netkeiba.html"

    shutuba_html = get_html(shutuba_html_path)
    odds_html = get_html(odds_html_path)

    card_list = build_card(race_id, shutuba_html, odds_html)
    df = pd.DataFrame(card_list)
    df["レースID"] = race_id
    print(df)
    # 必要ならExcelやCSV保存
    df.to_excel(f"card_{race_id}_full.xlsx", index=False)

if __name__ == "__main__":
    main()
