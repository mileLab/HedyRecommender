from dataclasses import asdict

import pytest
from fastapi.testclient import TestClient

from recommender.__main__ import app
from recommender.recommenderFunctionality import additional_validation
from recommender.typedefs.io_types import Input

client = TestClient(app)


@app.post("/read/")
async def recommend(inp: Input):
    return asdict(additional_validation(inp))


def ordered(obj):
    if isinstance(obj, dict):
        return sorted((k, ordered(v)) for k, v in obj.items() if v is not None)
    if isinstance(obj, list):
        return sorted(ordered(x) for x in obj)
    else:
        return obj


@pytest.mark.parametrize("pm", ["CUTTING", "PRIMARY_FORMING", "PCB_ASSEMBLY"])
def test_ambiguous_assignment(pm):
    input_json = {
        "components": [
            {
                "name": "string",
                "type": pm,
                "suppliers": [
                    {
                        "id": "string",
                        "parameters": {
                            "tolerance": 0.0,
                            "width": {
                                "min": 0,
                                "max": 0
                            },
                        },
                        "preferences": {
                            "environmental_tech": [
                                True
                            ],
                            "balance": 0,
                        }

                    }
                ],
                "demand": {
                    "parameters": {
                        "tolerance": 0.0,
                        "width": 0,
                    },
                    "preferences": {
                        "environmental_tech": [
                            True
                        ],
                        "balance": 0,
                    }
                }
            }
        ]
    }
    response = client.post("/read/", headers={}, json=input_json)

    assert response.status_code == 200
    result = response.json()
    assert ordered(result) == ordered(input_json)


def test_unique_identifer():
    input_json = {
        "components": [
            {
                "name": "string",
                "type": "CUTTING",
                "suppliers": [
                    {
                        "id": "string",
                        "parameters": {
                            "guaranteed_service": 0,
                            "width": {
                                "min": 0,
                                "max": 0
                            },
                        },
                        "preferences": {
                            "environmental_tech": [
                                True
                            ],
                            "balance": 0,
                        }
                    }
                ],
                "demand": {
                    "parameters": {
                        "guaranteed_service": 0,
                        "width": 0,
                    },
                    "preferences": {
                        "environmental_tech": [
                            True
                        ],
                        "balance": 0,
                    }
                }
            }
        ]
    }
    response = client.post("/read/", headers={}, json=input_json)

    assert response.status_code == 200
    result = response.json()
    assert ordered(result) == ordered(input_json)


def test_ambiguous_assignment_superset():
    pm = "PRIMARY_FORMING"
    input_json = {
        "components": [
            {
                "name": "string",
                "type": pm,
                "suppliers": [
                    {
                        "id": "string",
                        "parameters": {
                            "tolerance": 0.0,
                            "width": {
                                "min": 0,
                                "max": 0
                            },
                            "component_function": ["d"],
                        },
                        "preferences": {
                            "environmental_tech": [
                                True
                            ],
                            "balance": 0,
                        }

                    }
                ],
                "demand": {
                    "parameters": {
                        "tolerance": 0.0,
                        "width": 0,
                        "component_function": "d",
                    },
                    "preferences": {
                        "environmental_tech": [
                            True
                        ],
                        "balance": 0,
                    }
                }
            }
        ]
    }
    response = client.post("/read/", headers={}, json=input_json)

    assert response.status_code == 200
    result = response.json()
    assert ordered(result) == ordered(input_json)


def test_ambiguous_assignment_superset_failure():
    pm = "CUTTING"
    input_json = {
        "components": [
            {
                "name": "string",
                "type": pm,
                "suppliers": [
                    {
                        "id": "string",
                        "parameters": {
                            "tolerance": 0.0,
                            "width": {
                                "min": 0,
                                "max": 0
                            },
                            "component_function": ["d"],
                        },
                        "preferences": {
                            "environmental_tech": [
                                True
                            ],
                            "balance": 0,
                        }

                    }
                ],
                "demand": {
                    "parameters": {
                        "tolerance": 0.0,
                        "width": 0,
                        "component_function": "d",
                    },
                    "preferences": {
                        "environmental_tech": [
                            True
                        ],
                        "balance": 0,
                    }
                }
            }
        ]
    }
    response = client.post("/read/", headers={}, json=input_json)

    assert response.status_code == 422
    assert "unexpected keyword argument 'component_function'" in response.text


