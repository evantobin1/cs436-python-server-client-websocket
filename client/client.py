import os
import socket
from threading import Thread
import json


def server_listen(server_socket):
    while True:
        # Constantly listens for incoming message from a client
        data = server_socket.recv(1024).decode()

        # If the socket connection was closed by the client, stop the thread
        if not data:
            print("Server disconnected!")
            return
        
        msg = json.loads(data)

        # If the server has send a quit response
        if("QUIT_RESPONSE_FLAG" in msg):
            server_socket.close()
            os._exit(0)
        
        if("USER_QUIT_FLAG" in msg):
            username = msg["PAYLOAD"]["username"]
            print(f"[SERVER]: User {username} has left the chatroom.")
            continue
        
        if("USER_JOINED_FLAG" in msg):
            username = msg["PAYLOAD"]["username"]
            time = msg["PAYLOAD"]["time"]
            print(f"[{time}] Server: {username} has joined the chatroom.")
            continue

        # If the server has send an attachment
        if("ATTACHMENT_FLAG" in msg):
            username = msg["PAYLOAD"]["username"]
            filename = msg["FILENAME"]
            content = msg["PAYLOAD"]["content"]
            time = msg["PAYLOAD"]["time"]

            # Download the file into the downloads folder
            with open(f"downloads/{filename}", 'w') as f:
                f.write(content)

            # Print the content of the downloaded file
            with open(f"downloads/{filename}", 'r') as f:
                print(f"[{time}] {username}: {f.read()}")
            continue
            
        username = msg["PAYLOAD"]["username"]
        content = msg["PAYLOAD"]["content"]
        time = msg["PAYLOAD"]["time"]
        print(f"[{time}] {username}: {content}")


def join_chatroom(username, history, server_socket):

    print("\tThe server welcomes you to the chatroom.")
    print("\tType lowercase 'q' and press enter at any time to quit the chatroom.")
    print("\tType lowercase 'a' and press enter at any time to upload an attachment to the chatroom.\n\n")

    print("----------Chat History----------")   
    for message in history:
        print(f"[{message['time']}] {message['username']}: {message['content']}")
    print("------Chat History Finished------")   


    # Create a thread that listens for the server's messages
    t = Thread(target=server_listen, args=(server_socket,))
    # Make a daemon so thread ends when main thread ends
    t.daemon = True
    t.start()

    while True:
        user_input = input()
        # If the client is attempting to quit
        if(user_input == 'q'):
            output_payload = {"QUIT_REQUEST_FLAG": 1, "USERNAME": username}
            server_socket.send(json.dumps(output_payload).encode())
            continue
        # If the client wants to send an attachment
        if(user_input == 'a'):
            filename = input("Please enter the file path and name: ")
            try:
                with open(f"attachments/{filename}", 'r') as f:
                    attachment = f.read()
                    output_payload = {"ATTACHMENT_FLAG": 1, "FILENAME": filename, "USERNAME": username, "PAYLOAD": attachment}
                    server_socket.send(json.dumps(output_payload).encode())
            except Exception as e:
                print("Error, that file does not exist.")
                print(e)
            continue

        # Otherwise, just simply send a message with the default payload format
        message = {"USERNAME": username, "PAYLOAD": user_input}
        server_socket.send(json.dumps(message).encode())




if __name__ == "__main__":
    # get the absolute path of the file
    file_path = os.path.abspath(__file__)

    # get the directory of the file
    dir_path = os.path.dirname(file_path)

    # set the current working directory to the directory of the file
    os.chdir(dir_path)

    host_name = "192.168.0.118"
    port = 18000

    # Creates the TCP socket
    new_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("Connecting to", host_name, port, "...")
    new_socket.connect((host_name, port))
    print("Connected.")


    # Prompt the user for his initial input
    print("Please select one of the following options:")
    print("\t1. Get a report of the chatroom from the server.")
    print("\t2. Request to join the chatroom.")
    print("\t3. Quit the program.")
    try:
        user_input = int(input())
    except ValueError:
        print("Error, not a number")
        exit()


    match user_input:
        case 1:
            message = {"REPORT_REQUEST_FLAG": 1}
            new_socket.send(json.dumps(message).encode())
            response = json.loads(new_socket.recv(1024).decode())

            if("REPORT_RESPONSE_FLAG" not in response):
                print("Error, REPORT_RESPONSE_FLAG not in message.")
                exit()
            try:
                number = response["NUMBER"]
                payload = response["PAYLOAD"]

                print(f"There are {number} active users in the chatroom.")
                iterator = 0
                while(iterator <= number - 1):
                    print(f"{iterator + 1}. {payload[iterator]['username']} at IP: {payload[iterator]['ip']} and port: {payload[iterator]['port']}")
                    iterator+=1
            except Exception as e:
                print(e)


        case 2:
            username = input("What is your username: ")
            output_payload = {"JOIN_REQUEST_FLAG": 1, "USERNAME": username}    
            new_socket.send(json.dumps(output_payload).encode())
            response = json.loads(new_socket.recv(1024).decode())

            # Error handling
            if("JOIN_REJECT_FLAG" in response):
                print(f"Error, JOIN_REJECT_FLAG, {response['PAYLOAD']}.")
                exit()
            if("JOIN_ACCEPT_FLAG" not in response):
                print("Error, JOIN_ACCEPT_FLAG not in response")
                exit()
            
            # Successful join of chatroom
            join_chatroom(username=username, history=response['PAYLOAD'], server_socket=new_socket)
            
        case 3:
            print("Goodbye")
            exit()
 
        case _:
            print("Error, that's not an option!")
            exit();
