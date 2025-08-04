from flask import Flask, request, jsonify
import requests
import os
from github import upload_to_github

app = Flask(__name__)

@app.route("/", methods=["GET"])
def health_check():
    return "Uploader Base is running!"

@app.route("/upload-url", methods=["POST"])
def upload_url():
    # Пытаемся извлечь JSON
    data = request.get_json(force=True, silent=True) or {}
    file_url = data.get("file_url")
    filename = data.get("filename")

    # Логируем входящие данные
    print(f"[DEBUG] file_url={file_url}, filename={filename}")

    if not file_url or not filename:
        print("[ERROR] Missing file_url or filename in request.")
        return jsonify({"error": "Missing file_url or filename"}), 400

    try:
        # Загружаем файл с URL
        response = requests.get(file_url)
        response.raise_for_status()
        file_content = response.content
        print(f"[DEBUG] File downloaded: {len(file_content)} bytes")

        # Отправляем в GitHub
        upload_to_github(filename, file_content)
        print(f"[DEBUG] Uploaded {filename} to GitHub successfully")

        return jsonify({"status": "success", "message": f"Uploaded {filename} to GitHub"})
    except requests.RequestException as req_err:
        print(f"[ERROR] Download failed: {req_err}")
        return jsonify({"status": "error", "message": f"Download failed: {str(req_err)}"}), 502
    except Exception as e:
        print(f"[ERROR] Exception during GitHub upload: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

