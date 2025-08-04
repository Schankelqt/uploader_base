from flask import Flask, request, jsonify
import requests
import os
from utils.github import upload_to_github

app = Flask(__name__)

@app.route("/", methods=["GET"])
def health_check():
    return "Uploader Base is running!"

@app.route("/upload-url", methods=["POST"])
def upload_url():
    data = request.json
    file_url = data.get("file_url")
    filename = data.get("filename")

    if not file_url or not filename:
        return jsonify({"error": "Missing file_url or filename"}), 400

    try:
        # Загружаем файл по ссылке
        response = requests.get(file_url)
        response.raise_for_status()
        file_content = response.content

        # Загружаем на GitHub
        upload_to_github(filename, file_content)

        return jsonify({"status": "success", "message": f"Uploaded {filename} to GitHub"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))