from rich.table import Table
from textual.app import App
from textual.widget import Widget
from textual.widgets import Static, Footer

from network import Network


class ApplicationHeader(Static):
    def render(self):
        return "[bold]AddressScroll[/bold] - сканирование сетевых адресов и портов"


class PanelTitle(Static):
    def __init__(self, title):
        super().__init__()
        self.title = title

    def render(self):
        return self.title


class InterfacesPanel(Widget):
    def on_mount(self):
        self.update_render = self.set_interval(1 / 4, self.refresh)

    def render(self):
        table = Table(box=None, expand=True)
        table.add_column("Имя")
        table.add_column("IP")

        for interface in Network.interfaces:
            if interface == Cursor.interface:
                table.add_row(interface.name, interface.ip, style="bold yellow")
            else:
                table.add_row(interface.name, interface.ip)

        return table


class HostsPanel(Widget):
    def on_mount(self):
        self.update_render = self.set_interval(1 / 4, self.refresh)

    def render(self):
        table = Table(box=None, expand=True)
        table.add_column("IP")
        table.add_column("Время")

        if Cursor.interface:
            for host in Cursor.interface.hosts:
                if host.ping_time:
                    if host == Cursor.host:
                        table.add_row(host.ip, host.ping_time, style="bold yellow")
                    else:
                        table.add_row(host.ip, host.ping_time)

        return table


class PortsPanel(Widget):
    def on_mount(self):
        self.update_render = self.set_interval(1 / 4, self.refresh)

    def render(self):
        table = Table(box=None, expand=True)
        table.add_column("Порт")
        table.add_column("Описание")

        if Cursor.host:
            for port in Cursor.host.ports:
                if port.status:
                    table.add_row(
                        f"{port.port_number}",
                        f"{port.description}",
                    )

        return table


class Cursor:
    host = None
    interface = None

    @staticmethod
    def next_interface():
        if not Network.interfaces:
            return

        if not Cursor.interface:
            Cursor.interface = Network.interfaces[0]
        else:
            index = Network.interfaces.index(Cursor.interface)
            next_index = (index + 1) % len(Network.interfaces)
            Cursor.interface = Network.interfaces[next_index]

        Cursor.interface.ping_subnet()
        Cursor.host = None

    @staticmethod
    def next_host():
        if not Cursor.interface:
            return

        alive_hosts = [host for host in Cursor.interface.hosts if host.ping_time]

        if not Cursor.host:
            Cursor.host = alive_hosts[0]
        else:
            index = alive_hosts.index(Cursor.host)
            next_index = (index + 1) % len(alive_hosts)
            Cursor.host = alive_hosts[next_index]

        Cursor.host.check_ports()


class NetScroll(App):
    CSS_PATH = "styles.css"

    BINDINGS = [
        ("i", "interface", "Интерфейс"),
        ("h", "host", "Адрес"),
        ("q", "exit", "Выход"),
    ]

    def __init__(self):
        super().__init__()
        Network.__init__()

    def compose(self):
        yield ApplicationHeader()
        yield PanelTitle("Интерфейсы")
        yield PanelTitle("Адреса")
        yield PanelTitle("Порты")
        yield InterfacesPanel()
        yield HostsPanel()
        yield PortsPanel()
        yield Footer()

    def action_interface(self):
        Cursor.next_interface()

    def action_host(self):
        Cursor.next_host()

    def action_exit(self):
        self.exit()
