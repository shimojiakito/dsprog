import flet as ft
import json
import requests
from datetime import datetime

# ローカルJSONデータのファイルパス
DATA_FILE = "jma/data.json"
WEATHER_API_URL = "https://www.jma.go.jp/bosai/forecast/data/forecast/{office_code}.json"

# 日付フォーマット関数
def format_date(date_str: str) -> str:
    date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    return date.strftime("%Y年%m月%d日")

# 天気アイコンを取得する関数
def get_weather_icon(weather_code: str) -> str:
    weather_icons = {
        "100": "☀️",  # 晴れ
        "101": "🌤️",  # 晴れ時々曇り
        "102": "🌦️",  # 晴れ時々雨
        "200": "☁️",  # 曇り
        "300": "🌧️",  # 雨
        "317": "🌧️❄️☁️",  # 雨か雪のち曇り
        "400": "❄️",  # 雪
        "402": "❄️☁️",  # 雪時々曇り
        "500": "⛈️",  # 雷雨
        "413": "❄️→🌧️",  # 雪のち雨
        "314": "🌧️→❄️",  # 雨のち雪
        "201": "🌤️",
        "202": "☁️🌧️",
        "218": "☁️❄️",
        "270": "❄️☁️",
        "206": "🌧️☁️",
        "111": "🌧️☀️",
        "112": "🌧️❄️",
        "211": "❄️☀️",
        "212": "❄️☁️",
        "313": "❄️🌧️",
        "203": "☁️❄️",
        "302": "❄️",
        "114": "❄️☀️",
        "214": "☁️🌧️",
        "204": "☁️❄️⚡️",
        "207": "☁️🌧️❄️",
        "110": "☀️☁️",
        "205": "☁️❄️"
    }
    return weather_icons.get(weather_code, "❓")

# 天気テキストを取得する関数
def get_weather_text(code: str) -> str:
    weather_codes = {
        "100": "晴れ",
        "101": "晴れ時々曇り",
        "102": "晴れ時々雨",
        "200": "曇り",
        "201": "曇り時々晴れ",
        "202": "曇り時々雨",
        "218": "曇り時々雪",
        "270": "雪時々曇り",
        "300": "雨",
        "317": "雨か雪のち曇り",
        "400": "雪",
        "402": "雪時々曇り",
        "500": "雷雨",
        "413": "雪のち雨",
        "206": "雨時々曇り",
        "111": "雨時々晴れ",
        "112": "雨時々雪",
        "211": "雪時々晴れ",
        "206": "雨時々曇り",
        "212": "雪時々曇り",
        "313": "雪のち雨",
        "314": "雨のち雪",
        "203": "曇り時々雪",
        "302": "雪",
        "114": "雪時々晴れ",
        "214": "曇り後雨",
        "204": "曇り時々雪で雷を伴う",
        "207": "曇り時々雨か雪",
        "110": "晴れのち時々曇り",
        "205": "曇り時々雪"
    }
    return weather_codes.get(code, f"不明な天気 (コード: {code})")

# メイン関数
def main(page: ft.Page):
    page.title = "天気予報アプリ"
    page.scroll = ft.ScrollMode.AUTO
    page.bgcolor = ft.colors.WHITE

    # JSONデータを読み込む
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        page.add(ft.Text("JSONファイルが見つかりません。", color=ft.colors.RED))
        return
    except json.JSONDecodeError as e:
        page.add(ft.Text(f"JSONデータの読み込みに失敗しました: {e}", color=ft.colors.RED))
        return

    centers = data.get("centers", {})
    offices = data.get("offices", {})

    # 天気情報を表示する領域
    weather_display = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)

    # 天気情報を取得して表示する関数
    def display_weather(office_code: str):
        weather_display.controls.clear()
        try:
            # 天気情報を取得
            response = requests.get(WEATHER_API_URL.format(office_code=office_code))
            response.raise_for_status()
            weather_data = response.json()

            # 天気情報を表示
            for i, day in enumerate(weather_data[0]["timeSeries"][0]["timeDefines"]):
                date = format_date(day)
                # i 番目の天気コードを取得
                weather_code = weather_data[0]["timeSeries"][0]["areas"][0]["weatherCodes"][i]
                weather_display.controls.append(
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text(date, size=16, weight="bold"),
                                    ft.Text(get_weather_icon(weather_code)),
                                    ft.Text(get_weather_text(weather_code)),
                                    ft.Text(f"天気コード: {weather_code}"),
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                            ),
                            padding=10,
                        )
                    )
                )
        except Exception as e:
            weather_display.controls.append(ft.Text(f"天気情報の取得に失敗しました: {e}", color=ft.colors.RED))

        page.update()

    # 左側のリスト
    center_tiles = []
    for center_key, center_info in centers.items():
        # そのセンターに関連するオフィスを取得
        related_offices = [
            offices[office_key]
            for office_key in center_info.get("children", [])
            if office_key in offices
        ]

        # オフィスリスト
        office_tiles = [
            ft.ListTile(
                title=ft.Text(f"{offices[office_key]['name']} ({offices[office_key]['enName']})"),
                on_click=lambda e, office_code=office_key: display_weather(office_code),
            )
            for office_key in center_info.get("children", [])
            if office_key in offices
        ]

        # ExpansionTile
        center_tiles.append(
            ft.ExpansionTile(
                title=ft.Text(center_info["name"], color=ft.colors.BLACK),
                controls=office_tiles,
                initially_expanded=False,
                text_color=ft.colors.BLACK,
                collapsed_text_color=ft.colors.GREY,
            )
        )

    # 左側のリスト
    region_list = ft.Container(
        content=ft.Column(
            controls=center_tiles,
            scroll=ft.ScrollMode.AUTO,
        ),
        width=250,
        bgcolor=ft.colors.LIGHT_BLUE_50,
        padding=10,
    )

    # レイアウト
    page.add(
        ft.Row(
            controls=[
                region_list,
                ft.Container(content=weather_display, padding=10),
                ft.VerticalDivider(width=1),
            ],
            expand=True,
        )
    )

# 実行
ft.app(target=main)
