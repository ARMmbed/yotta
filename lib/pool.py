from multiprocessing.pool import ThreadPool

# this module just provides a shared thread pool for all multiprocessing users
# to use: the number of threads is high because tasks are expected to be
# IO-bound

pool = ThreadPool(4)

