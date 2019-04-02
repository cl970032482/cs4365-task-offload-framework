import pickle
import socket
import struct

import cv2

from taskified import tasks

HOST = ''
PORT = 8089

def run_task(task_func, args):
    # Call task
    if args is None:
        # No args to pass
        return task_func()
    elif type(args) is tuple:
        # Unzip tuple into args
        return task_func(*args)
    else:
        # Single arg
        return task_func(args)


def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print('Socket created')

    s.bind((HOST, PORT))
    print('Socket bind complete')
    s.listen(10)
    print('Socket now listening')

    conn, addr = s.accept()

    data = b''
    next_task_args_list = []
    num_next_task_args = 0
    next_task_num = 0
    payload_size = struct.calcsize("L")

    while True:
        # Retrieve number of args for next task
        # TODO handle 0 args with num args
        while len(data) < payload_size:
            data += conn.recv(4096)

        packed_num_next_task_args = data[:payload_size]
        data = data[payload_size:]
        num_next_task_args = struct.unpack("L", packed_num_next_task_args)[0]

        # Retrieve the next task index
        while len(data) < payload_size:
            data += conn.recv(4096)

        packed_next_task_num = data[:payload_size]
        data = data[payload_size:]
        next_task_num = struct.unpack("L", packed_next_task_num)[0]

        # Retrieve all args per task
        for i in range(num_next_task_args):
            # Retrieve each argument size
            while len(data) < payload_size:
                data += conn.recv(4096)
            packed_argsize = data[:payload_size]
            data = data[payload_size:]
            argsize = struct.unpack("L", packed_argsize)[0]

            # Retrieve data based on arg size
            while len(data) < argsize:
                data += conn.recv(4096)

            next_arg_data = data[:argsize]
            data = data[argsize:]
            # Extract next arg
            next_arg = pickle.loads(next_arg_data)

            next_task_args_list.append(next_arg)

        # Set variables and args for running tasks
        next_task_run_index = next_task_num
        if len(next_task_args_list) == 0:
            # No args to pass
            next_task_args = None
        elif len(next_task_args_list) == 1:
            next_task_args = next_task_args_list[0]
        else:
            # FIXME assuming more than 1 arg means tuple form is required for params
            next_task_args = tuple(next_task_args_list)

        # Save the args of the next task to be run in case task loop is reset
        next_task_args_saved = next_task_args

        while True:
            task = tasks[next_task_run_index]
            to_continue, next_task_args = run_task(task_func=task,
                                                   args=next_task_args)
            # Converting args to list format
            # next_task_args_list = []
            # if next_task_args is not None:
            #     if type(next_task_args) is tuple:
            #         for arg in next_task_args:
            #             next_task_args_list.append(arg)
            #     else:
            #         next_task_args_list.append(next_task_args)

            if next_task_run_index == (len(tasks) - 1):
                # data = b''
                break

            next_task_run_index += 1

            if to_continue is False:
                # FIXME reset to initially offloaded task or first task
                next_task_run_index = 0
                next_task_args = None
                # next_task_run_index = next_task_num
                # next_task_args = next_task_args_saved



if __name__ == '__main__':
    main()