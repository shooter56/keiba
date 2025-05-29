import argparse, time, os, sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, WebDriverException

def fetch_shutuba_html(race_ids, tag, outdir, wait=8, max_retry=3):
    base_url = "https://nar.netkeiba.com/race/shutuba.html?race_id={}" if tag == "NAR" else "https://race.netkeiba.com/race/shutuba/{}/"
    outdir = os.path.abspath(outdir)
    os.makedirs(outdir, exist_ok=True)

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1300,1000")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--ignore-ssl-errors=yes")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-features=CertificateTransparencyEnforcement")
    # WindowsのUser Data流用は一旦無効化
    # options.add_argument('--user-data-dir=...')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.set_page_load_timeout(120)
    for race_id in race_ids:
        url = base_url.format(race_id)
        out_path = os.path.join(outdir, f"shutuba_{race_id}.html")
        if os.path.exists(out_path):
            print(f"✅ {race_id}: 既に保存済み")
            continue
        success = False
        for retry in range(max_retry):
            try:
                print(f"[{race_id}] {url}")
                driver.get(url)
                # JS描画wait
                time.sleep(wait)
                html = driver.page_source
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(html)
                print(f"✅ {race_id}: {os.path.basename(out_path)}")
                success = True
                break
            except (TimeoutException, WebDriverException) as e:
                print(f"[WARN] {race_id} Seleniumエラー: {type(e).__name__}: {e}")
                if retry == max_retry - 1:
                    print(f"[FAIL] {race_id}: 最大リトライ到達、スキップ")
            except Exception as e:
                print(f"[FAIL] {race_id}: 予期せぬエラー: {e}")
                break
        if not success:
            # ファイル空でも置いておく
            with open(out_path, "w", encoding="utf-8") as f:
                f.write("")
    driver.quit()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raceid-csv", required=True)
    parser.add_argument("--tag", choices=["NAR", "JRA"], required=True)
    parser.add_argument("--outdir", required=True)
    parser.add_argument("--wait", type=int, default=8)
    args = parser.parse_args()
    import pandas as pd
    df = pd.read_csv(args.raceid_csv, dtype=str)
    if "race_id" in df.columns:
        race_ids = df["race_id"].tolist()
    else:
        race_ids = df.iloc[:, 0].tolist()
    fetch_shutuba_html(race_ids, args.tag, args.outdir, args.wait)

if __name__ == "__main__":
    main()
