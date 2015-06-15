#!/usr/bin/python

#import psycopg2
#import psycopg2.extensions
from psycopg2 import extensions as pg_extensions, connect as pg_connect 

class MyDB:
	
	def __init__(self,dbname,user,host,password,port=None):
		self.dbname = dbname
		self.user = user
		self.host = host
		self.password = password
		if port is None:
			parameters = "dbname='"+dbname+"' user='"+user+"' host='"+host+"' password='"+password+"'"
		else:
			parameters = "dbname='"+dbname+"' user='"+user+"' host='"+host+"' password='"+password+"' port='"+port+"'"
		self.debug=''
		try:    
			#for unicode
			pg_extensions.register_type(pg_extensions.UNICODE)
			#connecting to the database
			self.conn = pg_connect(parameters)
			#Useful for operation such as drop and insert
			self.conn.set_isolation_level(0)
			#enabling utf8 encode
			self.conn.set_client_encoding('UNICODE')
			self.cur = self.conn.cursor()
			self.debug='connected to db!\t'
		except: 
			self.debug='connection failed!\t'
			self.conn = None
	
	def parser_sql_string(self,mystring):
		#please, think to convert your data before passing to this function, e.g. maps = maps.encode('utf-8')
		special_char = ['\'','\"']
		for character in special_char:
			mystring = mystring.replace(character,'\\'+character)
		return mystring

			
	def getDebugMess(self):
		return self.debug


	def getSelect(self,cmd):
		rows = None
		
		if self.conn is not None:
			try:
				self.cur.execute(cmd)
				rows = self.cur.fetchall()
			except:
				self.debug = self.debug+"\nself.runDBcommand error: I can't run "+cmd
		
		return rows
			
	def pushInsert(self,cmd):
		if self.conn is not None:
			try:    
				self.cur.execute(cmd)
				return 1
			except: 
				self.debug = self.debug+"\nself.runDBcommand error: I can't run "+cmd
				return 0
		return None
		
	def genericRun(self,cmd):
		return self.pushInsert(cmd)		


	def __del__(self):
		if self.conn is not None:
			self.cur.close()
			self.conn.close()
			
			
			

