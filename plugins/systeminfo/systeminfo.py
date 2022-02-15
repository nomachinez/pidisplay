import threading
from datetime import datetime
import os
import platform
import re
import socket
import subprocess
import time

import psutil

import pygame
import requests

from lib.plugin import Singleton
from lib.fullscreen_plugin import FullScreenPlugin


class SystemInfo(FullScreenPlugin, metaclass=Singleton):
    """ System Info """

    def __init__(self, helper, canvas, app_plugin_config):
        FullScreenPlugin.__init__(self, helper, canvas, os.path.abspath(os.path.dirname(__file__)), app_plugin_config)

        font_str = self.plugin_config["font_face"]
        if font_str[-4:].lower() == ".ttf" or font_str[-4:].lower() == ".otf":
            filename = os.path.abspath(os.path.join(os.path.dirname(__file__), "fonts", font_str))
            self.default_font = pygame.font.Font(filename, self.plugin_config.getint("font_size"))
            self.helper.log(self.debug, "FONT: regular font loading {}".format(filename))
        else:
            self.default_font = pygame.font.SysFont(font_str, self.plugin_config.getint("font_size"))
            self.helper.log(self.debug, "FONT: loading default font {}".format(font_str))

        bold_font_str = self.plugin_config["font_face_bold"]
        if bold_font_str[-4:].lower() == ".ttf":
            filename = os.path.abspath(os.path.join(os.path.dirname(__file__), "fonts", bold_font_str))
            self.header_font = pygame.font.Font(filename, self.plugin_config.getint("font_size"))
            self.helper.log(self.debug, "FONT: bold font loading {}".format(filename))
        else:
            self.header_font = pygame.font.SysFont(bold_font_str, self.plugin_config.getint("font_size"), bold=True)
            self.helper.log(self.debug, "FONT: loading default font {}".format(bold_font_str))

        self.fg_color = eval(self.plugin_config["foreground"])
        self.bargraph_color = eval(self.plugin_config["bargraph_color"])
        self.bargraph_text_color = eval(self.plugin_config["bargraph_text_color"])
        self.bargraph_border_color = eval(self.plugin_config["bargraph_border_color"])
        self.bg_color = eval(self.plugin_config["background"])
        self.unit_type = self.plugin_config["unit_type"]
        if self.unit_type != helper.FAHRENHEIT and self.unit_type != helper.CELSIUS:
            self.unit_type = helper.CELSIUS
        self.ping_type = self.plugin_config["ping_type"]
        if self.ping_type != helper.PING and self.ping_type != helper.CONNECT:
            self.ping_type = helper.CONNECT

        self.update_interval = self.plugin_config.getint("update_interval")

        self.internet_test_connectivity_host = self.plugin_config["internet_test_connectivity_host"]
        self.internet_test_connectivity_port = self.plugin_config.getint("internet_test_connectivity_port")
        self.internet_ping_host = self.plugin_config["internet_ping_host"]
        self.internet_ping_port = self.plugin_config.getint("internet_ping_port")
        self.default_gateway_connect_port = self.plugin_config.getint("default_gateway_connect_port")
        self.date_format = self.plugin_config["date_format"]
        self.screen_margin = self.plugin_config.getint("screen_margin")

        # CPU
        self.cpu_stats = []
        self.cpu_temp = {}
        self.cpu_current_load = []
        self.cpu_average_load = []
        self.cpu_current_load_total = 0.0
        self.cpu_count = ""
        self.cpu_frequency = []
        self.cpu_speed = ""
        self.cpu_model = ""
        self.cpu_architecture = ""
        self.cpu_vendor = ""
        self.cpu_sockets = 0
        self.cpu_ram = 0  # vcgencmd get_mem arm && vcgencmd get_mem gpu
        self.gpu_ram = 0

        self.system_hostname = ""
        self.system_uptime = 0
        self.system_boot_time = ""
        self.system_current_users = []
        self.system_kernel_version = ""
        self.system_os_version = ""

        self.display_resolution = ""
        self.display_native_resolution = ""

        # with rx/tx
        self.networking_nics = []
        self.networking_nic_stats = []
        self.networking_public_ip_address = ""
        self.networking_ping_default_gateway = 0
        self.networking_ping_internet = 0

        self.memory_info = None
        self.memory_swap_info = None

        self.networking_wifi_name = ""
        self.networking_wifi_signal_strength = ""

        self.disk_io_counters = {}
        self.disk_mounts = []
        self.disk_usage = []
        self.networking_default_gateway = ""
        self.networking_connected_to_internet = False
        self.system_raspberry_pi_model = ""

        self.timer = self.update_interval
        self.image = pygame.Surface((self.screen_width, self.screen_height))
        self.upper_right_x = 0
        self.small_graph_width = 150
        self.small_graph_width_small = 100
        self.line_buffer = 10
        self.line_buffer_small = 1
        self.small_graph_height = self.default_font.get_linesize()
        self.surf_cpu_information_title_y = 0
        self.surf_cpu_graph_width = 0
        self.surf_cpu_graph_start = 0
        self.info_updated = False
        self.info_updated_light = False
        self.cpus_graph_start_x = 0
        self.cpus_graph_start_y = 0
        self.in_systeminfo_light_thread = False
        self.in_systeminfo_thread = False

        self.image.fill(self.bg_color)

    @staticmethod
    def get_os_version():
        result = ""
        osfile = ""
        if os.path.isfile("/etc/os-release"):
            osfile = "/etc/os-release"
        elif os.path.isfile("usr/lib/os-release"):
            osfile = "/usr/lib/os-release"

        if osfile != "":
            try:
                with open(osfile, 'r') as fh:
                    for line in fh:
                        if line is not None and "PRETTY_NAME" in line:
                            result = line.split("=", 1)
                            if len(result) > 1:
                                result = result[1].strip()
                                result = result.strip('"')
                                break
            except:
                pass

        return result

    @staticmethod
    def get_cpu_info():
        model_name = ""
        architecture = ""
        vendor_id = ""
        cpu_max = ""
        cpu_min = ""
        cpu_current = ""
        sockets = 0

        lscpu = ""
        try:
            lscpu = (subprocess.check_output("lscpu", stderr=subprocess.DEVNULL).strip()).decode()
        except:
            pass

        if lscpu != "":
            matches = re.findall(r"model name\s*:\s*([^\n]+)\n", lscpu, re.I)
            if len(matches) > 0:
                model_name = matches[0]
            matches = re.findall(r"architecture\s*:\s*([^\n]+)\n", lscpu, re.I)
            if len(matches) > 0:
                architecture = matches[0]
            matches = re.findall(r"vendor id\s*:\s*([^\n]+)\n", lscpu, re.I)
            if len(matches) > 0:
                vendor_id = matches[0]
            matches = re.findall(r"CPU max MHz\s*:\s*([^\n]+)\n", lscpu, re.I)
            if len(matches) > 0:
                cpu_max = matches[0]
            matches = re.findall(r"CPU min MHz\s*:\s*([^\n]+)\n", lscpu, re.I)
            if len(matches) > 0:
                cpu_min = matches[0]
            matches = re.findall(r"CPU MHz\s*:\s*([^\n]+)\n", lscpu, re.I)
            if len(matches) > 0:
                cpu_current = matches[0]
            matches = re.findall(r"Socket\(s\)\s*:\s*([^\n]+)\n", lscpu, re.I)
            if len(matches) > 0:
                sockets = matches[0]

        return model_name, architecture, vendor_id, cpu_max, cpu_min, cpu_current, sockets

    @staticmethod
    def is_connected_to_internet(hostname, port):
        try:
            socket.create_connection((hostname, port), 2)
            return True
        except:
            return False

    @staticmethod
    def connect_time(hostname, port):
        try:
            host = socket.gethostbyname(hostname)
            before = time.perf_counter()
            socket.create_connection((host, port), 2)
            after = time.perf_counter()
            return (after - before) / 1000 / 1000
        except:
            return -1

    @staticmethod
    def ping_time(hostname):
        try:
            ping = subprocess.check_output(["ping", "-c", "1", "-n", "-4", hostname], stderr=subprocess.DEVNULL).decode()
            matches = re.findall(r"min/avg/max/mdev = ([^/]+).*", ping, re.I)
            if len(matches) > 0:
                return "{}ms".format(matches[0].split(".")[0])
        except Exception as err:
            pass

        return "-1ms"

    @staticmethod
    def get_wifi_signal_level():
        signal_level = ""
        try:
            iwconfig = subprocess.check_output(["iwconfig"], stderr=subprocess.DEVNULL).stdout.decode()
            matches = re.findall('(wlan[0-9]+).*?Signal level=(-[0-9]+) dBm', iwconfig, re.DOTALL)
            if len(matches) > 1:
                signal_level = matches[1]
        except:
            pass
        return signal_level

    @staticmethod
    def get_default_resolution():
        try:
            fbset = subprocess.check_output(["fbset", "-s"], stderr=subprocess.DEVNULL).stdout.decode()
            matches = re.findall(r".+geometry (\d+) (\d+).*", fbset, re.DOTALL)
            if len(matches) > 1:
                return matches[0], matches[1]
        except:
            pass

        return 0, 0

    def get_info(self):
        self.helper.log(self.debug, "Updating SystemInfo with new system info.")
        # CPU
        self.cpu_temp = psutil.sensors_temperatures(fahrenheit=False)
        self.cpu_current_load = psutil.cpu_percent(interval=None, percpu=True)
        self.cpu_average_load = [x / psutil.cpu_count() * 100 for x in psutil.getloadavg()]  # 1, 5, and 15 minutes
        self.cpu_count = "{} / {}".format(len(psutil.Process().cpu_affinity()), psutil.cpu_count())
        self.cpu_frequency = psutil.cpu_freq(percpu=True)

        model_name, architecture, vendor_id, cpu_max, cpu_min, cpu_current, sockets = SystemInfo.get_cpu_info()
        self.cpu_model = model_name
        if cpu_min != "" and cpu_max != "":
            self.cpu_speed = "{} ({}/{})".format(cpu_current, cpu_min, cpu_max)
        else:
            self.cpu_speed = cpu_current

        self.cpu_architecture = architecture
        self.cpu_vendor = vendor_id
        self.cpu_sockets = sockets

        # raspberry pi only
        try:
            self.cpu_ram = subprocess.check_output(["vcgencmd", "get_mem", "arm"], stderr=subprocess.DEVNULL).stdout.decode()
            self.gpu_ram = subprocess.check_output(["vcgencmd", "get_mem", "gpu"], stderr=subprocess.DEVNULL).stdout.decode()
        except:
            pass

        # SYSTEM
        self.system_uptime = self.helper.get_time_delta_string(time.time(), psutil.boot_time(), False, False, True)
        self.system_kernel_version = platform.version()
        self.system_boot_time = datetime.fromtimestamp(psutil.boot_time()).strftime(self.date_format)
        self.system_current_users = psutil.users()
        self.system_os_version = SystemInfo.get_os_version()
        self.system_hostname = platform.node()

        # MEMORY
        # free memory is in the "available" property
        self.memory_info = psutil.virtual_memory()
        self.memory_swap_info = psutil.swap_memory()

        # DISK
        # with used/free
        self.disk_io_counters = psutil.disk_io_counters(perdisk=True)
        self.disk_mounts = psutil.disk_partitions(all=False)
        self.disk_usage = []
        for i in self.disk_mounts:
            self.disk_usage.append({"mountpoint": i.mountpoint, "usage": psutil.disk_usage(i.mountpoint)})

        # NETWORKING
        # with rx/tx
        self.networking_nics = psutil.net_if_addrs()
        self.networking_nic_stats = psutil.net_io_counters(pernic=True)
        try:
            self.networking_wifi_name = subprocess.check_output(["iwgetid", "-r"], stderr=subprocess.DEVNULL).stdout.decode()
        except:
            pass
        self.networking_wifi_signal_strength = SystemInfo.get_wifi_signal_level()

        # NETWORKING/IP
        try:
            self.networking_public_ip_address = requests.get('https://api.ipify.org').text
        except:
            pass

        try:
            default_gw = subprocess.check_output(["ip", "route", "list", "default"], stderr=subprocess.DEVNULL).decode()
            match = re.search(r"default via ([^\s]+).+", default_gw, re.I)
            if match is not None and len(match.groups()) > 0:
                self.networking_default_gateway = match.group(1)
        except:
            pass

        if self.networking_default_gateway != "":
            if self.ping_type == self.helper.CONNECT:
                self.networking_ping_default_gateway = SystemInfo.connect_time(self.networking_default_gateway, self.default_gateway_connect_port)
            else:
                self.networking_ping_default_gateway = SystemInfo.ping_time(self.networking_default_gateway)

        if self.ping_type == self.helper.CONNECT:
            self.networking_ping_internet = SystemInfo.connect_time(self.internet_ping_host, self.internet_ping_port)
        else:
            self.networking_ping_internet = SystemInfo.ping_time(self.internet_ping_host)

        self.networking_connected_to_internet = SystemInfo.is_connected_to_internet(self.internet_test_connectivity_host, self.internet_test_connectivity_port)

        # DISPLAY
        width, height = pygame.display.get_surface().get_size()
        self.display_resolution = "{}x{}".format(width, height)
        width, height = SystemInfo.get_default_resolution()
        self.display_native_resolution = "{}x{}".format(width, height)

        # RASPBERRY PI
        try:
            self.system_raspberry_pi_model = subprocess.check_output(["cat", "/proc/device-tree/model"], stderr=subprocess.DEVNULL).stdout.decode()
        except:
            pass

    def get_info_light(self):
        self.cpu_current_load_total = psutil.cpu_percent(interval=None, percpu=False)
        self.cpu_stats = psutil.cpu_times_percent(interval=None, percpu=True)

    def update_image_light(self):
        if self.upper_right_x > 0:
            # Current time
            surf_current_time = self.default_font.render("Now: {}".format(datetime.now().strftime(self.date_format)), True, self.fg_color, self.bg_color)
            self.image.blit(surf_current_time, (self.screen_width - self.upper_right_x - self.screen_margin, self.default_font.get_linesize() + self.line_buffer_small + self.screen_margin))

            # CPU usage graph
            surf_cpu_usage = pygame.Surface((self.surf_cpu_graph_width, self.small_graph_height))
            surf_cpu_usage.fill(self.bg_color)
            cpu_usage_width = self.cpu_current_load_total/100 * self.surf_cpu_graph_width
            pygame.draw.rect(surf_cpu_usage, self.bargraph_color, (0, 0, cpu_usage_width, surf_cpu_usage.get_height()))
            surf_cpu_usage_text = self.default_font.render("{}%".format(self.cpu_current_load_total), True, self.bargraph_text_color)
            surf_cpu_usage.blit(surf_cpu_usage_text, (surf_cpu_usage.get_width()/2 - surf_cpu_usage_text.get_width()/2, surf_cpu_usage.get_height()/2 - surf_cpu_usage_text.get_height()/2))
            pygame.draw.rect(surf_cpu_usage, self.bargraph_border_color, (0, 0, surf_cpu_usage.get_width(), surf_cpu_usage.get_height()), 1)
            self.image.blit(surf_cpu_usage, (self.surf_cpu_graph_start, self.surf_cpu_information_title_y + self.header_font.get_height()/2 - surf_cpu_usage.get_height()/2))

            # CPUs usage graph
            y = self.cpus_graph_start_y
            for i in range(len(self.cpu_stats)):
                surf = pygame.Surface((self.small_graph_width_small, self.small_graph_height))
                surf.fill(self.bg_color)
                cpu_usage_width = self.cpu_stats[i].user / 100 * self.small_graph_width_small

                pygame.draw.rect(surf, self.bargraph_color, (0, 0, cpu_usage_width, surf.get_height()))
                surf_cpu_usage_text = self.default_font.render("{}%".format(self.cpu_stats[i].user), True, self.bargraph_text_color)
                surf.blit(surf_cpu_usage_text, (surf.get_width() / 2 - surf_cpu_usage_text.get_width() / 2, surf.get_height() / 2 - surf_cpu_usage_text.get_height() / 2))
                pygame.draw.rect(surf, self.bargraph_border_color, (0, 0, surf.get_width(), surf.get_height()), 1)
                self.image.blit(surf, (self.cpus_graph_start_x, y+1))
                y += self.small_graph_height + self.line_buffer_small

    def update_image(self):

        surf_system_hostname = self.header_font.render(self.system_hostname, True, self.fg_color, self.bg_color)
        self.image.blit(surf_system_hostname, (self.screen_margin, self.screen_margin))

        indent = surf_system_hostname.get_width() / 2
        column_spacer = 20

        surf_system_uptime = self.default_font.render("Uptime: {}".format(self.system_uptime), True, self.fg_color, self.bg_color)

        surf_wifi_info = None
        if self.networking_wifi_name != "":
            surf_wifi_info = self.default_font.render(
                "Wifi: {} ({})".format(self.networking_wifi_name, self.networking_wifi_signal_strength), True, self.fg_color, self.bg_color)

        self.upper_right_x = surf_system_uptime.get_width()
        longest_date_surf = self.default_font.render("Now: {}".format(datetime(2022, 9, 14, 22, 22, 22).strftime(self.date_format)), True, self.fg_color, self.bg_color)
        if longest_date_surf.get_width() > self.upper_right_x:
            self.upper_right_x = longest_date_surf.get_width()
        if surf_wifi_info is not None:
            if surf_wifi_info.get_width() > self.upper_right_x:
                self.upper_right_x = surf_wifi_info.get_width()

        del longest_date_surf

        self.image.blit(surf_system_uptime, (self.screen_width - self.upper_right_x - self.screen_margin, self.screen_margin))

        if surf_wifi_info is not None:
            self.image.blit(surf_wifi_info, (self.screen_width - self.upper_right_x - self.screen_margin, self.default_font.get_linesize() * 2 + self.screen_margin))

        surf_os_info = self.default_font.render(
            "A {} system running on {} since {}".format(self.system_os_version, self.cpu_architecture,
                                                        self.system_boot_time), True, self.fg_color, self.bg_color)
        x = (self.screen_width - surf_system_hostname.get_width() - self.upper_right_x) / 2 - surf_os_info.get_width() / 2 + surf_system_hostname.get_width() + self.screen_margin
        self.image.blit(surf_os_info, (x, self.screen_margin))

        current_y = self.default_font.get_linesize() + self.line_buffer_small + self.screen_margin
        if self.system_raspberry_pi_model != "":
            surf_pi_version = self.default_font.render("Pi ver: {}".format(self.system_raspberry_pi_model), True, self.fg_color, self.bg_color)
            self.image.blit(surf_pi_version, (indent + self.screen_margin, self.default_font.get_linesize() + self.screen_margin))

        surf_display_info = self.default_font.render("Display: {} (native) {} (current)".format(self.display_native_resolution, self.display_resolution), True, self.fg_color, self.bg_color)
        self.image.blit(surf_display_info, (self.screen_width - self.upper_right_x - surf_display_info.get_width() - 100 - self.screen_margin, current_y))  # right-padding

        current_y += self.default_font.get_linesize() + self.line_buffer

        local_ip = ""
        subnet_mask = ""
        for k in self.networking_nics:
            if self.networking_nics[k] != "" and len(k) >= 2 and k[:2] != "lo":
                for i in self.networking_nics[k]:
                    if i.family == socket.AF_INET:
                        local_ip = i.address
                        subnet_mask = self.helper.get_subnet_mask_bits(i.netmask)
                        break
                if local_ip != "":
                    break

        surf_ip_info = self.default_font.render("IP: {}/{} ({}, {})".format(local_ip, subnet_mask, self.networking_public_ip_address, self.networking_ping_internet), True, self.fg_color, self.bg_color)
        self.image.blit(surf_ip_info, (indent + self.screen_margin, current_y))

        surf_default_gw = self.default_font.render("GW: {} ({})".format(self.networking_default_gateway, self.networking_ping_default_gateway), True, self.fg_color, self.bg_color)
        self.image.blit(surf_default_gw, (indent + surf_ip_info.get_width() + 50 + self.screen_margin, current_y))  # left-padding

        current_y += self.default_font.get_linesize()

        surf_cpu_information_title = self.header_font.render("CPU", True, self.fg_color, self.bg_color)
        surf_memory_information_title = self.header_font.render("Memory", True, self.fg_color, self.bg_color)
        surf_disk_information_title = self.header_font.render("Disks", True, self.fg_color, self.bg_color)
        surf_network_information_title = self.header_font.render("Network", True, self.fg_color, self.bg_color)

        current_y += self.line_buffer
        self.image.blit(surf_cpu_information_title, (self.screen_margin, current_y))
        self.surf_cpu_information_title_y = current_y
        self.surf_cpu_graph_start = surf_cpu_information_title.get_width() + column_spacer + self.screen_margin

        surf_cpu_info_text = self.default_font.render("{}x {} {} CPUs".format(self.cpu_sockets, self.cpu_vendor, self.cpu_model), True, self.fg_color, self.bg_color)
        self.image.blit(surf_cpu_info_text, (self.screen_width - surf_cpu_info_text.get_width() - self.screen_margin, current_y))
        self.surf_cpu_graph_width = self.screen_width - surf_cpu_info_text.get_width() - surf_cpu_information_title.get_width() - column_spacer*2 - self.screen_margin*2

        if len(self.cpu_average_load) > 0:
            surf_avg_cpu = self.default_font.render("1min: {:.1f}  5min: {:.1f}  15min: {:.1f}".format(self.cpu_average_load[0], self.cpu_average_load[1], self.cpu_average_load[2]), True, self.fg_color, self.bg_color)
        else:
            surf_avg_cpu = self.default_font.render("1min: {}  5min: {}  15min:{}".format(-1, -1, -1), True, self.fg_color, self.bg_color)

        temp_y = current_y + self.small_graph_height + self.line_buffer_small
        current_y += self.small_graph_height + self.line_buffer_small
        self.image.blit(surf_avg_cpu, (self.surf_cpu_graph_start, current_y))

        temp = -1
        if len(self.cpu_temp) > 0:
            if "cpu_thermal" in self.cpu_temp and len(self.cpu_temp["cpu_thermal"]) > 0:
                temp = self.cpu_temp["cpu_thermal"][0].current
            else:
                self.helper.log(self.debug, "No CPU Thermal!  Response was: {}".format(self.cpu_temp))

        surf_cpu_temp = self.default_font.render("Temp: {}".format(temp), True, self.fg_color, self.bg_color)

        self.image.blit(surf_cpu_temp, (self.surf_cpu_graph_start + self.surf_cpu_graph_width - surf_cpu_temp.get_width(), temp_y))

        current_y += self.default_font.get_linesize() + self.line_buffer

        x = self.screen_margin
        self.cpus_graph_start_y = current_y + self.header_font.get_linesize() + 1

        texts = []
        for i in range(len(self.cpu_stats)): texts.append("CPU {}".format(i))
        max_width = self.blit_column("", texts, x, current_y, all_headers=True, align="left", max_chars=5)

        # Leave room for the graphs
        self.cpus_graph_start_x = max_width + column_spacer + self.screen_margin
        x = max_width + column_spacer + self.small_graph_width_small + column_spacer + self.screen_margin

        x_step = (self.screen_width - x - self.screen_margin) / 9

        texts = []
        for i in range(len(self.cpu_stats)): texts.append("{:.1f}%".format(self.cpu_stats[i].nice))
        # %s here can be max 5 chars ... ##.#% . So whichever is longer between the header and 5, set max_chars to that
        max_width = self.blit_column("nice", texts, x, current_y, align="center", max_chars=5)
        x += x_step

        texts = []
        for i in range(len(self.cpu_stats)): texts.append("{:.1f}%".format(self.cpu_stats[i].system))
        max_width = self.blit_column("system", texts, x, current_y, align="center", max_chars=6)
        x += x_step

        texts = []
        for i in range(len(self.cpu_stats)): texts.append("{:.1f}%".format(self.cpu_stats[i].idle))
        max_width = self.blit_column("idle", texts, x, current_y, align="center", max_chars=5)
        x += x_step

        texts = []
        for i in range(len(self.cpu_stats)): texts.append("{:.1f}%".format(self.cpu_stats[i].iowait))
        max_width = self.blit_column("iowait", texts, x, current_y, align="center", max_chars=6)
        x += x_step

        texts = []
        for i in range(len(self.cpu_stats)): texts.append("{:.1f}%".format(self.cpu_stats[i].irq))
        max_width = self.blit_column("irq", texts, x, current_y, align="center", max_chars=5)
        x += x_step

        texts = []
        for i in range(len(self.cpu_stats)): texts.append("{:.1f}%".format(self.cpu_stats[i].softirq))
        max_width = self.blit_column("softirq", texts, x, current_y, align="center", max_chars=7)
        x += x_step

        texts = []
        for i in range(len(self.cpu_stats)): texts.append("{:.1f}%".format(self.cpu_stats[i].steal))
        max_width = self.blit_column("steal", texts, x, current_y, align="center", max_chars=5)
        x += x_step

        texts = []
        for i in range(len(self.cpu_stats)): texts.append("{}%".format(self.cpu_stats[i].guest))
        max_width = self.blit_column("guest", texts, x, current_y, align="center", max_chars=5)
        x += x_step

        texts = []
        for i in range(len(self.cpu_stats)): texts.append("{}%".format(self.cpu_stats[i].guest_nice))
        max_width = self.blit_column("guest nice", texts, x, current_y, align="center", max_chars=10)

        # MEMORY
        current_y += len(self.cpu_stats) * self.header_font.get_linesize() + self.line_buffer + 30
        self.image.blit(surf_memory_information_title, (self.screen_margin, current_y))

        # Memory usage graph
        surf_memory_usage = pygame.Surface((self.screen_width/2 - surf_memory_information_title.get_width() - column_spacer*2 - self.screen_margin, self.small_graph_height))
        surf_memory_usage.fill(self.bg_color)
        memory_usage_width = self.memory_info.percent / 100 * self.small_graph_width
        pygame.draw.rect(surf_memory_usage, self.bargraph_color, (0, 0, memory_usage_width, surf_memory_usage.get_height()))
        surf_memory_usage_text = self.default_font.render("{}%".format(self.memory_info.percent), True,
                                                          self.bargraph_text_color)
        surf_memory_usage.blit(surf_memory_usage_text, (surf_memory_usage.get_width() / 2 - surf_memory_usage_text.get_width() / 2,
                                                        surf_memory_usage.get_height() / 2 - surf_memory_usage_text.get_height() / 2))
        pygame.draw.rect(surf_memory_usage, self.bargraph_border_color,
                         (0, 0, surf_memory_usage.get_width(), surf_memory_usage.get_height()), 1)
        memory_usage_graph_x = surf_memory_information_title.get_width() + column_spacer + self.screen_margin
        self.image.blit(surf_memory_usage, (memory_usage_graph_x, current_y + self.header_font.get_height() / 2 - surf_memory_usage.get_height() / 2))

        surf_swap_information_title = self.header_font.render("Swap", True, self.fg_color, self.bg_color)
        self.image.blit(surf_swap_information_title, (self.screen_width/2, current_y))

        # Swap usage graph
        surf_swap_usage = pygame.Surface((self.screen_width/2 - surf_swap_information_title.get_width() - column_spacer*2 - self.screen_margin, self.small_graph_height))
        surf_swap_usage.fill(self.bg_color)
        swap_usage_width = self.memory_swap_info.percent / 100 * self.small_graph_width
        pygame.draw.rect(surf_swap_usage, self.bargraph_color,
                         (0, 0, swap_usage_width, surf_swap_usage.get_height()))
        surf_swap_usage_text = self.default_font.render("{}%".format(self.memory_swap_info.percent), True, self.bargraph_text_color)
        surf_swap_usage.blit(surf_swap_usage_text,
                             (surf_swap_usage.get_width() / 2 - surf_swap_usage_text.get_width() / 2,
                              surf_swap_usage.get_height() / 2 - surf_swap_usage_text.get_height() / 2))
        pygame.draw.rect(surf_swap_usage, self.bargraph_border_color,
                         (0, 0, surf_swap_usage.get_width(), surf_swap_usage.get_height()), 1)

        swap_usage_graph_x = self.screen_width/2 + surf_swap_information_title.get_width() + column_spacer
        self.image.blit(surf_swap_usage, (swap_usage_graph_x,
                                          current_y + self.header_font.get_height() / 2 - surf_swap_usage.get_height() / 2))

        current_y += self.header_font.get_height() / 2 - surf_swap_usage.get_height() / 2 + surf_swap_usage.get_height() + self.line_buffer_small

        surf = self.default_font.render("{} used / {} total / {} avail".format(
                    self.helper.convert_size(self.memory_info.used),
                    self.helper.convert_size(self.memory_info.total),
                    self.helper.convert_size(self.memory_info.available)
                ), True, self.fg_color, self.bg_color)

        self.image.blit(surf, (memory_usage_graph_x, current_y))

        surf = self.default_font.render("{} used / {} total / {} avail".format(
            self.helper.convert_size(self.memory_swap_info.used),
            self.helper.convert_size(self.memory_swap_info.total),
            self.helper.convert_size(self.memory_swap_info.free)
        ), True, self.fg_color, self.bg_color)
        self.image.blit(surf, (swap_usage_graph_x, current_y))

        current_y += self.line_buffer + surf.get_height()
        x = self.screen_margin
        x_step = (self.screen_width/2) / 3
        max_width = self.blit_column(None, ["active", "inactive"], x, current_y, align="left", max_chars=8)
        max_width += self.blit_column(None, [self.helper.convert_size(self.memory_info.active), self.helper.convert_size(self.memory_info.inactive)], x + max_width + column_spacer, current_y, align="left", max_chars=8)
        x += x_step
        max_width = self.blit_column(None, ["cached", "buffers"], x, current_y, align="left", max_chars=8)
        max_width += self.blit_column(None, [self.helper.convert_size(self.memory_info.cached), self.helper.convert_size(self.memory_info.buffers)], x + max_width + column_spacer, current_y, align="left", max_chars=8)
        x += x_step
        max_width = self.blit_column(None, ["shared", "slab"], x, current_y, align="left", max_chars=8)
        max_width += self.blit_column(None, [self.helper.convert_size(self.memory_info.shared), self.helper.convert_size(self.memory_info.slab)], x + max_width + column_spacer, current_y, align="left", max_chars=8)
        x += x_step

        x = self.screen_width/2
        max_width = self.blit_column(None, ["sin", "sout"], x, current_y, align="left", max_chars=8)
        max_width += self.blit_column(None, [self.helper.convert_size(self.memory_swap_info.sin), self.helper.convert_size(self.memory_swap_info.sout)], x + max_width + column_spacer, current_y, align="left", max_chars=8)

        current_y += self.default_font.get_linesize()*2 + self.line_buffer_small + self.line_buffer

        # DISKS
        self.image.blit(surf_disk_information_title, (self.screen_margin, current_y))
        pygame.draw.line(self.image, self.fg_color, (surf_disk_information_title.get_width() + column_spacer, current_y + surf_disk_information_title.get_height()/2),
                         (self.screen_width - column_spacer, current_y + surf_disk_information_title.get_height()/2))

        current_y += surf_disk_information_title.get_height() + self.line_buffer

        x = self.screen_margin
        texts = []
        for i in self.disk_mounts: texts.append(i.mountpoint)
        max_width = self.blit_column("Mount Point", texts, x, current_y, align="left", max_chars=8)

        x += max_width + column_spacer
        texts = []
        for i in self.disk_mounts: texts.append(i.device)
        max_width = self.blit_column("Device", texts, x, current_y, align="left", max_chars=8)

        x += max_width + column_spacer
        texts = []
        for i in self.disk_mounts: texts.append(i.fstype)
        max_width = self.blit_column("Type", texts, x, current_y, align="left", max_chars=8)

        x += max_width + column_spacer

        # % Used graphs
        y = self.header_font.get_linesize() + self.line_buffer_small
        # self.disk_usage.append({"mountpoint": i.mountpoint, "usage": psutil.disk_usage(i.mountpoint)})
        # sdiskusage(total=31207583744, used=2092957696, free=27812663296, percent=7.0)
        for i in self.disk_mounts:
            surf = pygame.Surface((self.small_graph_width_small, self.small_graph_height))
            surf.fill(self.bg_color)
            du = None
            for j in self.disk_usage:
                if j["mountpoint"] == i.mountpoint:
                    du = j["usage"]
                    break
            if du is not None:
                disk_usage_width = du.percent / 100 * self.small_graph_width_small

                pygame.draw.rect(surf, self.bargraph_color, (0, 0, disk_usage_width, surf.get_height()))
                surf_disk_usage_text = self.default_font.render("{}%".format(du.percent), True, self.bargraph_text_color)
                surf.blit(surf_disk_usage_text, (surf.get_width() / 2 - surf_disk_usage_text.get_width() / 2,
                                                 surf.get_height() / 2 - surf_disk_usage_text.get_height() / 2))
                pygame.draw.rect(surf, self.bargraph_border_color, (0, 0, surf.get_width(), surf.get_height()), 1)
                self.image.blit(surf, (x, current_y + y + 1))
                y += self.line_buffer_small + surf.get_height()

        x += self.small_graph_width_small + column_spacer
        texts = []
        for i in self.disk_mounts:
            for j in self.disk_usage:
                if j["mountpoint"] == i.mountpoint:
                    texts.append("{} used / {} total / {} avail".format(self.helper.convert_size(j["usage"].used), self.helper.convert_size(j["usage"].total), self.helper.convert_size(j["usage"].free)))
                    break
        max_width = self.blit_column("", texts, x, current_y, align="left", max_chars=8)

        tmp_current_y = current_y + (self.default_font.get_linesize() + self.line_buffer_small) * len(self.disk_mounts) + self.line_buffer + self.header_font.get_height() + self.line_buffer_small

        current_y = tmp_current_y + self.header_font.get_height() + self.line_buffer_small

        # DEVICES
        # disk_io_counters
        x = self.screen_margin
        x_step = self.screen_width / 10
        texts = []
        for i in self.disk_io_counters:
            if i[:4] == "loop" or i[:3] == "ram":
                continue
            texts.append(i)
        max_width = self.blit_column("Device", texts, x, current_y, align="left", max_chars=8)

        header_section_width = self.screen_width - max_width - x_step
        header_x_step = header_section_width / 4
        surf = self.header_font.render("Bytes", True, self.fg_color, self.bg_color)
        self.image.blit(surf, (max_width + header_x_step/2 - surf.get_width()/2, tmp_current_y))
        surf = self.header_font.render("Count", True, self.fg_color, self.bg_color)
        self.image.blit(surf, (max_width + header_x_step/2 - surf.get_width()/2 + header_x_step, tmp_current_y))
        surf = self.header_font.render("Merged Count", True, self.fg_color, self.bg_color)
        self.image.blit(surf, (max_width + header_x_step/2 - surf.get_width()/2 + header_x_step*2, tmp_current_y))
        surf = self.header_font.render("Time", True, self.fg_color, self.bg_color)
        self.image.blit(surf, (max_width + header_x_step/2 - surf.get_width()/2 + header_x_step*3, tmp_current_y))

        x += x_step
        texts = []
        for i in self.disk_io_counters:
            if i[:4] == "loop" or i[:3] == "ram":
                continue
            texts.append(self.helper.convert_size(self.disk_io_counters[i].read_bytes))
        max_width = self.blit_column("Read", texts, x, current_y, align="left", max_chars=8)

        x += x_step
        texts = []
        for i in self.disk_io_counters:
            if i[:4] == "loop" or i[:3] == "ram":
                continue
            texts.append(self.helper.convert_size(self.disk_io_counters[i].write_bytes))
        max_width = self.blit_column("Write", texts, x, current_y, align="left", max_chars=8)

        x += x_step
        texts = []
        for i in self.disk_io_counters:
            if i[:4] == "loop" or i[:3] == "ram":
                continue
            texts.append(str(self.disk_io_counters[i].read_count))
        max_width = self.blit_column("Read", texts, x, current_y, align="left", max_chars=8)

        x += x_step
        texts = []
        for i in self.disk_io_counters:
            if i[:4] == "loop" or i[:3] == "ram":
                continue
            texts.append(str(self.disk_io_counters[i].write_count))
        max_width = self.blit_column("Write", texts, x, current_y, align="left", max_chars=8)

        x += x_step
        texts = []
        for i in self.disk_io_counters:
            if i[:4] == "loop" or i[:3] == "ram":
                continue
            texts.append(str(self.disk_io_counters[i].read_merged_count))
        max_width = self.blit_column("Read", texts, x, current_y, align="left", max_chars=8)

        x += x_step
        texts = []
        for i in self.disk_io_counters:
            if i[:4] == "loop" or i[:3] == "ram":
                continue
            texts.append(str(self.disk_io_counters[i].write_merged_count))
        max_width = self.blit_column("Write", texts, x, current_y, align="left", max_chars=8)

        x += x_step
        texts = []
        for i in self.disk_io_counters:
            if i[:4] == "loop" or i[:3] == "ram":
                continue
            texts.append(str(self.disk_io_counters[i].read_time))
        max_width = self.blit_column("Read", texts, x, current_y, align="left", max_chars=8)

        x += x_step
        texts = []
        for i in self.disk_io_counters:
            if i[:4] == "loop" or i[:3] == "ram":
                continue
            texts.append(str(self.disk_io_counters[i].write_time))
        max_width = self.blit_column("Write", texts, x, current_y, align="left", max_chars=8)

        x += x_step
        texts = []
        for i in self.disk_io_counters:
            if i[:4] == "loop" or i[:3] == "ram":
                continue
            texts.append(str(self.disk_io_counters[i].busy_time))
        max_width = self.blit_column("Busy Time", texts, x, current_y, align="left", max_chars=8)

        current_y += len(texts)*(self.line_buffer_small + self.default_font.get_height()) + self.line_buffer_small*2 + self.header_font.get_height()*2

        # NETWORK
        self.image.blit(surf_network_information_title, (self.screen_margin, current_y))
        pygame.draw.line(self.image, self.fg_color, (surf_network_information_title.get_width() + column_spacer,
                                                     current_y + surf_network_information_title.get_height() / 2),
                         (self.screen_width - column_spacer, current_y + surf_network_information_title.get_height() / 2))

        current_y += surf_network_information_title.get_height() + self.line_buffer

        has_ipv6 = {}
        x = self.screen_margin
        texts = []
        for i in self.networking_nics:
            if i[:2] == "lo":
                continue
            texts.append(i)
            for j in self.networking_nics[i]:
                if j.family == socket.AddressFamily.AF_INET6:
                    if j.address != "":
                        texts.append("")
                        has_ipv6.update({i: True})

        max_width = self.blit_column("Device", texts, x, current_y, align="left", max_chars=8)

        x += max_width + column_spacer
        texts = []
        for i in self.networking_nics:
            if i[:2] == "lo":
                continue
            for j in self.networking_nics[i]:
                if j.family == socket.AddressFamily.AF_PACKET:
                    texts.append(j.address)
            if i in has_ipv6:
                texts.append("")
        max_width = self.blit_column("MAC Address", texts, x, current_y, align="left", max_chars=8)

        x += max_width + column_spacer
        ip_texts = []
        for i in self.networking_nics:
            if i[:2] == "lo":
                continue
            ipv4_address = ""
            ipv6_address = ""
            subnet_mask = ""
            for j in self.networking_nics[i]:
                if j.family == socket.AddressFamily.AF_INET:
                    ipv4_address = j.address
                    subnet_mask = self.helper.get_subnet_mask_bits(j.netmask)
                if j.family == socket.AddressFamily.AF_INET6:
                    ipv6_address = j.address
            if ipv4_address != "" and subnet_mask != "":
                ip_texts.append("{}/{}".format(ipv4_address, subnet_mask))
            else:
                ip_texts.append("")
            if ipv6_address != "":
                ip_texts.append("{}".format(ipv6_address))
            max_width = self.blit_column("IP Address", ip_texts, x, current_y, align="left", max_chars=8)

        x += max_width + column_spacer
        x_step = (self.screen_width - x - self.screen_margin) / 8

        texts = []
        for i in self.networking_nics:
            if i[:2] == "lo":
                continue
            if i in self.networking_nic_stats:
                texts.append(self.helper.convert_size(self.networking_nic_stats[i].bytes_sent))
                if i in has_ipv6:
                    texts.append("")

        max_width = self.blit_column("Sent", texts, x, current_y, align="left", max_chars=8)
        x += x_step
        texts = []
        for i in self.networking_nics:
            if i[:2] == "lo":
                continue
            if i in self.networking_nic_stats:
                texts.append(self.helper.convert_size(self.networking_nic_stats[i].bytes_recv))
                if i in has_ipv6:
                    texts.append("")
        max_width = self.blit_column("Recv", texts, x, current_y, align="left", max_chars=8)
        x += x_step
        texts = []
        for i in self.networking_nics:
            if i[:2] == "lo":
                continue
            if i in self.networking_nic_stats:
                texts.append(str(self.networking_nic_stats[i].packets_sent))
                if i in has_ipv6:
                    texts.append("")
        max_width = self.blit_column("Sent", texts, x, current_y, align="left", max_chars=8)
        x += x_step
        texts = []
        for i in self.networking_nics:
            if i[:2] == "lo":
                continue
            if i in self.networking_nic_stats:
                texts.append(str(self.networking_nic_stats[i].packets_recv))
                if i in has_ipv6:
                    texts.append("")
        max_width = self.blit_column("Recv", texts, x, current_y, align="left", max_chars=8)
        x += x_step
        texts = []
        for i in self.networking_nics:
            if i[:2] == "lo":
                continue
            if i in self.networking_nic_stats:
                texts.append(str(self.networking_nic_stats[i].errin))
                if i in has_ipv6:
                    texts.append("")
        max_width = self.blit_column("Err in", texts, x, current_y, align="left", max_chars=8)
        x += x_step
        texts = []
        for i in self.networking_nics:
            if i[:2] == "lo":
                continue
            if i in self.networking_nic_stats:
                texts.append(str(self.networking_nic_stats[i].errout))
                if i in has_ipv6:
                    texts.append("")
        max_width = self.blit_column("Err Out", texts, x, current_y, align="left", max_chars=8)
        x += x_step
        texts = []
        for i in self.networking_nics:
            if i[:2] == "lo":
                continue
            if i in self.networking_nic_stats:
                texts.append(str(self.networking_nic_stats[i].dropin))
                if i in has_ipv6:
                    texts.append("")
        max_width = self.blit_column("Drop in", texts, x, current_y, align="left", max_chars=8)
        x += x_step
        texts = []
        for i in self.networking_nics:
            if i[:2] == "lo":
                continue
            if i in self.networking_nic_stats:
                texts.append(str(self.networking_nic_stats[i].dropout))
                if i in has_ipv6:
                    texts.append("")
        max_width = self.blit_column("Drop Out", texts, x, current_y, align="left", max_chars=8)

    def blit_column(self, header_text, texts, start_x, start_y, max_chars, all_headers=False, align="left"):
        max_width = 0
        y = 0
        align_txt = "{:^" + str(max_chars) + "}"
        header_surf = None
        if header_text is not None:
            if align == "center":
                header_surf = self.header_font.render(align_txt.format(header_text), True, self.fg_color, self.bg_color)
            else:
                header_surf = self.header_font.render(header_text, True, self.fg_color, self.bg_color)

            self.image.blit(header_surf, (start_x, start_y + y))
            y += self.header_font.get_linesize() + self.line_buffer_small
            if max_width < header_surf.get_width():
                max_width = header_surf.get_width()

        for i in range(len(texts)):
            if all_headers:
                surf = self.header_font.render(texts[i], True, self.fg_color, self.bg_color)
            else:
                surf = self.default_font.render(texts[i], True, self.fg_color, self.bg_color)

            if max_width < surf.get_width():
                max_width = surf.get_width()

            if align == "center" and header_surf is not None:
                x = start_x + (header_surf.get_width()/2 - surf.get_width()/2)
            elif align == "left":
                x = start_x
            else:
                x = start_x
            self.image.blit(surf, (x, start_y + y))
            if all_headers:
                y += self.header_font.get_linesize() + self.line_buffer_small
            else:
                y += self.default_font.get_linesize() + self.line_buffer_small

        return max_width

    def update(self, tick, fps):
        if self.info_updated:
            self.image.fill(self.bg_color)
            self.update_image()
            self.update_image_light()
            self.info_updated = False
            self.info_updated_light = False
        elif self.info_updated_light:
            self.update_image_light()
            self.info_updated_light = False

        if tick == 1:
            if self.timer == self.update_interval:
                print("UPDATE--------------")
                self.update_systeminfo()
                self.timer = 0
            print("UPDATE LIGHT--------------")
            self.update_systeminfo_light()
            self.timer += 1
        else:
            self.canvas.blit(self.image, (0, 0))

    def update_systeminfo(self):
        if not self.in_systeminfo_thread:
            thread_timer = threading.Thread(target=self.update_systeminfo_thread, args=([]))
            thread_timer.daemon = False
            thread_timer.start()

    def update_systeminfo_thread(self):
        self.in_systeminfo_thread = True
        self.get_info()
        self.info_updated = True
        self.in_systeminfo_thread = False

    def update_systeminfo_light(self):
        if not self.in_systeminfo_light_thread:
            thread_timer = threading.Thread(target=self.update_systeminfo_light_thread, args=([]))
            thread_timer.daemon = False
            thread_timer.start()

    def update_systeminfo_light_thread(self):
        self.in_systeminfo_light_thread = True
        self.get_info_light()
        self.info_updated_light = True
        self.in_systeminfo_light_thread = False
