import requests
import json

# 取得するJSONデータのURL
URL = "https://www.jma.go.jp/bosai/common/const/area.json"  # 実際のURLに置き換えてください

try:
    # URLからJSONデータを取得
    data_json = requests.get(URL).json()  # JSONデータを直接取得

    # 取得したデータを確認（オプション）
    print("取得したJSONデータ:", data_json)

    # JSONデータをファイルに保存
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data_json, f, indent=4, ensure_ascii=False)

    print("JSONデータを 'data.json' として保存しました。")

except requests.exceptions.RequestException as e:
    print(f"リクエストに失敗しました: {e}")
except ValueError as e:
    print(f"JSONの解析に失敗しました: {e}")