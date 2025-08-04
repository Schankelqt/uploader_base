from flask import Flask, request, jsonify
from github import Github
from dotenv import load_dotenv
import os
import requests

load_dotenv()
app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "Сервер работает!"

@app.route("/upload", methods=["POST"])
def upload():
    try:
        # --- 1. Попытка получить JSON
        data = {}
        if request.is_json:
            data = request.get_json()
            app.logger.info(f"📥 Получен JSON: {data}")
        else:
            app.logger.info("⚠️ JSON не получен: content-type не application/json")

        file = request.files.get("file")
        file_url = data.get("file_url") if data else None

        if not file and file_url:
            # --- 2. Загружаем файл по ссылке
            app.logger.info(f"🔗 URL файла: {file_url}")
            if not file_url.endswith(".xmind"):
                return jsonify({"error": "❌ Поддерживаются только файлы с расширением .xmind"}), 400

            r = requests.get(file_url)
            if r.status_code != 200:
                return jsonify({"error": f"❌ Не удалось загрузить файл по ссылке. Код: {r.status_code}"}), 400

            content = r.content
            filename = os.path.basename(file_url)
        elif file:
            filename = file.filename
            if not filename.endswith(".xmind"):
                return jsonify({"error": "❌ Поддерживаются только файлы с расширением .xmind"}), 400
            content = file.read()
        else:
            return jsonify({"error": "❌ Файл не передан"}), 400

        # --- 3. Загрузка в GitHub
        github_token = os.getenv("GITHUB_TOKEN")
        repo_name = os.getenv("GITHUB_REPO")
        branch = os.getenv("GITHUB_BRANCH", "main")
        target_path = os.getenv("GITHUB_TARGET_PATH", "matrix.xmind")

        g = Github(github_token)
        repo = g.get_repo(repo_name)

        try:
            current_file = repo.get_contents(target_path, ref=branch)
            repo.update_file(
                path=target_path,
                message=f"Обновление файла {filename} через Dify",
                content=content,
                sha=current_file.sha,
                branch=branch
            )
        except Exception:
            repo.create_file(
                path=target_path,
                message=f"Первое добавление файла {filename} через Dify",
                content=content,
                branch=branch
            )

        return jsonify({"message": "✅ Файл успешно обновлён на GitHub"}), 200

    except Exception as e:
        app.logger.error(f"🔥 Ошибка сервера: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)