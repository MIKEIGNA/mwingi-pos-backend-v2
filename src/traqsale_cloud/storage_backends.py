from storages.backends.s3boto3 import S3Boto3Storage

# pylint: disable=abstract-method
class StaticStorage(S3Boto3Storage):
    location = 'traqsale/static'
    default_acl = 'public-read'

class PublicMediaStorage(S3Boto3Storage):
    location = 'traqsale/media'
    default_acl = 'public-read'
    file_overwrite = True

class PublicMediaTestStorage(S3Boto3Storage):
    location = 'traqsale/test/media'
    default_acl = 'public-read'
    file_overwrite = True