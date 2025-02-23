import subprocess
import glob 
import os 
import base58
import ecdsa
import re
import hashlib
import requests
import struct
import bech32
import asyncio
import aiohttp
from datetime import datetime
from binascii import *
from bitcoinUtils.src.FORMATutils import *
import smtplib
import sys

CWD = os.getcwd()
LOG_PATH = f"{CWD}/Logs"
datalog_name = f"{LOG_PATH}/datalog.txt"
MAX_LOGS = 1000

def incrementFileCounter(filePath):
    try:
        with open(filePath, "r", encoding="utf-8") as f:
            count = int(f.readline().strip())
    except (FileNotFoundError, ValueError):
        count = 0

    count += 1

    with open(filePath, "w", encoding="utf-8") as f:
        f.write(f"{count}\n")

def resetFileCounter(filePath):
    with open(filePath, "w") as f:
        f.write("0\n")

def readFileCount(filePath):
    with open(filePath, "r", encoding="utf-8") as f:
        count = int(f.readline().strip())
    return count

def incrementPuzzleScrapeCount():
    print("increment")
    incrementFileCounter(f"{LOG_PATH}/puzzleScrapeCount.txt")

def resetPuzzleScrapeCount():
    resetFileCounter(f"{LOG_PATH}/puzzleScrapeCount.txt")

def readPuzzleScrapeCount():
    count = readFileCount(f"{LOG_PATH}/puzzleScrapeCount.txt")
    return count

def removeFilesWithEnding(path, string):
    for file in glob.glob(f"{path}/*{string}"):
        os.remove(file)

def writeToFile(file_path, data, isList=False):
    with open(file_path, "w") as file:
        if (isList):
            file.write("\n".join(data))
        else:
            file.write(data)

def extractPatterns(data, pattern, startMarker=None, endMarker=None):
    dataStr = "\n".join(data)

    if startMarker:
        startMatch = re.search(re.escape(startMarker), dataStr)
        if startMatch:
            dataStr = dataStr[startMatch.end():]

    if endMarker:
        endMatch = re.search(re.escape(endMarker), dataStr)
        if endMatch:
            dataStr = dataStr[:endMatch.start()]

    compiledPattern = re.compile(pattern)
    matches = [list(match) for match in compiledPattern.findall(dataStr)]

    return matches

def getAddedLines(file, filePrev):
    with open(filePrev, 'r') as f1, open(file, 'r') as f2:
        lines1 = set(f1.readlines())
        lines2 = set(f2.readlines())
    addedLines = list(lines2 - lines1)
    return addedLines if addedLines else None

def appendToFile(filePath, text, norepeat=True):
    try:
        with open(filePath, "r+", encoding="utf-8") as f:
            lines = set(line.strip() for line in f) if norepeat else set()
            new_lines = [t for t in text.splitlines() if not norepeat or t not in lines]
            if new_lines:
                f.write("\n".join(new_lines) + "\n")
                return True
    except FileNotFoundError:
        with open(filePath, "w", encoding="utf-8") as f:
            f.write(text + "\n")
        return True
    return False

def _readLog():
    if os.path.exists(datalog_name):
        with open(datalog_name, "r") as file:
            return file.readlines()
    return []

def clearDatalogIfNeeded():
    logs = _readLog()
    if len(logs) >= MAX_LOGS:
        with open(datalog_name, "w") as file:
            file.truncate(0) 

def appendToDatalog(*entries):
    clearDatalogIfNeeded() 
    if not os.path.exists(datalog_name):
        open(datalog_name, "w").close()
    
    with open(datalog_name, "r+") as file:
        existing_content = file.read() 
        file.seek(0, 0) 
        for entry in entries:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.") + f"{int(datetime.now().microsecond / 10000):02d}"
            log_entry = f"({timestamp}): {entry}\n"
            file.write(log_entry + existing_content)

def readDatalog():
    with open(datalog_name, "r") as file:
        datalog = file.readlines()
    return datalog

commands = ['log', 'status','help']

def findCommandsInString(inputString):
    return [cmd for cmd in commands if cmd in inputString]