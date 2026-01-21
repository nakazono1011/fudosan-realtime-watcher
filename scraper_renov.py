"""リノベ百貨店のスクレイピングモジュール"""
import re
import json
import logging

import requests
from bs4 import BeautifulSoup

from config import RENOV_SEARCH_URL, RENOV_BASE_URL, RENOV_PROPERTIES_FILE
from scraper import Property

logger = logging.getLogger(__name__)


def fetch_renov_properties() -> list[Property]:
    """リノベ百貨店から物件一覧を取得（POSTリクエスト）"""
    logger.info(f"リノベ百貨店から物件情報を取得中: {RENOV_SEARCH_URL}")

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    # 検索条件:
    # - 家賃: 15万円〜30万円
    # - 間取り: 1LDK(203), 2K(205), 2DK(302), 2LDK(303)
    # - 設備: 0169（バス・トイレ別など）
    # - 募集中のみ
    form_data = [
        ("price[]", "15"),
        ("price[]", "30"),
        ("cond_money_combo", "1"),
        ("b_area[]", "0"),
        ("b_area[]", "99999"),
        ("eki_walk", "0"),
        ("madori[]", "203"),
        ("madori[]", "205"),
        ("madori[]", "302"),
        ("madori[]", "303"),
        ("setsubi_cd[]", "0169"),
        ("state_check", "2"),
        ("city_cd", ""),
        ("pref_cd_all", ""),
        ("ensen_cd", ""),
        ("eki_cd", ""),
        ("sch_flg", ""),
        ("pref_cd1", ""),
        ("pref_cd2", ""),
        ("required_time", ""),
        ("required_time2", ""),
        ("transfer_num", ""),
        ("transfer_num2", ""),
        ("ekitan_eki_name", ""),
        ("ekitan_eki_name2", ""),
        ("freeword", ""),
        ("item_div", ""),
        ("state", "2"),
        ("eki_json_flg", ""),
        ("categoly", ""),
    ]

    response = requests.post(RENOV_SEARCH_URL, data=form_data, headers=headers, timeout=30)
    response.raise_for_status()
    response.encoding = "utf-8"

    soup = BeautifulSoup(response.text, "html.parser")
    properties = []

    # property-item クラスの div を探す
    for item in soup.find_all("div", class_="property-item"):
        prop = parse_renov_property(item)
        if prop and prop.id not in [p.id for p in properties]:
            properties.append(prop)

    logger.info(f"リノベ百貨店: {len(properties)}件の物件を取得しました")
    return properties


def parse_renov_property(item) -> Property | None:
    """property-item 要素から物件情報をパース"""
    try:
        # 物件詳細リンクを探す
        link = item.find("a", href=re.compile(r"/detail/\d+/[\w\d_]+/"))
        if not link:
            return None

        href = link.get("href", "")
        # /detail/001/ka260120_2/ から ka260120_2 を抽出
        match = re.search(r"/detail/\d+/([\w\d_]+)/", href)
        if not match:
            return None

        property_id = match.group(1)
        url = f"{RENOV_BASE_URL}{href}"

        title = ""
        location = ""
        rent = ""
        area = ""
        station = ""

        # タイトル抽出（class="title fnt-bold"）
        title_elem = item.find("span", class_="title")
        if title_elem:
            title = title_elem.get_text(strip=True)

        # 駅情報抽出（class="place"）
        place_elem = item.find("span", class_="place")
        if place_elem:
            station = place_elem.get_text(strip=True)

        # 賃料・面積抽出（class="price"）
        price_elem = item.find("span", class_="price")
        if price_elem:
            price_text = price_elem.get_text(separator=" ", strip=True)
            # 賃料（例: "190,000円/5,300円"）
            rent_match = re.search(r'([\d,]+円(?:/[\d,]+円)?)', price_text)
            if rent_match:
                rent = rent_match.group(1)
            # 面積（例: "58.32㎡"）
            area_match = re.search(r'([\d.]+㎡)', price_text)
            if area_match:
                area = area_match.group(1)

        if not title:
            title = f"物件 {property_id}"

        return Property(
            id=property_id,
            title=title,
            location=location,
            rent=rent,
            area=area,
            station=station,
            url=url,
        )

    except Exception as e:
        logger.error(f"リノベ百貨店物件のパースに失敗: {e}")
        return None


def load_renov_saved_properties() -> dict[str, Property]:
    """保存済みのリノベ百貨店物件情報を読み込む"""
    if not RENOV_PROPERTIES_FILE.exists():
        return {}

    try:
        with open(RENOV_PROPERTIES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {p["id"]: Property.from_dict(p) for p in data}
    except Exception as e:
        logger.error(f"リノベ百貨店の保存済み物件の読み込みに失敗: {e}")
        return {}


def save_renov_properties(properties: list[Property]) -> None:
    """リノベ百貨店の物件情報を保存"""
    try:
        with open(RENOV_PROPERTIES_FILE, "w", encoding="utf-8") as f:
            json.dump([p.to_dict() for p in properties], f, ensure_ascii=False, indent=2)
        logger.info(f"リノベ百貨店の物件情報を保存しました: {RENOV_PROPERTIES_FILE}")
    except Exception as e:
        logger.error(f"リノベ百貨店の物件情報の保存に失敗: {e}")


if __name__ == "__main__":
    # テスト実行
    logging.basicConfig(level=logging.INFO)
    props = fetch_renov_properties()
    for p in props[:5]:
        print(f"ID: {p.id}, タイトル: {p.title}, 賃料: {p.rent}, 面積: {p.area}")
