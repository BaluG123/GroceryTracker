from django.conf import settings
from django.db import models


class AccountSecurityProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='security_profile',
    )
    reset_question = models.CharField(max_length=255, blank=True, default='')
    reset_answer_hash = models.CharField(max_length=255, blank=True, default='')
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Security profile for {self.user.username}"
