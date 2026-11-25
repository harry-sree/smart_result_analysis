import os


ALLOWED_EXTENSIONS = {"csv", "xlsx"}


def allowed_file(filename):

    if not filename:
        return False

    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )