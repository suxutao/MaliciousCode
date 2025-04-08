import unittest
from loguru import logger


class MyTestCase(unittest.TestCase):
    def test_logger(self):
        logger.trace("Executing program")
        logger.debug("Processing data...")
        logger.info("Server started successfully.")
        logger.success("Data processing completed successfully.")
        logger.warning("Invalid configuration detected.")
        logger.error("Failed to connect to the database.")
        logger.critical("Unexpected system error occurred. Shutting down.")


if __name__ == '__main__':
    unittest.main()
