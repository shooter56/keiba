#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
run_all_bets.py  (完全版 2025-05-12 v1.8)
-----------------------------------------
- keiba.go.jp はプロキシをバイパス
- HTML 構造で開催判定
- フォールバック: netkeiba race_list_sub.html
"""
from __future__ import annotations
import re, sys, logging, argparse
from datetime import datetime, timedelta
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests, pandas as pd
from requests_cache import CachedSession
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ----------------------------------------------------------------------
# 1. プロキシ（不要なら空 dict）
# ----------------------------------------------------------------------
PROX = {
    "http":  "http://proxy.scrapeops.io:5353",
    "https": "http://proxy.scrapeops.io:5353",
}

# ----------------------------------------------------------------------
# 2. requests セッション
# ----------------------------------------------------------------------
REQ = CachedSession("run_all_bets_cache", backend="sqlite", expire_after=3600)
REQ.proxies.update(PROX)
REQ.headers.update({
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/123.0.0.0 Safari/537.36"),
    "Accept-Language": "ja-JP,ja;q=0.9,en-US;q=0.8",
})
# プロキシなし専用セッション
REQ_NOPROXY = CachedSession("run_all_bets_cache_np", backend="sqlite", expire_after=3600)
REQ_NOPROXY.proxies.clear()
REQ_NOPROXY.headers = REQ.headers

# ----------------------------------------------------------------------
# 3. フォルダ
# ----------------------------------------------------------------------
BASE_DIR = Path(r"C:/keiba/data")
OUT_DIR  = BASE_DIR / "output"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------
# 4. ログ
# ----------------------------------------------------------------------
def setup_logger(verbose: bool):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

# ----------------------------------------------------------------------
# 5. NAR babaCode → netkeiba 2桁コード
# ----------------------------------------------------------------------
CODES = {
    "01": "30",  "03": "32",  "04": "33",  "05": "38",
    "06": "34",  "07": "35",  "08": "36",  "09": "37",
    "10": "39",  "11": "40",  "12": "41",  "13": "42",
    "14": "54",  "15": "55",
}

# ----------------------------------------------------------------------
# 6. 日付ユーティリティ
# ----------------------------------------------------------------------
def parse_base_date(d: str) -> datetime:
    today = datetime.now()
    return {"today": today, "tomorrow": today + timedelta(days=1)}.get(
        d, datetime.strptime(d, "%Y%m%d")
    )

def daterange(base: datetime, horizon: int):
    for i in range(horizon):
        yield (base + timedelta(days=i)).strftime("%Y%m%d")

# ----------------------------------------------------------------------
# 7. JRA race_id 取得
# ----------------------------------------------------------------------
def fetch_jra_race_ids(date: str) -> list[str]:
    url = f"https://race.netkeiba.com/top/race_list.html?kaisai_date={date}"
    try:
        html = REQ.get(url, timeout=20).text
    except requests.RequestException:
        return []
    return re.findall(r"race_id=(\d{12})", html)

# ----------------------------------------------------------------------
# 8. NAR 開催判定 & race_id 生成
# ----------------------------------------------------------------------
KEIBA_GO_URL = ("https://www2.keiba.go.jp/KeibaWeb/TodayRaceInfo/"
                "RaceList?k_babaCode={baba}&k_raceDate={yyyy}/{mm}/{dd}")
NETKEIBA_FALLBACK = ("https://nar.netkeiba.com/top/race_list_sub.html?"
                     "kaisai_date={yyyy}{mm}{dd}")

def is_track_active(baba: str, date: str) -> bool:
    yyyy, mm, dd = date[:4], date[4:6], date[6:]
    url = KEIBA_GO_URL.format(baba=baba, yyyy=yyyy, mm=mm, dd=dd)
    try:
        html = REQ_NOPROXY.get(url, timeout=10).text
        soup = BeautifulSoup(html, "html.parser")
        if soup.select_one("table.RaceList_Table"):
            return True
    except requests.RequestException:
        pass
    # フォールバック: netkeiba
    url2 = NETKEIBA_FALLBACK.format(yyyy=yyyy, mm=mm, dd=dd)
    try:
        html2 = REQ.get(url2, timeout=10).text
        pattern = rf"race_id={yyyy}{CODES[baba]}\d{{4}}01"
        if re.search(pattern, html2):
            return True
    except requests.RequestException:
        pass
    return False

def generate_nar_race_ids(date: str) -> list[str]:
    yyyy, mm, dd = date[:4], date[4:6], date[6:]
    race_ids = []
    for baba in CODES.keys():
        if not is_track_active(baba, date):
            continue
        code = CODES[baba]
        for r in range(1, 19):          # 13R 以上も対応
            rid = f"{yyyy}{code}{mm}{dd}{r:02d}"
            url = f"https://nar.netkeiba.com/race/shutuba.html?race_id={rid}"
            try:
                html = REQ.get(url, timeout=8).text
            except requests.RequestException:
                break
            if "404 Not Found" in html or "指定されたページは存在しません" in html:
                if r == 1:
                    logging.debug(" %s: track %s 開催なし", date, baba)
                break
            race_ids.append(rid)
    return race_ids

# ----------------------------------------------------------------------
# 9. Selenium オッズ取得
# ----------------------------------------------------------------------
def create_driver() -> webdriver.Chrome:
    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--ignore-certificate-errors")
    opts.add_argument("--user-agent=" + REQ.headers["User-Agent"])
    opts.add_argument(f"--proxy-server={PROX['http']}")
    return webdriver.Chrome(options=opts)

def fetch_odds_for_race(race_id: str) -> dict | None:
    url = f"https://race.netkeiba.com/odds/index.html?type=win&race_id={race_id}"
    drv = create_driver()
    try:
        drv.get(url)
        WebDriverWait(drv, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".OddsTbody tr"))
        )
        rows = drv.find_elements(By.CSS_SELECTOR, ".OddsTbody tr")
        odds = [float(c) for r in rows for c in r.text.split()[1::2]]
        return {"race_id": race_id, "odds": odds}
    except Exception as e:
        logging.debug("odds fetch fail %s : %s", race_id, e)
        return None
    finally:
        drv.quit()

# ----------------------------------------------------------------------
# 10. main
# ----------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default="today", help="today / tomorrow / YYYYMMDD")
    ap.add_argument("--horizon", type=int, default=1, help="基準日から何日分取得")
    ap.add_argument("--verbose", action="store_true", help="DEBUG ログ")
    args = ap.parse_args()
    setup_logger(args.verbose)

    base = parse_base_date(args.date)
    race_ids: list[str] = []
    for d in daterange(base, args.horizon):
        race_ids.extend(generate_nar_race_ids(d))
        # JRA を混ぜる場合はこちら
        # race_ids.extend(fetch_jra_race_ids(d))

    if not race_ids:
        logging.warning("No races found. Exit.")
        return

    logging.info("Odds scraping ▶ %d races", len(race_ids))
    results: list[dict] = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        fut = {ex.submit(fetch_odds_for_race, r): r for r in race_ids}
        for f in as_completed(fut):
            if (ret := f.result()):
                results.append(ret)

    if not results:
        logging.warning("Odds empty. Exit.")
        return

    df = pd.DataFrame(results)
    out = OUT_DIR / f"odds_demo_{args.date}.csv"
    df.to_csv(out, index=False, encoding="cp932")
    logging.info("CSV saved → %s", out)

if __name__ == "__main__":
    main()
