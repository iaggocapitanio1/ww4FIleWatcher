import logging.config
import time
from pathlib import Path
from typing import Union

from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer

import client
import settings

logging.config.dictConfig(settings.LOGGER)
logger = logging.getLogger(__name__)


def get_path_after_keyword(path: Union[str, Path], keyword: str = "clientes") -> Path:
    path = client.validate_path(path)
    return Path(*path.parts[path.parts.index(keyword):])


def get_email(path: Union[str, Path], keyword: str = "clientes") -> str:
    path = client.validate_path(path)
    return path.parts[path.parts.index(keyword) + 1]


def get_project_id(path: Union[str, Path], keyword: str = "clientes") -> str:
    path = client.validate_path(path)
    return path.parts[path.parts.index(keyword) + 2]


def get_pattern():
    if settings.CATEGORY == 'EASM':
        return ['*.easm']
    elif settings.CATEGORY == 'XLSX':
        return ['*.xlsx']
    else:
        ValueError("No valid pattern defined! \n options are: EASM or XLSX")


class FileHandler(PatternMatchingEventHandler):

    def __init__(self, *args, **kwargs):
        logger.info(f"Initializing {settings.CATEGORY} File Finder ....")
        super(FileHandler, self).__init__(patterns=get_pattern(), ignore_directories=True, case_sensitive=False)
        logger.info("Initialed")

    def on_created(self, event):
        logger.info(f"{settings.CATEGORY} file creation event triggerd!")
        logger.info("Trying to post file ....")
        response = client.send_file(get_email(event.src_path), get_project_id(event.src_path), file=event.src_path)
        if response.status_code == 400:
            logger.error(f"received the response: {response.status_code}")
            logger.error(f"received the response: {response.text}")
        else:
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response got: {response.text}")

    def on_modified(self, event):
        logger.info(f"Has been modified: {event.src_path}")
        logger.info("Trying to put file ....")
        email = get_email(event.src_path)
        project_id = get_project_id(event.src_path)
        filename = client.validate_path(event.src_path).name
        pk = client.get_file_id(owner_email=email, project_id=project_id, file_name=filename)
        if pk is not None:
            response = client.send_file(email, project_id, file=event.src_path, method='PUT', pk=pk)
            if response.status_code == 400:
                logger.error(f"received the response: {response.status_code}")
                logger.error(f"received the response: {response.text}")
            else:
                logger.info(f"Response status code: {response.status_code}")
                logger.info(f"Response got: {response.text}")

    def on_deleted(self, event):
        logger.info(f"Has been deleted: {event.src_path}")
        logger.info("Trying to delete file ....")
        email = get_email(event.src_path)
        project_id = get_project_id(event.src_path)
        filename = client.validate_path(event.src_path).name
        pk = client.get_file_id(owner_email=email, project_id=project_id, file_name=filename)
        if pk is not None:
            response = client.delete_file(pk=pk)
            if response.status_code == 400:
                logger.error(f"received the response: {response.status_code}")
                logger.error(f"received the response: {response.text}")
            else:
                logger.info(f"Response status code: {response.status_code}")
                logger.info(f"Response got: {response.text}")
        else:
            logger.error("Fail to delete file, no pk was found!")


if __name__ == "__main__":
    event_handler = FileHandler()
    observer = Observer()
    observer.schedule(event_handler, path=settings.WATCHING_DIR, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
