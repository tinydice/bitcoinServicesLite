from src.email import *
from src.bitcoin import *
from src.puzzleSiteScraper import *

directory = LOG_PATH
FILE_NAME = f"{LOG_PATH}/puzzle_spendable.txt"; 

# # Puzzle test + Email send test
# lines = open(FILE_NAME).readlines(); open(FILE_NAME, "w").writelines(lines[:-1])
# puzzleSiteScraper() 

# Bitcoin-cli ping test + Website ping test
blockStatusEmail() # Sends an email with the status of the node.

# # Block parser test
# blockParser() # Refreshes block recipients list. 

# # New address that we own, in a new block, detector test.
# for filename in os.listdir(directory):
#     if re.match(r'^\d+_addresses\.txt$', filename):
#         print(filename)
#         with open(os.path.join(directory, filename), "a") as f:
#             f.write("\n1GnNTmTVLZiqQfLbAdp9DVdicEnB5GoERE")
# checkAndSweep(blockDiff=True)

# #New address that we own, with UTXO that was there before. 
# with open(FILE_NAME, "a") as f:
#     f.write("bc1q72nyp6mzxjxm02j7t85pg0pq24684zdj2wuweu\tKwDiBf89QgGbjEhKnhXJuH8DvUBxVmJ3761ahfZuohBr53Zh9M3t\n")
# checkAndSweep(blockDiff=False)

# # Email WIF and command test. 
# debugEmail = [('raspi5bolt', 'L3nULRsoYyLUjaXdHr6Y1C6uFi6hSeiTjgzBaTNudmYE5JeKuuo3'), ('raspi5bolt', 'help'), ('raspi5bolt', 'status'), ('raspi5bolt', 'datalog')]
# debugEmail = [('raspi5bolt', 'L3nULRsoYyLUjaXdHr6Y1C6uFi6hSeiTjgzBaTNudmYE5JeKuuo3')]

# checkEmailAndSweep(debugEmail)

# checkEmailAndSweep()


# sweepAddress('1P5yTd2w1EgNY4zdTVxnT4G7ovXrWYYuRq',  'KxH3bvY8dhscgjsTy8fSsorP93F4UsyXoZY7aeK1W3AJjXEdZD4w')

# sweepAddress('bc1q72nyp6mzxjxm02j7t85pg0pq24684zdj2wuweu',  'KxH3bvY8dhscgjsTy8fSsorP93F4UsyXoZY7aeK1W3AJjXEdZD4w')






