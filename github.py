import base64
import os
import requests
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")  # Пример: "username/repo"
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "main")  # По умолчанию main

def upload_to_github(filename, content_bytes):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{filename}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    # Проверяем, существует ли уже файл
    resp = requests.get(url, headers=headers)
    sha = resp.json().get("sha") if resp.status_code == 200 else None

    message = f"Upload {filename}"
    content_base64 = base64.b64encode(content_bytes).decode("utf-8")

    data = {
        "message": message,
        "content": content_base64,
        "branch": GITHUB_BRANCH
    }
    if sha:
        data["sha"] = sha

    put_resp = requests.put(url, headers=headers, json=data)
    put_resp.raise_for_status()