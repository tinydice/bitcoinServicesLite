#!/usr/bin/env python3
from src.taskScheduler import *
import time

# Code to measure


def main():
    blockParser() 
    puzzleSiteScraper() 

if __name__ == "__main__":
    scheduler = TaskScheduler()
    while True:
        scheduler.RunTask(times=["06:00",  "9:00", "10:51", "12:00", "18:00"], func=blockStatusEmail)
        scheduler.RunTask(seconds=10, func=main)