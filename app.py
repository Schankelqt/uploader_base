from flask import Flask, request, Response
from github import Github
from dotenv import load_dotenv
import os
import json

# Загружаем переменные окружения из .env
load_dotenv()

app = Flask(__name__)

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")
    if not file:
        return Response(
            json.dumps({"error": "Файл не передан"}, ensure_ascii=False),
            mimetype='application/json',
            status=400
        )

    filename = file.filename
    if not filename.endswith(".xmind"):
        return Response(
            json.dumps({"error": "Неверный формат файла. Только .xmind"}, ensure_ascii=False),
            mimetype='application/json',
            status=400
        )

    content = file.read()

    try:
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

        return Response(
            json.dumps({"message": "Файл успешно обновлён на GitHub"}, ensure_ascii=False),
            mimetype='application/json',
            status=200
        )

    except Exception as e:
        return Response(
            json.dumps({"error": str(e)}, ensure_ascii=False),
            mimetype='application/json',
            status=500
        )

if __name__ == "__main__":
    app.run(debug=True)