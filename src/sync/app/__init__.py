from celery import Celery
from celery.schedules import crontab

app = Celery()

import os

app.conf.broker_url = os.environ.get("SYNC_BROKER", 'redis://locallhost:6379/0')

INTERVAL = os.environ.get("SYNC_INTERVAL", 10)
PROGRAM = os.environ.get("SYNC_PROGRAM", "?")

@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(float(INTERVAL), sync.s(), name='Runs {} every {} seconds'.format(PROGRAM, INTERVAL))

from subprocess import call

@app.task
def sync():
    call(PROGRAM)
