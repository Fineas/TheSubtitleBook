import argparse
import os
import time
from pathlib import Path

from open_gopro import WirelessGoPro, Params
from open_gopro.util import add_cli_args_and_parse

class OpenGoProService:

    def __init__(self, enable_wifi=False, sudo_passwd="ptg@darpa", enable_logging=False) -> None:
        self.enable_wifi = enable_wifi
        self.sudo_password = sudo_passwd

        if enable_logging:
            parser = argparse.ArgumentParser()
            args = add_cli_args_and_parse(parser, wifi=True)
            self.logger = setup_logging(__name__, args.log)

        self.gopro = WirelessGoPro(enable_wifi=enable_wifi, sudo_password=self.sudo_password)
        self.init_gopro(self.gopro)

    @staticmethod
    def init_gopro(gopro):
        if not gopro.is_open:
            gopro.open()
        print("Setting GoPro Configuration Settings for Photo Mode")
        gopro.ble_command.load_preset_group(group=Params.PresetGroup.PHOTO)
        gopro.ble_setting.photo_resolution.set(Params.PhotoResolution.RES_23MP_MEDIUM)
        gopro.ble_setting.photo_field_of_view.set(Params.PhotoFOV.LINEAR)

    def take_photo(self, folder_path, file_name):
        self.close_wifi_connection()
        print("Capturing photo")
        self.gopro.ble_command.set_shutter(shutter=Params.Toggle.ENABLE)
        self.gopro.ble_command.set_shutter(shutter=Params.Toggle.DISABLE)
        print("Photo captured")
        self.download_most_recent_photo(folder_path, file_name)

    def download_most_recent_photo(self, folder_path, file_name=None):
        print("Downloading the most recent photo")
        self.open_wifi_connection()
        media_list = [
            x["n"]
            for x in self.gopro.http_command.get_media_list().flatten
            if x["n"].lower().endswith(('.jpg', '.jpeg'))
        ]
        if not media_list:
            logger.error("No photos found on the camera")
            return
        recent_photo = sorted(media_list)[-1]
        if file_name is not None:
            local_file = os.path.abspath(os.path.join(folder_path, file_name))
        else:
            local_file = os.path.abspath(os.path.join(folder_path, recent_photo))
        local_path = Path(local_file)

        self.gopro.http_command.download_file(camera_file=recent_photo, local_file=local_path)
        self.close_wifi_connection()
        print(f"Downloaded photo to {local_file}")

    def close_all_connections(self):
        self.gopro.close()

    def open_wifi_connection(self):
        if not self.gopro.is_open or self.enable_wifi:
            return
        self.enable_wifi = True
        self.gopro.close()
        self.gopro = WirelessGoPro(enable_wifi=True, sudo_password=self.sudo_password)
        self.gopro.open()

    def close_wifi_connection(self):
        if not self.gopro.is_open or not self.enable_wifi:
            return
        self.enable_wifi = False
        self.gopro.close()
        self.gopro = WirelessGoPro(enable_wifi=False, sudo_password=self.sudo_password)
        self.gopro.open()


def test_take_photo():
    gopro = OpenGoProService(enable_wifi=False, enable_logging=False)

    gopro_photos_dir = "./images"
    if not os.path.exists(gopro_photos_dir):
        os.makedirs(gopro_photos_dir)
    file_name = "latest_photo.JPG"
    gopro.take_photo(gopro_photos_dir, file_name)

    gopro.close_all_connections()


if __name__ == '__main__':
    test_take_photo()
