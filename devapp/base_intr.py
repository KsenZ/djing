from abc import ABCMeta, abstractmethod
from datetime import timedelta
from typing import Union, Iterable, AnyStr, Generator, Optional, Dict
from easysnmp import Session

from django.utils.translation import gettext, gettext_lazy as _

ListOrError = Union[
    Iterable,
    Union[Exception, Iterable]
]


class DeviceImplementationError(NotImplementedError):
    pass


class DeviceConfigurationError(DeviceImplementationError):
    pass


class DevBase(object, metaclass=ABCMeta):
    def __init__(self, dev_instance=None):
        self.db_instance = dev_instance

    @property
    @abstractmethod
    def description(self) -> AnyStr:
        pass

    @classmethod
    def get_description(cls):
        return cls.description

    def reboot(self, save_before_reboot=False):
        """
        Send signal reboot to device
        :param save_before_reboot:
        :return: tuple of command return number and text of operation
        """
        return 5, _('Reboot not ready')

    @abstractmethod
    def get_ports(self) -> ListOrError:
        pass

    @abstractmethod
    def get_device_name(self) -> AnyStr:
        """Return device name by snmp"""

    @abstractmethod
    def uptime(self) -> timedelta:
        pass

    @abstractmethod
    def get_template_name(self) -> AnyStr:
        """Return path to html template for device"""

    @property
    @abstractmethod
    def has_attachable_to_subscriber(self) -> bool:
        """Can connect device to subscriber"""

    @property
    @abstractmethod
    def is_use_device_port(self) -> bool:
        """True if used device port while opt82 authorization"""

    @classmethod
    def get_is_use_device_port(cls) -> bool:
        return cls.is_use_device_port

    @staticmethod
    def validate_extra_snmp_info(v: str) -> None:
        """
        Validate extra snmp field for each device.
        If validation failed then raise en exception from devapp.expect_scripts.ExpectValidationError
        with description of error.
        :param v: String value for validate
        """
        raise NotImplementedError

    @abstractmethod
    def register_device(self, extra_data: Dict):
        pass

    @abstractmethod
    def monitoring_template(self, *args, **kwargs) -> Optional[str]:
        """
        Template for monitoring system config
        :return: string for config file
        """


class BasePort(object, metaclass=ABCMeta):
    __slots__ = 'num', 'snmp_num', 'nm', 'st', '_mac', 'sp', 'writable'

    def __init__(self, num, name, status, mac, speed, snmp_num=None, writable=False):
        self.num = int(num)
        self.snmp_num = int(num) if snmp_num is None else int(snmp_num)
        self.nm = name
        self.st = status
        self._mac = mac
        self.sp = speed
        self.writable = writable

    @abstractmethod
    def disable(self):
        pass

    @abstractmethod
    def enable(self):
        pass

    def mac(self) -> str:
        return ':'.join('%x' % ord(i) for i in self._mac)


class SNMPBaseWorker(object, metaclass=ABCMeta):
    ses = None

    def __init__(self, ip: Optional[str], community='public', ver=2):
        if ip is None or ip == '':
            raise DeviceImplementationError(gettext('Ip address is required'))
        self._ip = ip
        self._community = community
        self._ver = ver

    def start_ses(self):
        if self.ses is None:
            self.ses = Session(
                hostname=self._ip, community=self._community,
                version=self._ver
            )

    def set_int_value(self, oid: str, value):
        self.start_ses()
        return self.ses.set(oid, value, 'i')

    def get_list(self, oid) -> Generator:
        self.start_ses()
        for v in self.ses.walk(oid):
            yield v.value

    def get_list_keyval(self, oid) -> Generator:
        self.start_ses()
        for v in self.ses.walk(oid):
            snmpnum = v.oid.split('.')[-1:]
            yield v.value, snmpnum[0] if len(snmpnum) > 0 else None

    def get_item(self, oid):
        self.start_ses()
        v = self.ses.get(oid).value
        if v != 'NOSUCHINSTANCE':
            return v
