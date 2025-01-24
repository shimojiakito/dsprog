import flet as ft
import json
import requests
from datetime import datetime

# 定数
AREA_API_URL = "http://www.jma.go.jp/bosai/common/const/area.json"
WEATHER_API_URL = "https://www.jma.go.jp/bosai/forecast/data/forecast/{area_code}.json"

# 日付フォーマット関数
def format_date(date_str: str) -> str:
    date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    return date.strftime("%Y年%m月%d日")

# メインアプリケーション
def main(page: ft.Page):
    page.title = "気象庁 天気予報アプリ"
    page.scroll = ft.ScrollMode.AUTO

    # 左側の地域リスト
    area_list = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)

    # 天気情報表示領域
    weather_display = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)

    # 地域リストを取得
    try:
        area_response = requests.get(AREA_API_URL)
        area_response.raise_for_status()
        area_data = area_response.json()
    except Exception as e:
        page.add(ft.Text(f"地域データの取得に失敗しました: {e}", color=ft.colors.RED))
        return

    # 地域の天気情報を表示
    def display_weather(area_code: str):
        weather_display.controls.clear()
        try:
            weather_response = requests.get(WEATHER_API_URL.format(area_code=area_code))
            weather_response.raise_for_status()
            weather_data = weather_response.json()

            # 天気情報を表示
            for i, date in enumerate(weather_data[0]["timeSeries"][0]["timeDefines"]):
                formatted_date = format_date(date)
                weather_code = weather_data[0]["timeSeries"][0]["areas"][0]["weatherCodes"][i]
                weather_text = weather_data[0]["timeSeries"][0]["areas"][0]["weathers"][i]
                weather_display.controls.append(
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text(formatted_date, size=16, weight="bold"),
                                    ft.Text(f"天気: {weather_text}"),
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

    # 地域リストを作成
    for center_code, center_data in area_data["centers"].items():
        region_tiles = []
        for office_code in center_data["children"]:
            if office_code in area_data["offices"]:
                office_name = area_data["offices"][office_code]["name"]
                region_tiles.append(
                    ft.ListTile(
                        title=ft.Text(office_name),
                        on_click=lambda e, code=office_code: display_weather(code),
                    )
                )
        area_list.controls.append(
            ft.ExpansionTile(
                title=ft.Text(center_data["name"]),
                controls=region_tiles,
            )
        )

    # ページレイアウト
    page.add(
        ft.Row(
            controls=[
                ft.Container(content=area_list, width=300, bgcolor=ft.colors.LIGHT_BLUE_50, padding=10),
                ft.VerticalDivider(width=1),
                ft.Container(content=weather_display, expand=True, padding=10),
            ]
        )
    )

# アプリケーションを起動
ft.app(target=main)
