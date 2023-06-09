import concurrent.futures
import queue
import logging.config
import client
import settings
from pathlib import Path
from typing import Union, Literal, cast
import time

from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer

logging.config.dictConfig(settings.LOGGER)
logger = logging.getLogger(__name__)

file_event_queue = queue.Queue()


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
    elif settings.CATEGORY == 'ALPHA':
        return ['*.ard', '*.pgm']
    else:
        ValueError("No valid pattern defined! \n options are: EASM or XLSX")


def verify(source_path: Path, reference: str = 'Lists_and_Tags') -> bool:
    if source_path.is_dir():
        return False
    if reference not in source_path.parts:
        return False
    current_path = Path(*source_path.parts[source_path.parts.index(reference):])
    while current_path != current_path.parent:  # Stop when reaching the root directory
        if current_path.name == reference:
            return True
        current_path = current_path.parent

    return False


def isInsideDir(event, category: Literal['easm', 'cut-list'] = 'easm') -> bool:
    if category == 'easm':
        return verify(source_path=Path(event.src_path), reference='3D')
    elif category == 'cut-list':
        return verify(source_path=Path(event.src_path))
    return False


class FileHandler(PatternMatchingEventHandler):

    def __init__(self, *args, **kwargs):
        logger.info(f"Initializing {settings.CATEGORY} File Finder ....")

        super(FileHandler, self).__init__(patterns=get_pattern(), ignore_directories=True, case_sensitive=False)
        logger.info("Initialed")

    def on_created(self, event):
        file_event_queue.put(('created', event))

    def on_modified(self, event):
        file_event_queue.put(('modified', event))

    def on_deleted(self, event):
        file_event_queue.put(('deleted', event))


def process_event(event_type, event):
    category = 'easm'
    if settings.CATEGORY == "XLSX":
        category = 'cut-list'
        category = cast(Literal['easm', 'cut-list'], category)
    if not isInsideDir(event, category=category):
        logger.warning(f"File {Path(event.src_path).name.__str__()} is outside of reference Folder")
        return
    if event_type == 'created':
        logger.info(f"{settings.CATEGORY} fIle creation event triggerd!")
        logger.info("Trying to post file ....")
        response = client.send_file(get_email(event.src_path), get_project_id(event.src_path), file=event.src_path,
                                    category=category)
        if response.status_code == 400:
            logger.error(f"received the response: {response.status_code}")
            logger.error(f"received the response: {response.text}")
        else:
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response got: {response.text}")

    elif event_type == 'modified':
        logger.info(f"Has been modified: {event.src_path}")
        logger.info("Trying to put file ....")
        email = get_email(event.src_path)
        project_id = get_project_id(event.src_path)
        filename = client.validate_path(event.src_path).name
        pk = client.get_file_id(owner_email=email, project_id=project_id, file_name=filename)
        if pk is not None:
            response = client.send_file(email, project_id, file=event.src_path, method='PUT', pk=pk, category=category)
            if response.status_code == 400:
                logger.error(f"received the response: {response.status_code}")
                logger.error(f"received the response: {response.text}")
            else:
                logger.info(f"Response status code: {response.status_code}")
                logger.info(f"Response got: {response.text}")
    elif event_type == 'deleted':
        logger.info(f"Has been deleted: {event.src_path}")
        logger.info("Trying to delete file ....")
        email = get_email(event.src_path)
        project_id = get_project_id(event.src_path)
        filename = client.validate_path(event.src_path).name
        pk = client.get_file_id(owner_email=email, project_id=project_id, file_name=filename, category=category)
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


def worker():
    while True:
        event_tuple = file_event_queue.get()
        if event_tuple is None:
            break
        event_type, event = event_tuple
        process_event(event_type, event)


if __name__ == "__main__":
    # Create a ThreadPoolExecutor
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Start worker threads
        for _ in range(settings.NUM_WORKER_THREADS):
            executor.submit(worker)

        # Start the observer
        event_handler = FileHandler()
        observer = Observer()
        observer.schedule(event_handler, path=settings.WATCHING_DIR, recursive=True)
        logger.info(f"Watching DIR: {settings.WATCHING_DIR}")
        observer.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()

        # Stop worker threads
        for _ in range(settings.NUM_WORKER_THREADS):
            file_event_queue.put(None)
