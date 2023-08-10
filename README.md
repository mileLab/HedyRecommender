# hedy_recommender

This repository contains the code two docker containers:

* *Extractor*: Used to extract parameters from certain files, like STEP, STL or EAGLE
* *Recommender*: Takes as input parameters from the demand and parameters for each supplier in order to find the best
  fitting supplier for the given demand

## Building

The docker containers can be build by

```
cd source
docker build -t <Tag> -f ./extractor/Dockerfile .
docker build -t <Tag> -f ./recommender/Dockerfile .
```

In order to build the docker containers on Windows, "Docker Desktop" must be installed.

## Useage

### Recommender

The extractor provides a REST API on port 8080 with endpoint *extract*, i.e.,

```
http://127.0.0.1:8080/extract
```

The data for extracting has to be sent as a POST request as JSON in the body. The basic structure for submitting files
is:

```json
{
  "components": [
    {
      "name": "board",
      "method": "PCB_ASSEMBLY",
      "files": [
        {
          "type": "brd",
          "encoding": "utf-8",
          "content": " .... ",
          "...": "..."
        }
      ]
    },
    {
      "...": "..."
    }
  ]
}             
```

where *content* is a base64 encoded string of the file content.

The parameters for each component are returned in a similar manner:

```json
{
  "components": [
    {
      "name": "board",
      "parameters": {
        "length": 47.73,
        "width": 17.66,
        "height": 1.376,
        "...": "..."
      },
      "failures": {
        "parsing": [
          "..."
        ],
        "extracting": {
          "...": "..."
        }
      },
      "additional_info": {
        "info_parameter": {
          "...": "..."
        },
        "warnings": [
          "..."
        ],
        "info_packaging": {
          "failures": {
            "...": "..."
          },
          "success": {
            "...": "..."
          }
        }
      }
    },
    {
      "...": "..."
    }
  ]
}

```

### Recommender

The extractor provides a REST API on port 8050 with endpoint *recommend*, i.e.,

```
http://127.0.0.1:8050/recommend
```

The data for the recommender has to be sent as a POST request as JSON in the body. The basic structure for submitting
the parameters is:

```json
{
  "components": [
    {
      "name": "board",
      "type": "<production_method>",
      "suppliers": [
        {
          "id": "my_supplier1",
          "parameters": {
            "length": {
              "min": 2.0,
              "max": 12.0
            },
            "width": {
              "min": 2.0,
              "max": 10.0
            },
            "height": {
              "min": 0.1,
              "max": 5.0
            },
            "...": "..."
          },
          "preferences": {
            "...": "..."
          }
        },
        {
          "id": "my_supplier2",
          "...": "..."
        }
      ],
      "demand": {
        "parameters": {
          "length": 10.0,
          "width": 5.0,
          "height": 1.0
        },
        "preferences": {
          "...": "..."
        }
      }
    },
    {
      "...": "..."
    }
  ]
}     
```

The result of the recommender is a scoring for each supplier together with additional information about the scoring
process.

```json
{
  "components": [
    {
      "name": "board",
      "scores": [
        {
          "supplier_id": "my_supplier2",
          "score": 0.9,
          "scores_per_category": {
            "<CATEGORY>": 0.9
            },
          "failures": {
            "preferences": {
              "<CATEGORY>": {
                "failures": {
                  "...": "..."
                },
                "skipped": {
                  "...": "..."
                }
              },
              "...": {}
            },
            "parameters": {
              "<CATEGORY>": {
                "failures": {
                  "...":"..."
                },
                "skipped": {
                  "...": "..."
                }
              },
              "...": {}
            }
          }
        },
        {
          "supplier_id": "my_supplier1",
          "score": -1.0,
          "scores_per_category": {
            "<CATEGORY>": 0.7
          },
          "failures": {
            "preferences": {
              "...": "..."
            },
            "parameters": {
              "<CATEGORY>": {
                "failures": {
                  "height": "Demand value 3.0 is larger than upper bound of supplier range [0.1,2.0]"
                },
                "skipped": {
                  "...": "..."
                }
              },
              "...": {}
            }
          }
        }
      ]
    }
  ]
}
```

## Technical Information

The base image for the docker containers is a miniconda image (https://hub.docker.com/r/continuumio/miniconda3), which
is based on a debian bullseye image. The program is written in Python-3.9, but uses the following C++ libraries:

* KiCad
* OpenCascade

The webserver is provided via the package fastapi (https://fastapi.tiangolo.com/)


### Setup Development Environment

Create a conda environment using
```
conda env create -f dev-environment.yml
```

If an update of the environment is necessary call
```
conda env update -f dev-environment.yml
```
The dev-environment.yml is a superset of the packages of the recommender and extractor and is purely used for development. 

When updating the environment, all subpackages of packages get updated as well. However, no target version number is specified, which means that an update could introduce a breaking change
For the **Extractor** together with the environment.yml file a environment_lock.yml file is stored, which is manually generated by calling
```
conda env export -n <environment-name> > environment_lock.yml
```
and contains all version numbers of all packages in the environment. It is advised to call this command in the docker container to obtain the actual available environment.

For the **Recommender** together with the requirements.txt a requirements_lock.txt is stored, which is manually generated by calling
```
pip freeze --all > requirements_lock.txt
```
and contains all version numbers of all packages.  It is advised to call this command in the docker container to obtain the actual available environment.


If PyCharm is used, the created conda environment can/should be added in PyCharm for convenient development, the option can be found under:

File => Settings => Project "ProjetName" => Python Interpreter => Add => Conda Environment => Existing Environment => Select the newly created interpreter