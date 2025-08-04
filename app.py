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
    # 🔍 ЛОГИРОВАНИЕ ДЛЯ ОТЛАДКИ
    print("🔽 Получен POST-запрос на /upload")
    print("🔍 Заголовки:", dict(request.headers))

    # Попробуем понять, что было в теле
    try:
        json_data = request.get_json(force=True)
        print("🔍 Получен JSON:", json_data)
    except Exception:
        json_data = None
        print("⚠️ JSON не распарсился")

    print("🔍 Форм-поля:", request.form)
    print("🔍 Файлы:", request.files)

    # Поддержка загрузки через form-data
    file = request.files.get("file")

    # Если не найден файл – возможно, прислали URL в json
    if not file and json_data and "file" in json_data:
        from urllib.request import urlopen
        from io import BytesIO

        try:
            file_url = json_data["file"]
            filename = file_url.split("/")[-1] or "matrix.xmind"
            if not filename.endswith(".xmind"):
                return jsonify({"error": "Файл должен иметь расширение .xmind"}), 400

            print(f"⬇️ Загружаем файл по ссылке: {file_url}")
            response = urlopen(file_url)
            content = response.read()
        except Exception as e:
            return jsonify({"error": f"Не удалось загрузить файл по ссылке: {str(e)}"}), 400
    elif file:
        filename = file.filename
        if not filename.endswith(".xmind"):
            return jsonify({"error": "Неверный формат файла. Только .xmind"}), 400
        content = file.read()
    else:
        return jsonify({"error": "Файл не передан"}), 400

    # Обновление файла на GitHub
    try:
        github_token = os.getenv("GITHUB_TOKEN")
        repo_name = os.getenv("GITHUB_REPO")
        branch = os.getenv("GITHUB_BRANCH", "main")
        target_path = os.getenv("GITHUB_TARGET_PATH", "matrix.xmind")

        if not all([github_token, repo_name]):
            return jsonify({"error": "Не заданы переменные окружения GITHUB_TOKEN или GITHUB_REPO"}), 500

        g = Github(github_token)
        repo = g.get_repo(repo_name)
        current_file = repo.get_contents(target_path, ref=branch)

        repo.update_file(
            path=target_path,
            message=f"Обновление из Dify: {filename}",
            content=content,
            sha=current_file.sha,
            branch=branch
        )

        print("✅ Файл успешно обновлён на GitHub")
        return jsonify({"message": "Файл успешно обновлён на GitHub"}), 200

    except Exception as e:
        print("❌ Ошибка при обновлении файла:", str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)