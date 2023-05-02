import logging.config
from pathlib import Path
from typing import Literal, Union, Optional

import requests
from requests_auth import OAuth2ClientCredentials, OAuth2, JsonTokenFileCache

import settings

OAuth2.token_cache = JsonTokenFileCache('./cache.json')

logging.config.dictConfig(settings.LOGGER)
logger = logging.getLogger(__name__)

oauth = OAuth2ClientCredentials(
    client_id=settings.CLIENT_ID,
    client_secret=settings.CLIENT_SECRET,
    token_url=settings.TOKEN_URL,
    scope="easm"
)


def validate_path(path: Union[str, Path]):
    if isinstance(path, str):
        path = Path(path)
    return path.resolve()


def send_file(owner_email: str, project_id: str, file: Union[str, Path], field: str = 'file',
              category: Literal['easm', 'cut-list'] = 'easm', method: Literal['POST', 'PUT'] = 'POST', pk: str = None):
    logger.debug(f"received data: \n owner email: {owner_email}\n project_id: {project_id}\n category: {category}")
    url = settings.URL + f"/storages/{category}/"
    if method == "PUT" and pk is not None:
        url += f"{pk}/"
    file = validate_path(file)
    with open(file, "rb") as f:
        files = {field: (f"{file.name}", f)}
        payload = {
            "project": project_id,
            "owner_email": owner_email,
        }
        logger.debug("Payload created!")
        return requests.request(method, url, data=payload, files=files, auth=oauth)


def get_file_id(owner_email: str, project_id: str, file_name: Union[str, Path], category: Literal['easm'] = 'easm') \
        -> Optional[str]:
    logger.debug(f"received data: \n owner email: {owner_email}\n project_id: {project_id}\n category: {category}")
    url = settings.URL + f"/storages/{category}/"
    response = requests.request('GET', url, params=dict(project=project_id, owner__email=owner_email,
                                                        filename=file_name), auth=oauth)
    if response.status_code == 400:
        logger.error(f"received the response: {response.status_code}")
        logger.error(f"received the response: {response.json()}")
    elif response.status_code == 200:
        logger.debug(f"received the response: {response.status_code}")
        logger.debug(f"received the response: {response.json()}")
        if response.json().get('results'):
            return response.json().get('results')[0].get('id')
    logger.debug(f"received the response: {response.status_code}")
    logger.debug(f"received the response: {response.json()}")


def delete_file(pk: str, category: Literal['easm'] = 'easm') -> Optional[requests.Response]:
    url = settings.URL + f"/storages/{category}/"
    if pk is not None:
        url += f"{pk}/"
    response: requests.Response = requests.request('DELETE', url, auth=oauth)
    if response.status_code == 400:
        logger.error(f"received the response: {response.status_code}")
        logger.error(f"received the response: {response.json()}")
    elif response.status_code == 204:
        logger.debug(f"received the response: {response.status_code}")
        return response
