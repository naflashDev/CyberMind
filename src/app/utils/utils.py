# @ Author: naflashDev
# @ Create Time: 2025-04-08 15:17:59
# @ Project: Cebolla
# @ Description: The main function of this script is to interact with files, including 
# modules for reading and writing files.


from io import TextIOWrapper

def read_file(filename: str, lines_to_escape: list[str] = [])->tuple:
    '''
    Reads the file located at the path formed by filename, escaping lines 
    that start with any content from lines_to_escape.
    
    It tries to open the file in read mode, then reads it line by line, 
    skipping lines that match the escape condition and storing the rest.

    Args:
        filename (str): Name of the file to read.
        lines_to_escape (list[str], optional): List of strings that, if a 
                                                line starts with any of them, 
                                                it will be skipped.

    Returns:
        tuple: 
            - Execution code (int):
                0 - Successful read.
                1 - File not found.
                2 - Insufficient permissions.
                3 - OS error.
                4 - Unknown error.
                5 - Incorrect parameters.
            - Informational message (str): A message about the result of the execution.
            - Content (list[str]): Relevant lines read from the file that weren't skipped.
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
    Writes the content of the 'content' parameter to the file located at 
    the specified filename.
    
    It tries to open the file in write mode, overwriting any existing content, 
    and then writes the content from the 'content' parameter.

    Args:
        filename (str): Name of the file to write to.
        content (list[str], optional): List of strings to write to the file.
        mode (str, optional): Mode for file opening ('w' for write, etc.).

    Returns:
        tuple:
            - Execution code (int):
                0 - Successful write.
                1 - File not found.
                2 - Insufficient permissions.
                3 - OS error.
                4 - Unknown error.
                5 - Incorrect parameters.
            - Informational message (str): A message about the result of the execution.
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
    Retrieves the database connection parameters from the configuration file.

    Args:
        file_name (str):
            Name of the configuration file containing the connection
            parameters to the database server.

    Returns:
        tuple:
            Two or three elements:
            + Execution code (int):
                0 - Parameters successfully retrieved.
                1 - Error while reading the file.
                2 - Incorrect number of potentially valid lines.
                3 - Incorrect number of connection parameters.
                4 - Incorrect type of connection parameters.
                5 - Invalid input parameters.
            + Informative message (str): String describing the result of the method execution.
            + Connection parameters (tuple, optional): A tuple containing the connection
              parameters. It has four elements: Database name, username, user password, and 
              the port where the database server is running. This is optional; if execution fails, 
              it will not be returned.
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
    Retrieves the database connection parameters from the configuration file.

    Args:
        file_name (str):
            Name of the configuration file containing the connection
            parameters to the database server.

    Returns:
        tuple:
            Two or three elements:
            + Execution code (int):
                0 - Parameters successfully retrieved.
                1 - Error while reading the file.
                2 - Incorrect number of potentially valid lines.
                3 - Incorrect number of connection parameters.
                4 - Incorrect type of connection parameters.
                5 - Invalid input parameters.
            + Informative message (str): String describing the result of the method execution.
            + Connection parameters (tuple, optional): A tuple containing the connection
              parameters. It has four elements: Database name, username, user password, and 
              the port where the database server is running. This is optional; if execution fails, 
              it will not be returned.
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
    Requests the recreation of the configuration file.

    Args:
        file_name (str):
            Name of the configuration file.

        content (list[str]):
            Content to be written into the configuration file.

    Returns:
        tuple:
            Two elements:
              + Execution code (int): 
                0 - Successfully recreated.
                1 - Error recreating the file.
                2 - Invalid input parameters.
              + Informative message (str): String describing the result 
                of the method execution.
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
