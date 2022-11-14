import re


def chunks(lst: list, n: int):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def remove_bookmarks(str):
    return re.sub("<bookmark\s*mark\s*=['\"]\w*[\"']\s*/>", "", str)
