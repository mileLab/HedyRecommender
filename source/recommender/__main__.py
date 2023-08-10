from fastapi import FastAPI

from recommender.recommenderFunctionality import perform_recommendation, additional_validation
from recommender.typedefs.io_types import Input, Output

description = """
Recommender for given parameter sets

## recommend

Allows you to rank the given demand parameters with the given supplier parameters
"""

app = FastAPI(description=description, version="0.2.0")


@app.get("/")
async def root():
    return {"message": "Recommender is up and running."}


@app.post("/recommend/", response_model=Output)
async def recommend(inp: Input):
    validated_input = additional_validation(inp)

    return perform_recommendation(validated_input)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8050)
