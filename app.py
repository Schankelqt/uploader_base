import logging
from flask import Flask, request, jsonify
from github import Github
from dotenv import load_dotenv
import os
import requests

# Настройка логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

# Flask-приложение
app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "Сервер работает!"

@app.route("/upload", methods=["POST"])
def upload():
    try:
        logger.info(f"📦 Headers: {dict(request.headers)}")
        logger.info(f"📦 Raw body: {request.data}")

        # Попытка загрузки как JSON
        try:
            data = request.get_json(force=True)
        except Exception as json_error:
            logger.warning(f"⚠️ Не удалось распарсить JSON: {json_error}")
            data = request.form.to_dict()
            logger.info(f"📥 Попробовали как form-data: {data}")

        file_url = data.get("file_url")
        logger.info(f"🔗 URL файла: {file_url}")

        if not file_url or not file_url.endswith(".xmind"):
            return jsonify({"error": "❌ Поддерживаются только файлы с расширением .xmind"}), 400

        # Загрузка файла
        file_response = requests.get(file_url)
        if file_response.status_code != 200:
            return jsonify({"error": f"⚠️ Не удалось скачать файл. Код: {file_response.status_code}"}), 400

        content = file_response.content
        filename = file_url.split("/")[-1]

        github_token = os.getenv("GITHUB_TOKEN")
        repo_name = os.getenv("GITHUB_REPO")
        branch = os.getenv("GITHUB_BRANCH", "main")
        target_path = os.getenv("GITHUB_TARGET_PATH", "matrix.xmind")

        g = Github(github_token)
        repo = g.get_repo(repo_name)
        current_file = repo.get_contents(target_path, ref=branch)

        repo.update_file(
            path=target_path,
            message=f"Автоматическое обновление файла {filename} через Dify",
            content=content,
            sha=current_file.sha,
            branch=branch
        )

        logger.info("✅ Файл успешно обновлён на GitHub")
        return jsonify({"message": "Файл успешно обновлён на GitHub"}), 200

    except Exception as e:
        logger.error(f"🔥 Ошибка сервера: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)