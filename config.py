"""設定ファイル"""
import os
from pathlib import Path

# プロジェクトのベースディレクトリ
BASE_DIR = Path(__file__).parent

# 監視対象URL（東京R不動産の検索結果）
# 賃貸物件、賃料15-30万円、面積40㎡以上
SEARCH_URL = (
    "https://www.realtokyoestate.co.jp/estate_search.php"
    "?mode=key&display=inline&type%5B%5D=1&k=&type2%5B%5D=1"
    "&rent_from=15&rent_to=30&building_area_from=40&building_area_to=0"
)

# ベースURL（物件詳細ページのURL生成用）
BASE_URL = "https://www.realtokyoestate.co.jp"

# データ保存先
DATA_DIR = BASE_DIR / "data"
PROPERTIES_FILE = DATA_DIR / "properties.json"

# ログ設定
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "watcher.log"

# LINE Messaging API設定
# トークンとユーザーIDは環境変数から取得（セキュリティのため）
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_USER_ID = os.environ.get("LINE_USER_ID", "")

# LINE Messaging API URL（プッシュメッセージ用）
LINE_MESSAGING_API = "https://api.line.me/v2/bot/message/push"

# ディレクトリが存在しない場合は作成
DATA_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)
