from fastapi import FastAPI

from extractor.input_processor import process_input
from extractor.typedefs.io_types import Input, Output

description = """
Extractor for parameters of input files

## extract

You can extract parameters given a list of input files.
"""

app = FastAPI(description=description, version="0.2.0")


@app.get("/")
async def root():
    return {"message": "Extractor is up and running."}


@app.post("/extract/", response_model=Output)
async def extract(inp: Input):
    out = process_input(inp)
    return out


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
