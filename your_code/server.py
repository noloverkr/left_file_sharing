# coding for server part
# import part of code
import struct
import os
import socket
import json
import threading
import time


# function to traversal 'stare' folder
# store files in 'share' folder into a list
def traversal_folder(folder_name):
    # create a list
    files = list()

    # use os.listdir() to make a position
    folder_list = os.listdir(folder_name)

    # traverse and add elements to the list
    for folder_contain in folder_list:
        file = os.path.join(folder_name, folder_contain)

        # if the object at this path is a file, append it to the list
        if os.path.isfile(file):
            files.append(file)

        else:
            files.extend(traversal_folder(file))

    # return the result of the list
    return files


# function to get the md5 value of file
def get_md5_value(file):
    # In Linux, the md5sum command is used to generate and verify the md5 value of the file
    file_md5 = os.popen('md5sum ' + file).read().split()[0]
    return file_md5


# The connection function of server part
def server_connection(server_socket, file):
    connection_socket, address = server_socket.accept()
    print(address, 'begins to transfer', file, '!')

    # the size of buffer: 1MB
    buffer_size = 1024 * 1024

    # the size of file
    file_size = os.path.getsize(file)

    # the md5 value of file
    # it will take a lot of time to make a calculation, so annotate it
    # md5_value = get_md5_value(file)

    # the modify time of file
    file_mtime = os.path.getmtime(file)

    # sending-package structure
    # |<--4-UINT--->|<-string->|<-part of file->|
    # +-----------------------------------------+
    # |-len of JSON-|---JSON---|------BIN-------|
    # +-----------------------------------------+
    # |<--4 bytes-->|<--------N bytes---------->|

    # the header of transfer file
    # some basic information of this file will be stored in this header and used to make related calculation
    header = {'file_name': file, 'file_size': file_size,
              'file_buffer': buffer_size, 'file_mtime': file_mtime}

    # the json format of header
    header_json = json.dumps(header).encode()

    # struct: pack the json header ('!': network; '!': unit)
    header_len = struct.pack('!I', len(header_json))

    # send this information to client
    connection_socket.send(header_len)
    connection_socket.send(header_json)

    # receive_part -> receive the receive status from the client
    receive_len = connection_socket.recv(4)
    receive_unpack = struct.unpack('!I', receive_len)[0]
    receive_num = connection_socket.recv(receive_unpack).decode()
    receive_block_number = int(receive_num)

    # send file
    # 'rb': binary method to read binary files
    with open(file, 'rb') as f:
        # calculate the current position of sending
        updated_position = receive_block_number * buffer_size

        # seek the current position of sending
        f.seek(updated_position)

        while True:
            # read file in buffer size
            content = f.read(buffer_size)

            # if content is not empty, send information
            if content:
                connection_socket.send(content)

            # if content is empty, just break
            else:
                break

    # report the result: finish transfer
    print('the file transfer is finished!')

    # close the socket
    connection_socket.close()


# the main function the server part
def run_server(folder_name):
    # create two sockets: server_socket_1 and server_socket_2
    server_socket_1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket_2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # add port reuse properties
    # prevent port occupation
    server_socket_1.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket_2.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # binding function for binding information
    server_socket_1.bind(('', 26780))
    server_socket_2.bind(('', 28560))

    # function to listen state
    server_socket_1.listen(128)
    server_socket_2.listen(128)

    while True:
        # wait for client's connection
        print('prepare the connection!')

        connection_socket, client_address = server_socket_1.accept()

        # report the connection status
        print(client_address, 'has built a connection!')

        # begin to receive the file list from the client -> a json part
        receive_file_list_json = connection_socket.recv(20480).decode()

        # translate it from json to list
        receive_file_list = json.loads(receive_file_list_json)

        # local files in 'share' folder
        local_file_list = traversal_folder(folder_name)

        # different list: store some mission files or updated files
        # set means unique
        # function of difference: in local file list but not in the receive file list
        different_list = list(set(local_file_list).difference(set(receive_file_list)))

        # remove files (file ends with '.temp')
        for file_name in different_list:
            if file_name.endswith('.temp'):
                different_list.remove(file_name)

        # update the local file list
        local_file_list = traversal_folder(folder_name)

        # the current length of local file list -> need to be used to judge if the file list get update
        local_len = len(local_file_list)

        # method 1
        # create a dictionary to store the modify time of files in the current folder
        # method 2
        # create a dictionary to store the md5 value of files in the current folder
        # method 2 will cost more time to finish the whole program so we choose method 1
        local_file_time = dict()
        for file in local_file_list:
            # os.path.getmtime(): get the modify time of file
            local_file_time.update({file: os.path.getmtime(file)})

        # if there are not elements in different list, consider whether part of files get updated
        if len(different_list) == 0:

            # sleep 2 seconds, re-traverse folder to check whether folder get updated
            time.sleep(2)

            # current file number in the 'share' folder
            judge_len = len(traversal_folder(folder_name))

            # make a judgement
            if local_len == judge_len:

                # check the modify time (or md5 value) of current file
                # if modify time (or md5 value) is change, append this file to different list
                for file in local_file_list:

                    if os.path.exists(file):
                        file_mtime = os.path.getmtime(file)

                        # may cause error so we need to judge whether the file in dictionary's keys
                        if file in local_file_time.keys() and file_mtime != local_file_time[file]:
                            different_list.append(file)

        # due to update by using the time.sleep(), there may exist new file ends with '.temp'
        # again remove file ends with 'temp' to avoid a download error
        for file_name in different_list:
            if file_name.endswith('.temp'):
                different_list.remove(file_name)

        # report the different list
        print(different_list)

        # send this different list to the client
        different_list_json = json.dumps(different_list).encode()
        different_list_len = struct.pack('!I', len(different_list_json))

        connection_socket.send(different_list_len)
        connection_socket.send(different_list_json)

        # send every file in this different list
        for file in different_list:
            # create threads and manage them
            thread = threading.Thread(target=server_connection, args=(server_socket_2, file))

            thread.start()
            thread.join()


# **********************************************End of server part******************************************************
