"""
Encryption Decorators for Django REST Framework Views

Provides decorators to automatically encrypt response data and decrypt request data
for API views. Maintains plaintext 'success' and 'message' fields for error handling.

Usage:
    from common.encryption_decorators import encrypt_response, decrypt_request
    
    class MyView(APIView):
        @decrypt_request
        @encrypt_response
        def post(self, request):
            # Access decrypted data
            data = request.decrypted_data
            
            # Return response with 'data' field
            return Response({
                "success": True,
                "message": "Success",
                "data": {"result": "value"}
            })
            # Decorator will encrypt 'data' field automatically
"""

from functools import wraps
from rest_framework.response import Response
from rest_framework import status
import logging

from .crypto_utils import encrypt_data, decrypt_data, is_encrypted_format

logger = logging.getLogger(__name__)


def decrypt_request(view_func):
    """
    Decorator to decrypt request.data['encrypted_data'] and attach to request.decrypted_data.
    
    If request contains 'encrypted_data' field, it will be decrypted and attached
    to request.decrypted_data for the view to use. If decryption fails, returns
    400 Bad Request with plaintext error message.
    
    Usage:
        @decrypt_request
        def post(self, request):
            data = request.decrypted_data  # Use decrypted data
            # ... process data
    """
    @wraps(view_func)
    def wrapper(self, request, *args, **kwargs):
        # Check if request has encrypted data
        if hasattr(request, 'data') and is_encrypted_format(request.data):
            try:
                encrypted = request.data.get('encrypted_data')
                
                if not encrypted or not isinstance(encrypted, str):
                    return Response(
                        {
                            "success": False,
                            "message": "Invalid encrypted_data field: must be non-empty string",
                            "data": None
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Decrypt and attach to request
                decrypted = decrypt_data(encrypted)
                request.decrypted_data = decrypted
                
                logger.debug(f"Successfully decrypted request data for {view_func.__name__}")
                
            except ValueError as e:
                logger.warning(f"Decryption failed in {view_func.__name__}: {e}")
                return Response(
                    {
                        "success": False,
                        "message": "Invalid encrypted payload: decryption failed",
                        "data": None
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            except Exception as e:
                logger.error(f"Unexpected decryption error in {view_func.__name__}: {e}")
                return Response(
                    {
                        "success": False,
                        "message": "Unable to process encrypted request",
                        "data": None
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            # No encrypted data, set empty dict
            request.decrypted_data = {}
        
        # Call the original view function
        return view_func(self, request, *args, **kwargs)
    
    return wrapper


def encrypt_response(view_func):
    """
    Decorator to encrypt response 'data' field into 'encrypted_data'.
    
    If response is successful and contains a 'data' field, it will be encrypted
    and replaced with 'encrypted_data'. The 'success' and 'message' fields
    remain plaintext for error handling.
    
    Usage:
        @encrypt_response
        def get(self, request):
            return Response({
                "success": True,
                "message": "Data retrieved",
                "data": {"sensitive": "information"}
            })
            # Response will have 'encrypted_data' instead of 'data'
    """
    @wraps(view_func)
    def wrapper(self, request, *args, **kwargs):
        # Call the original view function
        response = view_func(self, request, *args, **kwargs)
        
        # Only encrypt if it's a Response object with successful status
        if not isinstance(response, Response):
            return response
        
        # Check if response has data to encrypt
        if not hasattr(response, 'data') or not isinstance(response.data, dict):
            return response
        
        # Only encrypt successful responses with 'data' field
        if response.data.get('success') and 'data' in response.data:
            try:
                data_to_encrypt = response.data['data']
                
                # Skip encryption if data is None
                if data_to_encrypt is None:
                    return response
                
                # Encrypt the data field
                encrypted = encrypt_data(data_to_encrypt)
                
                # Replace 'data' with 'encrypted_data'
                response.data['encrypted_data'] = encrypted
                del response.data['data']
                
                logger.debug(f"Successfully encrypted response data for {view_func.__name__}")
                
            except Exception as e:
                # Log error but don't fail the request
                # Keep original response if encryption fails
                logger.error(f"Response encryption failed in {view_func.__name__}: {e}")
                # Optionally, you could return an error response here
                # For now, we'll keep the original response
        
        return response
    
    return wrapper


def encrypt_request_and_response(view_func):
    """
    Combined decorator for both request decryption and response encryption.
    
    Equivalent to applying both @decrypt_request and @encrypt_response.
    
    Usage:
        @encrypt_request_and_response
        def post(self, request):
            data = request.decrypted_data
            return Response({
                "success": True,
                "message": "Success",
                "data": {"result": "value"}
            })
    """
    return decrypt_request(encrypt_response(view_func))
