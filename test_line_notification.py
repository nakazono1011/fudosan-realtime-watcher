#!/usr/bin/env python3
"""LINE通知のテストスクリプト"""
import logging
import sys
from datetime import datetime

from config import LINE_CHANNEL_ACCESS_TOKEN
from notifier import send_line_notification, notify_new_property, notify_new_properties
from scraper import Property

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_simple_message():
    """シンプルなテキストメッセージのテスト"""
    print("\n" + "=" * 60)
    print("テスト1: シンプルなテキストメッセージ")
    print("=" * 60)
    
    message = f"""テスト通知

これはLINE Messaging APIのテスト通知です。

実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

もしこのメッセージが届いていれば、設定は正常です！"""
    
    result = send_line_notification(message)
    if result:
        print("✓ 通知の送信に成功しました")
        return True
    else:
        print("✗ 通知の送信に失敗しました")
        return False


def test_property_notification():
    """物件通知のテスト"""
    print("\n" + "=" * 60)
    print("テスト2: 物件通知（単一物件）")
    print("=" * 60)
    
    test_prop = Property(
        id="test-001",
        title="テスト物件 - 渋谷区の1R",
        location="東京都渋谷区神南1-2-3",
        rent="22万円",
        area="45.5㎡",
        station="山手線「渋谷」駅 徒歩5分",
        url="https://www.realtokyoestate.co.jp/estate.php?n=test-001",
        description="テスト用の物件情報です"
    )
    
    result = notify_new_property(test_prop)
    if result:
        print("✓ 物件通知の送信に成功しました")
        print(f"  物件: {test_prop.title}")
        return True
    else:
        print("✗ 物件通知の送信に失敗しました")
        return False


def test_multiple_properties():
    """複数物件通知のテスト"""
    print("\n" + "=" * 60)
    print("テスト3: 複数物件通知")
    print("=" * 60)
    
    test_properties = [
        Property(
            id="test-002",
            title="テスト物件A - 新宿区の1K",
            location="東京都新宿区新宿1-1-1",
            rent="18万円",
            area="35.0㎡",
            station="JR「新宿」駅 徒歩8分",
            url="https://www.realtokyoestate.co.jp/estate.php?n=test-002"
        ),
        Property(
            id="test-003",
            title="テスト物件B - 目黒区の1LDK",
            location="東京都目黒区目黒1-2-3",
            rent="28万円",
            area="55.0㎡",
            station="東急東横線「目黒」駅 徒歩3分",
            url="https://www.realtokyoestate.co.jp/estate.php?n=test-003"
        ),
        Property(
            id="test-004",
            title="テスト物件C - 世田谷区の1R",
            location="東京都世田谷区世田谷1-3-4",
            rent="19万円",
            area="40.0㎡",
            station="小田急線「下北沢」駅 徒歩10分",
            url="https://www.realtokyoestate.co.jp/estate.php?n=test-004"
        ),
    ]
    
    result_count = notify_new_properties(test_properties)
    if result_count > 0:
        print(f"✓ {result_count}件の物件通知の送信に成功しました")
        return True
    else:
        print("✗ 物件通知の送信に失敗しました")
        return False


def test_long_message():
    """長いメッセージのテスト（5000文字制限の確認）"""
    print("\n" + "=" * 60)
    print("テスト4: 長いメッセージ（文字数制限の確認）")
    print("=" * 60)
    
    # 5000文字を超える長いメッセージを作成
    long_message = "これは長いメッセージのテストです。" * 200  # 約6000文字
    
    result = send_line_notification(long_message)
    if result:
        print("✓ 長いメッセージの送信に成功しました（自動的に5000文字に切り詰められました）")
        return True
    else:
        print("✗ 長いメッセージの送信に失敗しました")
        return False


def main():
    """メイン処理"""
    print("\n" + "=" * 60)
    print("LINE Messaging API 通知テスト")
    print("=" * 60)
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 設定確認
    print("\n設定確認:")
    if LINE_CHANNEL_ACCESS_TOKEN:
        print(f"  LINE_CHANNEL_ACCESS_TOKEN: {'*' * 20}...{LINE_CHANNEL_ACCESS_TOKEN[-10:]}")
    else:
        print("  ✗ LINE_CHANNEL_ACCESS_TOKEN が設定されていません")
        return 1

    print("  ※ Broadcast APIを使用（友だち全員に送信されます）")
    
    # テスト実行
    results = []
    
    # テスト1: シンプルなメッセージ
    results.append(("シンプルなメッセージ", test_simple_message()))
    
    # 少し待機（LINE APIのレート制限対策）
    import time
    time.sleep(1)
    
    # テスト2: 物件通知
    results.append(("物件通知", test_property_notification()))
    
    time.sleep(1)
    
    # テスト3: 複数物件通知
    results.append(("複数物件通知", test_multiple_properties()))
    
    time.sleep(1)
    
    # テスト4: 長いメッセージ
    results.append(("長いメッセージ", test_long_message()))
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("テスト結果サマリー")
    print("=" * 60)
    
    success_count = 0
    for test_name, result in results:
        status = "✓ 成功" if result else "✗ 失敗"
        print(f"  {test_name}: {status}")
        if result:
            success_count += 1
    
    print(f"\n成功: {success_count}/{len(results)}")
    
    if success_count == len(results):
        print("\n🎉 すべてのテストが成功しました！")
        return 0
    else:
        print("\n⚠️  一部のテストが失敗しました。設定を確認してください。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
