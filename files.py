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

new_recursion_limit = 4000
sys.setrecursionlimit(new_recursion_limit)


class Files:
    def __init__(self):
        self.mpu = MPU()
        # Set up logging
        self.log_folder = "Logged"
        self.configure()
        self.ABS_PATH = "/home/nvs/Desktop/my_env"
        self.NEW_DIRECTORY = f"{self.ABS_PATH}/readings"
        self.DESIRED_DURATION = 60
        self.START_TIME = time.time()
        self.ENDPOINT = "http://103.97.164.81:2121/"

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
            print("Readings Created")
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
            csv_file_path = os.path.join(self.NEW_DIRECTORY, file_path)

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
                        print("Csv created")
                        return True
        except Exception as e:
            session_logger.exception("An exception occurred in files_generation: %s", e)

    def get_files_status_to_delete(self, file_name):
        time_from_file = datetime.strptime(file_name.split(".")[0].replace("T", " "), "%Y-%m-%d %H-%M-%S")
        time_difference = datetime.now() - time_from_file
        if time_difference >= timedelta(minutes=1):
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
                print(f"File deleted with {file_name.split('/')[-1]}")
                cnt += 1
        print(f"total files deleted are {cnt}")

    def backup_check(self):
        try:
            logging.info("Backup Check")
            name = "Readings_Backup"
            path = f"{self.ABS_PATH}/{name}"

            try:
                os.mkdir(path)
                logging.info("Successfully created directory: %s", name)
            except FileExistsError:
                logging.info("Directory already exists: %s", name)

            source_directory = f"{self.ABS_PATH}/readings"
            destination_directory = f"{self.ABS_PATH}/Readings_Backup/"

            files_to_move = os.listdir(source_directory)
            if files_to_move:
                for file_name in files_to_move:
                    source_path = os.path.join(source_directory, file_name)
                    destination_path = os.path.join(destination_directory, file_name)
                    shutil.move(source_path, destination_path)

                logging.info("All the files are moved to the backup folder")
                print("All the files are moved to the backup folder")

                all_files = glob.glob(f"{self.ABS_PATH}/Readings_Backup/*.csv")
                logging.info("Length of all Files: %s", str(len(all_files)))

                file = self.max_accleration(all_files)

                return file
            else:
                return None
        except Exception as e:
            logging.exception("An exception occurred in BackUp Check: %s", e)

    def max_accleration(self, all_files):
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
                    print("Failed to read file: %s", file_)
                    failed_to_read += 1

            logging.info("Total No. of Files that are read: %s", str(read))
            logging.info("Total No. of Files that can't be read: %s", str(failed_to_read))
            print("Total No. of Files that are read: %s", str(read))
            print("Total No. of Files that can't be read: %s", str(failed_to_read))

            file_name = []
            high_acc = []

            for file_ in all_files:
                try:
                    df = pd.read_csv(file_, index_col=None, header=0)
                    file_name.append(file_.title())
                    high_acc.append(df["acceleration"].max())
                except Exception:
                    logging.warning("Exception while processing file: %s", file_)

            logging.info(
                "Total No. of Files that are perfectly read and saved the title: %s",
                str(len(file_name)),
            )
            logging.info(
                "Total No. of Files that are perfectly read and get the Highest Acceleration and saved: %s",
                str(len(high_acc)),
            )

            print(
                "Total No. of Files that are perfectly read and saved the title: %s",
                str(len(file_name)),
            )
            print(
                "Total No. of Files that are perfectly read and get the Highest Acceleration and saved: %s",
                (len(high_acc)),
            )
            file = self.convert_to_dictionary(file_name, high_acc)
            return file
        except Exception as e:
            logging.exception("An exception occurred in max acceleration: %s", e)
            print("An exception occurred in max acceleration: %s", e)

    def convert_to_dictionary(self, file_name, high_acc):
        try:
            logging.info("Converting to Dictionary")
            res = {}
            for key in file_name:
                for value in high_acc:
                    res[key] = value
                    high_acc.remove(value)
                    break

            for key, value in res.items():
                logging.info("File Name: %s, Highest Acceleration: %s", key, str(value))
                print("File Name: %s, Highest Acceleration: %s", key, str(value))

            logging.info("Total dictionary size: %s", str(len(res.items())))
            print("Total dictionary size: %s", str(len(res.items())))

            max_key_title = max(res, key=res.get)
            logging.info(
                "File Name: %s, Highest Acceleration: %s",
                max_key_title,
                str(res[max_key_title]),
            )

            logging.info("File having the maximum Acceleration: %s", max_key_title)
            print("File having the maximum Acceleration: %s", max_key_title)
            logging.info(
                "File having the maximum Acceleration is: %s", str(res[max_key_title])
            )
            print("File having the maximum Acceleration is: %s", str(res[max_key_title]))

            return max_key_title.title()
        except Exception as e:
            logging.exception("An exception occurred in converting to dictionary: %s", e)

    def move_to_test_directory(self, ms_test):
        try:
            logging.info("Move To Test Directory Function")
            path = f"{self.ABS_PATH}/TestDirectory"
            all_files = os.listdir(f"{self.ABS_PATH}/Readings_Backup")
            try:
                os.mkdir(path)
                logging.info("Successfully created directory: %s", path)
                print("Successfully created directory: %s", path)
            except FileExistsError:
                logging.info("Directory already exists: %s", path)
                print("Directory already exists: %s", path)
            del_start = False
            all_files_path = f"{self.ABS_PATH}/all files"
            if not os.path.exists(all_files_path):
                os.mkdir(all_files_path)
            for file_name in all_files:
                if file_name.title() == ms_test:
                    shutil.copy(file_name, path)
                    logging.info("Maximum Value File copied to the new directory")
                    print("Maximum Value File copied to the new directory")
                    del_start = True
                print("Moving to All directory")
                shutil.move(file_name, all_files_path)
            self.delete_old_data()

            if del_start:
                t1 = 0
                for _ in all_files:
                    os.remove(_)
                    t1 = t1 + 1
                logging.info("Total No. of Files that are deleted: %s", str(t1))
                print("Total No. of Files that are deleted: %s", str(t1))
            else:
                logging.info("File not copied to the new directory")
                print("File not copied to the new directory")
            return path
        except Exception as e:
            logging.exception("An exception occurred in moving to test directory: %s", e)

    def send_csv(self, path):
        try:
            logging.info("Files are being sent to server ....")
            print("Files are being sent to server ....")

            del_new_directory = False

            new_files = glob.glob(f"{path}/*.csv")
            logging.info("Length of all Files: %s", str(len(new_files)))
            print("Length of all Files: %s", str(len(new_files)))

            if not new_files:
                logging.warning("No CSV files found in the directory.")
                print("No CSV files found in the directory.")
                return

            file_path = new_files[0]
            logging.info("File Path: %s", file_path)

            for attempt in range(3):  # Retry up to 3 times
                try:
                    with open(file_path, "rb") as file:
                        files = {"file": (file_path, file)}
                        response = requests.post(f"{self.ENDPOINT}csv/upload", files=files)

                    if response.status_code == 200:
                        logging.info("File sent successfully.")
                        print("File sent successfully.")
                        del_new_directory = True
                        break  # Exit retry loop if successful
                    else:
                        logging.error("Failed to send file. Status Code: %s", response.status_code)
                        print("Failed to send file. Status Code: %s", response.status_code)
                except requests.RequestException as e:
                    logging.error("Error while sending file to server: %s", e)
                    print("Error while sending file to server: %s", e)

                time.sleep(2 ** attempt)  # Exponential backoff

            if del_new_directory:
                try:
                    count = 0
                    for file in new_files:
                        os.remove(file)
                        count += 1
                    logging.info("Total No. of Files that are deleted: %s", str(count))
                    print("Total No. of Files that are deleted: %s", str(count))
                except Exception as e:
                    logging.error("Error while deleting files: %s", e)
                    print("Error while deleting files: %s", e)

        except Exception as e:
            logging.exception("An exception occurred in send_csv: %s", e)
            print("An exception occurred in send_csv: %s", e)

    def send_log(self):
        try:
            logging.info("Log Send Server")
            print("Log Send Server")

            # Close the current log file
            logging.shutdown()

            delete_new_directory = False

            new_files_2 = glob.glob(f"{self.log_folder}/*.log")
            logging.info("Length of all Files: %s", str(len(new_files_2)))
            print("Length of all Files: %s", str(len(new_files_2)))

            file_path2 = new_files_2[0]
            logging.info("File Path: %s", file_path2)

            # Path to the txt file you want to send
            log_file_path = f"{file_path2}"  # Replace with the actual path

            # Open the log file and read its content
            with open(log_file_path, "rb") as log_file:
                log_content = log_file.read()

            # Prepare the files dictionary for the request
            files = {"file": ("logfile.log", log_content)}

            # Make the POST request to the FastAPI server
            response = requests.post(f"{self.ENDPOINT}logging/receive-logfile", files=files)

            # Check the response
            print(response.status_code)
            print(response.json())

            delete_new_directory = True

            if delete_new_directory:
                t1 = 0
                for _ in new_files_2:
                    os.remove(_)
                    t1 = t1 + 1
                logging.info("Total No. of Files that are deleted: %s", str(t1))
                print("Total No. of Files that are deleted: %s", str(t1))
        except Exception as e:
            logging.exception("An exception occurred in _7_LogSendServer: %s", e)

# # Create a new log file
# new_log_file_path = os.path.join(log_folder, "script_log.txt")
# logging.basicConfig(
#     filename=new_log_file_path,
#     level=logging.DEBUG,
#     format="%(asctime)s - %(levelname)s - %(message)s",
# )

# logging.info("New log file created: %s", new_log_file_path)
