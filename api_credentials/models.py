from django.db import models
from django.core.exceptions import ValidationError
from cryptography.fernet import Fernet
from django.conf import settings

class ServiceCredential(models.Model):
    name = models.CharField(max_length=100, unique=True)  # Unique name identifier
    tenant_id = models.CharField(max_length=100, unique=True)  # Ensures tenant_id is unique
    client_id = models.CharField(max_length=100, unique=True)  # Ensures client_id is unique
    _client_secret = models.BinaryField()  # Store encrypted client secret
    updated_at = models.DateTimeField(auto_now=True)  # Automatically updates timestamp on save

    def save(self, *args, **kwargs):
        if self.pk is None:
            if ServiceCredential.objects.exists():
                raise ValidationError("Only one service principal is allowed.")

        # Encrypt the client_secret before saving
        if self.client_secret:
            self._client_secret = self.encrypt_secret(self.client_secret)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Service Credentials for {self.name}"

    @property
    def client_secret(self):
        # Decrypt the client_secret when accessed
        if self._client_secret:
            return self.decrypt_secret(bytes(self._client_secret))
        return None

    @client_secret.setter
    def client_secret(self, value):
        # Encrypt the client_secret before saving
        if value:
            self._client_secret = self.encrypt_secret(value)

    @staticmethod
    def encrypt_secret(secret):
        cipher_suite = Fernet(settings.ENCRYPTION_KEY)
        encrypted_secret = cipher_suite.encrypt(secret.encode('utf-8'))
        return encrypted_secret

    @staticmethod
    def decrypt_secret(encrypted_secret):
        cipher_suite = Fernet(settings.ENCRYPTION_KEY)
        decrypted_secret = cipher_suite.decrypt(encrypted_secret).decode('utf-8')
        return decrypted_secret