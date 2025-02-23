from datetime import datetime
from src.puzzleSiteScraper import *
from src.email import *
from src.helpers import *
from src.bitcoin import *

class TaskScheduler:
    def __init__(self):
        self.last_run_times = {}  

    def RunTask(self, minutes=None, hours=None, days=None, seconds=None, times=None, func=None):
        now = datetime.now()
        task_name = func.__name__ 

        last_run = self.last_run_times.get(task_name)

        if last_run and last_run.second == now.second:
            return
        
        self.last_run_times[task_name] = now  

        if (
            (seconds and now.second % seconds == 0) or
            (minutes and now.minute % minutes == 0 and now.second == 0) or
            (hours and now.hour % hours == 0 and now.minute == 0 and now.second == 0) or
            (days and now.day % days == 0 and now.hour == 0 and now.minute == 0 and now.second == 0) or
            (times and now.strftime("%H:%M") in times)
        ):
            func()
