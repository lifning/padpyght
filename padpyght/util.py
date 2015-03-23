import collections


def recursive_default_dict():
    return collections.defaultdict(recursive_default_dict)
