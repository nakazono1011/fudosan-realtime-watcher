"""LINE通知モジュール（Messaging API版）"""
import json
import logging

import requests

from config import LINE_CHANNEL_ACCESS_TOKEN, LINE_USER_ID, LINE_MESSAGING_API
from scraper import Property

logger = logging.getLogger(__name__)


def send_line_notification(message: str) -> bool:
    """LINE Messaging APIでプッシュメッセージを送信"""
    if not LINE_CHANNEL_ACCESS_TOKEN:
        logger.warning("LINE_CHANNEL_ACCESS_TOKENが設定されていません")
        return False

    if not LINE_USER_ID:
        logger.warning("LINE_USER_IDが設定されていません")
        return False

    headers = {
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    # Messaging APIは5000文字が上限
    truncated_message = message[:5000] if len(message) > 5000 else message

    data = {
        "to": LINE_USER_ID,
        "messages": [
            {
                "type": "text",
                "text": truncated_message
            }
        ]
    }

    try:
        response = requests.post(
            LINE_MESSAGING_API,
            headers=headers,
            data=json.dumps(data),
            timeout=10
        )
        if response.status_code == 200:
            logger.info("LINE通知を送信しました")
            return True
        else:
            logger.error(f"LINE通知の送信に失敗: {response.status_code} {response.text}")
            return False
    except Exception as e:
        logger.error(f"LINE通知の送信中にエラー: {e}")
        return False


def notify_new_property(prop: Property, site_name: str = "東京R不動産") -> bool:
    """新着物件をLINEに通知"""
    message = f"""【新着物件】{site_name}

{prop.title}

{prop.location}
{prop.rent} / {prop.area}
{prop.station}

{prop.url}"""
    return send_line_notification(message)


def notify_new_properties(properties: list[Property], site_name: str = "東京R不動産") -> int:
    """複数の新着物件をLINEに通知"""
    if not properties:
        return 0

    success_count = 0

    # 物件数が多い場合はまとめて通知
    if len(properties) > 3:
        summary = f"【新着物件】{site_name}\n\n{len(properties)}件の新着物件があります！\n"
        for prop in properties[:5]:
            summary += f"\n{prop.title}\n{prop.rent} / {prop.area}\n{prop.url}\n"
        if len(properties) > 5:
            summary += f"\n...他{len(properties) - 5}件"

        if send_line_notification(summary):
            success_count = len(properties)
    else:
        # 個別に通知
        for prop in properties:
            if notify_new_property(prop, site_name):
                success_count += 1

    return success_count


if __name__ == "__main__":
    # テスト実行
    logging.basicConfig(level=logging.INFO)

    if not LINE_CHANNEL_ACCESS_TOKEN:
        print("LINE_CHANNEL_ACCESS_TOKEN環境変数を設定してください")
        print("例: export LINE_CHANNEL_ACCESS_TOKEN='your_token_here'")
    elif not LINE_USER_ID:
        print("LINE_USER_ID環境変数を設定してください")
        print("例: export LINE_USER_ID='your_user_id_here'")
    else:
        # テスト通知
        test_prop = Property(
            id="test",
            title="テスト物件",
            location="渋谷区",
            rent="20万円",
            area="45㎡",
            station="山手線「渋谷」駅 徒歩5分",
            url="https://example.com"
        )
        notify_new_property(test_prop)
