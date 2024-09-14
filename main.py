from files import Files
import time

if __name__ == "__main__":
    process = Files()
    try:
        DESIRED_DURATION = 10
        elapsed_time2 = time.time() - process.START_TIME
        while elapsed_time2 <= DESIRED_DURATION:
            process.files_generation()
            elapsed_time2 = time.time() - process.START_TIME
        try:
            process.send_csv(process.move_to_upload_queue(process.backup_check()))
        except Exception as e:
            process.logger.error(e)
            process.send_log()
    except Exception as e:
        process.logger.error(e)
        process.send_log()
