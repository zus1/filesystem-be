from rest_framework import status
from rest_framework.exceptions import APIException


class BadRequestApiException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = 'bad_request'