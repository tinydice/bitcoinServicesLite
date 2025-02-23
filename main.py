#!/usr/bin/env python3
from src.taskScheduler import *

def main():
    blockParser() 
    puzzleSiteScraper() 

if __name__ == "__main__":
    scheduler = TaskScheduler()
    while True:
        scheduler.RunTask(times=["06:00",  "9:00", "12:00", "18:00"], func=blockStatusEmail)
        scheduler.RunTask(minutes=1, func=main)
