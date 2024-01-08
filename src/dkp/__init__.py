import logging

if not logging.getLogger().handlers:
    # logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

    # Create a logger
    logger = logging.getLogger(__name__)

    logger.setLevel(logging.DEBUG)

    # Create a console handler and set the level to DEBUG
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    # Copilot: please add a file handler here
    file_handler = logging.FileHandler("dkp.log")
    file_handler.setLevel(logging.DEBUG)

    # Create a formatter and attach it to the console handler
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(module)s - %(message)s")
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # Add the console handler to the logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    logger.debug("Logging initialized")
