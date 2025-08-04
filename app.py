from flask import Flask, request, jsonify
from github import Github
from dotenv import load_dotenv
import os
import requests

# Загружаем переменные окружения из .env
load_dotenv()

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "Сервер работает!"

@app.route("/upload", methods=["POST"])
def upload():
    try:
        data = request.get_json()
        print(f"📥 Получен JSON: {data}")

        file_url = data.get("file")
        print(f"🔗 URL файла: {file_url}")

        if not file_url or not file_url.endswith(".xmind"):
            return jsonify({"error": "❌ Поддерживаются только файлы с расширением .xmind"}), 400

        # Скачиваем файл по URL
        response = requests.get(file_url)
        print(f"📡 Статус скачивания: {response.status_code}")
        if response.status_code != 200:
            return jsonify({"error": f"Не удалось скачать файл. Код: {response.status_code}"}), 400

        content = response.content
        filename = os.path.basename(file_url)

        github_token = os.getenv("GITHUB_TOKEN")
        repo_name = os.getenv("GITHUB_REPO")
        branch = os.getenv("GITHUB_BRANCH", "main")
        target_path = os.getenv("GITHUB_TARGET_PATH", "matrix.xmind")

        print(f"🛠 GitHub → Репозиторий: {repo_name}, Ветка: {branch}, Путь: {target_path}")

        g = Github(github_token)
        repo = g.get_repo(repo_name)

        try:
            current_file = repo.get_contents(target_path, ref=branch)
            repo.update_file(
                path=target_path,
                message=f"Автоматическое обновление файла {filename} через Dify",
                content=content,
                sha=current_file.sha,
                branch=branch
            )
            print("✅ Файл обновлён через update_file")
        except Exception as e:
            print(f"📄 Файл не найден, создаю заново. Ошибка: {e}")
            repo.create_file(
                path=target_path,
                message=f"Создание нового файла {filename} через Dify",
                content=content,
                branch=branch
            )
            print("✅ Файл создан через create_file")

        return jsonify({"message": "✅ Файл успешно загружен на GitHub"}), 200

    except Exception as e:
        print(f"🔥 Ошибка сервера: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)