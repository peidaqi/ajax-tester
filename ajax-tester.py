import sys
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import QObject
from requests import Session
import json
from datetime import datetime
from http.server import SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn
from http.server import HTTPServer
import threading

class AJAXRequestHandler(SimpleHTTPRequestHandler):	
	recvAJAXString = ""

	def do_POST(self):

		if self.client_address[0] != "127.0.0.1":
			print("Bad request from non localhost")
			self.send_response(404)
			return

		content_len = int(self.headers["content-length"])
		post_body = self.rfile.read(content_len)
		AJAXRequestHandler.recvAJAXString = post_body


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer, QObject):
	setRecvTextSignal = pyqtSignal("QString")

	def __init__(self, server_address, RequestHandlerClass, bind_and_activate=True):
		#
		# Cannot use super()/MRO because QObject and HTTPServer constructors have different signatures.
		#
		QObject.__init__(self)
		HTTPServer.__init__(self, server_address, RequestHandlerClass, bind_and_activate)

	def finish_request(self, request, client_address):
		super(ThreadedHTTPServer, self).finish_request(request, client_address)
		self.setRecvTextSignal.emit(self.RequestHandlerClass.recvAJAXString.decode())

class MainWnd(QWidget):
	def __init__(self):
		super(MainWnd, self).__init__()
		self.serverStarted = False
		self.initUI()

	def initUI(self):
		self.setWindowTitle("AJAX Tester v1.0")
		self.setGeometry(100, 100, 1200, 700)

		self.lblAddress = QLabel(self)
		self.lblAddress.setText("Target URL: ")

		self.ipAddressTextBox = QLineEdit(self)
		self.ipAddressTextBox.setText("http://127.0.0.1")

		self.portTextBox = QLineEdit(self)
		self.portTextBox.setText("8000")

		self.btnStartServer = QPushButton("Start AJAX Server", self)
		self.btnStartServer.clicked.connect(self.btnStartServer_OnClick)

		self.btnSendReq = QPushButton("Send AJAX Request", self)
		self.btnSendReq.clicked.connect(self.btnSendReq_OnClick)

		self.btnExit = QPushButton("Exit", self)
		self.btnExit.clicked.connect(self.btnExit_OnClick)

		self.lblAjax = QLabel(self)
		self.lblAjax.setText("JSON object in text to send:")

		self.sendAjaxContentTextBox = QTextEdit(self)
		self.sendAjaxContentTextBox.setText("{\"a\": 10, \"b\": 20}")

		self.lblServer = QLabel(self)
		self.lblServer.setText("JSON object received:")

		self.recvAjaxContentTextBox = QTextEdit(self)

		self.lblMsg = QLabel(self)
		self.lblMsg.setText("Messages:")

		self.msgTextBox = QTextEdit(self)


		layout = QGridLayout()
		layout.addWidget(self.lblAddress, 0, 0)
		layout.addWidget(self.ipAddressTextBox, 0, 1, 1, 1)
		layout.addWidget(self.portTextBox, 0, 2, 1, 1)
		layout.addWidget(self.btnStartServer, 1, 0)
		layout.addWidget(self.btnSendReq, 1, 1)
		layout.addWidget(self.btnExit, 1, 2)
		layout.addWidget(self.lblAjax, 2, 0, 1, 3)
		layout.addWidget(self.sendAjaxContentTextBox, 3, 0, 3, 3)
		layout.addWidget(self.lblServer, 6, 0, 1, 3)
		layout.addWidget(self.recvAjaxContentTextBox, 7, 0, 3, 3)
		layout.addWidget(self.lblMsg, 10, 0, 1, 3)
		layout.addWidget(self.msgTextBox, 11, 0, 2, 3)
		self.setLayout(layout)

	@pyqtSlot()
	def btnExit_OnClick(self):
		sys.exit()

	@pyqtSlot()
	def setRecvAjaxContentTextBox(msg):
		global mainWnd
		mainWnd.recvAjaxContentTextBox.setText(msg)

	@pyqtSlot()
	def btnStartServer_OnClick(self):
		if self.serverStarted is False:
			#
			# Remove the "http://" before sending to HTTPServer
			#
			ipAddr = self.ipAddressTextBox.text()
			idx = ipAddr.find("//")
			if idx != -1:
				ipAddr = ipAddr[idx + 2:]
				
			self.server = ThreadedHTTPServer((ipAddr, int(self.portTextBox.text())), AJAXRequestHandler)
			self.server.setRecvTextSignal.connect(MainWnd.setRecvAjaxContentTextBox)

			self.server_thread = threading.Thread(target=self.server.serve_forever)
			self.server_thread.daemon = True
			self.server_thread.start()

			self.btnStartServer.setText("Stop AJAX Server")
			self.serverStarted = True
		else:
			self.server.shutdown()

			self.btnStartServer.setText("Start AJAX Server")
			self.serverStarted = False

	@pyqtSlot()
	def btnSendReq_OnClick(self):
		session = Session()
		try:
			response = session.post(
				url = self.ipAddressTextBox.text() + ":" + self.portTextBox.text(),
				data = self.sendAjaxContentTextBox.toPlainText(),
			)
		except Exception as e:
			msg = self.msgTextBox.toPlainText()
			msg = msg + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " : " + str(e) + "\r\n"
			self.msgTextBox.setText(msg)

if __name__ == "__main__":
	app = QApplication(sys.argv)
	app.setFont(QFont("Arial", 13))
	mainWnd = MainWnd()
	mainWnd.show()
	sys.exit(app.exec())