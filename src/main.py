import json
import os

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader, APIKey
from starlette.status import HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR, HTTP_200_OK
from starlette.responses import JSONResponse

from .nodeodm_client import NodeodmClient

API_KEY = os.environ['API_KEY']
IMAGE_DIR = os.environ['IMAGE_DIR']
NODEODM_ENDPOINT = os.environ['NODEODM_ENDPOINT']
ALLOWED_ORIGINS = os.environ['ALLOWED_ORIGINS']

app = FastAPI()

origins = [
    ALLOWED_ORIGINS
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["get"],
    allow_headers=["*"],
)

with open('config.json', 'r') as file:
    config = json.load(file)

TASK_OPTIONS = config['TASK_OPTIONS']

api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)


async def get_api_key(
        api_key_header: str = Depends(api_key_header)
):
    if api_key_header == API_KEY:
        return api_key_header
    else:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Could not validate credentials"
        )


@app.get("/calculate_orthophoto/{transaction_id}", responses={
    200: {"description": "Task created successfully"},
    404: {"description": "No images for transaction ID in S3 bucket"},
    500: {"description": "Error creating task. Please check the logs."}
})
async def calculate_orthophoto(transaction_id: str, api_key: APIKey = Depends(get_api_key)):
    """ Calculates an orthophoto for a given transaction ID

    :param api_key: The API key to authenticate the request
    :param transaction_id: The transaction ID to calculate the orthophoto for
    :return: The task ID of the created task or an HttpException 404 if an error occurred

    """
    nodeodm_client = NodeodmClient(IMAGE_DIR, NODEODM_ENDPOINT)
    task_id, code = await nodeodm_client.calculate_orthophoto(transaction_id, TASK_OPTIONS)
    if code == 404:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="No images for transaction ID in S3 bucket")
    if code == 500:
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Error creating task. Please check the logs.")
    return JSONResponse(content={"uuid": task_id}, status_code=HTTP_200_OK)
