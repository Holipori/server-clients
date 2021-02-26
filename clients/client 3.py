import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog
from PyQt5 import QtGui
from clients_ui import Ui_clients
import socket
import struct, json
import os
import time
import threading

class MyMainForm(QMainWindow, Ui_clients):
    '''
    GUI class. this is the code mainly taking charge of the GUI
    '''
    def __init__(self):
        super(MyMainForm, self).__init__()
        self.setupUi(self)
        self.s = None # initialize the socket object
        self.writeText('please enter your username...')
        self.submit_button.clicked.connect(lambda: self.submit())
        self.upload_button.clicked.connect(lambda: self.openfile())
        self.kill_button.clicked.connect(lambda: self.kill())
        self.upload_button.setEnabled(False)
        self.kill_button.setEnabled(False)
    def kill(self):
        '''this function is for kill the process'''
        if self.s: #if socket exists, then print.
            self.writeText('connection stopped.')
        self.uploaded = True
        self.running = False # these flags are for dealing with the infinite loop issue
        self.kill_button.setEnabled(False)
        time.sleep(0.05)
    def submit(self):
        '''start a new thread for connecting to the server'''
        self.kill() # kill the potential process
        username = self.username_line.text() # get the username from the text box
        self.client_th = threading.Thread(target=self.connect, args=(username,)) # start a new thread to handle the socket process.
        self.client_th.start()
        self.kill_button.setEnabled(True)
    def writeText(self, text):
        '''this function is for displaying to the text browser'''
        self.textBrowser.insertPlainText(text+'\n')
        self.textBrowser.moveCursor(QtGui.QTextCursor.End)
    def openfile(self):
        '''get the file name and path'''
        self.file_path = QFileDialog.getOpenFileName()[0] # get the path and the name of the file that will be sent
        self.filename = self.file_path.split('/')[-1]# get the name of the file that will be sent
        self.dir = self.file_path.replace(self.filename, "") # get the path of the file that will be sent
        self.uploaded = True # this flag is for dealing with the infinite loop problem
    def send_file(self,s, filename):
        '''
        send data to the server
        :param s: socket object
        :param filename: name of the file that will be sent
        :return: Nothing
        '''
        # 1st: construct the header
        header_dic = {
            'filename': filename,
            'file_size': os.path.getsize(r'%s%s' % (self.dir, filename))
        }

        header_json = json.dumps(header_dic)
        header_bytes = header_json.encode()

        # 2nd: send the header's length
        s.send(struct.pack('i', len(header_bytes)))

        # 3rd: send the header
        s.send(header_bytes)

        # 4th: send the real data
        with open('%s%s' % (self.dir, filename), 'rb') as f:
            for line in f:
                s.send(line)
        self.writeText('sent data file to server.')
    def receive_file(self,s):
        '''
        receiving data file from the server
        :param s: socket object
        :return: nothing
        '''
        # 1st step: receive header's length
        obj = s.recv(4)
        header_size = struct.unpack('i', obj)[0]

        # 2nd step: receive header
        header_bytes = s.recv(header_size)

        # 3rd step: parse the data description from the header
        header_json = header_bytes.decode()
        header_dic = json.loads(header_json)

        total_size = header_dic['file_size']
        file_name = header_dic['filename']

        # 4th step: receive the real data
        with open(r'%sfiles/%s' % (self.dir, file_name), 'wb') as f:
            recv_size = 0
            while recv_size < total_size:
                line = s.recv(1024)
                f.write(line)
                recv_size += len(line)
            self.writeText('spell check sequence has completed.')
    def connect(self, username):
        '''
        main code for connecting to the server
        :param username: username
        :return: nothing
        '''
        self.uploaded = False
        self.running = True # set running flag to deal with the while loop problem when kill the process during opening file
        self.s = socket.socket()  # create socket object
        host = socket.gethostname()  # get local host name
        port = int(self.port_lineEdit.text())  # set port number form the GUI lineEdit.
        self.s.connect((host, port)) # connect to the server
        self.s.send(username.encode()) # send the user name
        self.writeText(self.s.recv(1024).decode()) # receive the information from the server
        if self.s.recv(1024).decode() == 'T': # receive the command, if the command is T, means connected successively
            self.upload_button.setEnabled(True)
            self.writeText('please upload a file...')
            start_time = time.time()  # record the start time for the timeout
            while (self.uploaded != True):
                QApplication.processEvents()
                time.sleep(0.05)
                if time.time()-start_time > 20:
                    self.writeText('timeout') ## set a waiting time, just in case the unexpected process termination.
                    self.kill()
            if self.running: # check the running flag to see if the process is running
                self.send_file(self.s, self.filename) # send the file to the server
                self.receive_file(self.s) # receive the file that has been spell checked from the server
                self.upload_button.setEnabled(False)
                self.writeText('connection closed.\n')
        self.s.close()
        self.kill_button.setEnabled(False)
        self.upload_button.setEnabled(False)
        self.writeText('please enter your username...')


if __name__ == '__main__':
    ''' display the GUI'''
    app = QApplication(sys.argv)
    myWin = MyMainForm()
    myWin.show()
    sys.exit(app.exec_())