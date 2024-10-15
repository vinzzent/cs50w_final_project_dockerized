import requests
from .models import ServiceCredential
from django.conf import settings
from django.http import Http404
from django.shortcuts import get_object_or_404

def get_access_token(service_credential_pk=None):

    credentials = {}

    # Attributes to check in settings
    attributes = [
        'SERVICE_CREDENTIALS_TENANT_ID',
        'SERVICE_CREDENTIALS_CLIENT_ID',
        'SERVICE_CREDENTIALS_CLIENT_SECRET'
    ]

    # Check if all settings attributes are defined, are strings, and are non-zero-length
    if all(
        isinstance(getattr(settings, attr, None), str) and len(getattr(settings, attr)) > 0 
        for attr in attributes
    ):
        
        # Populate the credentials dictionary from settings
        credentials = {
            'tenant_id': settings.SERVICE_CREDENTIALS_TENANT_ID,
            'client_id': settings.SERVICE_CREDENTIALS_CLIENT_ID,
            'client_secret': settings.SERVICE_CREDENTIALS_CLIENT_SECRET
        }
    else:
        # Retrieve ServiceCredential from the database
        if service_credential_pk is None:
            service_credential = ServiceCredential.objects.first()
            if service_credential is None:
                raise Http404("First ServiceCredential not found.")
        else:
            service_credential = get_object_or_404(ServiceCredential, pk=service_credential_pk)

        # Populate the credentials dictionary from the ServiceCredential instance
        credentials = {
            'tenant_id': service_credential.tenant_id,
            'client_id': service_credential.client_id,
            'client_secret': service_credential.client_secret
        }

    tenant_id = credentials['tenant_id']
    client_id = credentials['client_id']
    client_secret = credentials['client_secret']

    # Azure AD Token endpoint URL
    token_url = f'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token'

    # Headers for the request
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    # Data to be sent in the POST request
    data = {
        'grant_type': 'client_credentials',  # OAuth 2.0 client credentials grant type
        'client_id': client_id,
        'client_secret': client_secret,
        'scope': 'https://analysis.windows.net/powerbi/api/.default'  # Scope for Power BI API
    }

    try:
        # Make the POST request to obtain the access token
        response = requests.post(token_url, headers=headers, data=data)
        response.raise_for_status()  # Raise HTTPError for non-2xx responses

        # Parse JSON response to extract the access token
        token_response = response.json()
        access_token = token_response.get('access_token')
        return access_token

    except requests.exceptions.RequestException as e:
        # Handle any exceptions from the requests library (e.g., network issues)
        raise Exception(f'Request failed: {str(e)}')

    except Exception as e:
        # Handle other unexpected exceptions (e.g., JSON parsing errors)
        raise Exception(f'Error: {str(e)}')