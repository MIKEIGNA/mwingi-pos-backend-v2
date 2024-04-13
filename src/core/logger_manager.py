import logging

from django.conf import settings

# pylint: disable=logging-fstring-interpolation

class LoggerManager:


    @staticmethod
    def log_tasks(additional_message=''):
        """
        This is usually placed under an exception's except. Then when an error 
        occurs, it's logged in the page_critical_logger or test_page_critical_logger
        when the app is in test mode

        Args:
            additional_message: An optional additinal message that can be
            appended to the log's first line (titleis) 
        """
        logger_name=''

        if not settings.TESTING_MODE:
            logger_name='software_task_critical_logger'
        else:
            logger_name='test_software_task_critical_logger'

        """
        Makes it easy to log errors
        """

        # print(traceback.format_exc())
        # Get an instance of a logger
        logger = logging.getLogger(logger_name)
        logger.exception(additional_message)

    @staticmethod
    def log_critical_error(additional_message=''):
        """
        This is usually placed under an exception's except. Then when an error 
        occurs, it's logged in the page_critical_logger or test_page_critical_logger
        when the app is in test mode

        Args:
            additional_message: An optional additinal message that can be
            appended to the log's first line (titleis) 
        """

        logger_name=''

        if not settings.TESTING_MODE:
            logger_name='page_critical_logger'
        else:
            logger_name='test_page_critical_logger'

        """
        Makes it easy to log errors
        """

        # print(traceback.format_exc())
        # Get an instance of a logger
        logger = logging.getLogger(logger_name)
        logger.exception(additional_message)
        

    @staticmethod
    def log_page_critical_error_depreciated(origin='', message=''):

        logger_name=''

        if not settings.TESTING_MODE:
            logger_name='page_critical_logger'
        else:
            logger_name='test_page_critical_logger'

        """
        Makes it easy to log errors
        """
        # # Get an instance of a logger
        logger = logging.getLogger(logger_name)

        if origin and message:
            logger.exception(f'{origin} => {message}')
        else:
            logger.exception('')