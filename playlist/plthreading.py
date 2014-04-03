__author__ = 'Daan Debie'

from threading import Thread
from Queue import Queue
from generator import PlaylistGenerator


class PLGeneratorThread(Thread):
    """
    Class that provides threaded playlist generation. It takes one sentence off a queue and
    processes them. Results are stored in the Thread object itself.
    One of these Threads should be created for each message to be processed. Because of the average
    long running time of querying the API, race conditions or deadlocks should be rare to non-existant. Should one of
    the threads fail in some way, however, not all messages will be processed.
    """

    def __init__(self, queue, generator):
        Thread.__init__(self)
        self.queue = queue
        self.generator = generator
        self.payload = None
        self.incomplete = True # If the Thread fails somehow, it should be considered incomplete
        self.playlist = None
        self.position = None

    def run(self):
        self.payload = self.queue.get()
        self.position = self.payload[1]
        print "running thread {}".format(str(self.position))
        # We're processing multiple sentences, almost guaranteeing multiple playlist entries,
        # se we can use max_chunk_length
        self.playlist, self.incomplete = self.generator.generate_playlist(self.payload[0], True)
        self.queue.task_done()


def generate_multiple_playlists_threaded(list_of_messages, cache):
    queue = Queue()
    generator = PlaylistGenerator(cache)
    # spawn a pool of threads, and pass them queue instance
    threads = [PLGeneratorThread(queue, generator) for message in list_of_messages]
    for thread in threads:
        thread.setDaemon(True)
        thread.start()

    # populate queue with data, also providing a position so we can sort them back later
    for x in range(len(list_of_messages)):
        queue.put((list_of_messages[x], x))

    # wait on the queue until everything has been processed
    # NOTE: if a thread fails somehow (as in: doesn't execute at all), deadlock could occur, because part of the queue
    # won't be processed.
    queue.join()

    return [(thread.playlist, thread.incomplete) for thread in sorted(threads, key=lambda thread: thread.position)]


def generate_multiple_playlists_naive(list_of_messages, cache):
    generator = PlaylistGenerator(cache)
    results = [generator.generate_playlist(message) for message in list_of_messages]
    return results

