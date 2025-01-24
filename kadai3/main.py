import flet as ft
import json
import requests
import sqlite3
from datetime import datetime

# DBの設定
DB_PATH = "weather.db"
WEATHER_API_URL = "https://www.jma.go.jp/bosai/forecast/data/forecast/{office_code}.json"

# SQLiteデータベースの初期化
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS weather_forecasts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                office_code TEXT NOT NULL,
                forecast_date DATE NOT NULL,
                weather_code TEXT NOT NULL,
                weather_text TEXT NOT NULL,
                icon TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(office_code, forecast_date)
            )
        """)

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
        "400": "❄️",  # 雪
        "500": "⛈️",  # 雷雨
        # 他の天気コードも追加可能
    }
    return weather_icons.get(weather_code, "❓")

# 天気テキストを取得する関数
def get_weather_text(code: str) -> str:
    weather_codes = {
        "100": "晴れ",
        "101": "晴れ時々曇り",
        "102": "晴れ時々雨",
        "200": "曇り",
        "300": "雨",
        "400": "雪",
        "500": "雷雨",
        # 他の天気テキストも追加可能
    }
    return weather_codes.get(code, f"不明な天気 (コード: {code})")

# メイン関数
def main(page: ft.Page):
    page.title = "天気予報アプリ"
    page.bgcolor = ft.Colors.WHITE

    # DB初期化
    init_db()

    # JSONデータを読み込む
    try:
        with open("jma/data.json", "r", encoding="utf-8") as file:
            data = json.load(file)
    except Exception as e:
        page.add(ft.Text(f"エラー: {e}", color=ft.Colors.RED))
        return

    centers = data.get("centers", {})
    offices = data.get("offices", {})

    weather_display = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)

    # 天気情報を取得してDBに保存し、表示する関数
    def display_weather(office_code: str):
        weather_display.controls.clear()
        try:
            response = requests.get(WEATHER_API_URL.format(office_code=office_code))
            response.raise_for_status()
            weather_data = response.json()

            # デバッグ情報: 取得したweather_dataの表示
            print("取得した天気データ:", json.dumps(weather_data, ensure_ascii=False, indent=2))

            for i, day in enumerate(weather_data[0]["timeSeries"][0]["timeDefines"]):
                date = format_date(day)
                weather_code = weather_data[0]["timeSeries"][0]["areas"][0]["weatherCodes"][i]

                if not isinstance(weather_code, str):
                    raise ValueError(f"weather_codeが期待した型ではありません: {weather_code}")

                weather_text = get_weather_text(weather_code)
                icon = get_weather_icon(weather_code)

                # DBにデータを保存
                with sqlite3.connect(DB_PATH) as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO weather_forecasts (office_code, forecast_date, weather_code, weather_text, icon)
                        VALUES (?, ?, ?, ?, ?)
                    """, (office_code, date, weather_code, weather_text, icon))

                weather_display.controls.append(
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text(date, size=16, weight="bold"),
                                    ft.Text(icon),
                                    ft.Text(weather_text),
                                    ft.Text(f"天気コード: {weather_code}"),
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                            ),
                            padding=10,
                        )
                    )
                )

        except Exception as e:
            print("エラーが発生しました:", e)
            weather_display.controls.append(ft.Text(f"天気情報の取得に失敗しました: {e}", color=ft.Colors.RED))

        page.update()

    # 左側のリスト
    center_tiles = []
    for center_key, center_info in centers.items():
        office_tiles = [
            ft.ListTile(
                title=ft.Text(f"{offices[office_key]['name']} ({offices[office_key]['enName']})"),
                on_click=lambda e, office_code=office_key: display_weather(office_code),
            )
            for office_key in center_info.get("children", [])
            if office_key in offices
        ]

        center_tiles.append(
            ft.ExpansionTile(
                title=ft.Text(center_info["name"], color=ft.Colors.BLACK),
                controls=office_tiles,
                initially_expanded=False,
                text_color=ft.Colors.BLACK,
                collapsed_text_color=ft.Colors.GREY,
            )
        )

    # 左側のリスト
    region_list = ft.Container(
        content=ft.Column(
            controls=center_tiles,
            scroll=ft.ScrollMode.AUTO,
        ),
        width=250,
        bgcolor=ft.Colors.LIGHT_BLUE_50,
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