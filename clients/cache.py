import logging
import shutil
import json
import os


class NoCachedData(Exception):
    pass


class CacheClient:
    def __init__(self, local_dir_path: str):
        self.local_dir_path = local_dir_path
        self.create_local_cache_dir()

    def create_local_cache_dir(self):
        if not os.path.exists(self.local_dir_path):
            logging.info("creating local cache directory"
                         f" {self.local_dir_path}")
            os.makedirs(self.local_dir_path)
        else:
            logging.info("reusing local cache directory"
                         f" {self.local_dir_path}")
            return

    def save_data_to_file(self, file_data: dict,
                          dir_path: str, file_name: str = None):
        file_name = file_name if file_name else "data.json"
        dir_path = os.path.join(self.local_dir_path, dir_path)
        file_path = os.path.join(dir_path, file_name)

        if not os.path.exists(dir_path):
            logging.info(f"creating file {file_name} under path {dir_path}")
            os.makedirs(dir_path)

        logging.info(f"caching data to file {file_name}, path {dir_path}")
        with open(file_path, "w") as file:
            json.dump(file_data, file, ensure_ascii=False, indent=2)

    def load_data_from_file(self, dir_path: str, file_name: str = None):
        file_name = file_name if file_name else "data.json"
        dir_path = os.path.join(self.local_dir_path, dir_path)

        if not os.path.exists(dir_path):
            raise NoCachedData
        else:
            logging.info(f"loading cached data from file {file_name}, path {dir_path}")
            file_path = os.path.join(dir_path, file_name)
            with open(file_path, "r+") as file:
                file_data = json.load(file)
                return file_data

    def clean_up_empty_dirs(self):
        directories = [os.path.join(current_dir, _dir)
                       for current_dir, sub_dirs, files in os.walk(self.local_dir_path, topdown=False)
                       for _dir in sub_dirs]
        for dir_path in directories:
            try:
                if not os.listdir(dir_path):
                    logging.info(f"removing empty directory {dir_path}")
                    os.rmdir(os.path.realpath(os.path.join(dir_path)))
            except FileNotFoundError:
                logging.info(f"{dir_path} does not exist - "
                             f"probably removed by another processor?")

    def clean_up_cached_dir(self, dir_path: str):
        if not dir_path:
            logging.warning("no directory path was provided")
            return
        else:
            dir_path = os.path.join(self.local_dir_path, dir_path)
            logging.info(f"cleaning up directory path {dir_path}")
            shutil.rmtree(dir_path, onerror=FileNotFoundError)
            self.clean_up_empty_dirs()
            return
