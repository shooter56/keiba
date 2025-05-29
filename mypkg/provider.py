# mypkg/provider.py
import os
from dotenv import load_dotenv
import pandas as pd

class Spat4Provider:
    """
    SPAT4 (地方競馬ネット投票) にログインして馬券を購入する
    ……のはずですが、ここでは “ドライラン対応” のダミー実装です。
    """

    def __init__(self, headless: bool = True, **kwargs):
        self.headless = headless
        load_dotenv()                         # .env から ID/パス取得
        self.user = os.getenv("SPAT4_USER")
        self.password = os.getenv("SPAT4_PASS")

    # ----------------------------
    # - 実際には Selenium 等で実装 -
    # ----------------------------
    def login(self):
        print(f"[Spat4Provider] (headless={self.headless}) ログイン → {self.user}")

    def place_bets(
        self,
        bets_df: pd.DataFrame,
        stake: int,
        dry_run: bool = True,
    ):
        """
        Parameters
        ----------
        bets_df : DataFrame
            auto_bet.py から渡される選択済みベット行
        stake : int
            1 点あたりの金額（円）
        dry_run : bool
            True のときは実購入しない（ロジだけ確認）
        """
        if dry_run:
            print("[Spat4Provider] *** DRY-RUN MODE *** 購入内容は以下の通り")
            print(bets_df)
            print(f"  購入金額 (各 {stake} 円) 合計 = {stake * len(bets_df):,} 円")
        else:
            self.login()
            # TODO: Selenium で購入フローを実装
            print("[Spat4Provider] ★ 本番購入ロジック未実装 ★")
