#!/usr/bin/env python3
"""不動産 新着物件監視ツール（東京R不動産 + リノベ百貨店）"""
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
from scraper_renov import (
    fetch_renov_properties,
    load_renov_saved_properties,
    save_renov_properties,
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


def watch_tokyo_r(logger) -> bool:
    """東京R不動産の監視"""
    logger.info("-" * 30)
    logger.info("東京R不動産 監視開始")

    try:
        current_properties = fetch_properties()
        if not current_properties:
            logger.warning("東京R不動産: 物件を取得できませんでした")
            return False

        saved_properties = load_saved_properties()
        logger.info(f"東京R不動産 保存済み物件数: {len(saved_properties)}")

        new_properties = find_new_properties(current_properties, saved_properties)

        if new_properties:
            logger.info(f"東京R不動産 新着物件を検出: {len(new_properties)}件")
            for prop in new_properties:
                logger.info(f"  - {prop.title} ({prop.rent} / {prop.area})")

            if LINE_CHANNEL_ACCESS_TOKEN and LINE_USER_ID:
                notified = notify_new_properties(new_properties, "東京R不動産")
                logger.info(f"東京R不動産 LINE通知送信: {notified}件")
            else:
                logger.warning("LINE Messaging API設定が未完了のため通知をスキップ")
                print("\n=== 東京R不動産 新着物件（通知なし）===")
                for prop in new_properties:
                    print(f"\n{prop.title}")
                    print(f"{prop.location}")
                    print(f"{prop.rent} / {prop.area}")
                    print(f"{prop.station}")
                    print(f"{prop.url}")
        else:
            logger.info("東京R不動産 新着物件はありません")

        save_properties(current_properties)
        return True

    except Exception as e:
        logger.exception(f"東京R不動産でエラーが発生しました: {e}")
        return False


def watch_renov(logger) -> bool:
    """リノベ百貨店の監視"""
    logger.info("-" * 30)
    logger.info("リノベ百貨店 監視開始")

    try:
        current_properties = fetch_renov_properties()
        if not current_properties:
            logger.warning("リノベ百貨店: 物件を取得できませんでした")
            return False

        saved_properties = load_renov_saved_properties()
        logger.info(f"リノベ百貨店 保存済み物件数: {len(saved_properties)}")

        new_properties = find_new_properties(current_properties, saved_properties)

        if new_properties:
            logger.info(f"リノベ百貨店 新着物件を検出: {len(new_properties)}件")
            for prop in new_properties:
                logger.info(f"  - {prop.title} ({prop.rent} / {prop.area})")

            if LINE_CHANNEL_ACCESS_TOKEN and LINE_USER_ID:
                notified = notify_new_properties(new_properties, "リノベ百貨店")
                logger.info(f"リノベ百貨店 LINE通知送信: {notified}件")
            else:
                logger.warning("LINE Messaging API設定が未完了のため通知をスキップ")
                print("\n=== リノベ百貨店 新着物件（通知なし）===")
                for prop in new_properties:
                    print(f"\n{prop.title}")
                    print(f"{prop.location}")
                    print(f"{prop.rent} / {prop.area}")
                    print(f"{prop.station}")
                    print(f"{prop.url}")
        else:
            logger.info("リノベ百貨店 新着物件はありません")

        save_renov_properties(current_properties)
        return True

    except Exception as e:
        logger.exception(f"リノベ百貨店でエラーが発生しました: {e}")
        return False


def main():
    """メイン処理"""
    logger = setup_logging()
    logger.info("=" * 50)
    logger.info("不動産監視 開始")
    logger.info(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 東京R不動産の監視
    tokyo_r_ok = watch_tokyo_r(logger)

    # リノベ百貨店の監視
    renov_ok = watch_renov(logger)

    logger.info("=" * 50)
    logger.info("監視完了")

    # どちらかが失敗した場合は1を返す
    return 0 if (tokyo_r_ok or renov_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
