import logging
import time

log = logging.getLogger("FingerprintsREST.TimerUtility")
timers = {}

def log_task_start(task_name):
    """
    :param task_name:
    :type task_name: str
    """
    log.info("Begun task: '" + task_name + "'")
    timers[task_name] = time.time()


def log_task_end(task_name):
    task_duration = time.time() - timers[task_name]
    log.info("Ended task: '" + task_name + "'. Duration: " + str(task_duration))
