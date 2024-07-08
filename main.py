import os

from fastapi import FastAPI, Depends, HTTPException
from fastapi.security.api_key import APIKeyHeader, APIKey
from starlette.status import HTTP_403_FORBIDDEN
from fastapi.middleware.cors import CORSMiddleware

from nodeodm_client import NodeodmClient

app = FastAPI()

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

IMAGE_DIR = os.getenv('IMAGE_DIR')
API_KEY = os.getenv('API_KEY')
print(f"API_KEY")
print(API_KEY)
print(f"IMAGE_DIR")
print(IMAGE_DIR)
API_KEY_NAME = "access_token"

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


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
})
async def calculate_orthophoto(transaction_id: str, api_key: APIKey = Depends(get_api_key)):
    """ Calculates an orthophoto for a given transaction ID

    :param api_key: The API key to authenticate the request
    :param transaction_id: The transaction ID to calculate the orthophoto for
    :return: The task ID of the created task or an HttpException 404 if an error occurred

    """
    nodeodm_client = NodeodmClient(IMAGE_DIR)
    task_id = await nodeodm_client.calculate_orthophoto(transaction_id)
    if task_id is None:
        raise HTTPException(status_code=404, detail="No images for transaction ID in S3 bucket")
    return {"uuid": task_id}
