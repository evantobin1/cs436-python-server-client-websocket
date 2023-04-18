# cs436ProjectV4
This is a simple client-server chat room made with Python for our CS-436 class.

### Instructions

Change the *host_name* on line 111 in **client.py** to the host ip of the server.

Run `python server.py`

In another terminal, run `python client.py`


#### Note

When sending an attachment, the filepath is relative to the *server/* and *client/* directories respectively. Therefore, if you want to send a file, you must place it in the attachments folder and provide the filepath as simply the filename, 

i.e. `Please enter the file path and name: file1.txt`