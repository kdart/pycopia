#!/usr/bin/python2.4
# -*- coding: us-ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
# 
# $Id$
#
#    Copyright (C) 1999-2004  Keith Dart <keith@kdart.com>
#
#    This library is free software; you can redistribute it and/or
#    modify it under the terms of the GNU Lesser General Public
#    License as published by the Free Software Foundation; either
#    version 2.1 of the License, or (at your option) any later version.
#
#    This library is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.

############################################
# Py-TOC 1.2 
#
# Jamie Turner <jamwt@jamwt.com>
#

DEBUG = 1

import sys
import socket
import re
import struct

from pycopia import sysrandom


TOC_SERV_AUTH = ("login.oscar.aol.com", 5159 )
TOC_SERV = ( "toc.oscar.aol.com", 9898 )

class TOCError(Exception):
	pass

class TocTalk(object):
	def __init__(self,nick,passwd):
			self._nick = nick
			self._passwd = passwd
			self._agent = "PY-TOC"
			self._info = "I'm running the Python TOC Module by James Turner <jamwt@jamwt.com>"
			self._seq = whrandom.randint(0,65535)
			self.build_funcs()


	def build_funcs(self):
		self._dir = []
		for item in dir(self.__class__):
			if ( type( eval("self.%s" % item)) == type(self.__init__) and
			item[:3] == "on_" ):
				self._dir.append(item)

			
	def go(self):
			self.connect()
			self.process_loop()

	def start(self):
		pass

	def connect(self):
		#create the socket object
		try:
			self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		except:
			raise TOCError, "FATAL:  Couldn't create a socket"

		# make the connection
		try:
			self._socket.connect( TOC_SERV )
		except:
			raise TOCError, "FATAL: Could not connect to TOC Server"
		
		buf  = "FLAPON\r\n\r\n"
		bsent = self._socket.send(buf)
		
		if bsent <> len(buf):
			raise TOCError, "FATAL: Couldn't send FLAPON!"

	def start_log_in(self):
		ep = self.pwdenc()
		self._normnick = self.normalize(self._nick)
		msg = struct.pack("!HHHH",0,1,1,len(self._normnick)) + self._normnick
		self.flap_to_toc(1,msg)

		#now, login
		self.flap_to_toc(2,"toc_signon %s %s %s %s english %s" % (
		TOC_SERV_AUTH[0],TOC_SERV_AUTH[1],self._normnick,ep,self.encode(self._agent) ) )

		
	def normalize(self,data):
		data = re.sub("[^A-Za-z0-9]","",data)	
		return data.lower()

	def encode(self,data):
		for letter in "\\(){}[]$\"":
			data = data.replace(letter,"\\%s"%letter)
		return '"' + data + '"'

	def flap_to_toc(self,ftype,msg):
		if ftype == 2:
			msg = msg + struct.pack("!B", 0)
		ditems = []
		ditems.append("*")
		ditems.append(struct.pack("!BHH",ftype,self._seq,len(msg)))
		ditems.append(msg)


		data = "".join(ditems)

		derror( "SEND : \'%r\'" % data )
		bsent = self._socket.send(data)


		if bsent <> len(data):
			#maybe make less severe later
			raise TOCError, "FATAL: Couldn't send all data to TOC Server\n"

		self._seq = self._seq + 1

	def pwdenc(self):
		lookup = "Tic/Toc"
		ept = []

		x = 0
		for letter in self._passwd:
			ept.append("%02x" % ( ord(letter) ^ ord( lookup[x % 7]) ) )
			x = x + 1
		return "0x" + "".join(ept)
	
	def process_loop(self):
		# the "main" loop
		while 1:
			event = self.recv_event()
			if not event:
				continue

			derror( "RECV : %r" % event[1] )

			#else, fig out what to do with it
			#special case-- login
			if event[0] == 1:
				self.start_log_in()
				continue

			if not event[1].count(":"):
				data = ""

			else:
				ind = event[1].find(":")
				id = event[1][:ind].upper()
				data = event[1][ind+1:]

			#handle manually now
			if id == "SIGN_ON":
				self.c_SIGN_ON(id,data)
				continue

			if id == "ERROR":
				self.c_ERROR(id,data)
				continue

			#their imp
			if ("on_%s" % id ) in self._dir:
				exec ( "self.on_%s(data)" % id )

			else:
				werror("INFO : Received unimplemented '%s' id" % id)

	def recv_event(self):
		header = self._socket.recv(6) 

		if header == "":
			self.err_disconnect()
			return

		(marker,mtype,seq,buflen) = struct.unpack("!sBhh",header)

		#get the info
		dtemp = self._socket.recv(buflen)
		data = dtemp
		while len(data) != buflen:
			if dtemp == "":
				self.err_disconnect()
				return
			dtemp = self._socket.recv(buflen - len(data))
			data = data + dtemp

		return (mtype, data)

	def err_disconnect(self):
		sys.stdout.write("ERROR: We seem to have been disconnected from the TOC server.\n")
		sys.exit(0)

	# our event handling
	def c_ERROR(self,id,data):
		# let's just grab the errors we care about!

		#still more fields
		if data.count(":"): 
			data = int (data[:data.find(":")])
		else:
			data = int(data) # let's get an int outta it
		
		if data == 980:
			raise TOCError, "FATAL: Couldn't sign on; Incorrect nickname/password combination"

		if data == 981:
			raise TOCError, "FATAL: Couldn't sign on; The AIM service is temporarily unavailable"

		elif data == 982:
			raise TOCError, "FATAL: Couldn't sign on; Your warning level is too high"

		elif data == 983:
			raise TOCError, "FATAL: Couldn't sign on; You have been connecting and disconnecting too frequently"

		elif data == 989:
			raise TOCError, "FATAL: Couldn't sign on; An unknown error occurred"

		# ... etc etc etc
		else:
			# try to let further implementation handle it
			if ("on_%s" % id ) in self._dir:
				exec ( "self.on_%s(data)" % id )
			else:
				werror("ERROR: The TOC server sent an unhandled error code: #%d" % data)

	def c_SIGN_ON(self,type,data):
		self.flap_to_toc(2,"toc_add_buddy jamwt") # needs to start up corectly
		self.flap_to_toc(2,"toc_set_info %s" % self.encode(self._info) )
		self.flap_to_toc(2,"toc_init_done")
		self.start()

	def strip_html(self,data):
		return re.sub("<[^>]*>","",data)

	def normbuds(self,buddies):
		nbuds = []
		for buddy in buddies:
			nbuds.append(self.normalize(buddy))
		return " ".join(nbuds)
	
	#actions--help the user w/common tasks

	#the all-important
	def do_SEND_IM(self,user,message):
		self.flap_to_toc(2,"toc_send_im %s %s" % ( self.normalize(user), self.encode(message) )  )


	def do_ADD_BUDDY(self,buddies):
		self.flap_to_toc(2,"toc_add_buddy %s" % " ".join(self.normbuds(buddies) ) )

	def do_ADD_PERMIT(self,buddies):
		self.flap_to_toc(2,"toc_add_permit %s" % " ".join(self.normbuds(buddies) ) )

	def do_ADD_DENY(self,buddies):
		self.flap_to_toc(2,"toc_add_deny %s" % " ".join(self.normbuds(buddies) ) )

	def do_REMOVE_BUDDY(self,buddies):
		self.flap_to_toc(2,"toc_remove_buddy %s" % " ".join(self.normbuds(buddies) ) )

	# away, idle, user info handling
	def do_SET_IDLE(self,itime):
		self.flap_to_toc(2,"toc_set_idle %d" % itime )

	def do_SET_AWAY(self,awaymess):
		if awaymess == "":
			self.flap_to_toc(2,"toc_set_away")
			return

		self.flap_to_toc(2,"toc_set_away %s" % self.encode(awaymess) )
		
	def do_GET_INFO(self,user):
		self.flap_to_toc(2,"toc_get_info %s" % self.normalize(user) )

	def do_SET_INFO(self,info):
		self.flap_to_toc(2,"toc_set_info %s" % self.encode(info) )

	# warning capability
	def do_EVIL(self,user,anon=0):
		if anon:
			acode = "anon"
		else:
			acode = "norm"
			
		self.flap_to_toc(2,"toc_evil %s %s" % (self.normalize(user), acode) )

	#chat
	def do_CHAT_INVITE(self,room,imess,buddies):
		self.flap_to_toc(2,"toc_chat_invite %s %s %s" % (self.normalize(room),
		self.encode(imess), self.normbuds(buddies) ) )

	def do_CHAT_ACCEPT(self, id):
		self.flap_to_toc(2,"toc_chat_accept %s" % id)

	def do_CHAT_LEAVE(self,id):
		self.flap_to_toc(2,"toc_chat_leave %s" % id)
		
	def do_CHAT_WHISPER(self,room,user,message):
		self.flap_to_toc(2,"toc_chat_whisper %s %s %s" % (room, 
		self.normalize(user), self.encode(message) ) )

	def do_CHAT_SEND(self,room,message):
		self.flap_to_toc(2,"toc_chat_send %s %s" % (room, 
		self.encode(message) ) )
		
	def do_CHAT_JOIN(self,roomname):
		self.flap_to_toc(2,"toc_chat_join 4 %s" % roomname)

	def do_SET_CONFIG(self,configstr):
		self.flap_to_toc(2,"toc_set_config \"%s\"" % configstr)

	#todo more later!


def werror(errorstr):
	if DEBUG:
		sys.stdout.write("%s\n"%errorstr)

def derror(errorstr):
	if DEBUG > 1:
		sys.stdout.write("%s\n"%errorstr)
