import os


BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "smart-result-analysis-secret-key"
    )

    UPLOAD_FOLDER = os.path.join(BASE_DIR, "data", "uploads")
    MODEL_FOLDER = os.path.join(BASE_DIR, "models")
    REPORT_FOLDER = os.path.join(BASE_DIR, "reports", "generated")

    MAX_CONTENT_LENGTH = 10 * 1024 * 1024

    ALLOWED_EXTENSIONS = {"csv", "xlsx"}