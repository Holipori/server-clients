# server-clients
 server receives the data file from the clients, and turn back to them after modifying the data according to the lexicon file.
# objective
 A client will connect to the server over a socket and upload a user-supplied text file. The server will have a lexicon of commonly misspelled words that it will read from a file upon startup. The server will scan the user-supplied text file uploaded by the client and check each word against the lexicon. Any word in the user-supplied text file found in the lexicon will be surrounded by brackets. When the server is finished identifying words, the text file will be returned to the client and the connection will be closed.
 
 For more information please check the 'Lab1.pdf' file
# how to run
1.	Open ‘server’ folder, then open ‘server.py’ with pycharm. Run it.
2.	Open ‘clients’ folder, then open ‘client.py’ with pycharm. Run it. 
3.	Feel free to open ‘client2.py’ and ‘client3.py’ by the same way.
4.	Now you should see 1 server GUI and 3 clients GUI on the screen. The server should have start listening automatically. Now input username on the client GUI, click the ‘submit’ button. Then click the ‘upload’ button to upload a file to server. Then the spell checked file will be returned to the ‘files’ folder inside the ‘clients’ folder.
5.	Now click ‘kill’ button on the client GUI to end the process. Then click ‘exit’ button to close the window.
6.	Click the ‘kill button on the server GUI to stop listening. Then click ‘exit’ button to close the window.

# Screenshot examples
<img src="https://github.com/Holipori/server-clients/blob/main/images/server.png?raw" width="50%">
<img src="https://github.com/Holipori/server-clients/blob/main/images/client.png?raw" width="50%">
