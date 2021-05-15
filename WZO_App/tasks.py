from celery import shared_task
from time import sleep

@shared_task
def wait():
    sleep(10)
    return "DONE"
