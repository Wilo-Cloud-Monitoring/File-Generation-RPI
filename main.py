#!/bin/bash
from files import Files
import time

if __name__ == "__main__":
    process = Files()
    try:
        while True:
            process.START_TIME = time.time()
            elapsed_time = 0
            while elapsed_time <= process.DESIRED_DURATION:
                try:
                    process.files_generation()
                except Exception as e:
                    process.logger.error(f"Error during file generation: {e}")
                    process.send_log()
                finally:
                    elapsed_time = time.time() - process.START_TIME
            try:
                process.send_csv(process.move_to_upload_queue(process.backup_check()))
            except Exception as e:
                process.logger.error(e)
                process.send_log()
    except Exception as e:
        process.logger.error(e)
        process.send_log()
