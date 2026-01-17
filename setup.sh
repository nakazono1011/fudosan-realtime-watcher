#!/bin/bash
# 東京R不動産監視ツール セットアップスクリプト

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLIST_NAME="com.tokyorwatcher.plist"
PLIST_SRC="$SCRIPT_DIR/$PLIST_NAME"
PLIST_DST="$HOME/Library/LaunchAgents/$PLIST_NAME"

echo "=== 東京R不動産監視ツール セットアップ ==="
echo ""

# 依存関係のインストール
echo "1. 依存関係をインストール中..."
pip3 install -r "$SCRIPT_DIR/requirements.txt"
echo ""

# LINE Messaging API設定の確認
echo "2. LINE Messaging API設定を確認中..."
if [ -z "$LINE_CHANNEL_ACCESS_TOKEN" ] || [ -z "$LINE_USER_ID" ]; then
    echo ""
    echo "   LINE Messaging API の設定が必要です"
    echo ""
    echo "   === セットアップ手順 ==="
    echo "   1. LINE Developers (https://developers.line.biz/) にアクセス"
    echo "   2. Messaging API チャネルを作成"
    echo "   3. 「Messaging API設定」タブで以下を取得:"
    echo "      - チャネルアクセストークン（長期）"
    echo "      - ボットのベーシックID（友だち追加用）"
    echo "   4. 「チャネル基本設定」タブで Your user ID を取得"
    echo "   5. LINEアプリでボットを友だち追加"
    echo ""

    if [ -z "$LINE_CHANNEL_ACCESS_TOKEN" ]; then
        read -p "チャネルアクセストークンを入力（後で設定する場合は空欄でEnter）: " token
        if [ -n "$token" ]; then
            export LINE_CHANNEL_ACCESS_TOKEN="$token"
            echo "   トークンを設定しました"
        fi
    else
        echo "   LINE_CHANNEL_ACCESS_TOKEN は設定済みです"
    fi

    if [ -z "$LINE_USER_ID" ]; then
        read -p "Your user ID を入力（後で設定する場合は空欄でEnter）: " user_id
        if [ -n "$user_id" ]; then
            export LINE_USER_ID="$user_id"
            echo "   ユーザーIDを設定しました"
        fi
    else
        echo "   LINE_USER_ID は設定済みです"
    fi

    if [ -n "$LINE_CHANNEL_ACCESS_TOKEN" ] && [ -n "$LINE_USER_ID" ]; then
        echo ""
        echo "   .zshrc または .bashrc に以下を追加して永続化することをお勧めします:"
        echo "   export LINE_CHANNEL_ACCESS_TOKEN='$LINE_CHANNEL_ACCESS_TOKEN'"
        echo "   export LINE_USER_ID='$LINE_USER_ID'"
    fi
else
    echo "   LINE Messaging API は設定済みです"
fi
echo ""

# 動作テスト
echo "3. 動作テストを実行中..."
cd "$SCRIPT_DIR"
python3 main.py
echo ""

# launchd設定
echo "4. 定期実行を設定しますか？（15分おきに実行）"
read -p "   [y/N]: " answer
if [[ "$answer" =~ ^[Yy]$ ]]; then
    # 既存のジョブを停止
    if launchctl list | grep -q "com.tokyorwatcher"; then
        echo "   既存のジョブを停止中..."
        launchctl unload "$PLIST_DST" 2>/dev/null || true
    fi

    # plistにトークンとユーザーIDを設定
    cp "$PLIST_SRC" "$PLIST_DST"

    if [ -n "$LINE_CHANNEL_ACCESS_TOKEN" ] && [ -n "$LINE_USER_ID" ]; then
        # トークンとユーザーIDが設定されている場合、plistを更新
        sed -i '' 's|<!-- <key>LINE_CHANNEL_ACCESS_TOKEN</key> -->|<key>LINE_CHANNEL_ACCESS_TOKEN</key>|' "$PLIST_DST"
        sed -i '' "s|<!-- <string>YOUR_CHANNEL_ACCESS_TOKEN_HERE</string> -->|<string>$LINE_CHANNEL_ACCESS_TOKEN</string>|" "$PLIST_DST"
        sed -i '' 's|<!-- <key>LINE_USER_ID</key> -->|<key>LINE_USER_ID</key>|' "$PLIST_DST"
        sed -i '' "s|<!-- <string>YOUR_USER_ID_HERE</string> -->|<string>$LINE_USER_ID</string>|" "$PLIST_DST"
    fi

    # ジョブを登録
    launchctl load "$PLIST_DST"
    echo "   定期実行を設定しました"
    echo ""
    echo "   確認: launchctl list | grep tokyorwatcher"
    echo "   停止: launchctl unload $PLIST_DST"
fi

echo ""
echo "=== セットアップ完了 ==="
echo ""
echo "手動実行: cd $SCRIPT_DIR && python3 main.py"
echo "ログ確認: tail -f $SCRIPT_DIR/logs/watcher.log"
