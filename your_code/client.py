# coding for client part
# import part of code
import socket
import json
import os
import struct
import threading
# also need to traverse folder
# import the traversal function defined in the server part
from server import traversal_folder


# function to create dirs
def make_dirs(dir_path):
    # remove space
    dir_path = dir_path.strip()

    # remove '\' in final part
    dir_path = dir_path.rstrip('\\')

    # determine whether path is exist:
    # True: exist -> print 'already exist'
    # False: not exist -> create path
    is_exist = os.path.exists(dir_path)

    # for False
    if not is_exist:
        os.makedirs(dir_path)

        print(dir_path, 'has created successfully!')

        return True

    # for True
    else:
        print(dir_path, 'already exists!')

        return False


# the connection function of client part
def client_connection(server, server_port):
    # current connection status
    connection_status = False

    # build socket for client part
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # (try, except)->resume from interruption
    while True:
        # put statements to avoid warning
        # noinspection PyBroadException
        try:
            # if the current connection is failed, make the re-connection
            if not connection_status:
                client_socket.connect((server, server_port))

                # report the current connection status
                print('The connection is set up!')

                # change the connection status from False to True
                connection_status = True

                # if the connection status is True
                if connection_status:
                    try:
                        # get header of files
                        header_receive = client_socket.recv(4)
                        header_len = struct.unpack('!I', header_receive)[0]
                        header_json = client_socket.recv(header_len).decode()
                        header = json.loads(header_json)

                        # The total size of file
                        total_size = header['file_size']

                        # if the transferred file need to be re-transferred, delete the current one
                        if os.path.exists(header['file_name']):
                            os.remove(header['file_name'])

                        # if the file is last interrupt, the file will ends with 'temp'
                        if os.path.exists(header['file_name'] + '.temp'):
                            # get size of received part
                            receive_size = os.path.getsize(header['file_name'] + '.temp')

                        # if it is a new file, set 0
                        else:
                            receive_size = 0

                        # calculate received block numbers
                        # '//' means integer division
                        received_block_number = int(receive_size // header['file_buffer'])

                        # report the received block numbers
                        print(received_block_number)

                        # send the receive status to server
                        block_info = str(received_block_number).encode()
                        pack_block = struct.pack('!I', len(block_info))

                        # send
                        client_socket.send(pack_block)
                        client_socket.send(block_info)

                        # current position of file
                        current_position = received_block_number * header['file_buffer']

                        # receive files
                        # the meaning of open mode 'ab':
                        # Open a file in binary format for appending.
                        # If the file already exists, the file pointer will be placed at the end of the file.
                        # In other words, the new content will be written after the existing content.
                        # If the file does not exist, create a new file for writing.
                        with open(header['file_name'] + '.temp', 'ab') as f:
                            # seek position of file
                            f.seek(current_position)
                            while True:
                                # receive buffer sized block
                                content = client_socket.recv(header['file_buffer'])

                                # if content is not empty
                                if content:
                                    # write content to file
                                    f.write(content)

                                    # the transfer processing bar
                                    # not use sendall, the module tqdm may cause some bugs
                                    # use calculation to replace it (use cause some error caused by threads)
                                    current_size = os.path.getsize(header['file_name'] + '.temp')
                                    processing_line = float(current_size / total_size * 100)

                                    # report the status of processing
                                    # print the processing bar
                                    print('the program has successfully download %.2f %%' % processing_line)

                                # if content is empty, just break
                                else:
                                    break

                        # report the status of download
                        if os.path.getsize(header['file_name'] + '.temp') == total_size:
                            if os.path.exists(header['file_name']):
                                os.remove(header['file_name'])

                            # change the file name to its original status -> remove the flag '.temp'
                            # os.rename(src, dst)
                            os.rename(header['file_name'] + '.temp', header['file_name'])
                            print(header['file_name'], 'has download successfully!')

                        else:
                            os.remove(header['file_name'] + '.temp')
                            print(header['file_name'], 'download failed!')

                        client_socket.close()
                        break

                    # except the inner exception
                    except Exception as ex_1:
                        # print the content of this exception
                        print(ex_1)

        # except the outer exception
        except Exception:
            # set the connection status to False
            connection_status = False

            # close the socket
            client_socket.close()


# the main function of client part
def run_client(server, folder_name):
    # define the server port
    server_port_1 = 26780
    server_port_2 = 28560

    while True:
        # set the connection status to False
        connection_status = False
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # resume from interruption
        # put statements to avoid warning
        # noinspection PyBroadException
        try:
            # if the current connection status is False
            if not connection_status:
                # build a connection to server
                client_socket.connect((server, server_port_1))

                # change the connection statue to True
                connection_status = True

                # report the status of client part
                print('The client part start to work!')

                # traverse folder and send file list
                file_list = traversal_folder(folder_name)

                file_json = json.dumps(file_list).encode()
                client_socket.send(file_json)

                # list of different files
                different_files_receive = client_socket.recv(4)
                different_len = struct.unpack('!I', different_files_receive)[0]
                files_json = client_socket.recv(different_len).decode()
                different_list = json.loads(files_json)

                # path of the folder
                for file_name in different_list:
                    part_1, part_2 = os.path.split(file_name)
                    make_dirs(part_1)

                # processing times -> the amount of dealing files
                receive_times = len(different_list)

                # calling function client_connection to receive files
                for each_time in range(receive_times):
                    thread = threading.Thread(target=client_connection, args=(server, server_port_2))
                    thread.start()
                    thread.join()

        # except the exception -> OS Error: connection refused
        # print will affect the viewing of the program -> no print, just pass
        except Exception:
            # Maintain the integrity of the entire code
            pass


# *********************************************End of client part*******************************************************
