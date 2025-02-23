#!/usr/bin/env python3
from src.taskScheduler import *

if __name__ == "__main__":
    scheduler = TaskScheduler()
    while True:
        scheduler.RunTask(times=["00:00:00",  "9:00:00", "18:00:00"], func=blockStatusEmail)
        scheduler.RunTask(times=["00:01:00"], func=resetPuzzleScrapeCount)
        scheduler.RunTask(seconds=5, func=puzzleSiteScraper)