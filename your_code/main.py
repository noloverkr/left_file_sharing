# the main function of the coding -> the starting python script 'main.py'
# import part of code
import argparse
import os
import threading

# import the main function of server part
from server import run_server

# import the main function of client part
from client import run_client


# function to add information of ip address
# Run command: python3 main.py --ip <peer’s ipv4 address>
def __argparse():
    parser = argparse.ArgumentParser('This is a description!')
    parser.add_argument('--ip', action='store', required=True, dest='ip', help='The ip address of PC')
    return parser.parse_args()


# set a global variable of pc's ip address
pc_ip = 0


# function to require pc's ip address
def ip_address():
    ip_add = __argparse().ip
    global pc_ip
    pc_ip = ip_add


# function to check whether the program has created the 'share' folder
def created_folder(folder_name):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
        print('The ', folder_name, ' folder has created!')


# the main function of whole program
def main():
    # define the folder
    folder_name = 'share'

    # call the function the create the folder
    created_folder(folder_name)

    # define the ip address
    ip_address()

    while True:
        # create threads and manage them correctly
        # thread_1: for server part
        thread_1 = threading.Thread(target=run_server, args=(folder_name,))

        # thread_2: for client part
        thread_2 = threading.Thread(target=run_client, args=(pc_ip, folder_name))

        # run threads to finish the file sharing
        thread_1.start()
        thread_2.start()

        thread_2.join()


# run the whole program
if __name__ == '__main__':
    main()


# *************************************************End of main part*****************************************************
