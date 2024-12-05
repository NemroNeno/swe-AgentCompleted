import json
import inspect, os
from typing import Any, Dict, Callable, List
import git
from langchain_community.tools import ShellTool, tool
from pydantic import BaseModel

shell = ShellTool()
abs_project_dir = os.getcwd()

class CurrentDirectory:
    def __init__(self):
        self.cwd = '/'

directory = CurrentDirectory()
    
def getSearchTools():
    return [ls, goto_directory, goto_previous_dir, get_current_dir, number_of_lines, open_file, find_files, search_file, search_dir]

def getContentViewingTools():
    return [get_files_content]

@tool
def ls() -> str:
    """
    This function lists the files in the current directory.
    :function: ls
    :return: a string containing the path of current directory and the files present in the current directory
    """
    ls_out = shell.run({"commands": [f"cd test-repos{directory.cwd}", 'ls']})
    return f"""
Current Directory: {directory.cwd}

Files: 
{ls_out}
"""

@tool
def goto_directory(path: str) -> str:
    """
    This function changes the current directory to the specified directory. This function must be used to goto a directory not to open a file.
    :function: goto_dir
    :param str path: path of the new directory you want to change relative to the current directory e.g 'matplotlib/doc'
    :return: output of command 'fail' or 'success'
    """

    if '..' in path:
        return 'use goto_previous_dir tool instead to go to previous directory'
    out = shell.run({"commands": [f"cd test-repos{directory.cwd}", f'cd {path}']})
    if out == "":
        directory.cwd = f"{directory.cwd}{path}/"
        return 'successfully entered ' + directory.cwd
    else:
        return out

@tool
def goto_previous_dir() -> str:
    """
    This function takes the user to the previous directory.
    :function: goto_previous_dir
    :return: output 
    """
    if directory.cwd == '/':
        return "Already in top most directory. Can't go back anymore"
    else:
        paths = directory.cwd.split('/')[1:-1]
        paths.pop()
        directory.cwd = '/'
        for dir in paths:
            directory.cwd += dir + '/'
        return f"Current Directory: {directory.cwd}"

@tool
def get_current_dir() -> str:
    """
    This function returns the path of the currently opened directory.
    :function: get_current_dir
    :return: the current directory
    """
    return directory.cwd

def get_abs_current_dir() -> str:
    return os.path.join(abs_project_dir, 'test-repos', directory.cwd[1:-1])

@tool
def number_of_lines(path: str) -> str:
    """
    This function takes a file path as input and returns the number of lines in the file.
    :function: number_of_lines
    :param path: The relative path to the file (e.g., 'lib/matplotlib/axis.py').
    
    :return: The number of lines in the file.
    """

    abs_file_path = os.path.join(get_abs_current_dir(), path)
    if os.path.exists(abs_file_path):
        with open(abs_file_path, 'r') as file:
            return f"Number of lines in {directory.cwd+path}: {sum(1 for line in file)}"
    else:
        return f"File {directory.cwd+path} not found"

@tool
def open_file(path: str, line_number: int = 1, max_lines: int = 100) -> str:
    """
    This function takes a file path, a line number, and a maximum number of lines as input and returns the contents of the file starting from the specified line number, limited to the maximum number of lines.
    :function: open_file
    :param path: The relative path to the file (e.g., 'lib/matplotlib/axis.py').
    :param line_number: The line number from which to start reading the file. Defaults to 1.
    :param max_lines: The maximum number of lines to return from the starting line. Defaults to 100.
    :return: A string containing the file contents from the specified starting line, limited to max_lines.
    """

    if line_number < 1:
        return "Error: line number cannot be zero or negative"
    if max_lines < 1:
        return "Error: max_lines cannot be zero or negative"

    abs_file_path = os.path.join(get_abs_current_dir(), path)
    if os.path.exists(abs_file_path):
        with open(abs_file_path, 'r') as file:
            with open(abs_file_path, 'r') as temp_file:
                num_lines = sum(1 for line in temp_file)
            if line_number > num_lines:
                return f"Can't access {line_number} line. This file only contains {num_lines} lines"
            
            out = f"Showing contents of File: {directory.cwd+path} starting from {line_number}\n\n"
            for n, line in enumerate(file, 1):
                if n >= line_number:
                    out += f"{n}: {line}\n"
                    if n == line_number + max_lines - 1:
                        break
            return out
    else:
        return path + " doesn't exist"

@tool
def find_files(file_name: str) -> str:
    """
    Searches the current directory and its subdirectories for the files that have name containing the specified file_name.
    :function: find_files
    :param file_name: The file_name to search for in file names.
    :return: paths of the files that contain the specified file_name in their names.
    """
    matched_files = []
    
    # Walk through the current directory and all subdirectories
    for root, dirs, files in os.walk("test-repos" + directory.cwd):
        for file in files:
            if file_name in file:
                matched_files.append(os.path.join(directory.cwd, file))
    
    return "Files found:\n" + "\n".join(matched_files)

@tool
def search_file(path: str, search_term: str) -> str:
    """
    This function takes a file path and a search term as input and returns the lines in the file that contain the search term. 
    :param str path: The relative path to the file (e.g., 'lib/matplotlib/axis.py').
    :param str search_term: The term to search for in the file.
    :return: A string containing the lines in the file that contain the search term.
    """

    abs_file_path = os.path.join(get_abs_current_dir(), path)
    if os.path.exists(abs_file_path):
        with open(abs_file_path, 'r') as file:
            out = f"Searching for '{search_term}' in {directory.cwd+path}\n\n"
            for n, line in enumerate(file, 1):
                if search_term in line:
                    out += f"{n}: {line}\n"
            return out
    else:
        return f"File {directory.cwd+path} not found"
    

@tool
def search_dir(path: str, search_term: str) -> str:
    """
    Searches for files in the specified directory that contain the search term. It returns the file names and line numbers where the search term is found.

    :param path: The relative path to the directory (e.g., 'lib/matplotlib').
    :param search_term: The term to search for in the files in the directory.
    :return: A string containing the files in the directory that contain the search term.
    """
    abs_dir_path = os.path.join(get_abs_current_dir(), path)
    
    if os.path.exists(abs_dir_path):
        matched = ""
        for root, dirs, files in os.walk(abs_dir_path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as file_a:
                        for n, line in enumerate(file_a, 1):
                            if search_term in line:
                                matched += f"File: {file_path}, Line: {n}\n"
                                break
                except (UnicodeDecodeError, IOError):  # Handle decoding errors and file I/O errors
                    continue
        
        if matched:
            return "Files found:\n" + matched
        else:
            return "No files containing the search term were found."
    else:
        return f"Directory {abs_dir_path} not found."

@tool
def get_files_content(paths: List[str], line_numbers: List[int]) -> str:
    """
    This function takes a list of file paths and a list of line numbers as input and returns the contents of the files starting from the specified line numbers.
    :param paths: A list of relative paths to the files (e.g., ['lib/matplotlib/axis.py', 'lib/matplotlib/figure.py']).
    :param line_numbers: A list of line numbers from which to start reading the files.
    :return: A string containing the contents of the files from the specified starting line numbers.
    """
    out = ""
    for path, line_number in zip(paths, line_numbers):
        out += open_file.invoke({'path': path, "directory.cwd": directory.cwd, 'line_number': line_number, 'max_lines': 50}) + '\n\n'
    return out


def setup_repo(data: dict):
    repo_name = data['repo'].split('/')[-1]
    directory.cwd = f"/{repo_name}/" 
    if not os.path.exists("test-repos"):
        print(shell.run({"commands": [
            "mkdir test-repos",
        ]}))
    if not os.path.exists(f"test-repos/{repo_name}"):
        # git.Git("test-repos").clone(f"https://github.com/{data['repo']}.git")
        print(shell.run({"commands": [
            f"cd test-repos",
            f"git config --global http.postBuffer 524288000",
            f"git clone https://github.com/{data['repo']}.git"
        ]}))
    print(shell.run({"commands": [
        f"cd test-repos/{repo_name}",
        # f"pip install -e .",
        f"git checkout -b {data['instance_id']} {data['base_commit']}",
    ]}))
    print('Repo setup complete')


if __name__ == '__main__':
    print(1)
