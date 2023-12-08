from datetime import datetime, timedelta  
from pathlib import Path
import os
import re
from collections import OrderedDict
from pprint import pprint
import tempfile
import sys
# import urllib, requests

from dotenv import load_dotenv

from log import log, init_logger

load_dotenv()
init_logger(
    os.getenv("LOGFILE"),
    os.getenv("TELEGRAM_NOTIFICATION_BOT_TOKEN"),
    os.getenv("TELEGRAM_NOTIFICATION_CHAT_ID"),
    os.getenv("TELEGRAM_MESSAGE_THREAD_ID"),
    )

BACKUPS_PATH = Path(os.getenv("BACKUPS_DIR"))

BACKUP_FILENAME_TEMPLATE = "server_prod_{now}.tar.gz"

SQLDUMP_FILENAME_TEMPLATE = "server_prod_{now}.sql"

PG_DUMP_COMMAND_TEMPLATE = "PGPASSWORD={password} pg_dump -U {user} {database} -p {port} -h localhost > {filename}"

TAR_COMMAND_TEMPLATE = "tar -czf {archive_filename} -C {dump_dirname} {dump_filename} -C {media_dirpath} {media_dirname}"

FILENAME_DATETIME_FORMAT = "%Y_%m_%d_%H_%M_%S"

BACKUPS_TIMETABLE = [
    0,
    1, 
    2,
    3,
    7,
    30,
    180,
    360,
]

DUMP_MINIMAL_FILESIZE = int(os.getenv("DUMP_MINIMAL_FILESIZE_MB")) * 1024 * 1024

def main():
    now = datetime.now()
    now_str = now.strftime(FILENAME_DATETIME_FORMAT)
    log.info(f"Backup script started: {now_str}")
    create_backup_file(now_str)
    rotate_backups(now)
    log.warning(f"Backup prod data script was successfully ended. timestamp: {now_str}")
    
def create_backup_file(now):
    log.info("create_backup_file started")
    archive_filename = BACKUPS_PATH / BACKUP_FILENAME_TEMPLATE.format(now=now)
    with tempfile.TemporaryDirectory() as tmpdirname:
        dump_filename = SQLDUMP_FILENAME_TEMPLATE.format(now=now)
        dump_filepath = Path(tmpdirname) / dump_filename 
        create_dump_postgres(now, dump_filepath)
        tar_command = TAR_COMMAND_TEMPLATE.format(
            archive_filename=archive_filename,
            dump_dirname=tmpdirname,
            dump_filename=dump_filename,
            media_dirpath=os.getenv("MEDIA_DIRPATH"),
            media_dirname=os.getenv("MEDIA_DIRNAME"),
        )

        log.debug(f"tar_command = {tar_command}")
        result = os.system(tar_command)
        if result != 0:
            log.error(f"tar failed with code {result}, command = {tar_command}")
            sys.exit(20)
        file_size = os.path.getsize(archive_filename)
        if file_size < DUMP_MINIMAL_FILESIZE:
            log.warning(f"database dump filesize is too small {file_size} bytes. Expected to be more than {DUMP_MINIMAL_FILESIZE} bytes")
        
def  create_dump_postgres(now, dump_filename):     
    command = PG_DUMP_COMMAND_TEMPLATE.format(
        password=os.getenv("DATABASE_PASSWORD"),
        user=os.getenv("DATABASE_USER"),
        database=os.getenv("DATABASE_NAME"),
        port=os.getenv("DATABASE_PORT"),
        filename=dump_filename,
    )
    result = os.system(command)
    if result != 0:
        log.error(f"pg_dump failed with code {result}, command = {command}")
        sys.exit(10)

def rotate_backups(now):
    def add_backup(intervals, backup):
        for interval in intervals:
            if interval["start"] <= backup["timestamp"] and backup["timestamp"] < interval["end"]:
                interval["backups"].append(backup)
                return
        log.warning(f"found a file that does not belong to any interval: {backup}")


    def clear_extra_backups(intervals):
        for interval in intervals: 
            backups = sorted(interval["backups"], key=lambda a: a["timestamp"], reverse=True)
            for i in range(len(backups) - 1):
                filename = backups[i]["filename"] 
                log.info(f"deleting extra backup: {filename}")
                os.remove(filename)
                backups[i]["status"] = "deleted" 

    log.info("rotate_backups started") 
    intervals = []
    for i in range(len(BACKUPS_TIMETABLE) - 1):
        end = BACKUPS_TIMETABLE[i]
        start = BACKUPS_TIMETABLE[i + 1]
        intervals.append({
            "start": now - timedelta(days=start), 
            "end": now - timedelta(days=end),
            "backups": [],
            "days_end": BACKUPS_TIMETABLE[i],
            "days_start": BACKUPS_TIMETABLE[i + 1],
        })

    for filename in BACKUPS_PATH.iterdir():
        if filename.is_dir():
            log.warning(f"unexpected directory: {filename}")
        else:
            found = re.search("server_prod_(.+)\.tar\.gz", filename.name)
            if found is None:
                log.warning(f"found file without date in name: {filename}")
            else: 

                timestamp = found.group(1)    
                timestamp = datetime.strptime(timestamp, FILENAME_DATETIME_FORMAT)
                add_backup(intervals, {
                    "timestamp": timestamp,
                    "filename": filename,
                    "status": "exists",
                    }) 

    clear_extra_backups(intervals)       
    pprint(intervals)

if __name__ == "__main__":
    main()
