"""東京R不動産のスクレイピングモジュール"""
import re
import json
import logging
from dataclasses import dataclass, asdict
from typing import Optional

import requests
from bs4 import BeautifulSoup

from config import SEARCH_URL, BASE_URL, PROPERTIES_FILE

logger = logging.getLogger(__name__)


@dataclass
class Property:
    """物件情報"""
    id: str
    title: str
    location: str
    rent: str
    area: str
    station: str
    url: str
    description: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Property":
        return cls(**data)


def fetch_properties() -> list[Property]:
    """サイトから物件一覧を取得"""
    logger.info(f"物件情報を取得中: {SEARCH_URL}")

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }

    response = requests.get(SEARCH_URL, headers=headers, timeout=30)
    response.raise_for_status()
    response.encoding = response.apparent_encoding

    soup = BeautifulSoup(response.text, "html.parser")
    properties = []

    # 物件リンクを探す（/estate.php?n=XXXXX のパターン）
    for link in soup.find_all("a", href=re.compile(r"/estate\.php\?n=\d+")):
        prop = parse_property_link(link)
        if prop and prop.id not in [p.id for p in properties]:
            properties.append(prop)

    logger.info(f"{len(properties)}件の物件を取得しました")
    return properties


def parse_property_link(link) -> Optional[Property]:
    """リンク要素から物件情報をパース"""
    try:
        href = link.get("href", "")
        match = re.search(r"n=(\d+)", href)
        if not match:
            return None

        property_id = match.group(1)
        url = f"{BASE_URL}{href}"

        # リンク内のテキストから情報を抽出
        text = link.get_text(separator=" ", strip=True)

        # タイトル、所在地、賃料、面積、駅を抽出
        title = ""
        location = ""
        rent = ""
        area = ""
        station = ""
        description = ""

        # テキスト全体から正規表現で情報を抽出
        # 賃料（例: "22万円", "19万5,000円", "21万5,000～53万円"）
        rent_match = re.search(r'(\d+万[\d,]*円(?:（税込）)?(?:～[\d万,]+円)?)', text)
        if rent_match:
            rent = rent_match.group(1)

        # 面積（例: "40.04㎡", "35.54～83.75㎡"）
        area_match = re.search(r'([\d.]+(?:～[\d.]+)?㎡)', text)
        if area_match:
            area = area_match.group(1)

        # 駅情報（例: "中央線「中野」駅 徒歩7分"）
        station_match = re.search(r'([^\s]+線[^\s]*「[^」]+」駅\s*徒歩\d+分)', text)
        if station_match:
            station = station_match.group(1)
        else:
            # 別のパターン（例: "JR東海道線「辻堂」駅 徒歩13分"）
            station_match = re.search(r'((?:JR|都営|東急|京急|小田急)?[^\s「]*「[^」]+」駅\s*徒歩\d+分)', text)
            if station_match:
                station = station_match.group(1)

        # 所在地（区や市を含む短いテキスト）
        # テーブル内の情報を探す
        tables = link.find_all("table")
        for table in tables:
            cells = table.find_all("td")
            for cell in cells:
                cell_text = cell.get_text(strip=True)

                # 所在地（区や市を含む、短いテキスト）
                if re.search(r'[区市町]', cell_text) and "万円" not in cell_text and "駅" not in cell_text and "徒歩" not in cell_text:
                    if len(cell_text) < 30 and not location:
                        location = cell_text

        # 所在地がまだ空なら、テキストから抽出
        if not location:
            loc_match = re.search(r'((?:東京都)?[^\s]+[区市][^\s]*)', text)
            if loc_match:
                loc = loc_match.group(1)
                if len(loc) < 30 and "万円" not in loc:
                    location = loc

        # タイトルを抽出
        # 内部リンクのテキストを探す
        inner_links = link.find_all("a", href=re.compile(r"/estate\.php\?n=\d+"))
        for inner_link in inner_links:
            inner_text = inner_link.get_text(strip=True)
            if inner_text and 3 < len(inner_text) < 50 and "万円" not in inner_text and "㎡" not in inner_text:
                title = inner_text
                break

        # タイトルがまだ空なら、"rent" の後のテキストを探す
        if not title:
            rent_idx = text.find("rent")
            if rent_idx != -1:
                after_rent = text[rent_idx + 4:].strip()
                words = after_rent.split()
                if words:
                    potential_title = words[0]
                    if 3 < len(potential_title) < 50:
                        title = potential_title

        # 説明文を抽出
        paragraphs = link.find_all("p")
        for p in paragraphs:
            p_text = p.get_text(strip=True)
            if len(p_text) > 20:
                description = p_text[:100]
                break

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
            description=description
        )

    except Exception as e:
        logger.error(f"物件情報のパースに失敗: {e}")
        return None


def load_saved_properties() -> dict[str, Property]:
    """保存済みの物件情報を読み込む"""
    if not PROPERTIES_FILE.exists():
        return {}

    try:
        with open(PROPERTIES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {p["id"]: Property.from_dict(p) for p in data}
    except Exception as e:
        logger.error(f"保存済み物件の読み込みに失敗: {e}")
        return {}


def save_properties(properties: list[Property]) -> None:
    """物件情報を保存"""
    try:
        with open(PROPERTIES_FILE, "w", encoding="utf-8") as f:
            json.dump([p.to_dict() for p in properties], f, ensure_ascii=False, indent=2)
        logger.info(f"物件情報を保存しました: {PROPERTIES_FILE}")
    except Exception as e:
        logger.error(f"物件情報の保存に失敗: {e}")


def find_new_properties(current: list[Property], saved: dict[str, Property]) -> list[Property]:
    """新着物件を検出"""
    new_properties = []
    for prop in current:
        if prop.id not in saved:
            new_properties.append(prop)
    return new_properties


if __name__ == "__main__":
    # テスト実行
    logging.basicConfig(level=logging.INFO)
    props = fetch_properties()
    for p in props[:5]:
        print(f"ID: {p.id}, タイトル: {p.title}, 賃料: {p.rent}, 面積: {p.area}")
