import cloudscraper
from bs4 import BeautifulSoup
from src.email import * 
import os
from src.helpers import *
from src.bitcoin import *

def puzzleSiteScraper():
    appendToDatalog(f"Running puzzleSiteScraper()")
    pattern = (
            r"(\d+)(?!:)\n"                                                 # Index
            r"([0-9a-fA-F]+:[0-9a-fA-F:]+)\n"                               # Range
            r"(?:([0-9a-fA-F]{60,70})\n)?"                                  # Key
            r"C\n"                                                          # C
            r"(bc1[qpzry9x8gf2tvdw0s3jn54khce6mua7l]{39,59}|[13][a-km-zA-HJ-NP-Z1-9]{25,33})\n"        # Address
            r"(UNSOLVED|SOLVED)"                                            # Puzzle State
        )

    url = "https://privatekeys.pw/puzzles/bitcoin-puzzle-tx"
    scraper = cloudscraper.create_scraper()
    response = scraper.get(url)
    siteText = BeautifulSoup(response.text, "html.parser").get_text("\n", True).split("\n")

    matches = extractPatterns(siteText, pattern, startMarker="Private Keys & Addresses", endMarker="Top Solvers")
    matches_string = ["\t".join(map(str, row)) for row in matches]

    writeToFile(f"{LOG_PATH}/puzzle.txt", matches_string, True)

    puzzle_dict = {}
    for match in matches:
        index = match[0]
        range = match[1]
        range_min = range.split(':')[0]
        range_max = range.split(':')[1]
        key = match[2]
        addess = match[3]
        state = match[4]

        puzzle_dict[index] = {}
        puzzle_dict[index]['range_min'] = range_min
        puzzle_dict[index]['range_max'] = range_max
        puzzle_dict[index]['key'] = key
        puzzle_dict[index]['addess'] = addess
        puzzle_dict[index]['state'] = state

    if os.path.exists(f"{LOG_PATH}/puzzle_spendable.txt"):
        os.rename(f"{LOG_PATH}/puzzle_spendable.txt", f"{LOG_PATH}/puzzle_spendable_prev.txt")
    else:
        print('hey')
        open(f"{LOG_PATH}/puzzle_spendable_prev.txt", "w").close()
        
    puzzle_spendable_dict = {}
    for index, value in puzzle_dict.items():
        state = puzzle_dict[index]['state']
        if state == 'SOLVED':
            puzzle = puzzle_dict[index]
            address = puzzle['addess']
            key = puzzle['key']
            wif_compressed = generateWifCompressed(key)

            puzzle_spendable_dict[address] = wif_compressed

        FILE_PATH = f"{LOG_PATH}/puzzle_spendable.txt"

        with open(FILE_PATH, "w") as f:
            for k, v in puzzle_spendable_dict.items():
                f.write(f"{k}\t{v}\n")

    new_solutions = getAddedLines(f"{LOG_PATH}/puzzle_spendable.txt", f"{LOG_PATH}/puzzle_spendable_prev.txt")

    if new_solutions:
        for solution in new_solutions:
            address, wif = solution.strip('\n').split("\t")
            sweepAddress(address, wif)
            appendToDatalog(f"New puzzle solution found: {address} - {wif}")
            send_email(f"New Puzzle Solution Found!", f"Address:\n{address}\n\nWIF:\n{wif}")

    incrementPuzzleScrapeCount()
    