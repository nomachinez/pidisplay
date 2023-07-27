import json
import os
import re
import subprocess
import threading
import time
from datetime import datetime, timedelta

import pygame
import requests

from lib.fullscreen_plugin import FullScreenPlugin
from lib.plugin import Singleton


class PiHole(FullScreenPlugin, metaclass=Singleton):
    """ PiHole Display """
    def __init__(self, helper, canvas, app_plugin_config):
        FullScreenPlugin.__init__(self, helper, canvas, os.path.abspath(os.path.dirname(__file__)), app_plugin_config)
        self.update_interval = self.plugin_config.getint("update_interval")
        self.server = self.plugin_config["pihole_server_ip"]
        self.api_type = self.plugin_config["api"]
        if self.api_type != "http" and self.api_type != "telnet" and self.api_type != "ssh":
            self.helper.log(self.debug, "Got a bad API Type value: {}".format(self.api_type))
            self.api_type = "telnet"
        self.api_key = self.plugin_config["api_key"]
        self.ssh_user = self.plugin_config["ssh_user"]
        self.pihole_server_telnet_port = self.plugin_config["pihole_server_telnet_port"]
        self.pihole_server_ssh_port = self.plugin_config["pihole_server_ssh_port"]
        self.pihole_server_http_port = self.plugin_config.getint("pihole_server_http_port")

        font_str = self.plugin_config["font_face"]
        if font_str[-4:].lower() == ".ttf":
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

        self.bg_color = eval(self.plugin_config["background"])
        self.fg_color = eval(self.plugin_config["foreground"])
        self.recently_blocked_bg_color = eval(self.plugin_config["recently_blocked_bg_color"])

        self.status_orb_online_color = eval(self.plugin_config["status_orb_online_color"])
        self.status_orb_offline_color = eval(self.plugin_config["status_orb_offline_color"])
        self.bargraph_bg_color = eval(self.plugin_config["bargraph_bg_color"])
        self.bargraph_border_color = eval(self.plugin_config["bargraph_border_color"])
        self.bargraph_bar_color = eval(self.plugin_config["bargraph_bar_color"])
        self.bargraph_header_fg_color = eval(self.plugin_config["bargraph_header_fg_color"])
        self.bargraph_value_fg_color = eval(self.plugin_config["bargraph_value_fg_color"])

        self.screen_margin = self.plugin_config.getint("screen_margin")

        self.num_history = 5
        self.recently_blocked_num_history = 10
        self.timer = -1
        self.pihole_updated = False

        self.pihole_status = {}

        self.privacy_descriptions = {
            "0": "Show everything",
            "1": "Hide domains only",
            "2": "Hide domains and clients",
            "3": "Anonymous"
        }
        self.privacy_colors = {
            "0": (200, 0, 0),
            "1": (255, 127, 80),
            "2": (255, 192, 0),
            "3": (50, 205, 50)
        }
        self.timer_bar_color = eval(self.plugin_config["timer_bar_color"])
        self.timer_bar_height = self.plugin_config.getint("timer_bar_height")
        self.timer_bar_width = 0
        self.ratio = self.screen_width * 1.0 / (self.update_interval * 1000)
        self.timer_bar_y = self.screen_height - self.timer_bar_height
        self.image = self.canvas.copy()

    def update(self, tick, fps):
        if int(time.time() * 1000) - self.timer > self.update_interval * 1000:
            self.get_pihole_data()
            self.timer = int(time.time() * 1000)

        if self.pihole_updated:
            self.update_pihole_surface()
            self.pihole_updated = False

        if self.image is not None:
            self.canvas.blit(self.image, (0, 0))
            self.draw_timer_bar()

    def update_pihole_surface(self):
        x_spacer = 10
        x_spacer_small = 3
        y_spacer = 10
        y_spacer_small = 2

        current_y = self.screen_margin
        self.image.fill(self.bg_color)

        # HOSTNAME
        surf_hostname_header = self.default_font.render("Pi-Hole Host: ", True, self.fg_color, self.bg_color)
        surf_hostname = self.header_font.render(self.server, True, self.fg_color, self.bg_color)

        current_x = self.screen_margin
        self.image.blit(surf_hostname_header, (current_x, current_y))
        current_x += surf_hostname_header.get_width()
        self.image.blit(surf_hostname, (current_x, current_y))
        current_x += surf_hostname.get_width() + x_spacer

        # STATUS LIGHT
        if self.pihole_status["summary"]["status"] == "enabled":
            color = self.status_orb_online_color
        else:
            color = self.status_orb_offline_color

        circle_rect = pygame.draw.circle(self.image, color,
                                         (current_x + int(surf_hostname_header.get_height() / 2), current_y + int(surf_hostname_header.get_height() / 2)),
                                         int(surf_hostname_header.get_height() / 2))

        current_x += circle_rect.width + x_spacer

        # =======================================
        # RECENTLY BLOCKED SECTION

        surf_recently_blocked_header = self.header_font.render("Recently blocked", True, self.fg_color, self.recently_blocked_bg_color)
        blocked = []
        blocked_widest = surf_recently_blocked_header.get_width()
        blocked_height = surf_recently_blocked_header.get_height() + y_spacer*2
        recently_blocked = set(self.pihole_status["recently_blocked"])
        for i in recently_blocked:
            surf = self.default_font.render(i, True, self.fg_color, self.recently_blocked_bg_color)
            self.helper.log(self.debug, "PiHole: RecentlyBlocked text: '{}', width: {} widest: {}".format(i, surf.get_width(), blocked_widest))
            if blocked_widest < surf.get_width():
                blocked_widest = surf.get_width()
            blocked_height += surf.get_height() + y_spacer_small
            blocked.append(surf)

        blocked_height += y_spacer
        surf_blocked = pygame.Surface((blocked_widest + x_spacer*2, blocked_height))
        surf_blocked.fill(self.recently_blocked_bg_color)
        pygame.draw.rect(surf_blocked, self.fg_color, (0, 0, surf_blocked.get_width(), surf_blocked.get_height()), 1)
        y = y_spacer
        surf_blocked.blit(surf_recently_blocked_header, (surf_blocked.get_width()/2 - surf_recently_blocked_header.get_width()/2, y))
        y += surf_recently_blocked_header.get_height() + y_spacer
        for i in blocked:
            surf_blocked.blit(i, (x_spacer, y))
            y += i.get_height() + y_spacer_small

        self.image.blit(surf_blocked, (self.screen_width - self.screen_margin - surf_blocked.get_width(), current_y))

        recently_blocked_width = surf_blocked.get_width()

        top_clients_start_y = current_y + surf_blocked.get_height() + y_spacer

        del surf_recently_blocked_header, surf_blocked

        # ===================================================

        # ====================================================
        # TOP CLIENTS
        surf_top_clients_header = self.header_font.render("Top clients", True, self.fg_color, self.bg_color)

        widest_surf_title = 0
        counts = {}
        for i in self.pihole_status["top_clients"]:
            txt = i.split("|", 2)
            txt = txt[0]
            if txt not in counts:
                counts.update({txt: 1})
            else:
                counts[txt] += 1

        surfs_titles = []
        for i in counts:
            surf = self.default_font.render(i, True, self.fg_color, self.bg_color)
            surfs_titles.append(surf)
            if widest_surf_title < surf.get_width():
                widest_surf_title = surf.get_width()

        widest_surf_value = 0
        surfs_values = []
        for i in counts:
            surf = self.default_font.render(str(counts[i]), True, self.fg_color, self.bg_color)
            surfs_values.append(surf)
            if widest_surf_value < surf.get_width():
                widest_surf_value = surf.get_width()

        top_clients_width = widest_surf_title + widest_surf_value + x_spacer
        top_clients_start_x = self.screen_width - self.screen_margin - recently_blocked_width + (recently_blocked_width/2 - top_clients_width/2)
        self.image.blit(surf_top_clients_header, (top_clients_start_x + top_clients_width/2 - surf_top_clients_header.get_width()/2, top_clients_start_y))

        y = top_clients_start_y + surf_top_clients_header.get_height() + y_spacer_small
        for i in surfs_titles:
            self.image.blit(i, (top_clients_start_x, y))
            y += i.get_height() + y_spacer_small

        y = top_clients_start_y + surf_top_clients_header.get_height() + y_spacer_small
        for i in surfs_values:
            self.image.blit(i, (top_clients_start_x + widest_surf_title + x_spacer, y))
            y += i.get_height() + y_spacer_small

        top_clients_bottom_y = y

        # ==================================

        if recently_blocked_width > top_clients_width:
            right_column_width = recently_blocked_width
        else:
            right_column_width = top_clients_width

        # ========================================
        # PRIVACY MODE
        privacy_level = str(self.pihole_status["summary"]["privacy_level"])
        if privacy_level in ["0", "1", "2", "3"]:
            surf_privacy_mode = self.default_font.render("Privacy mode: {}".format(self.privacy_descriptions[privacy_level]), True, self.privacy_colors[privacy_level])
            privacy_level_x_start = (self.screen_width - self.screen_margin - right_column_width - current_x - surf_privacy_mode.get_width())/2 + current_x
            self.image.blit(surf_privacy_mode, (privacy_level_x_start, current_y)) # TODO: HACK

        current_y += surf_hostname_header.get_height() + y_spacer

        # =============================
        # TODAY STATS
        top_width = self.screen_width - self.screen_margin*2 - right_column_width - x_spacer

        try:
            float_val = float(self.pihole_status["summary"]["ads_percentage_today"])
        except ValueError:
            float_val = -1.0

        surf1 = self.default_font.render("Today: {} ads blocked with {} total DNS queries ({:.1f}%)"
                                         .format(self.pihole_status["summary"]["ads_blocked_today"],
                                                 self.pihole_status["summary"]["dns_queries_today"],
                                                 float_val), True, self.fg_color, self.bg_color)

        self.image.blit(surf1, (self.screen_margin, current_y))

        # =========================================

        current_y += surf1.get_height() + y_spacer

        del surf1

        current_x = self.screen_margin

        # ====================================================================
        # DNS RESPONSE GRAPH
        surf_dns_response_source_graph = self.build_dns_response_source_graph(self.screen_width - self.screen_margin*2 - right_column_width - x_spacer,
                                                                              self.header_font.get_linesize(), x_spacer, y_spacer)
        self.image.blit(surf_dns_response_source_graph, (current_x, current_y))

        current_y += surf_dns_response_source_graph.get_height() + y_spacer

        surf_summary_title = self.header_font.render("Summary", True, self.fg_color, self.bg_color)
        self.image.blit(surf_summary_title, (current_x, current_y))

        pygame.draw.line(self.image, self.fg_color, (self.screen_margin + surf_summary_title.get_width() + x_spacer, current_y + surf_summary_title.get_height() / 2),
                                                    (self.screen_width - x_spacer - right_column_width - self.screen_margin, current_y + surf_summary_title.get_height() / 2))
        current_x = self.screen_margin
        current_y += surf_summary_title.get_height() + y_spacer

        del surf_summary_title, surf_dns_response_source_graph

        total_width = self.screen_width - x_spacer - right_column_width - self.screen_margin*2

        # COL 1
        surf_label1 = self.default_font.render("Unique clients: ", True, self.fg_color, self.bg_color)
        surf_label2 = self.default_font.render("Unique domains: ", True, self.fg_color, self.bg_color)
        surf_label3 = self.default_font.render("Queries cached: ", True, self.fg_color, self.bg_color)
        surf_label4 = self.default_font.render("Queries forwarded: ", True, self.fg_color, self.bg_color)

        widest_label = surf_label1.get_width()
        if widest_label < surf_label2.get_width():
            widest_label = surf_label2.get_width()
        if widest_label < surf_label3.get_width():
            widest_label = surf_label3.get_width()
        if widest_label < surf_label4.get_width():
            widest_label = surf_label4.get_width()

        surf_val1 = self.default_font.render("{}".format(self.pihole_status["summary"]["unique_clients"]), True, self.fg_color, self.bg_color)
        surf_val2 = self.default_font.render("{}".format(self.pihole_status["summary"]["unique_domains"]), True, self.fg_color, self.bg_color)
        surf_val3 = self.default_font.render("{}".format(self.pihole_status["summary"]["queries_cached"]), True, self.fg_color, self.bg_color)
        surf_val4 = self.default_font.render("{}".format(self.pihole_status["summary"]["queries_forwarded"]), True, self.fg_color, self.bg_color)

        widest_val = surf_val1.get_width()
        if widest_val < surf_val2.get_width():
            widest_val = surf_val2.get_width()
        if widest_val < surf_val3.get_width():
            widest_val = surf_val3.get_width()
        if widest_val < surf_val4.get_width():
            widest_val = surf_val4.get_width()

        self.image.blit(surf_label1, (current_x, current_y))
        self.image.blit(surf_label2, (current_x, current_y + (surf_label1.get_height() + y_spacer_small)))
        self.image.blit(surf_label3, (current_x, current_y + (surf_label2.get_height() + y_spacer_small)*2))
        self.image.blit(surf_label4, (current_x, current_y + (surf_label3.get_height() + y_spacer_small)*3))

        current_x += widest_label + x_spacer_small
        self.image.blit(surf_val1, (current_x, current_y))
        self.image.blit(surf_val2, (current_x, current_y + (surf_val1.get_height() + y_spacer_small)))
        self.image.blit(surf_val3, (current_x, current_y + (surf_val2.get_height() + y_spacer_small)*2))
        self.image.blit(surf_val4, (current_x, current_y + (surf_val3.get_height() + y_spacer_small)*3))

        col1_width = widest_label + x_spacer_small + widest_val
        del surf_label1, surf_label2, surf_label3, surf_label4, surf_val1, surf_val2, surf_val3, surf_val4, widest_label, widest_val

        # COL 3
        surf_label1 = self.default_font.render("CNAME replies: ", True, self.fg_color, self.bg_color)
        surf_label2 = self.default_font.render("IP replies: ", True, self.fg_color, self.bg_color)
        surf_label3 = self.default_font.render("NODATA replies: ", True, self.fg_color, self.bg_color)
        surf_label4 = self.default_font.render("NXDOMAIN replies: ", True, self.fg_color, self.bg_color)

        widest_label = surf_label1.get_width()
        if widest_label < surf_label2.get_width():
            widest_label = surf_label2.get_width()
        if widest_label < surf_label3.get_width():
            widest_label = surf_label3.get_width()
        if widest_label < surf_label4.get_width():
            widest_label = surf_label4.get_width()

        surf_val1 = self.default_font.render("{}".format(self.pihole_status["summary"]["reply_CNAME"]), True, self.fg_color, self.bg_color)
        surf_val2 = self.default_font.render("{}".format(self.pihole_status["summary"]["reply_IP"]), True, self.fg_color, self.bg_color)
        surf_val3 = self.default_font.render("{}".format(self.pihole_status["summary"]["reply_NODATA"]), True, self.fg_color, self.bg_color)
        surf_val4 = self.default_font.render("{}".format(self.pihole_status["summary"]["reply_NXDOMAIN"]), True, self.fg_color, self.bg_color)

        widest_val = surf_val1.get_width()
        if widest_val < surf_val2.get_width():
            widest_val = surf_val2.get_width()
        if widest_val < surf_val3.get_width():
            widest_val = surf_val3.get_width()
        if widest_val < surf_val4.get_width():
            widest_val = surf_val4.get_width()

        current_x = self.screen_margin + total_width - (widest_label + x_spacer_small + widest_val)
        self.image.blit(surf_label1, (current_x, current_y))
        self.image.blit(surf_label2, (current_x, current_y + (surf_label1.get_height() + y_spacer_small)))
        self.image.blit(surf_label3, (current_x, current_y + (surf_label2.get_height() + y_spacer_small)*2))
        self.image.blit(surf_label4, (current_x, current_y + (surf_label3.get_height() + y_spacer_small)*3))

        current_x += widest_label + x_spacer_small
        self.image.blit(surf_val1, (current_x, current_y))
        self.image.blit(surf_val2, (current_x, current_y + (surf_val1.get_height() + y_spacer_small)))
        self.image.blit(surf_val3, (current_x, current_y + (surf_val2.get_height() + y_spacer_small)*2))
        self.image.blit(surf_val4, (current_x, current_y + (surf_val3.get_height() + y_spacer_small)*3))

        col3_width = widest_label + x_spacer_small + widest_val
        del surf_label1, surf_label2, surf_label3, surf_label4, surf_val1, surf_val2, surf_val3, surf_val4, widest_label, widest_val

        # COL 2
        surf_label1 = self.default_font.render("Clients ever: ", True, self.fg_color, self.bg_color)
        surf_label2 = self.default_font.render("DNS queries: ", True, self.fg_color, self.bg_color)
        surf_label3 = self.default_font.render(" ", True, self.fg_color, self.bg_color)
        surf_label4 = self.default_font.render("# Domains blocked: ", True, self.fg_color, self.bg_color)

        widest_label = surf_label1.get_width()
        if widest_label < surf_label2.get_width():
            widest_label = surf_label2.get_width()
        if widest_label < surf_label3.get_width():
            widest_label = surf_label3.get_width()
        if widest_label < surf_label4.get_width():
            widest_label = surf_label4.get_width()

        surf_val1 = self.default_font.render("{}".format(self.pihole_status["summary"]["clients_ever_seen"]), True, self.fg_color, self.bg_color)
        surf_val2 = self.default_font.render("{}".format(self.pihole_status["summary"]["dns_queries_all_types"]), True, self.fg_color, self.bg_color)
        surf_val3 = self.default_font.render(" ", True, self.fg_color, self.bg_color)
        surf_val4 = self.default_font.render("{}".format(self.pihole_status["summary"]["domains_being_blocked"]), True, self.fg_color, self.bg_color)

        widest_val = surf_val1.get_width()
        if widest_val < surf_val2.get_width():
            widest_val = surf_val2.get_width()
        if widest_val < surf_val3.get_width():
            widest_val = surf_val3.get_width()
        if widest_val < surf_val4.get_width():
            widest_val = surf_val4.get_width()

        col2_width = widest_label + x_spacer_small + widest_val
        second_column_start = (total_width - (col1_width + col2_width + col3_width))/2 + self.screen_margin + col1_width
        current_x = second_column_start

        self.image.blit(surf_label1, (current_x, current_y))
        self.image.blit(surf_label2, (current_x, current_y + (surf_label1.get_height() + y_spacer_small)))
        self.image.blit(surf_label3, (current_x, current_y + (surf_label2.get_height() + y_spacer_small)*2))
        self.image.blit(surf_label4, (current_x, current_y + (surf_label3.get_height() + y_spacer_small)*3))

        current_x += widest_label + x_spacer_small

        self.image.blit(surf_val1, (current_x, current_y))
        self.image.blit(surf_val2, (current_x, current_y + (surf_val1.get_height() + y_spacer_small)))
        self.image.blit(surf_val3, (current_x, current_y + (surf_val2.get_height() + y_spacer_small)*2))
        self.image.blit(surf_val4, (current_x, current_y + (surf_val3.get_height() + y_spacer_small)*3))

        del surf_label1, surf_label2, surf_label3, surf_label4, surf_val1, surf_val2, surf_val3, surf_val4

        current_y += 4*self.default_font.get_height() + y_spacer_small*3 + y_spacer + y_spacer_small

        current_x = self.screen_margin

        # TOP STUFF
        surf_top_title = self.header_font.render("Leaderboard", True, self.fg_color, self.bg_color)
        self.image.blit(surf_top_title, (current_x, current_y))

        pygame.draw.line(self.image, self.fg_color, (self.screen_margin + surf_top_title.get_width() + x_spacer, current_y + surf_top_title.get_height() / 2),
                                                    (self.screen_width - x_spacer - right_column_width - self.screen_margin, current_y + surf_top_title.get_height() / 2))

        current_y += surf_top_title.get_height() + y_spacer
        del surf_top_title

        # ================================================================
        # TOP ADS SURFACES

        # top_ads_height = 0
        widest_top_ads_surf_domains = 0
        surfs_top_ads_domains = []
        widest_top_ads_surf_val = 0
        surfs_top_ads_values = []
        for i in self.pihole_status["top_items"]["top_ads"]:
            surf_domain = self.default_font.render(i, True, self.fg_color, self.bg_color)
            surfs_top_ads_domains.append(surf_domain)
            if widest_top_ads_surf_domains < surf_domain.get_width():
                widest_top_ads_surf_domains = surf_domain.get_width()

            surf_value = self.default_font.render(str(self.pihole_status["top_items"]["top_ads"][i]), True, self.fg_color, self.bg_color)
            surfs_top_ads_values.append(surf_value)
            if widest_top_ads_surf_val < surf_value.get_width():
                widest_top_ads_surf_val = surf_value.get_width()

        # TOP QUERIES SURFACES
        # top_queries_height = 0
        widest_top_queries_title_surf = 0
        top_queries_titles = []
        widest_top_queries_values_surf = 0
        top_queries_values = []
        for i in self.pihole_status["top_items"]["top_queries"]:
            surf_query = self.default_font.render(i, True, self.fg_color, self.bg_color)
            top_queries_titles.append(surf_query)
            if widest_top_queries_title_surf < surf_query.get_width():
                widest_top_queries_title_surf = surf_query.get_width()

            surf_value = self.default_font.render(str(self.pihole_status["top_items"]["top_queries"][i]), True, self.fg_color, self.bg_color)
            top_queries_values.append(surf_value)
            if widest_top_queries_values_surf < surf_value.get_width():
                widest_top_queries_values_surf = surf_value.get_width()

        top_ads_width_total = widest_top_ads_surf_domains + x_spacer + widest_top_ads_surf_val
        top_queries_width_total = widest_top_queries_title_surf + x_spacer + widest_top_queries_values_surf

        col_space_x = (top_width - top_ads_width_total - top_queries_width_total)/3

        # Now blit them both
        # BLIT TOP ADS
        surf_top_ads = self.header_font.render("Top ads", True, self.fg_color, self.bg_color)
        self.image.blit(surf_top_ads, (self.screen_margin + col_space_x + (top_ads_width_total/2 - surf_top_ads.get_width()/2), current_y))
        top_ads_start_x = self.screen_margin + col_space_x
        y = current_y + surf_top_ads.get_height() + y_spacer_small
        for i in surfs_top_ads_domains:
            self.image.blit(i, (top_ads_start_x, y))
            y += i.get_height() + y_spacer_small

        y = current_y + surf_top_ads.get_height() + y_spacer_small
        for i in surfs_top_ads_values:
            self.image.blit(i, (top_ads_start_x + widest_top_ads_surf_domains + x_spacer, y))
            y += i.get_height() + y_spacer_small

        top_ads_bottom_y = y

        # BLIT TOP QUERIES
        surf_top_queries = self.header_font.render("Top queries", True, self.fg_color, self.bg_color)
        self.image.blit(surf_top_queries, (self.screen_margin + col_space_x*2 + top_ads_width_total + (top_ads_width_total/2 - surf_top_ads.get_width()/2), current_y))

        # BLIT
        top_queries_start_x = self.screen_margin + col_space_x*2 + top_ads_width_total
        y = current_y + surf_top_queries.get_height() + y_spacer_small
        for i in top_queries_titles:
            self.image.blit(i, (top_queries_start_x, y))
            y += i.get_height() + y_spacer_small

        y = current_y + surf_top_queries.get_height() + y_spacer_small
        for i in top_queries_values:
            self.image.blit(i, (top_queries_start_x + widest_top_queries_title_surf + x_spacer, y))
            y += i.get_height() + y_spacer_small

        top_queries_bottom_y = y

        # ============================================
        # GRAPHS

        now = datetime.now()
        now_fmt = now.strftime("%-I%p")
        now_minus_one_fmt = (now - timedelta(hours=1)).strftime("%-I%p")
        now_minus_two_fmt = (now - timedelta(hours=2)).strftime("%-I%p")
        now_minus_three_fmt = (now - timedelta(hours=3)).strftime("%-I%p")

        current_y = top_queries_bottom_y
        if current_y < top_ads_bottom_y:
            current_y = top_ads_bottom_y
        if current_y < top_clients_bottom_y:
            current_y = top_clients_bottom_y

        current_y += y_spacer

        end_datetime = datetime.now()
        start_datetime = end_datetime - timedelta(hours=1)
        sum_ads_hour0 = 0
        for i in self.pihole_status["ads_over_time"]:
            if start_datetime.timestamp() <= int(i) < end_datetime.timestamp():
                sum_ads_hour0 += int(self.pihole_status["ads_over_time"][i])

        end_datetime = start_datetime
        start_datetime = end_datetime - timedelta(hours=2)
        sum_ads_hour1 = 0
        for i in self.pihole_status["ads_over_time"]:
            if start_datetime.timestamp() <= int(i) < end_datetime.timestamp():
                sum_ads_hour1 += int(self.pihole_status["ads_over_time"][i])

        end_datetime = start_datetime
        start_datetime = end_datetime - timedelta(hours=3)
        sum_ads_hour2 = 0
        for i in self.pihole_status["ads_over_time"]:
            if start_datetime.timestamp() <= int(i) < end_datetime.timestamp():
                sum_ads_hour2 += int(self.pihole_status["ads_over_time"][i])

        end_datetime = start_datetime
        start_datetime = end_datetime - timedelta(hours=4)
        sum_ads_hour3 = 0
        for i in self.pihole_status["ads_over_time"]:
            if start_datetime.timestamp() <= int(i) < end_datetime.timestamp():
                sum_ads_hour3 += int(self.pihole_status["ads_over_time"][i])

        self.helper.log(self.debug, "ADS: {}-{}-{}-{}".format(sum_ads_hour0, sum_ads_hour1, sum_ads_hour2, sum_ads_hour3))
        ads_bargraph = self.build_bargraph((self.screen_width - self.screen_margin*2)/2 - x_spacer_small,
                                           self.screen_height - self.screen_margin - current_y,
                                           [{now_fmt: sum_ads_hour0}, {now_minus_one_fmt: sum_ads_hour1}, {now_minus_two_fmt: sum_ads_hour2}, {now_minus_three_fmt: sum_ads_hour3}],
                                           "Ads Blocked by Hour")
        current_x = self.screen_margin
        self.image.blit(ads_bargraph, (current_x, current_y))

        del ads_bargraph, sum_ads_hour0, sum_ads_hour1, sum_ads_hour2, sum_ads_hour3, start_datetime, end_datetime

        end_datetime = datetime.now()
        start_datetime = end_datetime - timedelta(hours=1)
        sum_domains_hour0 = 0
        for i in self.pihole_status["domains_over_time"]:
            if start_datetime.timestamp() <= int(i) < end_datetime.timestamp():
                sum_domains_hour0 += int(self.pihole_status["domains_over_time"][i])

        end_datetime = start_datetime
        start_datetime = end_datetime - timedelta(hours=2)
        sum_domains_hour1 = 0
        for i in self.pihole_status["domains_over_time"]:
            if start_datetime.timestamp() <= int(i) < end_datetime.timestamp():
                sum_domains_hour1 += int(self.pihole_status["domains_over_time"][i])

        end_datetime = start_datetime
        start_datetime = end_datetime - timedelta(hours=3)
        sum_domains_hour2 = 0
        for i in self.pihole_status["domains_over_time"]:
            if start_datetime.timestamp() <= int(i) < end_datetime.timestamp():
                sum_domains_hour2 += int(self.pihole_status["domains_over_time"][i])

        end_datetime = start_datetime
        start_datetime = end_datetime - timedelta(hours=4)
        sum_domains_hour3 = 0
        for i in self.pihole_status["domains_over_time"]:
            if start_datetime.timestamp() <= int(i) < end_datetime.timestamp():
                sum_domains_hour3 += int(self.pihole_status["domains_over_time"][i])

        self.helper.log(self.debug, "DOMAINS: {}-{}-{}-{}".format(sum_domains_hour0, sum_domains_hour1, sum_domains_hour2, sum_domains_hour3))

        domains_bargraph = self.build_bargraph((self.screen_width - self.screen_margin*2)/2 - x_spacer_small,
                                               self.screen_height - self.screen_margin - current_y,
                                               [{now_fmt: sum_domains_hour0}, {now_minus_one_fmt: sum_domains_hour1}, {now_minus_two_fmt: sum_domains_hour2}, {now_minus_three_fmt: sum_domains_hour3}],
                                               "Domains Blocked by Hour")
        current_x += (self.screen_width - self.screen_margin*2)/2 - x_spacer_small + x_spacer_small
        self.image.blit(domains_bargraph, (current_x, current_y))

        del domains_bargraph, sum_domains_hour0, sum_domains_hour1, sum_domains_hour2, sum_domains_hour3, start_datetime, end_datetime

    def draw_timer_bar(self):
        self.timer_bar_width = ((self.update_interval * 1000) - (int(time.time() * 1000) - self.timer)) * self.ratio
        pygame.draw.rect(self.canvas, self.timer_bar_color, (0, self.timer_bar_y, self.timer_bar_width, self.timer_bar_height))

    def build_bargraph(self, graph_width, graph_height, values, title):

        self.helper.log(self.debug, "WxH = {}x{}".format(graph_width, graph_height))
        x_spacer = 10
        margin = 10
        bar_width = (graph_width - margin*2 - (len(values)-1)*x_spacer) / len(values)
        y_spacer = 4

        surf = pygame.Surface((graph_width, graph_height))
        surf.fill(self.bargraph_bg_color)
        pygame.draw.rect(surf, self.bargraph_border_color, (0, 0, surf.get_width(), surf.get_height()), 1)

        max_val = 0
        for i in values:
            val = list(i.values())[0]
            if max_val < val:
                max_val = val

        surf_title = self.header_font.render(title, True, self.bargraph_header_fg_color)

        max_bar_height = graph_height - margin*2 - self.default_font.get_height() - surf_title.get_height() - y_spacer
        if max_val > 0:
            ratio = max_bar_height / max_val
        else:
            ratio = 0

        surf.blit(surf_title, ((graph_width - margin*2)/2 - surf_title.get_width()/2, margin/2))
        # Everything is going to be relative to max_bar_height
        x = margin
        for i in values:
            key = list(i.keys())[0]
            val = list(i.values())[0]
            bar_height = ratio * val

            surf_x_header = self.default_font.render(key, True, self.bargraph_header_fg_color)
            surf.blit(surf_x_header, (x + (bar_width / 2 - surf_x_header.get_width() / 2), graph_height - margin - surf_x_header.get_height()))

            surf_val = self.default_font.render(str(val), True, self.bargraph_value_fg_color)

            bar_y = max_bar_height - bar_height + margin + surf_title.get_height() + y_spacer
            pygame.draw.rect(surf, self.bargraph_bar_color, (x, bar_y, bar_width, bar_height))

            if bar_height < surf_val.get_height():
                bar_y = max_bar_height - surf_val.get_height() + margin + surf_title.get_height() + y_spacer

            surf.blit(surf_val, (x + (bar_width/2 - surf_val.get_width()/2), bar_y))

            x += bar_width + x_spacer

        return surf

    def build_dns_response_source_graph(self, width, height, x_spacer, y_spacer):
        blacklist_color = (164, 125, 248)
        cache_color = (163, 172, 223)
        start_color = pygame.Vector3(64, 128, 64)
        end_color = pygame.Vector3(128, 200, 128)

        steps = len(self.pihole_status["forward_destinations"]) - 1
        step = 1.0 / (steps + 1)
        lerp_value = step
        colors = []

        for i in self.pihole_status["forward_destinations"]:
            if i == "blocklist|blocklist":
                colors.append({"name": i, "percent": self.pihole_status["forward_destinations"][i], "color": blacklist_color})
            elif i == "cache|cache":
                colors.append({"name": i, "percent": self.pihole_status["forward_destinations"][i], "color": cache_color})
            else:
                my_start_color = start_color.lerp(end_color, lerp_value)
                colors.append({"name": i, "percent": self.pihole_status["forward_destinations"][i], "color": my_start_color})
                lerp_value += step

        surf = pygame.Surface((width, height + self.default_font.get_linesize() + y_spacer))
        x = 0
        labels = []
        for i in colors:
            try:
                float_val = float(i["percent"])
            except ValueError:
                float_val = -1.0

            w = width * (float_val/100)
            pygame.draw.rect(surf, i["color"], (x, 0, w, height))

            rect = pygame.Surface((height, height))
            rect.fill(i["color"])
            labels.append(rect)
            label = i["name"]
            if "|" in label:
                label = label.split("|", 2)[1]
            if "#" in label:
                label = label.split("#", 2)[0]

            surf_label = self.default_font.render(label, True, self.fg_color)
            labels.append(surf_label)
            percent_label = "{:.1f}%".format(float_val)
            surf_percent_label = self.default_font.render(percent_label, True, self.bg_color)
            surf.blit(surf_percent_label, (x + (w/2 - surf_percent_label.get_width()/2), height/2 - surf_percent_label.get_height()/2))

            x += w
        total_width = 0
        for i in labels:
            total_width += i.get_width() + x_spacer

        if width > total_width:
            start_x = width/2 - total_width/2
        else:
            start_x = total_width / 2 - width / 2
        y = height + y_spacer
        for i in labels:
            surf.blit(i, (start_x, y))
            start_x += i.get_width() + x_spacer

        return surf

    def get_pihole_data(self):
        thread_timer = threading.Thread(target=self.get_pihole_data_thread, args=([]))
        thread_timer.daemon = False
        thread_timer.start()

    def get_pihole_data_thread(self):
        self.helper.log(self.debug, "Getting updated Pi-Hole stats from {}://{}".format(self.api_type, self.server))
        results = {}
        if self.api_type == "http":
            try:
                r = requests.get("http://{}:{}/admin/api.php?getCacheInfo&auth={}".format(self.server, self.pihole_server_http_port, self.api_key))
                results.update({"cache_info": r.json()["cacheinfo"]})
                r.close()
            except requests.RequestException as e:
                lock = threading.Lock()
                lock.acquire()
                self.helper.log(self.debug, "There was an error retrieving pi hole cache info: {}".format(e))
                lock.release()

            try:
                r = requests.get("http://{}:{}/admin/api.php?recentBlocked={}&auth={}".format(self.server, self.pihole_server_http_port, self.recently_blocked_num_history, self.api_key))
                try:
                    self.helper.log(self.debug, "PiHole: Getting Recently Blocked from JSON: {}".format(r.json()))
                    results.update({"recently_blocked": r.json()["recent_blocked"]})
                except:
                    self.helper.log(self.debug, "PiHole: That didnt work! Getting Recently Blocked from text: {}".format(r.text))
                    results.update({"recently_blocked": r.text})
                r.close()
            except requests.RequestException as e:
                lock = threading.Lock()
                lock.acquire()
                self.helper.log(self.debug, "There was an error retrieving pi hole recently blocked: {}".format(e))
                lock.release()

            try:
                r = requests.get("http://{}:{}/admin/api.php?summary&auth={}".format(self.server, self.pihole_server_http_port, self.api_key))
                results.update({"summary": r.json()})
                r.close()
            except requests.RequestException as e:
                lock = threading.Lock()
                lock.acquire()
                self.helper.log(self.debug, "There was an error retrieving pi hole recently blocked: {}".format(e))
                lock.release()

            try:
                r = requests.get("http://{}:{}/admin/api.php?topItems={}&auth={}".format(self.server, self.pihole_server_http_port, self.num_history, self.api_key))
                results.update({"top_items": r.json()})
                r.close()
            except requests.RequestException as e:
                lock = threading.Lock()
                lock.acquire()
                self.helper.log(self.debug, "There was an error retrieving pi hole top items: {}".format(e))
                lock.release()

            try:
                r = requests.get("http://{}:{}/admin/api.php?topClients={}&auth={}".format(self.server, self.pihole_server_http_port, self.num_history, self.api_key))
                results.update({"top_clients": r.json()["top_sources"]})
                r.close()
            except requests.RequestException as e:
                lock = threading.Lock()
                lock.acquire()
                self.helper.log(self.debug, "There was an error retrieving pi hole top clients: {}".format(e))
                lock.release()

            try:
                r = requests.get("http://{}:{}/admin/api.php?getForwardDestinations={}&auth={}".format(self.server, self.pihole_server_http_port, self.num_history, self.api_key))
                results.update({"forward_destinations": r.json()["forward_destinations"]})
                r.close()
            except requests.RequestException as e:
                lock = threading.Lock()
                lock.acquire()
                self.helper.log(self.debug, "There was an error retrieving pi hole forward destinations: {}".format(e))
                lock.release()

            try:
                r = requests.get("http://{}:{}/admin/api.php?overTimeData10mins&auth={}".format(self.server, self.pihole_server_http_port, self.api_key))
                results.update({"ads_over_time": r.json()["ads_over_time"]})
                results.update({"domains_over_time": r.json()["domains_over_time"]})
                r.close()
            except requests.RequestException as e:
                lock = threading.Lock()
                lock.acquire()
                self.helper.log(self.debug, "There was an error retrieving pi hole over time data: {}".format(e))
                lock.release()

            try:
                r = requests.get("http://{}:{}/admin/api.php?getAllQueries&auth={}".format(self.server, self.pihole_server_http_port, self.api_key))
                results.update({"getallqueries": r.json()["data"]})
                r.close()
            except requests.RequestException as e:
                lock = threading.Lock()
                lock.acquire()
                self.helper.log(self.debug, "There was an error retrieving pi hole all queries data: {}".format(e))
                lock.release()

        else:
            if self.api_type == "telnet":
                p = subprocess.Popen(["nc", "-N", self.server, self.pihole_server_telnet_port], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                cache_info = p.communicate(">cacheinfo".encode())[0].decode()
                p = subprocess.Popen(["nc", "-N", self.server, self.pihole_server_telnet_port], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                recent_blocked = p.communicate(">recentBlocked ({})".format(self.recently_blocked_num_history).encode())[0].decode()
                p = subprocess.Popen(["nc", "-N", self.server, self.pihole_server_telnet_port], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                summary = p.communicate(">stats".encode())[0].decode()

                p = subprocess.Popen(["php", "-r", "chdir('/var/www/html/admin'); require_once('scripts/pi-hole/php/gravity.php'); print json_encode(gravity_last_update(true));"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                gravity_last_update = p.communicate()[0].decode()

                p = subprocess.Popen(["nc", "-N", self.server, self.pihole_server_telnet_port], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                top_ads = p.communicate(">top-ads ({})".format(self.num_history).encode())[0].decode()
                p = subprocess.Popen(["nc", "-N", self.server, self.pihole_server_telnet_port], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                top_queries = p.communicate(">top-domains ({})".format(self.num_history).encode())[0].decode()

                p = subprocess.Popen(["nc", "-N", self.server, self.pihole_server_telnet_port], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                top_clients = p.communicate(">top-clients ({})".format(self.num_history).encode())[0].decode()
                p = subprocess.Popen(["nc", "-N", self.server, self.pihole_server_telnet_port], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                forward_destinations = p.communicate(">forward-dest".encode())[0].decode()

                p = subprocess.Popen(["nc", "-N", self.server, self.pihole_server_telnet_port], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                overtime = p.communicate(">overTime".encode())[0].decode()
                p = subprocess.Popen(["nc", "-N", self.server, self.pihole_server_telnet_port], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                all_queries = p.communicate(">getallqueries".encode())[0].decode()
            else:
                # SSH
                p = subprocess.Popen(["ssh", "-p", self.pihole_server_ssh_port, "{}@{}".format(self.ssh_user, self.server), 'echo ">cacheinfo"|nc -N 127.0.0.1 4711'], stdout=subprocess.PIPE)
                cache_info = p.communicate()[0].decode()
                p = subprocess.Popen(["ssh", "{}@{}".format(self.ssh_user, self.server), 'echo ">recentBlocked ({})"|nc -N 127.0.0.1 4711'.format(self.recently_blocked_num_history)], stdout=subprocess.PIPE)
                recent_blocked = p.communicate()[0].decode()
                p = subprocess.Popen(["ssh", "{}@{}".format(self.ssh_user, self.server), 'echo ">stats"|nc -N 127.0.0.1 4711'], stdout=subprocess.PIPE)
                summary = p.communicate()[0].decode()
                p = subprocess.Popen(["ssh", "{}@{}".format(self.ssh_user, self.server), 'php -r "chdir(\'/var/www/html/admin\'); require_once(\'scripts/pi-hole/php/gravity.php\'); print json_encode(gravity_last_update(true));"'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
                gravity_last_update = p.communicate()[0].decode()
                p = subprocess.Popen(["ssh", "{}@{}".format(self.ssh_user, self.server), 'echo ">top-ads ({})"|nc -N 127.0.0.1 4711'.format(self.num_history)], stdout=subprocess.PIPE)
                top_ads = p.communicate()[0].decode()

                p = subprocess.Popen(["ssh", "{}@{}".format(self.ssh_user, self.server), 'echo ">top-domains ({})"|nc -N 127.0.0.1 4711'.format(self.num_history)], stdout=subprocess.PIPE)
                top_queries = p.communicate()[0].decode()

                p = subprocess.Popen(["ssh", "{}@{}".format(self.ssh_user, self.server), 'echo ">top-clients ({})"|nc -N 127.0.0.1 4711'.format(self.num_history)], stdout=subprocess.PIPE)
                top_clients = p.communicate()[0].decode()
                p = subprocess.Popen(["ssh", "{}@{}".format(self.ssh_user, self.server), 'echo ">forward-dest"|nc -N 127.0.0.1 4711'], stdout=subprocess.PIPE)
                forward_destinations = p.communicate()[0].decode()

                p = subprocess.Popen(["ssh", "{}@{}".format(self.ssh_user, self.server), 'echo ">overTime"|nc -N 127.0.0.1 4711'], stdout=subprocess.PIPE)
                overtime = p.communicate()[0].decode()
                p = subprocess.Popen(["ssh", "{}@{}".format(self.ssh_user, self.server), 'echo ">getallqueries"|nc -N 127.0.0.1 4711'], stdout=subprocess.PIPE)
                all_queries = p.communicate()[0].decode()

            cache_info_obj = {}
            if len(cache_info) > 0:
                cache_info_obj.update(PiHole.find_key(cache_info, "cache-inserted", 0))
                cache_info_obj.update(PiHole.find_key(cache_info, "cache-live-freed", 0))
                cache_info_obj.update(PiHole.find_key(cache_info, "cache-size", 0))
                cache_info_obj.update(PiHole.find_key(cache_info, "cname", 0))
                cache_info_obj.update(PiHole.find_key(cache_info, "dnskey", 0))
                cache_info_obj.update(PiHole.find_key(cache_info, "ds", 0))
                cache_info_obj.update(PiHole.find_key(cache_info, "expired", 0))
                cache_info_obj.update(PiHole.find_key(cache_info, "immortal", 0))
                cache_info_obj.update(PiHole.find_key(cache_info, "ipv4", 0))
                cache_info_obj.update(PiHole.find_key(cache_info, "ipv6", 0))
                cache_info_obj.update(PiHole.find_key(cache_info, "other", 0))
                cache_info_obj.update(PiHole.find_key(cache_info, "srv", 0))
            results.update({"cache_info": cache_info_obj})

            forward_destinations_obj = {}
            if len(forward_destinations) > 0:
                for i in forward_destinations.splitlines():
                    parts = i.split(" ")
                    if len(parts) >= 4 and parts[3] != "":
                        forward_destinations_obj.update({"{}|{}".format(parts[3], parts[2]): parts[1]})
                    elif len(parts) >= 3:
                        forward_destinations_obj.update({"{}".format(parts[2]): parts[1]})
            results.update({"forward_destinations": forward_destinations_obj})

            recent_blocked_obj = []
            if len(recent_blocked) > 0:
                if isinstance(recent_blocked, str):
                    if "\n" in recent_blocked:
                        arr = []
                        for i in recent_blocked.splitlines():
                            if i != "---EOM---" and len(i) > 0:
                                arr.append(i)
                        recent_blocked_obj = arr
                    else:
                        recent_blocked_obj.append(recent_blocked)
                elif isinstance(recent_blocked, list):
                    recent_blocked_obj = recent_blocked
            results.update({"recently_blocked": recent_blocked_obj})

            summary_obj = {}
            if len(summary) > 0:
                summary_obj.update(PiHole.find_key(summary, "ads_blocked_today", 0, " "))
                summary_obj.update(PiHole.find_key(summary, "ads_percentage_today", 0, " "))
                summary_obj.update(PiHole.find_key(summary, "clients_ever_seen", 0, " "))
                summary_obj.update(PiHole.find_key(summary, "dns_queries_all_types", 0, " "))
                summary_obj.update(PiHole.find_key(summary, "dns_queries_today", 0, " "))
                summary_obj.update(PiHole.find_key(summary, "domains_being_blocked", 0, " "))
                summary_obj.update(PiHole.find_key(summary, "privacy_level", 0, " "))
                summary_obj.update(PiHole.find_key(summary, "queries_cached", 0, " "))
                summary_obj.update(PiHole.find_key(summary, "queries_forwarded", 0, " "))
                summary_obj.update(PiHole.find_key(summary, "reply_CNAME", 0, " "))
                summary_obj.update(PiHole.find_key(summary, "reply_IP", 0, " "))
                summary_obj.update(PiHole.find_key(summary, "reply_NODATA", 0, " "))
                summary_obj.update(PiHole.find_key(summary, "reply_NXDOMAIN", 0, " "))
                summary_obj.update(PiHole.find_key(summary, "status", 0, " "))
                summary_obj.update(PiHole.find_key(summary, "unique_clients", 0, " "))
                summary_obj.update(PiHole.find_key(summary, "unique_domains", 0, " "))

            if len(gravity_last_update) > 0:
                summary_obj.update({"gravity_last_updated": json.loads(gravity_last_update)})
            else:
                summary_obj.update({"gravity_last_updated": ""})
            results.update({"summary": summary_obj})

            top_clients_obj = {}
            if len(top_clients) > 0:
                for i in top_clients.splitlines():
                    parts = i.split(" ")
                    if len(parts) >= 4 and parts[3] != "":
                        top_clients_obj.update({"{}|{}".format(parts[3], parts[2]): parts[1]})
                    elif len(parts) >= 3:
                        top_clients_obj.update({"{}".format(parts[2]): parts[1]})
            results.update({"top_clients": top_clients_obj})

            top_items_obj = {}
            top_ads_obj = {}
            if len(top_ads) > 0:
                for i in top_ads.splitlines():
                    parts = i.split(" ")
                    if len(parts) >= 3:
                        top_ads_obj.update({parts[2]: parts[1]})
            top_items_obj.update({"top_ads": top_ads_obj})

            top_queries_obj = {}
            if len(top_queries) > 0:
                for i in top_queries.splitlines():
                    parts = i.split(" ")
                    if len(parts) >= 3:
                        top_queries_obj.update({parts[2]: parts[1]})
            top_items_obj.update({"top_queries": top_queries_obj})
            results.update({"top_items": top_items_obj})

            ads_over_time = {}
            domains_over_time = {}
            if len(overtime) > 0:
                for i in overtime.splitlines():
                    parts = i.split(" ")
                    if len(parts) >= 3:
                        domains_over_time.update({parts[0]: parts[1]})
                        ads_over_time.update({parts[0]: parts[2]})
            results.update({"ads_over_time": ads_over_time})
            results.update({"domains_over_time": domains_over_time})

            get_all_queries_obj = []
            if len(all_queries) > 0:
                for i in all_queries.splitlines():
                    parts = i.split(" ", 11)
                    if len(parts) >= 11:
                        parts[len(parts)-1] = parts[len(parts)-1].strip('"')
                        get_all_queries_obj.append(parts)
            results.update({"getallqueries": get_all_queries_obj})

        self.pihole_status = results
        self.pihole_updated = True

    @staticmethod
    def find_key(text, key, default_value, separator=":"):
        val = re.findall(r"{}\s*{}\s*(.+)".format(key, separator), text)
        if len(val) > 0:
            return {key: val[0]}
        else:
            return {key: default_value}

    @staticmethod
    def try_int_parse(val, default_val):
        try:
            return int(val)
        except:
            return default_val
