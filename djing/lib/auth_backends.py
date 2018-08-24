from ipaddress import ip_address, AddressValueError

from django.contrib.auth.backends import ModelBackend
from accounts_app.models import BaseAccount, UserProfile
from abonapp.models import Abon
from ip_pool.models import IpLeaseModel


class CustomAuthBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(BaseAccount.USERNAME_FIELD)
        try:
            user = BaseAccount._default_manager.get_by_natural_key(username)
            if user.check_password(password):
                if user.is_staff:
                    auser = UserProfile.objects.get_by_natural_key(username)
                else:
                    auser = Abon.objects.get_by_natural_key(username)
                if self.user_can_authenticate(auser):
                    return auser
        except BaseAccount.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a non-existing user (#20760).
            BaseAccount().set_password(password)

    def get_user(self, user_id):
        try:
            user = BaseAccount._default_manager.get(pk=user_id)
            if user.is_staff:
                user = UserProfile._default_manager.get(pk=user_id)
            else:
                user = Abon._default_manager.get(pk=user_id)
        except BaseAccount.DoesNotExist:
            return
        return user if self.user_can_authenticate(user) else None


class LocationAuthBackend(ModelBackend):
    def authenticate(self, request, byip, **kwargs):
        try:
            remote_ip = ip_address(request.META.get('REMOTE_ADDR'))
            lease = IpLeaseModel.objects.filter(ip=str(remote_ip)).first()
            if lease is None:
                return
            user = Abon.objects.get(ip_addresses=lease)
            if self.user_can_authenticate(user):
                return user
        except (AddressValueError, Abon.DoesNotExist):
            return

    def get_user(self, user_id):
        try:
            user = Abon.objects.get(pk=user_id)
        except Abon.DoesNotExist:
            return
        return user if self.user_can_authenticate(user) else None
