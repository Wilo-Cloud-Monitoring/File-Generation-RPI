# File Generation for Raspberry Pi

This repository contains scripts and tools for generating configuration files and data files on a Raspberry Pi. It is part of the **Cloud-Based Condition Monitoring for Diagnostic Health Monitoring of Machine Tool** project, aimed at managing and processing sensor data for real-time health monitoring of machine tools.

## Project Overview

The **File Generation for Raspberry Pi** project provides utilities for automating the creation and management of files necessary for sensor data processing. This includes setup scripts, data logs, and configuration files specifically for the MPU6050 sensors used in the system.

## Features

- **File Creation**: Automates the generation of configuration and data files for Raspberry Pi.
- **MPU6050 Configuration**: Generates and manages configuration files for integrating MPU6050 sensors.
- **Data Logging**: Creates logs for tracking data generated by the MPU6050 sensors.

## Getting Started

### Prerequisites

- **Raspberry Pi**: Set up with an appropriate OS (e.g., Raspberry Pi OS).
- **Python**: Ensure Python 3.x is installed on your Raspberry Pi.
- **Git**: Ensure Git is installed to clone the repository.
- **MPU6050 Sensors**: Connected to the Raspberry Pi via I2C.

### Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/Wilo-Cloud-Monitoring/File-Generation-RPI-.git
   cd File-Generation-RPI-
   ```

2. **Install Dependencies**:
   - Navigate to the directory containing the project.
   - Install any required Python libraries. For example:
     ```bash
     pip install -r requirements.txt
     ```
3. **Create env file**:
    - Create a .env file.
    - Add info about wifi there.
   ```bash
    touch .env
   ```
   - Add following in the file
   - Don't Give space in between
   ```chatinput
    SSID=name_of_wifi
    WIFI_PASSWORD=password
   ```
4. **Run the Scripts**:
   - Execute the main script to generate the necessary files:
     ```bash
     python main.py
     ```

## Usage

- **Configuration Files**: Modify `config_template.json` to customize settings for the MPU6050 sensors and data collection.
- **Data Logs**: Logs are saved in the `logs` directory. Review these logs to ensure proper data generation and file creation.

## Contact

For questions or support, please contact [rahulaauji71@gmail.com](mailto:rahulaauji71@gmail.com).
