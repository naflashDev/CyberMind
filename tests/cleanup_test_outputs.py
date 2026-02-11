"""
@file cleanup_test_outputs.py
@author naflashDev
@brief Utilidad para eliminar carpetas outputs y data tras los tests.
@details Script auxiliar para limpieza de artefactos generados por tests en la raíz del proyecto.
"""

import shutil
from pathlib import Path


def remove_test_artifacts():
    '''
    @brief Remove outputs and data folders from project root.

    Deletes the 'outputs' and 'data' directories (and their contents) from the project root if they exist.

    @return None
    '''
    root = Path(__file__).parent.parent
    for folder in ["outputs", "data"]:
        target = root / folder
        if target.exists() and target.is_dir():
            shutil.rmtree(target)

if __name__ == "__main__":
    remove_test_artifacts()
