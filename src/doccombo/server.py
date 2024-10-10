import io
from pathlib import Path
import tempfile

from flask import Flask, request, send_file
from werkzeug.utils import secure_filename

from . import configuration
from . import layout


# https://pymupdf.readthedocs.io/en/latest/how-to-open-a-file.html#supported-file-types
ALLOWED_EXTENSIONS = {
    # Documents
    "pdf",
    "xps",
    "epub",
    "mobi",
    "fb2",
    "cbz",
    "svg",
    "txt",
    # Images
    "jpg",
    "jpeg",
    "png",
    "bmp",
    "gif",
    "tiff",
    "pnm",
    "pgm",
    "pbm",
    "ppm",
    "pam",
    "jxr",
    "jpx",
    "jp2",
    "psd",
}


app = Flask(__name__)


@app.get("/")
def index():
    return """
    <html>
    <head>
    </head>
    <body>
        <form method="POST" enctype="multipart/form-data" target="_blank">
        <input type="file" name="files" multiple required
            accept="image/*,application/pdf,text/plain,.epub,.mobi,.xps,.fb2,.cbz"
        ><br>
        <input type="submit">
        </form>
    </body>
    </html>
    """


@app.post("/")
def post_index():
    config = configuration.load_config(Path("config.toml"))
    if "files" not in request.files:
        raise ValueError("No files")

    files = request.files.getlist("files")

    with tempfile.TemporaryDirectory() as tmpdir:
        dirpath = Path(tmpdir)
        for idx, file in enumerate(files):
            fname = file.filename
            if fname is not None:
                fpath = Path(secure_filename(fname))
                if fpath.suffix.lstrip(".").lower() in ALLOWED_EXTENSIONS:
                    file.save(dirpath / f"{idx:03}-{fpath}")
                    continue

            raise ValueError(f"Invalid file: {fname}")

        doc = layout.layout_from_directory(
            dirpath,
            config,
        )

    return send_file(io.BytesIO(doc.tobytes()), mimetype="application/pdf")
