from datetime import datetime
import json
import os
import signal
import socket
import sys
from threading import Thread


NUM_CLIENTS = 3


if __name__ == "__main__":

    # get the absolute path of the file
    file_path = os.path.abspath(__file__)

    # get the directory of the file
    dir_path = os.path.dirname(file_path)

    # set the current working directory to the directory of the file
    os.chdir(dir_path)

    # Create and Bind a TCP Server Socket
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host_name = socket.gethostname()
    s_ip = socket.gethostbyname(host_name)
    port = 18000
    serverSocket.bind((host_name, port))

    # Outputs Bound Contents
    print("Socket Bound")
    print("Server IP: ", s_ip, " Server Port:", port)

    # Listens for NUM_CLIENTS Users
    serverSocket.listen(NUM_CLIENTS)

    # Creates a set of clients
    active_users = []
    message_history = []


# Function to constantly listen for an client's incoming messages and sends them to the other clients
def clientWatch(cs, client_address):
    while True:
        # Constantly listens for incoming message from a client
        try:
            data = cs.recv(1024).decode()
        except ConnectionResetError as e:
            print("Client forcibly closed connection")
            for user in active_users:
                # If an active user socket connection was broken, remove them from the active user list
                if user['socket'] == cs:
                    active_users.remove(user)
            return
            

        # If the socket connection was closed by the client, stop the thread
        if not data:
            for user in active_users:
                # If an active user socket connection was broken, remove them from the active user list
                if user['socket'] == cs:
                    active_users.remove(user)
            print(f"{client_address} disconnected!")
            return
        
        msg = json.loads(data)
        print(f"- Received {msg}")
        
        # CHECKING FLAGS
        if "QUIT_REQUEST_FLAG" in msg:
            username = msg["USERNAME"]
            
            output_payload = {
                "QUIT_RESPONSE_FLAG": 1,
                }
            print(f"- Sending {output_payload}")
            cs.send(json.dumps(output_payload).encode())

            # Send a goodbye message to all clients
            for user in active_users:
                output_payload = {"USER_QUIT_FLAG": 1, "PAYLOAD": {"username": username}}
                print(f"- Sending {output_payload}")
                user["socket"].send(json.dumps(output_payload).encode())

            # Remove the socket from the active users list now that it is closed
            for user in active_users:
                if user['socket'] == cs:
                    active_users.remove(user)
            return
        
        if "REPORT_REQUEST_FLAG" in msg:
            output_payload = {
                "REPORT_RESPONSE_FLAG": 1,
                "NUMBER": len(active_users),
                "PAYLOAD": list(map(lambda user: {"username": user["username"], "ip": user["ip"], "port": user["port"]}, active_users))
                }
            print(f"- Sending {output_payload}")
            cs.send(json.dumps(output_payload).encode())
            continue
        if "JOIN_REQUEST_FLAG" in msg:
            username = msg["USERNAME"]

            # Error handling
            if len(active_users) >= NUM_CLIENTS:
                print("Error, too many clients")
                output_payload = {"JOIN_REJECT_FLAG": 1, "PAYLOAD": "The server rejects the join request. The chatroom has reached its maximum capacity."}
                print(f"- Sending {output_payload}")
                cs.send(json.dumps(output_payload).encode())
                return
            for user in active_users:
                if(user["username"] == username):
                    print("Error, name already taken.")
                    output_payload = {"JOIN_REJECT_FLAG": 1, "PAYLOAD": f"The server rejects the join request. The name {username} has already been taken"}
                    print(f"- Sending {output_payload}")
                    cs.send(json.dumps(output_payload).encode())
                    return

            # Successful connection
            print("Client joining chatroom")
            output_payload = {"JOIN_ACCEPT_FLAG": 1, "USERNAME": username, "PAYLOAD": message_history}
            print(f"- Sending {output_payload}")
            cs.send(json.dumps(output_payload).encode())

            # Tell all other clients that the new user has joined
            for user in active_users:
                user["socket"].send(json.dumps({"USER_JOINED_FLAG": 1, "PAYLOAD": {"username": msg["USERNAME"], "time": datetime.now().strftime('%H:%M:%S')}}).encode())

            
            # Add the new user to the list of active users
            active_users.append({"username": msg["USERNAME"], "socket": cs, "ip": client_address[0], "port": client_address[1] })
            message_history.append({"username": "Server", "content": f"{username} has joined the chatroom.", "time": datetime.now().strftime('%H:%M:%S')})
            continue

        # Listening for messages
        username = msg["USERNAME"]
        payload = msg["PAYLOAD"]
        
        if "ATTACHMENT_FLAG" in msg:
            filename = msg["FILENAME"]
            with open(f"downloads/{filename}", 'w') as f:
                f.write(payload)
            
            # Add the message to the chatroom history
            message_history.append({"username": username, "content": payload, "time": datetime.now().strftime('%H:%M:%S')})

            # Send the message to all clients
            for user in active_users:
                with open(f"downloads/{filename}", 'r') as f:
                    attachment = f.read()
                    output_payload = {"ATTACHMENT_FLAG": 1, "FILENAME": filename, "PAYLOAD": {"username": username, "content": attachment, "time": datetime.now().strftime('%H:%M:%S')}}
                    print(f"- Sending {output_payload} to {user['username']}")
                    user["socket"].send(json.dumps(output_payload).encode())
            continue
        


        # Check if this user is in the active user pool
        is_an_active_user = False
        for user in active_users:
            if user["username"] == username:
                is_an_active_user = True
        if(not is_an_active_user):
            print(f"{username} is not an acitve user in the chatroom, not responding.")
            continue

        # Add the message to the chatroom history
        message_history.append({"username": username, "content": payload, "time": datetime.now().strftime('%H:%M:%S')})

        # Send the message to all clients
        for user in active_users:
            output_payload = {
                "PAYLOAD": {"username": username, "content": payload, "time": datetime.now().strftime('%H:%M:%S')}
                }
            print(f"- Sending {output_payload} to {user['username']}")
            user["socket"].send(json.dumps(output_payload).encode())

while True:
    try:
        # Continues to listen / accept new clients
        client_socket, client_address = serverSocket.accept()
        print(client_address, "Connected!")

        # Create a thread that listens for each client's messages
        t = Thread(target=clientWatch, args=(client_socket,client_address,))
        # Make a daemon so thread ends when main thread ends
        t.daemon = True
        t.start()
    except Exception as e:
        print(e)

