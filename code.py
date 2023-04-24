import os
import shutil
import argparse
import logging
import time
import threading
from configparser import ConfigParser

# Define the functions for listing, copying, and logging files

def list_files(path):
    files = []
    for root, directories, filenames in os.walk(path):
        for filename in filenames:
            files.append(os.path.join(root, filename))
    return files

def copy_files(files, dst):
    for file in files:
        dst_file = os.path.join(dst, os.path.relpath(file, args.source))
        dst_dir = os.path.dirname(dst_file)
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)
        shutil.copy2(file, dst_file)

def log_operation(operation, src_file, dst_file=None):
    if operation == 'copy':
        logging.info(f'Copied {src_file} to {dst_file}')
        print(f'Copied {src_file} to {dst_file}')
    elif operation == 'remove':
        logging.info(f'Removed {src_file}')
        print(f'Removed {src_file}')

# Read the configuration options from the config.ini file

config = ConfigParser()
config.read('config.ini')

parser = argparse.ArgumentParser(description='Synchronize two folders')
parser.add_argument('--source', type=str, default=config.get('sync', 'source'),
                    help='The path of the source folder')
parser.add_argument('--replica', type=str, default=config.get('sync', 'replica'),
                    help='The path of the replica folder')
parser.add_argument('--interval', type=int, default=config.getint('sync', 'interval'),
                    help='The synchronization interval in seconds')
parser.add_argument('--log', type=str, default=config.get('sync', 'log'),
                    help='The path of the log file')
args = parser.parse_args()

logging.basicConfig(filename=args.log, level=logging.INFO,
                    format='%(asctime)s %(levelname)s: %(message)s')

# Define the function for synchronizing the folders periodically

def sync_folders():
    # Compare the source and replica folders
    src_files = set(list_files(args.source))
    dst_files = set(list_files(args.replica))

    # Copy new and modified files from source to replica
    files_to_copy = src_files - dst_files
    copy_files(files_to_copy, args.replica)
    for file in files_to_copy:
        log_operation('copy', file, os.path.join(args.replica, os.path.relpath(file, args.source)))

    # Remove deleted files from replica
    files_to_remove = dst_files - src_files
    for file in files_to_remove:
        if os.path.exists(os.path.join(args.source, os.path.relpath(file, args.replica))):
            continue  # File exists in source, so don't remove
        os.remove(file)
        log_operation('remove', file)

    # Schedule the next synchronization
    threading.Timer(args.interval, sync_folders).start()

# Start the initial synchronization
sync_folders()

# Wait for the program to be interrupted
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    pass
