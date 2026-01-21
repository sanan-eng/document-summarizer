
import os
import tempfile
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from AI import extract_text, short_summary, medium_summary, long_summary


app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
app.config["UPLOAD_FOLDER"] = tempfile.gettempdir()
app.config["ALLOWED_EXTENSIONS"] = {"pdf", "docx", "pptx", "txt"}


def allowed_file(filename):
    return "." in filename and \
        filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/summarize", methods=["POST"])
def summarize():
    try:
        summary_type = request.form.get("summary_type", "medium")

        if summary_type not in ["short", "medium", "long"]:
            return jsonify({"error": "Invalid summary type"}), 400

        text_to_summarize = ""

        # File input
        if "file" in request.files:
            file = request.files["file"]

            if file.filename:
                if not allowed_file(file.filename):
                    return jsonify({"error": "Unsupported file type"}), 400

                filename = secure_filename(file.filename)
                temp_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(temp_path)

                try:
                    text_to_summarize = extract_text(temp_path)
                finally:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)

        # Text input fallback
        if not text_to_summarize:
            text_to_summarize = request.form.get("text_input", "").strip()

        if len(text_to_summarize) < 20:
            return jsonify({"error": "Text too short to summarize"}), 400

        # Generate summary
        if summary_type == "short":
            summary = short_summary(text_to_summarize)
        elif summary_type == "medium":
            summary = medium_summary(text_to_summarize)
        else:
            summary = long_summary(text_to_summarize)

        return jsonify({
            "success": True,
            "summary": summary,
            "summary_type": summary_type,
            "original_length": len(text_to_summarize),
            "summary_length": len(summary)
        })

    except Exception as e:
        app.logger.error(str(e))
        return jsonify({"error": "Internal summarization error"}), 500


if __name__ == "__main__":
    from waitress import serve
    print("AI Summarizer running on http://localhost:8080")
    serve(app, host="0.0.0.0", port=8080)
