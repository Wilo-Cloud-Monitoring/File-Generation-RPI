import os
import subprocess
import csv
import pandas as pd
import time
import glob
import shutil
import requests
from time import sleep
from datetime import datetime, timedelta
from pathlib import Path
import sys
import logging
from mpu import MPU
import platform
from dotenv import load_dotenv

new_recursion_limit = 4000
sys.setrecursionlimit(new_recursion_limit)


class Files:
    def __init__(self):
        self.mpu = MPU()
        # Set up logging
        self.log_folder = "Logged"
        self.configure()
        self.ABS_PATH = "/home/nvs/Desktop/File-Generation-RPI"  # Add your path
        self.readings_directory = f"{self.ABS_PATH}/readings"
        self.DESIRED_DURATION = 60
        self.START_TIME = 0
        self.ENDPOINT = "http://103.97.164.81:2121/"
        self.backup_directory = f"{self.ABS_PATH}/Backup"
        self.files_repository_directory = f"{self.ABS_PATH}/Files Repository"
        self.upload_queue_directory = f"{self.ABS_PATH}/Upload Queue"
        load_dotenv()
        self.ssid = os.getenv("SSID")
        self.wifi_password = os.getenv("WIFI_PASSWORD")
        self.logger = logging
        self.check_directory("readings")

    def configure(self):
        if not os.path.exists(self.log_folder):
            os.makedirs(self.log_folder)
            print("Log folder created")
        # log_file_path = os.path.join(log_folder, "script_log.txt")
        logging.basicConfig(
            # filename=log_file_path,
            level=logging.DEBUG,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )

    def check_directory(self, directory):
        if not os.path.exists(directory):
            os.makedirs(directory)
            logging.info("Directory created: %s", directory)
        else:
            logging.info("Directory already exists: %s", directory)

    def files_generation(self):
        try:
            current_time = time.time()
            datetime_object = datetime.fromtimestamp(current_time)
            formatted_time = datetime_object.strftime("%Y-%b-%dT%H-%M-%S")

            inner_start_time = time.time()
            d_duration = 2
            m_duration = 0
            file_path = f"{formatted_time}.csv"
            csv_file_path = os.path.join(self.readings_directory, file_path)

            # Create or get the logger for the current session
            session_logger = logging.getLogger("session_logger")
            if (
                    not session_logger.handlers
            ):  # Add file handler only if it's not added before
                session_logger.setLevel(logging.DEBUG)
                file_handler = logging.FileHandler(
                    os.path.join(self.log_folder, "session_log.log")
                )
                file_handler.setLevel(logging.DEBUG)
                file_formatter = logging.Formatter(
                    "%(asctime)s - %(levelname)s - %(message)s"
                )
                file_handler.setFormatter(file_formatter)
                session_logger.addHandler(file_handler)

            with open(csv_file_path, mode="w", newline="") as csvfile:
                csvwriter = csv.writer(csvfile)
                csvwriter.writerow(["timestamp", "acceleration"])

                while True:
                    acc_x = self.mpu.read_raw_data(self.mpu.ACCEL_XOUT_H)
                    acc_y = self.mpu.read_raw_data(self.mpu.ACCEL_YOUT_H)
                    acc_z = self.mpu.read_raw_data(self.mpu.ACCEL_ZOUT_H)

                    gyro_x = self.mpu.read_raw_data(self.mpu.GYRO_XOUT_H)
                    gyro_y = self.mpu.read_raw_data(self.mpu.GYRO_YOUT_H)
                    gyro_z = self.mpu.read_raw_data(self.mpu.GYRO_ZOUT_H)

                    ax = acc_x / 16384.0
                    ay = acc_y / 16384.0
                    az = acc_z / 16384.0

                    gx = gyro_x / 131.0
                    gy = gyro_y / 131.0
                    gz = gyro_z / 131.0
                    acl = acc_z

                    m_duration += 1
                    current_time = time.time()
                    datetime_object = datetime.fromtimestamp(current_time)
                    formatted_time = datetime_object.strftime("%H-%M-%S.%f")

                    csvwriter.writerow([formatted_time, acl])
                    csvfile.flush()

                    sleep(0.05)

                    elapsed_time1 = time.time() - inner_start_time
                    elapsed_time2 = time.time() - self.START_TIME

                    if elapsed_time1 >= d_duration:
                        if elapsed_time2 >= self.DESIRED_DURATION:
                            return
                        session_logger.info("Csv File Created!")
                        return True
        except Exception as e:
            logging.exception("An exception occurred in files_generation: %s", e)

    def get_files_status_to_delete(self, file_name):
        time_from_file = datetime.strptime(file_name.split(".")[0].replace("T", " "), "%Y-%b-%d %H-%M-%S")
        time_difference = datetime.now() - time_from_file
        if time_difference >= timedelta(hours=4):
            return True
        else:
            return False

    def delete_old_data(self):
        path = f"{self.ABS_PATH}/all files"
        files = glob.glob(f"{path}/*.csv")
        cnt = 0
        for file_name in files:
            if self.get_files_status_to_delete(file_name.split("/")[-1]):
                os.remove(file_name)
                logging.info(f"File deleted with {file_name.split('/')[-1]}")
                cnt += 1
        logging.info(f"total files deleted are {cnt}")

    def backup_check(self):
        try:
            logging.info("Backup Check")
            self.check_directory("Backup")
            source_directory = self.readings_directory
            destination_directory = self.backup_directory
            files_to_move = os.listdir(source_directory)
            print(files_to_move)
            if files_to_move:
                for file_name in files_to_move:
                    source_path = os.path.join(source_directory, file_name)
                    destination_path = os.path.join(destination_directory, file_name)
                    shutil.move(source_path, destination_path)
                logging.info("All the files are moved to the backup folder")
                all_files = glob.glob(f"{self.backup_directory}/*.csv")
                logging.info("Length of all Files: %s", str(len(all_files)))
                file = self.max_acceleration(all_files)
                return file
            else:
                return None
        except Exception as e:
            logging.exception("An exception occurred in BackUp Check: %s", e)

    def max_acceleration(self, all_files):
        try:
            logging.info("Maximum Acceleration")
            read = 0
            failed_to_read = 0
            max_list = []
            for file_ in all_files:
                try:
                    df = pd.read_csv(file_, index_col=None, header=0)
                    max_list.append(df["acceleration"].max())
                    read += 1
                except Exception as e:
                    logging.warning("Failed to read file: %s", file_)
                    logging.exception(e)
                    failed_to_read += 1
            logging.info("Total No. of Files that are read: %s", str(read))
            logging.info("Total No. of Files that can't be read: %s", str(failed_to_read))
            file_name = []
            high_acc = []
            for file_ in all_files:
                try:
                    df = pd.read_csv(file_, index_col=None, header=0)
                    file_name.append(file_.title())
                    high_acc.append(df["acceleration"].max())
                except Exception as e:
                    logging.warning("Exception while processing file: %s", file_)
                    logging.exception(e)

            logging.info(
                "Total Files that are perfectly read and saved the title: %s",
                str(len(file_name)),
            )
            logging.info(
                "Total Files that are perfectly read and get the Highest Acceleration and saved: %s",
                str(len(high_acc)),
            )
            return self.convert_to_dictionary(file_name, high_acc)
        except Exception as e:
            logging.exception("An exception occurred in max acceleration: %s", e)

    def convert_to_dictionary(self, file_name, high_acc):
        try:
            logging.info("Converting to Dictionary")
            file_acceleration_map = {}
            for key in file_name:
                if high_acc:
                    value = high_acc.pop(0)
                    file_acceleration_map[key] = value
            logging.info("Total dictionary size: %s", str(len(file_acceleration_map.items())))
            top_5_files = sorted(file_acceleration_map.items(), key=lambda item: item[1], reverse=True)[:5]
            return top_5_files
        except Exception as e:
            logging.exception("An exception occurred in converting to dictionary: %s", e)

    def move_to_upload_queue(self, top_files):
        try:
            logging.info("Move To upload queue Function")
            self.check_directory("Upload Queue")
            self.check_directory("Files Repository")
            files_copied_count = 0
            for file, _ in top_files:
                file_name = file.split("/")[-1]
                for backup_file_name in os.listdir(self.backup_directory):
                    if file_name.lower() == backup_file_name.lower():
                        try:
                            shutil.copy(os.path.join(self.backup_directory, backup_file_name),
                                        self.upload_queue_directory)
                            files_copied_count += 1
                            break
                        except Exception as e:
                            logging.error("Error copying file %s: %s", file_name, e)
            self.delete_old_data()
            if files_copied_count == 5:
                for backup_file_name in os.listdir(self.backup_directory):
                    shutil.move(f"{self.backup_directory}/{backup_file_name}", self.files_repository_directory)
                logging.info("File with max acceleration copied to the upload queue")
            else:
                logging.error("File with max acceleration not copied to the upload queue")
            return glob.glob(f"{self.upload_queue_directory}/*.csv")
        except Exception as e:
            logging.exception("An exception occurred in moving to test directory: %s", e)

    def send_csv(self, files):
        if not self.is_device_connected_to_internet():
            self.connect_to_wifi(self.ssid, self.wifi_password)
            if not self.is_device_connected_to_internet():
                return
        if self.check_server_status():
            logging.info("Seems Like Server is down.")
            return
        try:
            logging.info("Files are being sent to server ....")
            successfully_sent_files = []
            logging.info("Length of all Files: %s", str(len(files)))
            if not files:
                logging.warning("No CSV files found in the directory.")
                return
            for file in files:
                logging.info("File Path: %s", file)
                file_sent_successfully = False
                try:
                    response = requests.post(f"{self.ENDPOINT}csv/upload", files={'file': open(file, 'rb')},
                                             timeout=15)
                    if response.status_code == 200:
                        logging.info("File sent successfully.")
                        file_sent_successfully = True
                        successfully_sent_files.append(file)  # Track successful files
                        break  # Exit retry loop if successful
                    else:
                        logging.error("Failed to send file. Status Code: %s", response.status_code)
                except requests.RequestException as e:
                    logging.error("Error while sending file to server: %s", e)

                if not file_sent_successfully:
                    logging.warning("Failed to send file after 3 attempts: %s", file)

            # Now delete only the successfully sent files
            if successfully_sent_files:
                try:
                    count = 0
                    for file in successfully_sent_files:
                        os.remove(file)
                        count += 1
                    logging.info("Total Files that are deleted: %s", str(count))
                except Exception as e:
                    logging.error("Error while deleting files: %s", e)
            else:
                logging.warning("No files were successfully sent, so none were deleted.")

        except Exception as e:
            logging.exception("An exception occurred in send_csv: %s", e)

    def send_log(self):
        # TODO 1: Check for internet connection and connect to Wi-Fi if not connected
        if not self.is_device_connected_to_internet():
            self.connect_to_wifi(self.ssid, self.wifi_password)
            if not self.is_device_connected_to_internet():
                logging.error("Could not connect to the internet. Aborting log file upload.")
                return

        try:
            # TODO 2: Log that we are sending the log file
            logging.info("Preparing to send log files...")
            # TODO 3: Close the current log file to make sure everything is written to disk
            logging.shutdown()
            # TODO 4: Collect all .log files from the log folder
            log_files = glob.glob(f"{self.log_folder}/*.log")
            logging.info("Number of log files found: %s", str(len(log_files)))
            if not log_files:
                logging.warning("No log files found to send.")
                return
            # TODO 5: Iterate over each log file, send it to the server, and delete it if successful
            successfully_sent_files = []
            for log_file_path in log_files:
                logging.info("Sending log file: %s", log_file_path)
                try:
                    # Open the log file and prepare it for sending
                    with open(log_file_path, "rb") as log_file:
                        log_content = log_file.read()

                    # Prepare the files dictionary for the POST request
                    files = {"file": (os.path.basename(log_file_path), log_content)}

                    # Make the POST request to the FastAPI server
                    response = requests.post(f"{self.ENDPOINT}/logging/receive-logfile", files=files, timeout=15)

                    # Check if the file was sent successfully
                    if response.status_code == 200:
                        logging.info("Log file sent successfully: %s", log_file_path)
                        successfully_sent_files.append(log_file_path)
                    else:
                        logging.error("Failed to send log file: %s, Status code: %s", log_file_path,
                                      response.status_code)

                except Exception as e:
                    logging.error("Error sending log file: %s, Exception: %s", log_file_path, e)
            # TODO 6: Delete successfully sent log files
            if successfully_sent_files:
                try:
                    count_deleted = 0
                    for file_path in successfully_sent_files:
                        os.remove(file_path)
                        count_deleted += 1
                    logging.info("Successfully deleted %d log files.", count_deleted)
                except Exception as e:
                    logging.error("Error deleting log files: %s", e)
            else:
                logging.warning("No log files were successfully sent, so none were deleted.")

        except Exception as e:
            logging.exception("An exception occurred in send_log: %s", e)

    def is_device_connected_to_internet(self):
        try:
            # Try to ping Google's DNS server to check for an internet connection
            subprocess.run(["ping", "8.8.8.8", "-c", "1"], check=True, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
            print("Internet is connected.")
            return True
        except subprocess.CalledProcessError:
            print("No internet connection.")
            return False

    def connect_to_wifi(self, ssid, password):
        # Get the operating system
        os_type = platform.system()

        if os_type == "Windows":
            # Windows Wi-Fi connection command
            command = f'netsh wlan connect name="{ssid}" ssid="{ssid}" key="{password}"'
        elif os_type == "Linux":
            # Linux Wi-Fi connection command using nmcli
            command = f'nmcli dev wifi connect "{ssid}" password "{password}"'
        elif os_type == "Darwin":
            # macOS Wi-Fi connection command using networksetup
            command = f'networksetup -setairportnetwork en0 "{ssid}" "{password}"'
        else:
            print(f"OS {os_type} not supported for automatic Wi-Fi connection.")
            return

        try:
            subprocess.run(command, shell=True, check=True)
            logging.info(f"Connected to Wi-Fi network: {ssid}")
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to connect to Wi-Fi: {e}")

    def check_server_status(self):
        try:
            response = requests.get(self.ENDPOINT, timeout=10)
            # If the response status code is in the range [200, 399], consider it reachable
            if response.status_code >= 200 and response.status_code < 400:
                return False
            else:
                return True
        except requests.RequestException as e:
            logging.info(e)
            # If an exception occurs, the server is not reachable
            return True
