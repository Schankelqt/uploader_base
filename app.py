from flask import Flask, request, jsonify
from github import Github
from dotenv import load_dotenv
import os

# Загружаем переменные окружения из .env
load_dotenv()

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "Сервер работает!"

@app.route("/upload", methods=["POST"])
def upload():
    try:
        # Логируем заголовки и тело запроса
        app.logger.info(f"📦 Headers: {dict(request.headers)}")
        app.logger.info(f"📦 Raw body: {request.data}")

        # Пытаемся распарсить JSON или form-data
        try:
            data = request.get_json(force=True)
        except Exception:
            data = request.form.to_dict()

        app.logger.info(f"📥 Получен JSON или Form: {data}")

        file_url = data.get("file_url")
        if not file_url:
            return jsonify({"error": "❌ Не удалось получить file_url из запроса"}), 400

        app.logger.info(f"🔗 URL файла: {file_url}")

        # Проверка расширения
        if not file_url.endswith(".xmind"):
            return jsonify({"error": "❌ Поддерживаются только файлы с расширением .xmind"}), 400

        # Скачиваем файл по URL
        import requests
        response = requests.get(file_url)
        if response.status_code != 200:
            return jsonify({"error": f"❌ Не удалось скачать файл: {response.status_code}"}), 400

        file_content = response.content
        filename = file_url.split("/")[-1]

        # Загружаем настройки GitHub
        github_token = os.getenv("GITHUB_TOKEN")
        repo_name = os.getenv("GITHUB_REPO")
        branch = os.getenv("GITHUB_BRANCH", "main")
        target_path = os.getenv("GITHUB_TARGET_PATH", "matrix.xmind")

        # Обновляем файл на GitHub
        g = Github(github_token)
        repo = g.get_repo(repo_name)
        current_file = repo.get_contents(target_path, ref=branch)

        repo.update_file(
            path=target_path,
            message=f"Автоматическое обновление файла {filename} через Dify",
            content=file_content,
            sha=current_file.sha,
            branch=branch
        )

        return jsonify({"message": "✅ Файл успешно обновлён на GitHub"}), 200

    except Exception as e:
        app.logger.error(f"🔥 Ошибка сервера: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)