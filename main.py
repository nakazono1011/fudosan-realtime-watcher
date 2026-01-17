#!/usr/bin/env python3
"""東京R不動産 新着物件監視ツール"""
import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler

from config import LOG_FILE, LINE_CHANNEL_ACCESS_TOKEN, LINE_USER_ID
from scraper import (
    fetch_properties,
    load_saved_properties,
    save_properties,
    find_new_properties,
)
from notifier import notify_new_properties


def setup_logging():
    """ロギングを設定"""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # ファイルハンドラ（ローテーション付き）
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=1024 * 1024,  # 1MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(file_handler)

    # コンソールハンドラ
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(console_handler)

    return logger


def main():
    """メイン処理"""
    logger = setup_logging()
    logger.info("=" * 50)
    logger.info("東京R不動産 監視開始")
    logger.info(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # 現在の物件を取得
        current_properties = fetch_properties()
        if not current_properties:
            logger.warning("物件を取得できませんでした")
            return 1

        # 保存済み物件を読み込み
        saved_properties = load_saved_properties()
        logger.info(f"保存済み物件数: {len(saved_properties)}")

        # 新着物件を検出
        new_properties = find_new_properties(current_properties, saved_properties)

        if new_properties:
            logger.info(f"新着物件を検出: {len(new_properties)}件")
            for prop in new_properties:
                logger.info(f"  - {prop.title} ({prop.rent} / {prop.area})")

            # LINE通知を送信
            if LINE_CHANNEL_ACCESS_TOKEN and LINE_USER_ID:
                notified = notify_new_properties(new_properties)
                logger.info(f"LINE通知送信: {notified}件")
            else:
                logger.warning("LINE Messaging API設定が未完了のため通知をスキップ")
                print("\n=== 新着物件（通知なし）===")
                for prop in new_properties:
                    print(f"\n{prop.title}")
                    print(f"{prop.location}")
                    print(f"{prop.rent} / {prop.area}")
                    print(f"{prop.station}")
                    print(f"{prop.url}")
        else:
            logger.info("新着物件はありません")

        # 現在の物件を保存
        save_properties(current_properties)

        logger.info("監視完了")
        return 0

    except Exception as e:
        logger.exception(f"エラーが発生しました: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
