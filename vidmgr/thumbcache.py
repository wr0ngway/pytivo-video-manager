'''
Created on Jun 14, 2011

@author: jbernard
'''
import cPickle as pickle
import os
import thread

CACHEFILE = 'thumbs.cache'

def loadpic(fn):
	try:
		f = open(fn, "rb")
		data = f.read()
		f.close()
	except:
		return None
	
	if len(data) == 0:
		return None
	
	return data

class ThumbCache:
	def __init__(self, dir, size):
		self.filename = os.path.join(dir, 'thumbs.cache')
		self.cacheChanged = False
		self.lrumap = []
		self.maxSize = size
		self.mutex = thread.allocate_lock()
		
		# try to load the cache file if it exists
		self.cache = {}
		
		if (os.path.exists(self.filename)):
			print "Loading thumbnail cache"
			
			try:
				f = open(self.filename)
			except:
				print "Error opening thumbnail cache file"
			else:
				try:
					self.cache = pickle.load(f)
				except:
					print "Error loading thumbnail cache"
					self.cache = {}
					return
					
			for k in self.cache:
				self.appendMap(k)
			self.adjustMap()
			print str(len(self.cache)) + " thumbnails loaded from cache"
		else:
			print "Cache file does not exist - no thumbnails loaded"
	
	def sortMap(self):
		def cmplru (left, right):
			if (left[0] > right[0]): return 1
			if (left[0] < right[0]): return -1
			return 0
		
		self.lrumap = sorted(self.lrumap, cmp=cmplru)
	
	def adjustMap(self):
		while len(self.lrumap) > self.maxSize:
			(lru, key) = self.lrumap[0]
			del self.cache[key]
			del self.lrumap[0]
		i = 0
		for m in self.lrumap:
			m[0] = i
			i += 1
			
	def appendMap(self, key):		
		self.lrumap.append([self.maxSize, key])

	def addMap(self, key):
		self.appendMap(key)
		self.adjustMap()

	def updateMap(self, key):
		for m in self.lrumap:
			if m[1] == key:
				m[0] = self.maxSize # force to have the highest possible lru value
				break
		self.sortMap()
		self.adjustMap()

	def getImageData(self, filename):
		mt = 0
		try:
			mt = os.path.getmtime(filename)
		except os.error:
			# file does not exist
			return None
		
		self.mutex.acquire()

		adding = False
		if filename in self.cache:
			if self.cache[filename]['mtime'] >= mt:
				# don't load the file - just use the cache
				self.updateMap(filename)
				self.mutex.release()
				return self.cache[filename]['data']
			
			# file is in the cache but out of date
		else:
			# file is not in the cache - add it
			adding = True
			
		# either file is newer than cache
		# or file is NOT yet in the cache
		# load it in either case
		pdata = loadpic(filename)
		if pdata == None:
			self.mutex.release();
			return None

		if adding:
			self.cache[filename] = {}
		
		self.cache[filename]['data'] = pdata
		self.cache[filename]['mtime'] = mt

		self.cacheChanged = True
		if adding:
			self.addMap(filename)
		else:
			self.updateMap(filename)

		self.mutex.release()
		return self.cache[filename]['data']
	
	def hasChanged(self):
		return self.cacheChanged
	
	def size(self):
		return len(self.cache)
	
	def __str__(self):
		return str(self.lrumap)
	
	def saveCache(self):
		if self.hasChanged():
			self.mutex.acquire()
			try:
				f = open(self.filename, 'w')
			except:
				print "Error opening thumbnail cache file for write"
			else:
				try:
					pickle.dump(self.cache, f)
				except:
					print "Error saving thumbnail cache"
				else:
					f.close()
					self.cacheChanged = False
			self.mutex.release()
		