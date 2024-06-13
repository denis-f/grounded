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


def rename_file(filepath, new_name):
    # Check if the filepath exists
    if not os.path.exists(filepath):
        print("Error: The specified file does not exist.")
        return

    # Extract the filename and extension
    filename, extension = os.path.splitext(filepath)
    directory = os.sep.join(filename.split(os.sep)[:-1])
    # Construct the new file name
    new_filepath = os.path.join(directory, f"{new_name}{extension}")
    counter = 1

    # If the new name already exists, add a counter
    while os.path.exists(new_filepath):
        new_filepath = os.path.join(directory, f"{new_name}({counter}){extension}")
        counter += 1

    # Rename the file
    os.rename(filepath, new_filepath)

    return new_filepath


def move_file_to_directory(source, destination_directory):
    if not os.path.exists(source):
        raise FileNotFoundError("The source file does not exist.")

    if not os.path.isdir(destination_directory):
        raise NotADirectoryError("The destination path is not a directory.")

    filename = os.path.basename(source)
    destination = os.path.join(destination_directory, filename)

    if os.path.exists(destination) and not os.path.samefile(source, destination):
        raise FileExistsError("A file with the same name already exists in the destination directory.")

    os.rename(source, destination)
    return destination


def config_builer(object, module_name: str) -> str:
    attributes = vars(object)
    config = f"{module_name}("
    for i, (cle, valeur) in enumerate(attributes.items()):
        config += f"{cle}={valeur}"
        if i < len(attributes) - 1:
            config += ", "
    config += ")"
    return config

def check_module_executable_path(path: str, module_name):
    if not path_exist(path):
        raise FileNotFoundError(f"Le fichier {path} n'a pas été trouvé. "
                                f"Impossible d'instancier le module {module_name}")

def path_exist(path: str) -> bool:
    return os.path.exists(path)
