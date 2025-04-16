from kivymd.app import MDApp
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.textfield import MDTextField
from kivymd.uix.toolbar import MDTopAppBar

from kivy.uix.widget import Widget
from kivy.graphics import Color, Ellipse, Line
from kivy.clock import Clock
from kivy.storage.jsonstore import JsonStore

from bitcoinlib.services.services import Service as Ahmed
from bitcoinlib.keys import HDKey

import threading
import requests

store = JsonStore("wallet_data.json")

class BitcoinLogo(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self.update_canvas, size=self.update_canvas)

    def update_canvas(self, *args):
        self.canvas.clear()
        with self.canvas:
            center_x = self.center_x
            center_y = self.center_y
            radius = min(self.width, self.height) / 2 - 10

            Color(1, 0.6, 0.1, 1)  # Orange Circle
            Ellipse(pos=(center_x - radius, center_y - radius), size=(radius * 2, radius * 2))

            Color(1, 1, 1, 1)
            Line(points=[center_x - 10, center_y + 20, center_x + 10, center_y + 20], width=3)
            Line(points=[center_x - 10, center_y - 20, center_x + 10, center_y - 20], width=3)
            Line(circle=(center_x, center_y, radius), width=2)


class WalletCheckerApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Orange"
        self.theme_cls.theme_style = "Light"
        self.running = False
        self.hit = 0
        self.bad = 0
        self.total = 0
        self.threads = []

        self.token_input = MDTextField(
            hint_text="Telegram Bot Token",
            mode="rectangle"
        )
        self.chat_id_input = MDTextField(
            hint_text="Telegram Chat ID",
            mode="rectangle"
        )

        if store.exists("credentials"):
            self.token_input.text = store.get("credentials")["token"]
            self.chat_id_input.text = store.get("credentials")["chat_id"]

        self.status_label = MDLabel(
            text="Ready to start",
            halign="center",
            theme_text_color="Secondary"
        )

        self.address_label = MDLabel(
            text="Address: ---",
            halign="center",
            theme_text_color="Custom",
            text_color=(0.2, 0.2, 0.2, 1)
        )

        self.stats_label = MDLabel(
            text="Hits: 0 | Bad: 0 | Total: 0",
            halign="center",
            theme_text_color="Custom",
            text_color=(0.1, 0.1, 0.1, 1),
            font_style="H6"
        )

        self.stats_card = MDCard(
            orientation='vertical',
            size_hint=(1, None),
            height="160dp",
            padding="12dp",
            md_bg_color=self.theme_cls.primary_light
        )
        self.stats_card.add_widget(self.stats_label)
        self.stats_card.add_widget(self.address_label)

        self.start_button = MDRaisedButton(
            text="Start",
            md_bg_color=(0, 0.7, 0.2, 1),  # Green
            size_hint=(1, None),
            height="48dp",
            on_release=self.start_checking
        )

        self.stop_button = MDRaisedButton(
            text="Stop",
            md_bg_color=(1, 0, 0, 1),  # Red
            size_hint=(1, None),
            height="48dp",
            on_release=self.stop_checking
        )

        self.toolbar = MDTopAppBar(
            title="Wallet Checker",
            right_action_items=[["weather-night", lambda x: self.toggle_theme()]],
            elevation=10
        )

        self.logo = BitcoinLogo(size_hint=(1, None), height="120dp")

        layout = MDBoxLayout(orientation="vertical", spacing=10, padding=20)
        layout.add_widget(self.toolbar)
        layout.add_widget(self.token_input)
        layout.add_widget(self.chat_id_input)
        layout.add_widget(self.status_label)
        layout.add_widget(self.logo)
        layout.add_widget(self.stats_card)
        layout.add_widget(self.start_button)
        layout.add_widget(self.stop_button)

        return layout

    def toggle_theme(self):
        self.theme_cls.theme_style = "Dark" if self.theme_cls.theme_style == "Light" else "Light"

    def start_checking(self, instance):
        self.token = self.token_input.text.strip()
        self.chat_id = self.chat_id_input.text.strip()

        if not self.token or not self.chat_id:
            self.status_label.text = "[ Please enter both token and chat ID ]"
            return

        store.put("credentials", token=self.token, chat_id=self.chat_id)
        self.running = True
        self.status_label.text = "Checking wallets..."

        for _ in range(5):
            t = threading.Thread(target=self.generate_wallet)
            t.start()
            self.threads.append(t)

    def stop_checking(self, instance):
        self.running = False
        self.status_label.text = "Stopped"

    def update_stats(self, address="---"):
        self.stats_label.text = f"Hits: {self.hit} | Bad: {self.bad} | Total: {self.total}"
        self.address_label.text = f"Address: {address[:20]}..." if address else "Address: ---"

    def Check(self, private_key, address, public_key):
        try:
            service = Ahmed(network='bitcoin')
            balance = service.getbalance(address) / 1e8
            self.total += 1
            Clock.schedule_once(lambda dt: self.update_stats(address))

            if balance > 0.0 or balance > 0:
                self.hit += 1
                msg = f"""Found Balance: {balance}
Address: {address}
Public Key: {public_key}
Private Key (WIF): {private_key}
By: alhranyahmed@gmail.com
{'-'*40}"""

                with open("/storage/emulated/0/dumpwallet.txt", "a", encoding="utf-8") as g:
                    g.write(msg + "\n")

                requests.post(
                    f'https://api.telegram.org/bot{self.token}/sendMessage',
                    data={'chat_id': self.chat_id, 'text': msg}
                )
            else:
                self.bad += 1
        except:
            pass
        finally:
            Clock.schedule_once(lambda dt: self.update_stats(address))

    def generate_wallet(self):
        while self.running:
            try:
                key = HDKey()
                private_key = key.wif()
                public_key = key.public()
                address = key.address()
                self.Check(private_key, address, public_key)
            except:
                pass

if __name__ == '__main__':
    WalletCheckerApp().run()

