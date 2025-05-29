function Invoke-NARDayJob {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][ValidatePattern('^\d{8}$')]
        [string]$Date             # 例: 20250430
    )

    #── ファイル名（PWD に連続生成）────────────────────────────
    $CsvOdds     = "nar_tansho_${Date}.csv"
    $FeatherRaw  = "odds_${Date}_clean.feather"
    $FeatherHit  = "odds_features_${Date}_withhit.feather"
    $CsvWithHit  = "nar_tansho_${Date}_withhit.csv"
    $CsvFeature  = "nar_tansho_${Date}_features.csv"
    $ResultsCsv  = "C:\TFJV\TXT\keiba_data\merged_results.csv"
    #──────────────────────────────────────────────────────────

    ## 0) オッズ取得 ----------------------------------------------------
    Write-Host "[${Date}] 0) Fetch odds"
    python netkeiba_scraping\nar_odds_fetch.py $Date
    if (-not (Test-Path $CsvOdds)) { Write-Warning "CSV not found"; return }

    ## 1) CSV → Feather -------------------------------------------------
    Write-Host "[${Date}] 1) CSV -> Feather"
    python netkeiba_scraping\tansho_csv_to_feather.py `
        $Date $CsvOdds $FeatherRaw
    if (-not (Test-Path $FeatherRaw)) { Write-Warning "Feather NG"; return }

    ## 2) hit_flg 付与（Feather in/out）--------------------------------
    Write-Host "[${Date}] 2) add hit_flg"
    python netkeiba_scraping\add_hitflag_from_results.py `
        --feat $FeatherRaw --results $ResultsCsv --out $FeatherHit
    if (-not (Test-Path $FeatherHit)) { Write-Warning "hit_flg NG"; return }

    ## 3) Feather → CSV -------------------------------------------------
    Write-Host "[${Date}] 3) Feather -> CSV"
    python -c "import pandas as pd, sys; pd.read_feather(r'$FeatherHit').to_csv(r'$CsvWithHit', index=False)"
    if (-not (Test-Path $CsvWithHit)) { Write-Warning "CSV with hit NG"; return }

    ## 4) 特徴量生成（CSV in/out・位置引数 + -o）------------------------
    Write-Host "[${Date}] 4) create features"
    python netkeiba_scraping\create_features_from_odds.py `
        $CsvWithHit -o $CsvFeature
    if (-not (Test-Path $CsvFeature)) { Write-Warning "features NG"; return }

    Write-Host "[${Date}] ✅ DONE → $CsvFeature" -ForegroundColor Green
}
