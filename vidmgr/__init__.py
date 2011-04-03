from hme import *
import os
import socket
import metadata
import ConfigParser
import urllib
from string import maketrans

TITLE = 'PyTivo Video Manager'
goodexts = ['.mp4', '.mpg', '.avi', '.wmv']

PAGE_SHARES = 0
PAGE_LIST = 1
PAGE_DETAIL = 2

MODE_MENU = 0
MODE_TIVOMENU = 1
MODE_DELCONFIRM = 2
MODE_PUSHCONFIRM = 3

MENU_PUSH = 0
MENU_DELETE = 1
MENU_CONFIRM = 3

p = os.path.dirname(__file__)
if os.path.sep == '/':
	quote = urllib.quote
	unquote = urllib.unquote_plus
else:
	quote = lambda x: urllib.quote(x.replace(os.path.sep, '/'))
	unquote = lambda x: os.path.normpath(urllib.unquote_plus(x))
	
def prevVideo(list, index):
	ret = -1;
	i = index - 1
	
	while (i >= 0 and ret == -1):
		if list[i]['dir']:
			i = i - 1
		else:
			ret = i

	return ret

def nextVideo(list, index):
	ret = -1;
	i = index + 1
	
	while (i < len(list) and ret == -1):
		if list[i]['dir']:
			i = i + 1
		else:
			ret = i

	return ret

class Images:
	def __init__(self, app):
		self.Background = Image(app, os.path.join(p, 'background.png'))
		self.CueUp      = Image(app, os.path.join(p, 'cueup.png'))
		self.CueDown    = Image(app, os.path.join(p, 'cuedown.png'))
		self.CueLeft    = Image(app, os.path.join(p, 'cueleft.png'))
		self.HiLite     = Image(app, os.path.join(p, 'hilite.png'))
		self.MenuBkg    = Image(app, os.path.join(p, 'menubkg.png'))
		self.IconFolder = Image(app, os.path.join(p, 'folder.png'))
		self.IconVideo  = Image(app, os.path.join(p, 'video.png'))

class Fonts:
	def __init__(self, app):
		self.fnt16 = Font(app, size=16)
		self.fnt20 = Font(app, size=20)
		self.fnt24 = Font(app, size=24)
		self.fnt30 = Font(app, size=30)
	
class Vidmgr(Application):
	def startup(self):
		config = self.context.server.config

		# get the tivo information out of the startup comfig file.  For each tivo, we need to know:
		# tivox.name - the user friendly name and
		# tivox.tsn - the TSN
		# these fields all go into a section named [tivos]		
		self.tivo = []
		self.loadTivos(config)
		if len(self.tivo) == 0:
			print "No Tivos found - exiting"
			self.sound('bonk')
			self.active = False
			return

		# get the pytivo information.  For each pytivo instance, we need the following:
		# pytivox.config - the location of the config file
		# pytivox.ip - the ip address
		#
		# also, if the pytivo port number is not specified in the pytivo config file, you must have
		# pytivox.port - the port number
		self.share = []		
		self.loadShares(config)
		if len(self.share) == 0:
			print "No shares found - exiting"
			self.sound('bonk')
			self.active = False
			return
		
		# initialize our image and font resources, put up the screen background	and the title
		self.images = Images(self)
		self.fonts = Fonts(self)
		self.root.set_resource(self.images.Background)
		self.TitleView = View(self, height=40, width=640)
		self.SubTitleView= View(self, height=32, width=640, ypos=41)
		self.TitleView.set_text(TITLE, font=self.fonts.fnt30, colornum=0xffffff)
		
		# attributes for shares screen
		self.shareSelection = 0
		self.shareOffset = 0
		
		# attributes for listing page
		self.listSize = 8
		self.listOffset = 0
		self.listSelection = 0
		self.currentDir = ""
		self.directoryStack = []
		# now create the listing page (and shares page) views
		self.createListingViews()
		
		# attributes for the details page		
		self.indexDetail = 0
		self.detailMenuSelection = 0
		self.detailMode = MODE_MENU
		self.subMenuSelection = 0
		self.subMenuOffset = 0
		self.subMenuSize = 4
		# now create the details page views
		self.createDetailsViews()

		# get things started - set up the first page
		# if there is only 1 share - jump right to it - otherwise, put up a page of the shares
		if len(self.share) == 1:
			self.currentPage = PAGE_LIST
			self.createListing()		
			self.drawScreen()
		else:
			self.currentPage = PAGE_SHARES;
			self.drawScreen();
	
	# create all the views for the listing screen and the shares screen
	def createListingViews(self):
		self.vwList = View(self)
		self.vwListText = []
		self.vwListBkg = []
		self.vwListIcon = []
		self.vwListCue = []
		for i in range(self.listSize):
			yval = 81 + (i*40)
			bkg = View(self, height=40, ypos=yval, parent=self.vwList)
			self.vwListBkg.append(bkg)
			self.vwListText.append(View(self, height=40, width=480, ypos=0, xpos=100, parent=bkg))
			self.vwListIcon.append(View(self, height=32, width=32, ypos=4, xpos=60, parent=bkg))
			self.vwListCue.append(View(self, height=32, width=32, ypos=4, xpos=20, parent=bkg))
			
		self.vwListCueTop = View(self, height=32, width=32, ypos=45, xpos=20, parent=self.vwList)
		self.vwListCueBot = View(self, height=32, width=32, ypos=401, xpos=20, parent=self.vwList)

	# create the views for the details screen		
	def createDetailsViews(self):
		self.vwDetail = View(self, visible=False)
		self.vwDetailTitle = View(self, height=40, ypos=81, xpos=60, parent=self.vwDetail)
		self.vwDetailSubTitle = View(self, height=24, ypos=121, xpos=60, parent=self.vwDetail)
		self.vwDetailDescription = View(self, height=120, width=540, ypos=146, xpos=60, parent=self.vwDetail)
		self.vwDetailMenuBkg = []
		self.vwDetailMenuText = []
		self.vwDetailSubMenuBkg = []
		self.vwDetailSubMenuText = []

		minyval = 270

		for i in range(self.subMenuSize):
			yval = minyval + (i*32)
			bkg = View(self, height=30, width=240, xpos=70, ypos=yval, parent=self.vwDetail)
			txt = View(self, height=30, width=220, xpos=20, parent=bkg)
			bkg.set_resource(self.images.MenuBkg)
			self.vwDetailMenuBkg.append(bkg)
			self.vwDetailMenuText.append(txt)
			bkg = View(self, height=30, width=240, xpos=330, ypos=yval, parent=self.vwDetail)
			txt = View(self, height=30, width=220, xpos=20, parent=bkg)
			bkg.set_resource(self.images.MenuBkg)
			self.vwDetailSubMenuBkg.append(bkg)
			self.vwDetailSubMenuText.append(txt)
			if i < len(self.tivo):
				self.vwDetailSubMenuText[i].set_text(self.tivo[i]['name'], font=self.fonts.fnt20,
										colornum=0xffffff, flags=RSRC_HALIGN_LEFT)

		self.vwDetailSubMenuCueTop = View(self, height=32, width=32, ypos=minyval-32, xpos=350, parent=self.vwDetail)
		self.vwDetailSubMenuCueBot = View(self, height=32, width=32, ypos=minyval+(self.subMenuSize*32)+5, xpos=350, parent=self.vwDetail)

		self.vwDetailCueTop = View(self, height=32, width=32, ypos=45, xpos=520, parent=self.vwDetail)
		self.vwDetailCueBot = View(self, height=32, width=32, ypos=401, xpos=520, parent=self.vwDetail)
		
		self.vwDetailMenuBkg[2].set_transparency(1) # unused for now
		self.vwDetailMenuBkg[MENU_CONFIRM].set_transparency(1)
		self.vwDetailMenuText[MENU_PUSH].set_text('Push Video', font=self.fonts.fnt20,
									colornum=0xffffff,
									flags=RSRC_HALIGN_LEFT)
		self.vwDetailMenuText[MENU_DELETE].set_text('Delete Video', font=self.fonts.fnt20,
									colornum=0xffffff,
									flags=RSRC_HALIGN_LEFT)

	# load up tivo information from the config file
	def loadTivos(self, cfg):
		def cmptivo (left, right):
			if (left['name'] == right['name']): return 0
			if (left['name'] < right['name']): return -1
			return 0
		
		tlist = []
		section = 'tivos'
		if cfg.has_section(section):
			i = 0
			while (True):
				i = i + 1
				namekey = 'tivo' + str(i) + '.name'
				tsnkey = 'tivo' + str(i) +  '.tsn'
				if cfg.has_option(section, namekey) and cfg.has_option(section, tsnkey):
					tlist.append({'name' : cfg.get(section, namekey),
									'tsn' : cfg.get(section, tsnkey)})
				else:
					break
				
		self.tivo = sorted(tlist, cmp=cmptivo)

	# load up pytivo and shares information from config and from pytivo config(s)
	def loadShares(self, cfg):
		def cmpshare (left, right):
			if (left['name'] == right['name']): return 0
			if (left['name'] < right['name']): return -1
			return 0
		
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		s.connect(('4.2.2.1', 123))
		defip = s.getsockname()[0]
	
		section = 'pytivos'
		if cfg.has_section(section):
			i = 0
			while (True):
				i = i + 1
				key = "pytivo" + str(i) + ".config"
				if not cfg.has_option(section, key): break
				cfgfile = cfg.get(section, key)
				
				sep = None
				sepkey = 'pytivo' + str(i) + '.sep'
				if cfg.has_option(section, sepkey): sep = cfg.get(section, sepkey)
				
				ip = defip
				key = "pytivo" + str(i) + ".ip"
				if cfg.has_option(section, key):
					ip = cfg.get(section, key)

				port = None				
				key = "pytivo" + str(i) + ".port"
				if cfg.has_option(section, key):
					port = cfg.get(section, key)
				
				self.parseCfgFile(cfgfile, ip, port, sep)
		
		self.share = sorted(self.share, cmp=cmpshare)

	# parse a pytivo config looking for shares				
	def parseCfgFile(self, cf, ip, defport, sep):
		pyconfig = ConfigParser.ConfigParser()
		configs_found = pyconfig.read(cf)
		if not configs_found:
			print "ERROR: pyTivo config file " + cf + " does not exist."
			return

		port = defport
		if pyconfig.has_option('Server', 'port') : port = pyconfig.get('Server', 'port')
		
		if port == None:
			print "Neither main config file nor pytivo config file " + cf + " has port number specified"
		else:
			for section in pyconfig.sections():
				if (pyconfig.has_option(section, "type") and pyconfig.get(section, "type") == "video" and 
					pyconfig.has_option(section, 'path')):
					path = pyconfig.get(section, 'path')
					self.share.append({'name' : section, 'ip' : ip, 'port' : port, 'path' : path, 'sep' : sep})

	# handle a single remote key press - branch based on what screen is currently up				
	def handle_key_press(self, keynum, rawcode):
		if self.currentPage == PAGE_LIST:
			self.handle_key_pressList(keynum, rawcode)
		elif self.currentPage == PAGE_DETAIL:
			self.handle_key_pressDetail(keynum, rawcode)
		else: # PAGE_SHARES
			self.handle_key_pressShares(keynum, rawcode)

	# handle a keypress on the directory listing screen.  This screen needs to handle the situation
	# where the directory is empty - in this case, only the left arrow if permissible		
	def handle_key_pressList(self, keynum, rawcode):
		snd = 'updown'
		if len(self.listing) == 0 and keynum != KEY_LEFT:
			snd = 'bonk'
		else:
			# if I get herem either 1) there are directory entries in the listing list, or
			# 2) the directory list is empty and the ket is KEY_LEFT
			if keynum == KEY_DOWN:
				if self.listSelection+self.listOffset < len(self.listing)-1:
					if self.listSelection < self.listSize-1:
						self.listSelection = self.listSelection + 1
					else:
						self.listOffset = self.listOffset + 1
				else:
					snd = 'bonk'
						
			elif keynum == KEY_UP:
				if self.listSelection == 0:
					if self.listOffset == 0:
						snd = 'bonk'
					else:
						self.listOffset = self.listOffset - 1
				else:
					self.listSelection = self.listSelection - 1
					
			elif keynum == KEY_CHANNELUP:
				if self.listOffset == 0:
					if self.listSelection == 0:
						snd = 'bonk'
					else:
						self.listSelection = 0
				else:
					self.listOffset = self.listOffset - self.listSize
					if (self.listOffset < 0):
						self.listOffset = 0
					self.listSelection = 0
			
			elif keynum == KEY_CHANNELDOWN:
				if (self.listOffset + self.listSize >= len(self.listing)):
					if self.listSelection == len(self.listing) - self.listOffset - 1:
						snd = 'bonk'
					else:
						self.listSelection = len(self.listing) - self.listOffset - 1
				else:
					self.listSelection = 0;
					self.listOffset = self.listOffset + self.listSize
					
			elif keynum == KEY_REPLAY:
				self.listSelection = 0
				self.listOffset = 0
				
			elif keynum == KEY_ADVANCE:
				self.listOffset = len(self.listing) - self.listSize
				if self.listOffset < 0:
					self.listOffset = 0
					self.listSelection = len(self.listing)-1
				else:
					self.listSelection = self.listSize - 1
					
			elif keynum in [KEY_SELECT, KEY_RIGHT]:
				index = self.listOffset + self.listSelection;
				if self.listing[index]['dir']:
					# recurse into the next directory
					self.directoryStack.append({'dir': self.currentDir, 'selection' : self.listSelection, 'offset': self.listOffset})
					self.currentDir = self.listing[index]['path']
					self.listSelection = 0
					self.listOffset = 0
					self.createListing()
				else:
					# bring up the details about the selected video
					self.vwList.set_visible(False)
					self.vwDetail.set_visible(True)
					self.indexDetail = index
					self.currentPage = PAGE_DETAIL
					self.detailMode = MODE_MENU
					self.detailMenuSelection = MENU_PUSH
				
			elif keynum == KEY_CLEAR:
				self.active = False
				snd = None
					
			elif keynum == KEY_LEFT:
				if len(self.directoryStack) == 0:
					# no more level to pop out from - either bring up
					# the shares page, or if there is only i share, exit
					if len(self.share) == 1:
						self.active = False
						snd = None
					else:
						self.currentPage = PAGE_SHARES
				else:
					# pop back one directory level
					s = self.directoryStack.pop()
					self.currentDir = s['dir']
					self.listSelection = s['selection']
					self.listOffset = s['offset']
					self.createListing()
				
			else:
				snd = 'bonk'

		if snd: self.sound(snd)		
		self.drawScreen()

	# handle a keypress on the shares screen - no need to worry if it's empty because
	# if it is empty, we have already exited, and if it's only 1 long, we bypass		
	def handle_key_pressShares(self, keynum, rawcode):
		snd = 'updown'

		if keynum == KEY_DOWN:
			if self.shareSelection+self.shareOffset < len(self.share)-1:
				if self.shareSelection < self.listSize-1:
					self.shareSelection = self.shareSelection + 1
				else:
					self.shareOffset = self.shareOffset + 1
			else:
				snd = 'bonk'
		
		elif keynum == KEY_UP:
			if self.shareSelection == 0:
				if self.shareOffset == 0:
					snd = 'bonk'
				else:
					self.shareOffset = self.shareOffset - 1
			else:
				self.shareSelection = self.shareSelection - 1
				
		elif keynum == KEY_CHANNELUP:
			if self.shareOffset == 0:
				if self.shareSelection == 0:
					snd = 'bonk'
				else:
					self.shareSelection = 0
			else:
				self.shareOffset = self.shareOffset - self.listSize
				if (self.shareOffset < 0):
					self.shareOffset = 0
				self.shareSelection = 0
		
		elif keynum == KEY_CHANNELDOWN:
			if (self.shareOffset + self.listSize >= len(self.share)):
				if self.shareSelection == len(self.share) - self.shareOffset - 1:
					snd = 'bonk'
				else:
					self.shareSelection = len(self.share) - self.shareOffset - 1
			else:
				self.shareSelection = 0;
				self.shareOffset = self.shareOffset + self.listSize
				
		elif keynum == KEY_REPLAY:
			self.shareSelection = 0
			self.shareOffset = 0
			
		elif keynum == KEY_ADVANCE:
			self.shareOffset = len(self.share) - self.listSize
			if self.shareOffset < 0:
				self.shareOffset = 0
				self.shareSelection = len(self.share)-1
			else:
				self.shareSelection = self.listSize - 1

		# jump into the chose directory			
		elif keynum in [KEY_SELECT, KEY_RIGHT]:
			self.currentDir = ""
			self.listSelection = 0
			self.listOffset = 0
			self.createListing()
			self.currentPage = PAGE_LIST
			
		elif keynum in [ KEY_LEFT, KEY_CLEAR ]:
			self.active = False
			snd = None
				
		else:
			snd = 'bonk'
	
		if snd: self.sound(snd)		
		self.drawScreen()

	# handle a keypress while on the details screen.  This screen operates in one of 3 modes:
	# MODE_DELCONFIRM - only a thunmbs up is allowed - everything else will exit this mode
	# MODE_MENU - the user is choosing an action to perform from the left menu, or
	# MODE_TIVOMENU - the user has chosen push and is now choosing a tivo to push to		
	def handle_key_pressDetail(self, keynum, rawcode):
		snd = 'updown'	
		if self.detailMode == MODE_DELCONFIRM:	
			if keynum == KEY_THUMBSUP:
				self.delVideo(self.indexDetail)
				self.sleep(2);
				self.createListing();
				
				self.detailMode = MODE_MENU
				if (self.indexDetail >= len(self.listing)):
					self.indexDetail = prevVideo(self.listing, self.indexDetail)
					if (self.indexDetail == -1):
						self.listOffset = 0
						self.listSelection = 0
						self.vwDetail.set_visible(False)
						self.vwList.set_visible(True)
						self.currentPage = PAGE_LIST
					
			else:
				# not a thumbs up - back to MODE_MENU
				self.detailMode = MODE_MENU
				
		elif self.detailMode == MODE_TIVOMENU:
			if keynum == KEY_LEFT:
				# they changed their minds about pushing - back to MODE_MENU
				self.detailMode = MODE_MENU
					
			if keynum == KEY_DOWN:
				if self.subMenuSelection+self.subMenuOffset < len(self.tivo)-1:
					if self.subMenuSelection < self.subMenuSize-1:
						self.subMenuSelection = self.subMenuSelection + 1
					else:
						self.subMenuOffset = self.subMenuOffset + 1
				else:
					snd = 'bonk'
					
			elif keynum == KEY_UP:
				if self.subMenuSelection == 0:
					if self.subMenuOffset == 0:
						snd = 'bonk'
					else:
						self.subMenuOffset = self.subMenuOffset - 1
				else:
					self.subMenuSelection = self.subMenuSelection - 1
				
			elif keynum == KEY_CHANNELUP:
				if self.subMenuOffset == 0:
					if self.subMenuSelection == 0:
						snd = 'bonk'
					else:
						self.subMenuSelection = 0
				else:
					self.subMenuOffset = self.subMenuOffset - self.subMenuSize
					if (self.subMenuOffset < 0):
						self.subMenuOffset = 0
					self.subMenuSelection = 0
			
			elif keynum == KEY_CHANNELDOWN:
				if (self.subMenuOffset + self.subMenuSize >= len(self.tivo)):
					if self.subMenuSelection == len(self.tivo) - self.subMenuOffset - 1:
						snd = 'bonk'
					else:
						self.subMenuSelection = len(self.tivo) - self.subMenuOffset - 1
				else:
					self.subMenuSelection = 0;
					self.subMenuOffset = self.subMenuOffset + self.subMenuSize
					
			elif keynum == KEY_REPLAY:
				self.subMenuSelection = 0
				self.subMenuOffset = 0
				
			elif keynum == KEY_ADVANCE:
				self.subMenuOffset = len(self.tivo) - self.subMenuSize
				if self.subMenuOffset < 0:
					self.subMenuOffset = 0
					self.subMenuSelection = len(self.tivo)-1
				else:
					self.subMenuSelection = self.subMenuSize - 1
					
			elif keynum in [ KEY_RIGHT, KEY_SELECT ]:
				# push the video and then back to MODE_MENU
				self.pushVideo(self.indexDetail, self.subMenuSelection, self.shareSelection)
				self.detailMode = MODE_PUSHCONFIRM
				snd = 'alert'
			else:
				snd = 'bonk'
				
		elif self.detailMode == MODE_PUSHCONFIRM:
			# we don't care what they press
			self.detailMode = MODE_MENU
				
		# the user is choosing between PUSH and DELETE
		else: #MODE_MENU
			if keynum == KEY_CHANNELUP:
				i = prevVideo(self.listing, self.indexDetail)
				if i == -1:
					snd = 'bonk'
				else:
					self.indexDetail = i
			
			elif keynum == KEY_CHANNELDOWN:
				i = nextVideo(self.listing, self.indexDetail)
				if i == -1:
					snd = 'bonk'
				else:
					self.indexDetail = i
					
			elif keynum == KEY_LEFT:
				# back to listing page - we need to do some crazy stuff here in case they 
				# deleted videos and our cursor is now beyond the end of the list
				self.vwDetail.set_visible(False)
				self.vwList.set_visible(True)
				self.currentPage = PAGE_LIST
				if self.listOffset + self.listSelection >= len(self.listing):
					self.listSelection = 0
					if self.listOffset > len(self.listing):
						self.listOffset = self.listOffset - self.listSize
						if self.listOffset < 0:
							self.listOffset = 0
				
			elif keynum in [KEY_UP, KEY_DOWN]:
				self.detailMenuSelection = 1 - self.detailMenuSelection
					
			elif keynum in [KEY_RIGHT, KEY_SELECT]:
				# act on their choice - either go into MODE_DELCONFIR or MODE_TIVOMENU
				# if there is only 1 tivo, bypass the tivo menu and just push it
				if self.detailMenuSelection == MENU_DELETE:
					self.detailMode = MODE_DELCONFIRM
					snd = 'alert'
				else: # MENU_PUSH
					if len(self.tivo) == 1:
						self.pushVideo(self.indexDetail, 0, self.shareSelection)
						snd = 'alert'
						self.detailMode = MODE_PUSHCONFIRM
					else:
						self.detailMode = MODE_TIVOMENU
						self.subMenuSelection = 0
						self.subMenuOffset = 0
									
			elif keynum == KEY_CLEAR:
				self.active = False
				snd = None
				
			else:
				snd = 'bonk'
		
		if snd: self.sound(snd)		
		self.drawScreen()

	# delete the video and it's associated metadata file		
	def delVideo(self, index):
		path = os.path.join(self.share[self.shareSelection]['path'], self.listing[index]['path'])
		try:
			os.remove(path)
		except:
			self.sound('bonk')
		
		metapath = path + '.txt'
		if os.path.exists(metapath):
			try:
				os.remove(metapath)
			except:
				self.sound('bonk')

	# push the video to the seletced tivo
	def pushVideo(self, vidindex, tivoindex, shareindex):
		ip = self.share[shareindex]['ip']
		port = self.share[shareindex]['port']
		container = self.share[shareindex]['name']
		sep = self.share[shareindex]['sep']
		if sep is None or sep == os.path.sep:
			relfile = (os.path.sep + self.listing[vidindex]['path'])
		else:
			relfile = sep + self.listing[vidindex]['path'].translate(maketrans(os.path.sep, sep))
			
		tsn = self.tivo[tivoindex]['tsn']
		params = urllib.urlencode({'Command': 'Push', 'Container': container,
						'File': relfile,
						'tsn': tsn})
		url = 'http://%s:%s/TivoConnect' % (ip, port)
		
		try:
			f = urllib.urlopen(url, params)
			html = f.read()
		except:
			self.pushText = "Exception during Push request"
		else:
			if html.lower().count('queue') != 0:
				self.pushText = "Queued for push to " + self.tivo[tivoindex]['name']
			else:
				self.pushText = "Push error from PyTivo"

	# create a listing of the current directory
	def createListing(self):
		# we sort directories first, and then asciibetically by name
		def cmplist (left, right):
			if (left['dir'] == right['dir']):
				if (left['text'] < right['text']): return -1
				if (left['text'] > right['text']): return 1
				return 0
			elif (left['dir']): return -1
			else: return 1
			
		self.listing = []
		
		llist = []

		root = self.share[self.shareSelection]['path']
		fulldir = os.path.join(root, self.currentDir)
		names = os.listdir(fulldir)
		for name in names:
			relpath = os.path.join(self.currentDir, name)
			fullpath = os.path.join(fulldir, name)
			if os.path.isdir(fullpath):
				llist.append({'text': name, 
									'icon': self.images.IconFolder, 
									'path': relpath,
									'dir': True})
			else:
				if os.path.splitext(name)[1].lower() in goodexts:
					meta = metadata.from_text(fullpath)
					if not 'title' in meta:
						meta = metadata.basic(fullpath)
						
					if 'episodeTitle' in meta:
						if 'title' in meta:
							title = meta['title'] + ':' + meta['episodeTitle']
						else:
							title = meta['episodeTitle']
					elif 'title' in meta:
						title = meta['title']
					else:
						title = name
					llist.append({'text': title,
									'meta': meta,
									'icon': self.images.IconVideo,
									'path': relpath,
									'dir': False})
			
		self.listing = sorted(llist, cmp=cmplist)

	# paint the screen - first determine which screen we are painting		
	def drawScreen(self):
		if self.currentPage == PAGE_LIST:
			self.drawScreenList()
		elif self.currentPage == PAGE_DETAIL:
			self.drawScreenDetail()
		else: # PAGE_SHARES
			self.drawScreenShares()
	# draw the listing screen - this is the main screen that the user will be interacting with - this
	# allows browsing through the directories	
	def drawScreenList(self):
		off = self.listOffset
		self.SubTitleView.set_text(self.share[self.shareSelection]['name'] + ":" + self.currentDir,
								font=self.fonts.fnt20,
								colornum=0xffffff)
		
		# if there are no videos in this directory, just print a message to that effect and
		# prompt for the left key
		if (len(self.listing) == 0):
			for i in range(self.listSize):
				self.vwListBkg[i].clear_resource();
				self.vwListCue[i].clear_resource();
				self.vwListText[i].clear_resource()
				self.vwListIcon[i].clear_resource()
			self.vwListCueTop.clear_resource();
			self.vwListCueBot.clear_resource();
			self.vwListText[3].set_text('No videos in this folder - press LEFT to continue', font=self.fonts.fnt20,
									colornum=0xffffff, flags=RSRC_HALIGN_LEFT);
			self.vwListCue[3].set_resource(self.images.CueLeft)
		
		else:
			self.vwListCueTop.clear_resource();
			if self.listSelection == 0 and off != 0:
				self.vwListCueTop.set_resource(self.images.CueUp)
				
			self.vwListCueBot.clear_resource();
			if (self.listSelection == self.listSize-1) and (self.listSelection+self.listOffset < len(self.listing)-1):
				self.vwListCueBot.set_resource(self.images.CueDown)
			
			for i in range(self.listSize):
				self.vwListBkg[i].clear_resource()
				self.vwListCue[i].clear_resource()
				if (i+off < len(self.listing)):
					if i == self.listSelection:
						self.vwListBkg[i].set_resource(self.images.HiLite)
						self.vwListCue[i].set_resource(self.images.CueLeft)
					if i == self.listSelection-1:
						self.vwListCue[i].set_resource(self.images.CueUp)
					if i == self.listSelection+1:
						self.vwListCue[i].set_resource(self.images.CueDown)
					self.vwListText[i].set_text(self.listing[i+off]['text'], font=self.fonts.fnt24,
										colornum=0xffffff, flags=RSRC_HALIGN_LEFT)
					self.vwListIcon[i].set_resource(self.listing[i+off]['icon'])
				else:
					self.vwListText[i].clear_resource()
					self.vwListIcon[i].clear_resource()
					
	# paint the shares screen - this is much like the listing screen above except that 1) it lists shares only, 
	# and 2) we don't have to worry about it being empty because if it was empty we would have exited by now
	def drawScreenShares(self):
		self.SubTitleView.set_text("Shares", font=self.fonts.fnt20,
									colornum=0xffffff)
		
		off = self.shareOffset
		self.vwListCueTop.clear_resource();
		if self.shareSelection == 0 and off != 0:
			self.vwListCueTop.set_resource(self.images.CueUp)
			
		self.vwListCueBot.clear_resource();
		if (self.shareSelection == self.listSize-1) and (self.shareSelection+off < len(self.share)-1):
			self.vwListCueBot.set_resource(self.images.CueDown)		
		
		for i in range(self.listSize):
			self.vwListBkg[i].clear_resource()
			self.vwListCue[i].clear_resource()
			self.vwListIcon[i].clear_resource()
			sx = i + off
			if (sx < len(self.share)):
				if i == self.shareSelection:
					self.vwListBkg[i].set_resource(self.images.HiLite)
					self.vwListCue[i].set_resource(self.images.CueLeft)
				if i == self.shareSelection-1:
					self.vwListCue[i].set_resource(self.images.CueUp)
				if i == self.shareSelection+1:
					self.vwListCue[i].set_resource(self.images.CueDown)
				self.vwListText[i].set_text(self.share[sx]['name'], font=self.fonts.fnt24,
									colornum=0xffffff, flags=RSRC_HALIGN_LEFT)
			else:
				self.vwListText[i].clear_resource()

	# paint the detail screen
	# this is the most detailed of all of the screens - in addition to the detail
	# about the current video, it needs to paing the action menu and if in push mode, the
	# submenu of tivos
	def drawScreenDetail(self):		
		index = self.indexDetail
		self.SubTitleView.set_text("", font=self.fonts.fnt20,
									colornum=0xffffff)
	
		if ((prevVideo(self.listing, index) == -1) or
					(self.detailMode in [ MODE_DELCONFIRM, MODE_TIVOMENU ])):
			self.vwDetailCueTop.clear_resource()
		else:
			self.vwDetailCueTop.set_resource(self.images.CueUp)
			
		if ((nextVideo(self.listing, index) == -1) or
					(self.detailMode in [ MODE_DELCONFIRM, MODE_TIVOMENU ])):
			self.vwDetailCueBot.clear_resource()
		else:
			self.vwDetailCueBot.set_resource(self.images.CueDown)

		meta = self.listing[index]['meta']
		
		self.vwDetailTitle.set_text(meta['title'], font=self.fonts.fnt30,
								colornum=0xffffff, flags=RSRC_HALIGN_LEFT)
		if 'episodeTitle' in meta:
			self.vwDetailSubTitle.set_text(meta['episodeTitle'], font=self.fonts.fnt24,
								colornum=0xffffff, flags=RSRC_HALIGN_LEFT)
		else:
			self.vwDetailSubTitle.set_text("")
			
		if 'description' in meta:
			self.vwDetailDescription.set_text(meta['description'], font=self.fonts.fnt16,
								colornum=0x000000,
								flags=RSRC_TEXT_WRAP + RSRC_HALIGN_LEFT)
		else:
			self.vwDetailDescription.set_text("")

		self.vwDetailSubMenuCueTop.clear_resource()
		self.vwDetailSubMenuCueBot.clear_resource()
		
		if self.detailMode == MODE_MENU:			
			for i in range(self.subMenuSize):
				self.vwDetailSubMenuBkg[i].set_transparency(1) 
			if self.detailMenuSelection == MENU_PUSH:
				self.vwDetailMenuBkg[MENU_PUSH].set_transparency(0)
				self.vwDetailMenuBkg[MENU_DELETE].set_transparency(0.75)
				self.vwDetailMenuBkg[MENU_CONFIRM].set_transparency(1)
			else:
				self.vwDetailMenuBkg[MENU_PUSH].set_transparency(0.75)
				self.vwDetailMenuBkg[MENU_DELETE].set_transparency(0)
				self.vwDetailMenuBkg[MENU_CONFIRM].set_transparency(1)
				
		elif self.detailMode == MODE_DELCONFIRM:
			self.vwDetailMenuBkg[MENU_PUSH].set_transparency(0.75)
			self.vwDetailMenuBkg[MENU_DELETE].set_transparency(0.75)
			self.vwDetailMenuText[MENU_CONFIRM].set_text('Press Thumbs-Up to Confirm',
									font=self.fonts.fnt20,
									colornum=0xffffff,
									flags=RSRC_HALIGN_LEFT)
			self.vwDetailMenuBkg[MENU_CONFIRM].set_transparency(0)
			
		elif self.detailMode == MODE_PUSHCONFIRM:
			for i in range(self.subMenuSize):
				self.vwDetailSubMenuBkg[i].set_transparency(0.75) 
			self.vwDetailMenuBkg[MENU_PUSH].set_transparency(0.75)
			self.vwDetailMenuBkg[MENU_DELETE].set_transparency(0.75)
			self.vwDetailMenuText[MENU_CONFIRM].set_text(self.pushText,
									font=self.fonts.fnt16,
									colornum=0xffffff,
									flags=RSRC_HALIGN_LEFT)
			self.vwDetailMenuBkg[MENU_CONFIRM].set_transparency(0)
			
		else: # MODE_TIVOMENU
			if self.subMenuOffset != 0:
				self.vwDetailSubMenuCueTop.set_resource(self.images.CueUp);
			if self.subMenuOffset + self.subMenuSize < len(self.tivo):
				self.vwDetailSubMenuCueBot.set_resource(self.images.CueDown);
				
			for i in range(self.subMenuSize):
				tx = i + self.subMenuOffset
				if tx < len(self.tivo):
					self.vwDetailSubMenuText[i].set_text(self.tivo[tx]['name'],
												font=self.fonts.fnt20,
												colornum=0xffffff,
												flags=RSRC_HALIGN_LEFT)
					if i == self.subMenuSelection:
						trans = 0
					else:
						trans = 0.75
				else:
					trans = 1
				self.vwDetailSubMenuBkg[i].set_transparency(trans)
			pass
				
		
