from ipaddress import ip_network, ip_address
from typing import Optional, Generator

from django.db.utils import IntegrityError
from django.shortcuts import resolve_url
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from djing.fields import MACAddressField
from djing.lib import DuplicateEntry
from ip_pool.fields import GenericIpAddressWithPrefix
from group_app.models import Group


class NetworkModel(models.Model):
    _netw_cache = None

    network = GenericIpAddressWithPrefix(
        verbose_name=_('IP network'),
        help_text=_('Ip address of network. For example: '
                    '192.168.1.0 or fde8:6789:1234:1::'),
        unique=True
    )
    NETWORK_KINDS = (
        ('inet', _('Internet')),
        ('guest', _('Guest')),
        ('trust', _('Trusted')),
        ('device', _('Devices')),
        ('admin', _('Admin'))
    )
    kind = models.CharField(
        _('Kind of network'), max_length=6,
        choices=NETWORK_KINDS, default='guest'
    )
    description = models.CharField(_('Description'), max_length=64)
    groups = models.ManyToManyField(Group, verbose_name=_('Groups'))

    # Usable ip range
    ip_start = models.GenericIPAddressField(_('Start work ip range'))
    ip_end = models.GenericIPAddressField(_('End work ip range'))

    def __str__(self):
        netw = self.get_network()
        return "%s: %s" % (self.description, netw.with_prefixlen)

    def get_network(self):
        if self.network is None:
            return
        if self._netw_cache is None:
            self._netw_cache = ip_network(self.network)
        return self._netw_cache

    def get_absolute_url(self):
        return resolve_url('ip_pool:net_edit', self.pk)

    def clean(self):
        errs = {}
        if self.network is None:
            errs['network'] = ValidationError(
                _('Network is invalid'),
                code='invalid'
            )
            raise ValidationError(errs)
        net = self.get_network()
        if self.ip_start is None:
            errs['ip_start'] = ValidationError(
                _('Ip start is invalid'),
                code='invalid'
            )
            raise ValidationError(errs)
        start_ip = ip_address(self.ip_start)
        if start_ip not in net:
            errs['ip_start'] = ValidationError(
                _('Start ip must be in subnet of specified network'),
                code='invalid'
            )
        if self.ip_end is None:
            errs['ip_end'] = ValidationError(
                _('Ip end is invalid'),
                code='invalid'
            )
            raise ValidationError(errs)
        end_ip = ip_address(self.ip_end)
        if end_ip not in net:
            errs['ip_end'] = ValidationError(
                _('End ip must be in subnet of specified network'),
                code='invalid'
            )
        if errs:
            raise ValidationError(errs)

        other_nets = NetworkModel.objects.exclude(
            pk=self.pk
        ).only('network').order_by('network')
        if not other_nets.exists():
            return
        for onet in other_nets.iterator():
            onet_netw = onet.get_network()
            if net.overlaps(onet_netw):
                errs['network'] = ValidationError(
                    _('Network is overlaps with %(other_network)s'),
                    params={
                        'other_network': str(onet_netw)
                    }
                )
                raise ValidationError(errs)

    def get_scope(self) -> str:
        net = self.get_network()
        if net.is_global:
            return _('Global')
        elif net.is_link_local:
            return _('Link local')
        elif net.is_loopback:
            return _('Loopback')
        elif net.is_multicast:
            return _('Multicast')
        elif net.is_private:
            return _('Private')
        elif net.is_reserved:
            return _('Reserved')
        elif net.is_site_local:
            return _('Site local')
        elif net.is_unspecified:
            return _('Unspecified')
        return "I don't know"

    def get_free_ip(self, employed_ips: Optional[Generator]):
        """
        Find free ip in network.
        :param employed_ips: Sorted from less to more
         ip addresses from current network.
        :return: single found ip
        """
        network = self.get_network()
        work_range_start_ip = ip_address(self.ip_start)
        work_range_end_ip = ip_address(self.ip_end)
        if employed_ips is None:
            for ip in network.hosts():
                if work_range_start_ip <= ip <= work_range_end_ip:
                    return ip
            return
        for ip in network.hosts():
            if ip < work_range_start_ip:
                continue
            elif ip > work_range_end_ip:
                break  # Not found
            used_ip = next(employed_ips)
            if used_ip is None:
                return ip
            used_ip = ip_address(used_ip)
            if ip < used_ip:
                return ip

    class Meta:
        db_table = 'ip_pool_network'
        verbose_name = _('Network')
        verbose_name_plural = _('Networks')
        ordering = ('network',)
