from django.conf import settings

class DbUtils:

    @staticmethod
    def check_if_we_are_in_production():
        """
        Checks if the application is in production.
        """
        print(settings.DATABASES['default']['NAME'])
        return 'prod' in settings.DATABASES['default']['NAME']
    
    @staticmethod
    def check_if_we_are_in_staging():
        """
        Checks if the application is in testing.
        """
        return 'dev' in settings.DATABASES['default']['NAME']
            