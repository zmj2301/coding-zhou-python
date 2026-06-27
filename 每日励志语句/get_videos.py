import requests
import time
import json

MID = "480205745"
BASE_URL = "https://api.bilibili.com/x/space/arc/search"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Referer": "https://space.bilibili.com/",
}

def fetch_page(mid, page):
    params = {
        "mid": mid,
        "ps": 30,
        "pn": page,
        "order": "pubdate",
    }
    resp = requests.get(BASE_URL, params=params, headers=HEADERS)
    if resp.status_code != 200:
        print(f"第 {page} 页请求失败: {resp.status_code}")
        return None
    return resp.json()

def main():
    all_videos = []
    page = 1
    total = None

    while True:
        print(f"正在获取第 {page} 页...")
        data = fetch_page(MID, page)
        if data is None or data.get("code") != 0:
            print("获取失败，停止")
            break

        page_data = data.get("data", {})
        if total is None:
            total = page_data.get("page", {}).get("count", 0)
            print(f"共 {total} 个视频")

        vlist = page_data.get("list", {}).get("vlist", [])
        if not vlist:
            break

        for v in vlist:
            all_videos.append({
                "bvid": v.get("bvid"),
                "title": v.get("title"),
                "description": v.get("description"),
                "play": v.get("play"),
                "danmaku": v.get("video_review"),
                "comment": v.get("comment"),
                "length": v.get("length"),
                "created": v.get("created"),
                "pic": v.get("pic"),
            })

        page += 1
        time.sleep(2)

    with open("videos.json", "w", encoding="utf-8") as f:
        json.dump(all_videos, f, ensure_ascii=False, indent=2)

    print(f"完成！共获取 {len(all_videos)} 个视频信息，已保存到 videos.json")

if __name__ == "__main__":
    main()