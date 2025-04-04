import flet as ft
import requests
import json
from datetime import datetime
import os

# Default configuration
DEFAULT_CONFIG = {
    "HA_URL": "http://192.168.100.75:8123",
    "HA_TOKEN": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJhMTJjODNmZmY2YWM0ZTQ2OWE1ZjE1OWIzY2RiN2ZlYyIsImlhdCI6MTc0Mzc0MDI2OSwiZXhwIjoyMDU5MTAwMjY5fQ.s_IXEWBwWR8RDhOV2vEOtdyTchjo_HwPVcs6muTvty4",
    "CAMERA_ENTITY_ID": "camera.esp32_cam_stream",
    "SWITCH_ENTITY_ID": "switch.esp8266maingate"
}

# Try to load saved configuration
CONFIG_FILE = "ha_esp32_config.json"
current_config = DEFAULT_CONFIG.copy()

def load_config():
    global current_config
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                saved_config = json.load(f)
                current_config.update(saved_config)
        except:
            pass

def save_config():
    with open(CONFIG_FILE, "w") as f:
        json.dump(current_config, f)

load_config()

def main(page: ft.Page):
    page.title = "Home Assistant ESP32 Controller"
    page.theme_mode = ft.ThemeMode.DARK
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.padding = 20
    
    # State variables
    switch_state = False
    last_update = "Never"
    
    # Configuration dialog controls
    ha_url_field = ft.TextField(
        label="Home Assistant URL",
        value=current_config["HA_URL"],
        width=400
    )
    ha_token_field = ft.TextField(
        label="Access Token",
        value=current_config["HA_TOKEN"],
        width=400,
        password=True,
        can_reveal_password=True
    )
    camera_entity_field = ft.TextField(
        label="Camera Entity ID",
        value=current_config["CAMERA_ENTITY_ID"],
        width=400
    )
    switch_entity_field = ft.TextField(
        label="Switch Entity ID",
        value=current_config["SWITCH_ENTITY_ID"],
        width=400
    )
    
    def close_settings_dlg(e):
        settings_dlg.open = False
        page.update()
    
    def save_settings(e):
        current_config["HA_URL"] = ha_url_field.value
        current_config["HA_TOKEN"] = ha_token_field.value
        current_config["CAMERA_ENTITY_ID"] = camera_entity_field.value
        current_config["SWITCH_ENTITY_ID"] = switch_entity_field.value
        save_config()
        close_settings_dlg(e)
        # Refresh with new settings
        get_switch_state()
        refresh_camera(None)
    
    settings_dlg = ft.AlertDialog(
        modal=True,
        title=ft.Text("Settings"),
        content=ft.Column(
            [
                ha_url_field,
                ha_token_field,
                camera_entity_field,
                switch_entity_field,
            ],
            tight=True,
        ),
        actions=[
            ft.TextButton("Cancel", on_click=close_settings_dlg),
            ft.TextButton("Save", on_click=save_settings),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    
    def open_settings(e):
        page.dialog = settings_dlg
        settings_dlg.open = True
        page.update()
    
    def get_headers():
        return {
            "Authorization": f"Bearer {current_config['HA_TOKEN']}",
            "Content-Type": "application/json",
        }
    
    def get_switch_state():
        nonlocal switch_state, last_update
        try:
            response = requests.get(
                f"{current_config['HA_URL']}/api/states/{current_config['SWITCH_ENTITY_ID']}",
                headers=get_headers()
            )
            if response.status_code == 200:
                data = response.json()
                switch_state = data['state'] == "on"
                last_update = datetime.now().strftime("%H:%M:%S")
                switch_control.value = switch_state
                status_text.value = f"Switch is {'ON' if switch_state else 'OFF'} (Updated: {last_update})"
                page.update()
            else:
                status_text.value = f"Error getting state: {response.status_code}"
                page.update()
        except Exception as ex:
            status_text.value = f"Error: {str(ex)}"
            page.update()
    
    def toggle_switch(e):
        nonlocal switch_state, last_update
        try:
            new_state = not switch_state
            service_data = {
                "entity_id": current_config["SWITCH_ENTITY_ID"]
            }
            
            response = requests.post(
                f"{current_config['HA_URL']}/api/services/switch/{'turn_on' if new_state else 'turn_off'}",
                headers=get_headers(),
                data=json.dumps(service_data)
            )
            
            if response.status_code == 200:
                switch_state = new_state
                last_update = datetime.now().strftime("%H:%M:%S")
                switch_control.value = switch_state
                status_text.value = f"Switch is {'ON' if switch_state else 'OFF'} (Updated: {last_update})"
                page.update()
                refresh_camera(None)
            else:
                status_text.value = f"Failed to toggle switch: {response.status_code}"
                page.update()
        except Exception as ex:
            status_text.value = f"Error: {str(ex)}"
            page.update()
    
    def refresh_camera(e):
        timestamp = int(datetime.now().timestamp())
        camera_view.src = (
            f"{current_config['HA_URL']}/api/camera_proxy/"
            f"{current_config['CAMERA_ENTITY_ID']}?timestamp={timestamp}"
        )
        page.update()
    
    # Create UI components
    camera_view = ft.Image(
        src=f"{current_config['HA_URL']}/api/camera_proxy/{current_config['CAMERA_ENTITY_ID']}",
        width=640,
        height=480,
        fit=ft.ImageFit.CONTAIN,
        border_radius=10,
    )
    
    switch_control = ft.Switch(
        value=switch_state,
        label="Toggle Switch",
        on_change=toggle_switch,
    )
    
    toggle_button = ft.ElevatedButton(
        text="Toggle Switch",
        on_click=toggle_switch,
        icon=ft.icons.POWER_SETTINGS_NEW,
    )
    
    refresh_button = ft.IconButton(
        icon=ft.icons.REFRESH,
        on_click=refresh_camera,
        tooltip="Refresh Camera",
    )
    
    settings_button = ft.IconButton(
        icon=ft.icons.SETTINGS,
        on_click=open_settings,
        tooltip="Settings",
    )
    
    status_text = ft.Text(
        value="Status: Loading...",
        size=16,
        weight=ft.FontWeight.BOLD,
    )
    
    # App bar with settings button
    page.appbar = ft.AppBar(
        title=ft.Text("Home Assistant ESP32 Controller"),
        center_title=True,
        bgcolor=ft.colors.SURFACE_VARIANT,
        actions=[settings_button],
    )
    
    # Main content
    page.add(
        ft.Column(
            [
                camera_view,
                ft.Divider(height=20),
                ft.Row(
                    [switch_control, toggle_button],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=30,
                ),
                status_text,
                ft.ElevatedButton(
                    "Get Current State",
                    on_click=lambda e: get_switch_state(),
                    icon=ft.icons.UPDATE,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
    )
    
    # Initial state update
    get_switch_state()

# Run the app
ft.app(target=main)