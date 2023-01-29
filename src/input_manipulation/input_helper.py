import os
import pathlib


#### #### #### ####
#### global
#### #### #### ####
## constant
SCRIPT_NAME = os.path.basename(__file__).split(".")[0]
SCRIPT_PATH = os.path.abspath(__file__)
SCRIPT_DIRECTORY = os.path.dirname(SCRIPT_PATH)
APP_DIRECTORY = pathlib.Path(SCRIPT_DIRECTORY).parent.absolute()
SCRIPT_RELATIVE_DIRECTORY = os.path.relpath(SCRIPT_DIRECTORY, APP_DIRECTORY)
## getch
## \[[Cod](https://gist.github.com/payne92/11090057)\] payne92/gist:11090057
try:
    import msvcrt

    getch = lambda: msvcrt.getch().decode("utf-8")
except ImportError:
    import sys, tty, termios

    def _unix_getch():
        """Get a single character from stdin, Unix version"""

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())  # Raw read
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

    getch = _unix_getch


#### #### #### ####
#### class
#### #### #### ####
class InputHelper:
    @classmethod
    def getch(cls) -> str:
        return getch()
