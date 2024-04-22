import os
import re


def find_files_regex(directory, regex_pattern):
    """
    Searches for files matching a regular expression pattern using os.walk() and re.

    Args:
        directory: The starting directory to search from.
        regex_pattern: The regular expression pattern to match against filenames.

    Returns:
        A list of full paths to matching files.
    """

    matching_files = []
    regex = re.compile(regex_pattern)  # Compile the regex pattern

    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            if regex.search(filename):
                matching_files.append(os.path.join(root, filename))

    return matching_files

