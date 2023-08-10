"""Script to export the ReDoc documentation page into a standalone HTML file."""

import json
import os
from pathlib import Path

from extractor.__main__ import app as app_extractor
from recommender.__main__ import app as app_recommender

HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="content-type" content="text/html; charset=UTF-8">
    <title>My Project - ReDoc</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="shortcut icon" href="https://fastapi.tiangolo.com/img/favicon.png">
    <style>
        body {
            margin: 0;
            padding: 0;
        }
    </style>
    <style data-styled="" data-styled-version="4.4.1"></style>
</head>
<body>
    <div id="redoc-container"></div>
    <script src="https://cdn.jsdelivr.net/npm/redoc/bundles/redoc.standalone.js"> </script>
    <script>
        var spec = %s;
        Redoc.init(spec, {}, document.getElementById("redoc-container"));
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    source_path = Path(__file__).resolve()
    source_dir = source_path.parent

    output_path = os.path.join(source_dir, 'API_HTML_Docu')
    os.makedirs(output_path, exist_ok=True)

    with open(os.path.join(output_path, f"extractor.html"), "w") as fd:
        print(HTML_TEMPLATE % json.dumps(app_extractor.openapi()), file=fd)

    with open(os.path.join(output_path, f"recommender.html"), "w") as fd:
        print(HTML_TEMPLATE % json.dumps(app_recommender.openapi()), file=fd)
