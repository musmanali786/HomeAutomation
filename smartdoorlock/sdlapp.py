import flet as ft
import requests

# Replace with your Home Assistant details
HOME_ASSISTANT_URL = "http://your-home-assistant-url:8123"
HOME_ASSISTANT_TOKEN = "your-long-lived-access-token"
ESP32_CAM_URL = "http://your-esp32-cam-url/stream"

# Headers for Home Assistant API
HEADERS = {
    "Authorization": f"Bearer {HOME_ASSISTANT_TOKEN}",
    "Content-Type": "application/json",
}

def toggle_switch():
    # Replace with your switch entity ID
    switch_entity_id = "switch.your_switch_entity_id"
    # Get the current state of the switch
    state_url = f"{HOME_ASSISTANT_URL}/api/states/{switch_entity_id}"
    response = requests.get(state_url, headers=HEADERS)
    if response.status_code == 200:
        current_state = response.json()["state"]
        # Toggle the switch
        service_url = f"{HOME_ASSISTANT_URL}/api/services/switch/turn_on" if current_state == "off" else f"{HOME_ASSISTANT_URL}/api/services/switch/turn_off"
        requests.post(service_url, headers=HEADERS, json={"entity_id": switch_entity_id})
    else:
        print("Failed to fetch switch state.")

def main(page: ft.Page):
    page.title = "Smart Door Lock with ESP32-CAM"
    page.scroll = "adaptive"

    # ESP32-CAM image stream
    cam_image = ft.Image(src=ESP32_CAM_URL, width=640, height=480)

    # Button to toggle the switch
    toggle_button = ft.ElevatedButton(
        text="Toggle Switch",
        on_click=lambda _: toggle_switch(),
    )

    # Add components to the page
    page.add(
        ft.Column(
            [
                ft.Text("ESP32-CAM Stream", size=20, weight="bold"),
                cam_image,
                toggle_button,
            ],
            alignment="center",
            horizontal_alignment="center",
        )
    )

ft.app(target=main)