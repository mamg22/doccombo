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


APP_HTML = """
<html>
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>doccombo</title>
    <style>
    body {
        width: 100svw;
        height: 100svh;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    main {
        text-align: center;
        border: 3px solid gray;
        border-radius: 1em;
        padding: 1em;
        background-color: #eeeeee;
    }
    input {
        margin: 0.5em;
    }
    </style>
</head>
<body>
    <main>
        <h2><pre>doccombo</pre></h2>
        <p>Seleccione los archivos a reducir<br>Se aceptan documentos e imágenes</p>
        <form method="POST" enctype="multipart/form-data" target="_blank">
            <input type="file" name="files" multiple required
                accept="image/*,application/pdf,text/plain,.epub,.mobi,.xps,.fb2,.cbz"
            ><br>
            <input type="submit" value="Enviar">
        </form>
    </main>
</body>
</html>
"""


app = Flask(__name__)


@app.get("/")
def index():
    return APP_HTML


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
