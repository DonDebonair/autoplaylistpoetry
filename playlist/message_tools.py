"""
Tools for generating different word-combinations from a message
"""

__author__ = 'Daan Debie'


def get_nested_list_len(lst):
    """
    Returns the combined length of all lists within a list. Non-recursive, so only goes one level deep
    """
    ls_len = 0
    if lst:
        for item in lst:
            ls_len += len(item)
    return ls_len


def generate_smaller_sublists(word_list, max_chunk_length=None):
    """
    This function takes (a part of) a list and returns a new list containing all small sublists of
    the original (partial) list in shrinking order Ie.: [a, sample, list] will return:
    [['a', 'sample', 'list'], ['a', 'sample'], ['a']]

    """

    if not max_chunk_length or max_chunk_length > len(word_list):
        max_chunk_length = len(word_list)
    return [word_list[0:x] for x in range(max_chunk_length, 0, -1)]


class MessageChunker(object):
    """
    This class creates an iterable object giving back all the different combinations a message can be broken down
    in groups of words. It only processes one part of the message at a time, and expects "outside help" to determine
    when to progress() to the next part. This way we can test if a certain group/chunk is "valid" (in our specific case
    this depends on what the Spotify API returns) and search for the next group based on that.
    It tries to find groups as large as possible, keeping in mind the max_chunk_length

    """
    def __init__(self, message, max_chunk_length=None):
        self.prefix = []
        self.word_list = message.split()
        if max_chunk_length:
            self.max_chunk_length = max_chunk_length
        else:
            self.max_chunk_length = len(self.word_list)
        self.chunks = generate_smaller_sublists(self.word_list, self.max_chunk_length)
        self.counter = 0

    def __iter__(self):
        return self

    def next(self):
        """ returns the next group of words """

        if get_nested_list_len(self.prefix) >= len(self.word_list):
            raise StopIteration

        self.counter += 1
        try:
            # The prefix consists of all the "accepted" groups
            current_chunk = self.chunks[self.counter - 1]
            index = get_nested_list_len(self.prefix) + len(current_chunk)
            return self.prefix + [current_chunk] + [self.word_list[index:]]
        except IndexError:
            if self.prefix:
                if len(self.prefix) == 1 and len(self.prefix[0]) == 1:
                    raise StopIteration
                self._backtrack()
                return None
            else:
                raise StopIteration

    def progress(self):
        """
        Accepts the current group and starts processing the rest of the message
        """
        
        # Group accepted. That group is now part of our prefix
        self.prefix.append(self.chunks[self.counter - 1])
        # New index is chosen such that we can process anything not yet in our prefix
        index = get_nested_list_len(self.prefix)
        # Any group after the first group can potentially consist of all the remaining words
        self.max_chunk_length = len(self.word_list) - index
        self.chunks = generate_smaller_sublists(self.word_list[index:], self.max_chunk_length)
        self.counter = 0

    def _backtrack(self):
        """
        The remaining groups are not valid, so this method discards the last accepted group
        and shrinks that group by one and continues processing from there
        """

        # Let's try one smaller and see if we can generate valid groups from there
        prefix_length = get_nested_list_len(self.prefix)
        last_prefix_group_length = len(self.prefix.pop())
        index = prefix_length - last_prefix_group_length
        self.max_chunk_length = last_prefix_group_length - 1
        self.chunks = generate_smaller_sublists(self.word_list[index:], self.max_chunk_length)
        self.counter = 0