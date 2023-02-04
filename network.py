import psutil
import socket
import icmplib
import asyncio
import ipaddress


POPULAR_PORTS = {
    21: "FTP",
    22: "SSH",
    23: "Telnet",
    25: "SMTP",
    53: "DNS",
    67: "DHCP",
    69: "TFTP",
    80: "HTTP",
    110: "POP3",
    123: "NTP",
    135: "Microsoft RPC",
    137: "NetBIOS Name Service",
    138: "NetBIOS Datagram Service",
    139: "NetBIOS Session Service",
    143: "IMAP",
    161: "SNMP",
    162: "SNMP-trap",
    389: "LDAP",
    443: "HTTPS",
    445: "Microsoft-DS",
    587: "SMTP (submission)",
    993: "IMAP (over SSL/TLS)",
    995: "POP3 (over SSL/TLS)",
    1433: "Microsoft SQL Server",
    1521: "Oracle",
    1723: "PPTP",
    2221: "FTP (alternative)",
    3306: "MySQL",
    3389: "Microsoft RDP",
    5900: "VNC",
    8080: "HTTP (alternate)",
    8888: "HTTP (alternate)",
    27017: "MongoDB",
    28017: "MongoDB web interface",
    6379: "Redis",
    11211: "Memcached",
}


class Port:
    def __init__(self, port_number, description):
        self.port_number = port_number
        self.description = description
        self.status = False

    async def check_async(self, ip):
        connection = asyncio.open_connection(ip, self.port_number)

        try:
            _, writer = await asyncio.wait_for(connection, 2)
            self.status = True
        except asyncio.TimeoutError:
            self.status = False
        finally:
            writer.close()


class Host:
    def __init__(self, ip):
        self.ip = ip
        self.ping_time = None
        self.ports = []

        for number, description in POPULAR_PORTS.items():
            self.ports.append(Port(number, description))

    def check_ports(self):
        for port in self.ports:
            asyncio.create_task(port.check_async(self.ip))

    async def ping_async(self):
        ping = await icmplib.async_ping(
            self.ip,
            count=5,
            interval=0.05,
            privileged=False,
        )

        if ping.is_alive:
            self.ping_time = f"{ping.avg_rtt:8.3f} мс"
        else:
            self.ping_time = None


class Interface:
    def __init__(self, name, ip, mask):
        self.name = name
        self.ip = ip
        self.mask = mask
        self.hosts = []

        address = f"{self.ip}/{self.mask}"
        subnet = ipaddress.IPv4Network(address, strict=False)

        for ipv4 in subnet.hosts():
            self.hosts.append(Host(str(ipv4)))

    def ping_subnet(self):
        for host in self.hosts:
            asyncio.create_task(host.ping_async())


class Network:
    interfaces = []

    @staticmethod
    def __init__():
        interfaces = psutil.net_if_addrs()
        for interface, addresses in interfaces.items():
            for address in addresses:
                if address.family == socket.AF_INET and address.address != "127.0.0.1":
                    Network.interfaces.append(
                        Interface(
                            interface,
                            address.address,
                            address.netmask,
                        )
                    )
