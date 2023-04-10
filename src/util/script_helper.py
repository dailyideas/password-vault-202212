import logging
import logging.config
import pathlib


#### #### #### ####
#### class
#### #### #### ####
class ScriptHelper:
    @classmethod
    def get_script_logger(
        cls, script_relative_directory: str, script_name: str
    ):
        """Get logger for the script.

        Args:
            script_relative_directory (str): Directory of the script relative
                to the service's top directory.
            script_name (str): Name of the script.

        Returns:
            logging.Logger: Logger for the script.
        """
        ## Logging
        logger_name = str(
            pathlib.PurePosixPath(
                "project",
                "app",
                pathlib.Path(script_relative_directory),
                script_name,
            )
        ).replace("/", ".")
        logger = logging.getLogger(logger_name)
        return logger
