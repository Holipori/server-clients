import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog
from PyQt5.QtCore import *
from PyQt5 import QtGui
from server_ui import Ui_server
import socket
import struct, json
import os
import time
import re
import threading
import select

class MyMainForm(QMainWindow, Ui_server):
    '''
    GUI class. this is the code mainly taking charge of the GUI
    '''
    def __init__(self):
        super(MyMainForm, self).__init__()
        self.setupUi(self)
        self.new_therad()
        self.start_button.setEnabled(False)
        self.stop_button.clicked.connect(lambda: self.stop())
        self.start_button.clicked.connect(lambda: self.new_therad())
    def stop(self):
        '''this is the function handling the stopping listening'''
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.update_userlist('clearTheBox') # clear the user list
        self.work.terminate() # terminate the thread
        self.writeText('stopped listening')
    def new_therad(self):
        '''create a new thread to listen for incoming connection'''
        port = int(self.port_lineEdit.text())
        self.work = MyThread(port) # new thread object
        self.work.signals.connect(self.writeText)
        self.work.user_signals.connect(self.update_userlist)
        self.work.start()
    def update_userlist(self, text):
        '''this function is for updating the active users box.'''
        if text == 'clearTheBox': # check the command to see if it's clearing command or usernames.
            self.activeUsers_browser.clear()
        else:
            self.activeUsers_browser.insertPlainText(text+'\n')
            self.textBrowser.moveCursor(QtGui.QTextCursor.End) # move the cursor the end so that the text browser can be displayed properly
    def writeText(self, text):
        '''this is the function for status updating.'''
        self.textBrowser.insertPlainText(text+'\n')
        self.textBrowser.moveCursor(QtGui.QTextCursor.End)



class MyThread(QThread):
    '''this is the thread class for handling the connection'''
    signals = pyqtSignal(str) #define signals to be string. signals will be used to communicate with the main thread.
    user_signals = pyqtSignal(str)
    def __init__(self, port):
        super(MyThread, self).__init__()
        self.running = True # running flag is for dealing with the infinite loop problem
        self.port = port
        self.dir = os.getcwd()  # get the current directory
        self.lexicon = [] # initiate the lexicon list
        self.get_lexicon() # get lexicon list
    def get_lexicon(self):
        '''read the lexicon data'''
        with open(r'%s/%s' % (self.dir, 'lexicon.txt'), 'r') as f:
            line = f.readline()
            self.lexicon += line.split( )

    def receive_file(self,c, username):
        '''
        receiving data file from user
        :param c: connection instance
        :param username: username of this connection
        :return: file name of the received data file
        '''
        # 1st step: receive header's length
        obj = c.recv(4)
        header_size = struct.unpack('i', obj)[0]

        # 2nd step: receive header
        header_bytes = c.recv(header_size)

        # 3rd step: parse the data description from the header
        header_json = header_bytes.decode()
        header_dic = json.loads(header_json)

        total_size = header_dic['file_size']
        file_name = header_dic['filename']

        # 4th step: receive the real data
        with open(r'%s/files/%s' % (self.dir, file_name), 'wb') as f:
            recv_size = 0
            while recv_size < total_size:
                line = c.recv(1024)
                f.write(line)
                recv_size += len(line)
            self.signals.emit("received data file from user '" + username + "'")
        return file_name
    def send_file(self,s, filename):
        '''
        send data to a user
        :param s: a connection instance
        :param filename: name of the file that will be sent
        :return: Nothing
        '''
        # 1st: construct the header
        header_dic = {
            'filename': filename,
            'file_size': os.path.getsize(r'%s/files/%s' % (self.dir, filename))
        }

        header_json = json.dumps(header_dic)
        header_bytes = header_json.encode()

        # 2nd: send the header's length
        s.send(struct.pack('i', len(header_bytes)))

        # 3rd: send the header
        s.send(header_bytes)

        # 4th: send the real data
        with open('%s/files/%s' % (self.dir, filename), 'rb') as f:
            for line in f:
                s.send(line)
        username = filename.split('-')[0]
        self.signals.emit("sent updated file to user '" + username + "'")
    def check_file(self, file, username):
        '''
        this function is for the spell check
        :param file: name of the file that need to be checked
        :param username: username of this user
        :return: nothing
        '''
        final_data = "" # initiate the data that will be write into the updated file
        with open(self.dir+'/files/'+file,'r') as f: # read from received data firstly
            for line in f:
                for item in self.lexicon:
                    if item in line:
                        line = re.sub(item, '['+item+']', line, flags = re.IGNORECASE) # surround the words that found in the lexicon file with brackets. also ignore thecharacter case
                final_data += line
        with open(self.dir+'/files/'+ username+'-updated-'+file, 'w') as f: # write the final data to a new file
            f.write(final_data)
    def update_userlist(self):
        '''this is for updating the userlist'''
        self.user_signals.emit('clearTheBox')
        time.sleep(0.05) # add a sleep time to prevent potential issue
        for i in range(len(self.userlist)):
            self.user_signals.emit(self.userlist[i])

    def run(self):
        ''' main code of the thread'''
        self.s = socket.socket()  # create socket object
        # self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        host = socket.gethostname()  # get local host name
        port = self.port  # set the port
        self.s.bind((host, port))  # bind the port
        self.signals.emit('start listening...')
        self.s.listen(3)  # waiting for clients to connect
        # initiating variables
        self.userlist = []
        self.inputs = [self.s, ]
        outputs = []
        message_dict = {}
        username_dict = {}
        while True:
            r_list, w_list, e_list = select.select(self.inputs, outputs, self.inputs, 1) # using select to handle multiple clients simultaneously
            for s_or_c in r_list: # traverse all the elements in the reading list
                if s_or_c == self.s: # if the element is socket, that means theres is a new connection.
                    c, addr = self.s.accept() # get the connection and the address
                    username = c.recv(1024).decode() # receive the username firstly
                    if username in self.userlist: # if the username is occupied, then reject this connection
                        self.signals.emit("occupied username '"+username+"'. Reject!")
                        c.send('the user name is occupied, please use another username...'.encode())
                        time.sleep(0.05)
                        c.send('F'.encode()) # F command means failed to connect
                        c.close()
                    else: # else, accept this connection
                        self.signals.emit("user '"+username+"' has connected!")
                        self.signals.emit('username: ' + username)
                        c.send("you've successively connected! ".encode())
                        time.sleep(0.05) # add a wait time to split the text and the command
                        c.send('T'.encode()) # T command means connected successively
                        self.userlist.append(username) # add to userlist
                        self.update_userlist()
                        self.inputs.append(c)
                        username_dict[c] = username
                        message_dict[c] = []
                else:
                    # existing users is sending data
                    try:
                        username = username_dict[s_or_c]
                        file_name = self.receive_file(s_or_c, username) # receiving file from the user
                    except:
                        # means the user has logged out
                        self.signals.emit("'"+ username+"' logged out")
                        self.inputs.remove(s_or_c)
                        self.userlist.remove(username)
                        self.update_userlist()
                    else:
                        # if everything is fine, then check the file and return it to the client
                        self.check_file(file_name, username)
                        self.send_file(s_or_c, username + '-updated-' + file_name)
                        s_or_c.close()
                        self.inputs.remove(s_or_c)
                        self.userlist.remove(username)
                        self.update_userlist()

            for sk in e_list: # remove the exception socket
                self.inputs.remove(sk)
                self.userlist.remove(username)
                self.update_userlist()


if __name__ == '__main__':
    ''' display the GUI'''
    app = QApplication(sys.argv)
    myWin = MyMainForm()
    myWin.show()
    sys.exit(app.exec_())