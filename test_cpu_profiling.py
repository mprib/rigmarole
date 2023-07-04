"""
I want to see what happens if I spawn a bunch of threads using pure python. I think I should 
be able to push everything onto one core, but I could be wrong.

"""

# from threading import Thread
# from random import random


# def add_random():
#     x = 0
#     while True:
#         x+=random()-.5
        
# threads = []
         
# while True:
#     thread = Thread(target=add_random, args=[], daemon=True)
#     thread.start()
#     threads.append(thread)
#     print(f"Creating thread {len(threads)}")
    
    
import os
import time
from random import random

def factorial(n):
    print(f"Processing factorial({n}) on PID: {os.getpid()}")
    fact = 1
    for i in range(1, n+1):
        fact *= i
    return fact

if __name__ == "__main__":
    number = 50000  # Large number to cause CPU spike

    print(f"Starting factorial computation on PID: {os.getpid()}")
    start = time.time()

    while True:
        factorial(int(number*random()))

    # end = time.time()
    # print(f"Time taken: {end - start} seconds")