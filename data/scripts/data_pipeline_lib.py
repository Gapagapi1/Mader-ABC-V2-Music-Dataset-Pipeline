import os
import sys
import time
import json
import psutil
import subprocess
import concurrent.futures


def default_path_converter(from_path: str, is_folder: bool):
    return os.path.basename(from_path)


def verify_software_dependency(executable_path):
    abs_executable_path = os.path.abspath(os.path.join("softwares", executable_path))
    if not os.path.exists(abs_executable_path):
        print("Executable ({}) does not exist.".format(abs_executable_path))
        sys.exit(1)
    return abs_executable_path


class Process:
    def __init__(self, name: str, from_folder_path: str, to_folder_path: str, to_folder_exist_ok: bool = False):
        self.name = name
        self.from_folder_path = from_folder_path
        self.to_folder_path = to_folder_path

        if not os.path.exists(self.from_folder_path):
            print("[{}] Source directory ({}) not found.".format(self.name, self.from_folder_path))
            sys.exit(1)

        if not to_folder_exist_ok and os.path.exists(self.to_folder_path):
            print("[{}] Target directory ({}) already exists.".format(self.name, self.to_folder_path))
            sys.exit(1)

        os.makedirs(self.to_folder_path)

        print("[{}] Process from {} to {} created.".format(self.name, self.from_folder_path, self.to_folder_path))


    def step_by_function(self,
                         process_function,
                         path_converter = default_path_converter,
                         folder_exist_ok: bool = False,
                         file_exist_ok: bool = False,
                         consider_empty_folders: bool = False,
                         empty_folder_ok: bool = False,
                         allocated_cores: int = None,
                         status_update_time_delta_threshold: float = 1):
        if allocated_cores is None:
            allocated_cores = psutil.cpu_count()

        print("[{}] Process from {} to {} running {} on {} cores.".format(self.name, self.from_folder_path, self.to_folder_path, process_function.__name__, allocated_cores))

        start_time = time.time()
        last_status_update_time = start_time

        i = 0

        futures = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=allocated_cores) as executor:
            for root, folders, files in os.walk(self.from_folder_path):
                if not consider_empty_folders and len(files) == 0:
                    if empty_folder_ok:
                        print("[{}] Empty folder ({}) found.".format(self.name, root))
                        sys.exit(1)
                    continue

                folder_path = root
                new_folder_path = os.path.join(self.to_folder_path, path_converter(os.path.abspath(folder_path), True))

                if not folder_exist_ok and os.path.exists(new_folder_path):
                    print("[{}] Folder path ({}) already exists.".format(self.name, new_folder_path))
                    sys.exit(1)

                os.makedirs(new_folder_path)

                for file in files:
                    file_path = os.path.join(root, file)
                    new_file_path = os.path.join(new_folder_path, path_converter(os.path.abspath(file_path), False))

                    if not file_exist_ok and os.path.exists(new_file_path):
                        print("[{}] File path ({}) already exists.".format(self.name, new_file_path))
                        sys.exit(1)

                    future = executor.submit(process_function, os.path.abspath(file_path), os.path.abspath(new_file_path))
                    futures.append(future)
                    i += 1

                if time.time() - last_status_update_time > status_update_time_delta_threshold and i != 0:
                    print("[{}] Processing: {}.".format(self.name, i))
                    last_status_update_time = time.time()

        for future in concurrent.futures.as_completed(futures):
            exception = future.exception()
            if exception is not None:
                print("[{}] There was an exception during the process: {}.".format(self.name, exception))

        print("[{}] Processing: {}.".format(self.name, i))

    def step_by_popen(self,
                      process_command: str,
                      job_args: list[str],
                      default_data: list,
                      print_stdout: bool,
                      print_stderr: bool,
                      max_retry_count: int = 1,
                      print_stdout_to_file: bool = False,
                      job_args_stdout_file_name_index: int = None,
                      allocated_cores: int = None,
                      status_update_time_delta_threshold: float = 1,
                      scheduler_tick_rate: float = 0.1,
                      debug: bool = False):
        if allocated_cores is None:
            allocated_cores = psutil.cpu_count()

        if print_stdout_to_file and job_args_stdout_file_name_index is None:
            print("[{}] print_stdout_to_file is True but job_args_stdout_file_name is None.".format(self.name))
            sys.exit(1)

        print("[{}] Process from {} to {} running {} with {} cores.".format(self.name, self.from_folder_path, self.to_folder_path, process_command, allocated_cores))

        retries = {}
        data = {}
        for i in range(len(job_args)):
            retries[i] = 0
            data[i] = default_data.copy()

        start_time = time.time()
        last_status_update_time = start_time

        job_index = 0
        running_processes = []

        failed_jobs = []

        while job_index < len(job_args) or len(running_processes) > 0:
            while job_index < len(job_args) and len(running_processes) < allocated_cores:
                job = job_args[job_index]

                cmd = process_command.format(*job)

                proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                running_processes.append((proc, cmd, job, job_index))

                job_index += 1

            for proc_tuple in running_processes.copy():
                curr_proc, curr_cmd, curr_job, curr_job_index = proc_tuple

                try:
                    stdout, stderr = curr_proc.communicate(timeout=0.01)
                    # buff[job[0]][1] += stdout
                    # buff[job[0]][2] += stderr
                except subprocess.TimeoutExpired:
                    pass

                if curr_proc.poll() is not None:  # process finished
                    stdout, stderr = curr_proc.communicate()
                    # buff[job[0]][1] += stdout
                    # buff[job[0]][2] += stderr
                    # stdout, stderr = buff[job[0]][1], buff[job[0]][2]
                    if debug:
                        print("[{}] Outcome for process {}:\n\t• Command: {}\n\t• Number of fails: {}".format(self.name, curr_proc.pid, curr_cmd, retries[curr_job_index]))
                        if print_stdout or print_stderr:
                            print("\t• Logs:")
                            if print_stdout:
                                print("___________stdout___________\n\n{}\n____________________________".format(stdout))
                            if print_stderr:
                                print("___________stderr___________\n\n{}\n____________________________".format(stderr))
                    if curr_proc.returncode != 0:
                        if debug:
                            print("\t• Error code: {}".format(curr_proc.returncode))
                        if retries[curr_job_index] > max_retry_count:
                            failed_jobs.append(curr_job)
                            del data[curr_job_index]
                            del retries[curr_job_index]
                        else:
                            retries[curr_job_index] += 1

                            cmd_restart = process_command.format(*curr_job)
                            new_proc = subprocess.Popen(cmd_restart, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                            running_processes.append((new_proc, cmd_restart, curr_job, curr_job_index))

                            data[curr_job_index] = default_data.copy()
                    else:
                        if debug:
                            print("\t• Successful!")
                        del data[curr_job_index]
                        del retries[curr_job_index]
                        if print_stdout_to_file:
                            with open(curr_job[job_args_stdout_file_name_index], "wb") as json_file:
                                json_file.write(stdout)
                    running_processes.remove(proc_tuple)
            if time.time() - last_status_update_time > status_update_time_delta_threshold:
                print("[{}] Processing: {}/{} ({:.2f}h) | {} instance(s) | {} job(s) failed.".format(self.name, job_index, len(job_args), ((len(job_args) - job_index) * ((time.time() - start_time) / job_index)) / 3600.0, len(running_processes), len(failed_jobs)))
                last_status_update_time = time.time()
            time.sleep(scheduler_tick_rate)

        print("[{}] Processing: {}/{} ({:.2f}h) | {} instance(s) | {} job(s) failed.".format(self.name, job_index, len(job_args), ((len(job_args) - job_index) * ((time.time() - start_time) / job_index)) / 3600.0, len(running_processes), len(failed_jobs)))

        print("[{}] Failed jobs:".format(self.name), failed_jobs)

        with open("./results/failed_jobs_{}.json".format(self.name), "w") as wrong_file:
            json.dump(failed_jobs, wrong_file)
