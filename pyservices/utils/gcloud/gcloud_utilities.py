import os

from .exceptions import GcloudEnvironmentException


def check_if_gcloud():
    # TODO: use env
    return "GOOGLE_CLOUD_PROJECT" in os.environ.keys()


def check_gcloud_production():
    if not check_if_gcloud():
        raise GcloudEnvironmentException()
    if os.getenv('GAE_ENV', '').startswith('standard'):
        return True  # Production in the standard environment
    else:
        return False  # dev_appserver execution


def get_project_id():
    try:
        project: str = os.environ.get("GOOGLE_CLOUD_PROJECT")
        return project.lower()
    except Exception:
        raise GcloudEnvironmentException()


def get_location_id():
    return "europe-west1"


def get_service_id():
    try:
        project: str = os.environ.get("GAE_SERVICE")
        return project.lower()
    except Exception:
        raise GcloudEnvironmentException()


def get_queue_id():
    service: str = get_service_id()
    return f'queue-{service}'


def setup_logging():
    from google.cloud import logging

    client = logging.Client()
    client.setup_logging()
