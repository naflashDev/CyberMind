"""
@file utils.py
@author naflashDev
@brief File interaction utilities (read/write helpers).
@details Provides functions to read and write files, including line filtering and content manipulation for the CyberMind project.
"""

from io import TextIOWrapper

def read_file(filename: str, lines_to_escape: list[str] = []) -> tuple:
    '''
    @brief Read a file, skipping lines with specific prefixes.

    Reads the file located at the given path, skipping lines that start with any string in lines_to_escape. Returns a tuple with the filtered lines and the number of skipped lines.

    @param filename Name of the file to read (str).
    @param lines_to_escape List of string prefixes to skip (list[str]).
    @return Tuple (filtered_lines, skipped_count) (tuple).
    '''
# @ Author: naflashDev
# @ Create Time: 2025-04-08 15:17:59
# @ Project: Cebolla
# @ Description: The main function of this script is to interact with files, including 
# modules for reading and writing files.


from io import TextIOWrapper

def read_file(filename: str, lines_to_escape: list[str] = [])->tuple:
    '''
    @brief Reads the file located at the path formed by filename, escaping lines that start with any content from lines_to_escape.

    Tries to open the file in read mode, then reads it line by line, skipping lines that match the escape condition and storing the rest.

    @param filename Name of the file to read (str).
    @param lines_to_escape List of strings that, if a line starts with any of them, it will be skipped (list[str]).
    @return Tuple: (execution code, informational message, content) (tuple).
    '''
    # Local variables
    file: TextIOWrapper = None  # File descriptor for reading
    line: str  # Line read from the file
    content: list[str] = []  # Relevant content read from the file
    result: tuple  # Tuple that will contain the execution result
    index: int  # Loop index
    found: bool  # Boolean indicating if a line should be skipped

    # Validate parameters
    if (not isinstance(filename, str) or not isinstance(lines_to_escape, list) or 
        not all(isinstance(x, str) for x in lines_to_escape)):
        result = (5, 'Incorrect parameters.')

    else:
        try:
            # Open the file for reading
            file = open(filename, 'r')

            for line in file:
                index = 0
                found = False

                # Check if the line should be skipped
                while (not found and index < len(lines_to_escape)):
                    if (line.startswith(lines_to_escape[index])):
                        found = True
                    else:
                        index += 1

                if (not found):  # The line is relevant
                    content.append(line.replace('\n', ''))

            result = (0, f'File \'{filename}\' read successfully.', content)

        except FileNotFoundError:
            result = (1, 'File not found.')

        except PermissionError:
            result = (2, 'Insufficient permissions.')

        except OSError:
            result = (3, 'OS error.')

        except Exception as e:
            result = (4, f'Unknown error: {e.__class__.__name__}.')

        finally:  # Ensure the file is closed
            if (file is not None):
                try:
                    file.close()
                except Exception:
                    pass

    return result

# ######################################################################### #
def write_file(filename: str, content: list[str] = [], mode: str = 'w')->tuple:
    '''
    @brief Writes the content of the 'content' parameter to the file located at the specified filename.

    Tries to open the file in write mode, overwriting any existing content, and then writes the content from the 'content' parameter.

    @param filename Name of the file to write to (str).
    @param content List of strings to write to the file (list[str]).
    @param mode Mode for file opening ('w' for write, etc.) (str).
    @return Tuple: (execution code, informational message) (tuple).
    '''
    # Local variables
    file: TextIOWrapper = None  # File descriptor for writing
    result: tuple  # Tuple that will contain the execution result

    # Validate parameters
    if (not isinstance(filename, str) or not isinstance(content, list) or 
        not isinstance(mode, str) or not all(isinstance(x, str) for x in content)):
        result = (5, 'Incorrect parameters.')

    else:
        try:
            file = open(filename, mode)  # Open file in the specified mode

            for line in content:  # Write each line to the file
                file.write(line)

            result = (0, f'File \'{filename}\' written successfully.')

        except FileNotFoundError:
            result = (1, 'File not found.')

        except PermissionError:
            result = (2, 'Insufficient permissions.')

        except OSError:
            result = (3, 'OS error.')

        except Exception as e:
            result = (4, f'Unknown error: {e.__class__.__name__}.')

        finally:  # Ensure the file is closed
            if (file is not None):
                try:
                    file.close()
                except Exception:
                    pass

    return result

def get_connection_parameters(file_name: str)->tuple:
    '''
    @brief Retrieves the database connection parameters from the configuration file.

    Reads the configuration file and extracts the connection parameters for the database server.

    @param file_name Name of the configuration file (str).
    @return Tuple: (execution code, informative message, connection parameters) (tuple).
    '''
    # Local variables
    other_return: tuple       # Tuple containing the return values from other methods.
    line: list[str]           # Line read from the file, split by ';'.

    # Local code
    if isinstance(file_name, str):
        other_return = read_file( file_name, ['\n', '# '])

        if other_return[0] != 0:
            result = (1, f'Error while reading the file: {other_return[1]}')

        else:
            lines = other_return[2]

            if len(lines) != 1:
                result = (2, 'Incorrect number of potentially valid lines.')

            else:
                line = lines[0].split(';')

                if len(line) != 2:
                    result = (3, 'Incorrect number of parameters in the file.')

                else:
                    if not all(isinstance(x, str) for x in line) and not line[1].isdigit():
                        result = (4, 'Incorrect type of parameters.')

                    else:
                        result = (0, 'Connection parameters successfully retrieved.', (line[0], line[1]))
    
    else:
        result = (5, 'Invalid input parameters.')

    return result

def get_connection_service_parameters(file_name: str)->tuple:
    '''
    @brief Retrieves the database connection parameters from the configuration file.

    Reads the configuration file and extracts the connection parameters for the database server.

    @param file_name Name of the configuration file (str).
    @return Tuple: (execution code, informative message, connection parameters) (tuple).
    '''
    # Local variables
    other_return: tuple       # Tuple containing the return values from other methods.
    line: list[str]           # Line read from the file, split by ';'.

    # Local code
    if isinstance(file_name, str):
        other_return = read_file( file_name, ['\n', '# '])

        if other_return[0] != 0:
            result = (1, f'Error while reading the file: {other_return[1]}')

        else:
            lines = other_return[2]

            if len(lines) != 1:
                result = (2, 'Incorrect number of potentially valid lines.')

            else:
                line = lines[0].split(';')

                if len(line) != 2:
                    result = (3, 'Incorrect number of parameters in the file.')

                else:
                    if not all(isinstance(x, str) for x in line):
                        result = (4, 'Incorrect type of parameters.')

                    else:
                        result = (0, 'Connection parameters successfully retrieved.', (line[0], line[1]))
    
    else:
        result = (5, 'Invalid input parameters.')

    return result

def create_config_file( file_name: str, content: list[str])-> tuple:
    '''
    @brief Requests the recreation of the configuration file.

    Writes the provided content into the configuration file, recreating it if necessary.

    @param file_name Name of the configuration file (str).
    @param content Content to be written into the configuration file (list[str]).
    @return Tuple: (execution code, informative message) (tuple).
    '''
    # Local variables
    other_return: tuple  # Tuple containing the return values from other methods.
    result: tuple        # Tuple that will contain the method's return info.
                         # Two elements:
                         #   - Execution code (int): 
                         #     0 - Successfully recreated.
                         #     1 - Error recreating the file.
                         #     2 - Invalid input parameters.
                         #   - Informative message (str): Describes the result of execution.

    # Local code
    if (not isinstance(file_name, str) or not isinstance(content, list) or not all(isinstance(x, str) for x in content)
    ):
        result = (2, 'Invalid input parameters.')

    else:
        other_return = write_file(file_name, content)

        if other_return[0] != 0:
            result = (1, f'Error recreating the file: {other_return[1]}')

        else:
            result = (0, f'File \'{file_name}\' successfully recreated.')

    return result
