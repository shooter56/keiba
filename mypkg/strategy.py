# mypkg/strategy.py
import random
import pandas as pd

def random_selector(
    odds_df: pd.DataFrame,
    max_bets: int = 3,
    **kwargs
) -> pd.DataFrame:
    """
    取得したオッズ (odds_df) から max_bets 行だけ
    ランダムに抽出して返すシンプルなベット戦略。

    Parameters
    ----------
    odds_df : DataFrame
        nar_odds_scraper.fetch_odds() が返すデータ
    max_bets : int
        1 日あたり購入する最大点数

    Returns
    -------
    DataFrame (len <= max_bets)
        auto_bet.py がそのまま Provider に渡す
    """
    if odds_df.empty:
        return odds_df.iloc[0:0]

    sample_n = min(max_bets, len(odds_df))
    return odds_df.sample(n=sample_n, random_state=random.randint(0, 2**32 - 1))
