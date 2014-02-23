from hme import *
import os
import re
import socket
import metadata
import ConfigParser
import urllib
from time import asctime
from string import maketrans
from thumbcache import ThumbCache

TITLE = 'PyTivo Video Manager'
version = '0.7c'

print asctime(), TITLE + " version " + version + " starting"

goodexts = ['.mp4', '.mpg', '.avi', '.wmv']
metaFirst = [ 'title', 'seriesTitle', 'episodeTitle', 'description' ]
metaSpaceAfter = []
metaSpaceBefore = []
metaIgnore = [ 'isEpisode', 'isEpisodic' ]
metaXlate = { 'title': 'Title',
			'originalAirDate': 'Original Air Date',
			'time': 'Time',
			'duration': 'Duration',
			'description': 'Description',
			'seriesTitle': 'Series Title',
			'seriesId': 'Series ID',
			'episodeTitle': 'Episode Title',
			'episodeNumber': 'Episode Number',
			'movieYear': 'Movie Year',
			'tvRating': 'TV Rating',
			'mpaaRating': 'MPAA Rating',
			'starRating': 'Star Rating',
			'colorCode': 'Color Code',
			'showingBits': 'Showing Bits',
			'partCount': 'Part Count',
			'partIndex': 'Part Index',
			'callsign': 'Call Sign',
			'displayMajorNumber': 'Display Major Number',
			'vSeriesGenre': 'Series Genre',
			'vProgramGenre': 'Program Genre',
			'vChoreographer': 'Choreographer',
			'vExecProducer': 'Exec Producer',
			'vGuestStar': 'Guest Star',
			'vHost': 'Host',
			'vProducer': 'Producer',
			'vDirector': 'Director',
			'vActor': 'Actor',
			'vWriter': 'Writer',
			}

keymap = { KEY_NUM1: 10.0, KEY_NUM2: 20.0, KEY_NUM3: 30.0, KEY_NUM4: 40.0, KEY_NUM5: 50.0,
		KEY_NUM6: 60.0, KEY_NUM7: 70.0, KEY_NUM8: 80.0, KEY_NUM9: 90.0 }

regex = re.compile(r'Title\s*(\d+)')

infoLabelPercent = 30
infoRightMargin = 20


SHARE_VIDEO = 0
SHARE_DVDVIDEO = 1

PAGE_SHARES = 0
PAGE_LIST = 1
PAGE_DETAIL = 2

MODE_MENU = 0
MODE_TIVOMENU = 1
MODE_DELCONFIRM = 2
MODE_PUSHCONFIRM = 3
MODE_INFO = 4

MENU_PUSH = 0
MENU_DELETE = 1
MENU_CONFIRM = 3

RES_SD = 0
RES_HD = 1

DISP_NORMAL = 0
DISP_FILE = 1
DISP_EPTITLE = 2
DISP_EPNUMTITLE = 3

SORT_NORMAL = 0
SORT_FILE = 1
SORT_EPNUM = 2

screenWidth = [ 640, 1280 ]
screenHeight = [ 480, 720 ]
infoHeight = [ 420, 600 ]
infoWidth = [ 580, 1160 ]
listViewWidth = [ 640, 640 ]
listSize = [ 8, 14 ]
titleYPos = [ 24, 36 ]
subTitleYPos = [ 56, 84 ]
listYStart = [ 81, 121 ]
listHeight = [ 40, 40 ]
listXText = [ 100, 150 ]
listXIcon = [ 60, 90 ]
listXCue = [ 20, 30 ]
subMenuSize = [ 4, 4 ]
detailViewWidth = [ 640, 640 ]
detailDescHeight = [ 120, 140 ]
detailDescWidth = [ 540, 590 ]
detailDescXPos = [ 60, 10 ]
detailDescYPos = [ 146, 121 ]
detailViewXPos = [ 0, 640 ]
detailMenuYPos = [ 270, 290 ]
detailMenuXPos = [ 70, 340 ]
detailSubMenuYPos = [ 270, 442 ]
detailSubMenuXPos = [ 330, 340 ]
detailSubCueTopY = [ 238, 410 ]
detailSubCueBotY = [ 403, 575 ]
detailSubCueXPos = [ 350, 300 ]
ThumbNailWidth = 620
ThumbNailHeight = 450
ThumbCacheSize = 100
thumbFlag = RSRC_HALIGN_LEFT

p = os.path.dirname(__file__)
tc = ThumbCache(p, ThumbCacheSize, ThumbNailWidth, ThumbNailHeight)

if os.path.sep == '/':
	quote = urllib.quote
	unquote = urllib.unquote_plus
else:
	quote = lambda x: urllib.quote(x.replace(os.path.sep, '/'))
	unquote = lambda x: os.path.normpath(urllib.unquote_plus(x))
	
class Images:
	def __init__(self, app):
		self.Background  = self.loadimage(app, 'background')
		self.CueUp       = self.loadimage(app, 'cueup')
		self.CueDown     = self.loadimage(app, 'cuedown')
		self.CueLeft     = self.loadimage(app, 'cueleft')
		self.HiLite      = self.loadimage(app, 'hilite')
		self.MenuBkg     = self.loadimage(app, 'menubkg')
		self.IconFolder  = self.loadimage(app, 'folder')
		self.IconDVD     = self.loadimage(app, 'dvdfolder')
		self.IconVideo   = self.loadimage(app, 'video')
		self.PleaseWait  = self.loadimage(app, 'pleasewait')
		self.Info        = self.loadimage(app, 'info')
		self.InfoUp      = self.loadimage(app, 'infoup')
		self.InfoDown    = self.loadimage(app, 'infodown')
	
	def loadimage(self, app, name):
		if app.res == RES_HD:
			fn = os.path.join(p, 'skins', app.skin, name + "HD.png")
			if os.path.exists(fn):
				return Image(app, fn)

		fn = os.path.join(p, 'skins', app.skin, name + ".png")
		if os.path.exists(fn):
			return Image(app, fn)
		
		print "image '" + name + "' missing for skin '" + app.skin + "'"
		return None
			

class Fonts:
	def __init__(self, app):
		self.fnt16 = Font(app, size=16)
		self.fnt20 = Font(app, size=20)
		self.fnt24 = Font(app, size=24)
		self.fnt30 = Font(app, size=30)
		self.descfont = Font(app, size=app.descsize)
		self.infofont = Font(app, size=24, flags=FONT_METRICS_BASIC|FONT_METRICS_GLYPH)
	
class Vidmgr(Application):
	def handle_resolution(self):
		for (hres, vres, x, y) in self.resolutions:
			if (hres == 640):
				self.res = RES_SD
				return (hres, vres, x, y)
			elif (hres == 1280):
				self.res = RES_HD
				return (hres, vres, x, y)
			
		self.active = False
		self.sound('bonk')
		return self.resolutions[0]
	
	def startup(self):
		global goodexts, metaFirst, metaIgnore, metaSpaceBefore, metaSpaceAfter
		global infoLabelPercent, infoRightMargin, thumbFlag
		
		config = self.context.server.config
		self.descsize = 20
		self.skin = "orig"
		self.deleteallowed = True
		self.dispopt = DISP_NORMAL
		self.sortopt = SORT_NORMAL
		self.mergefiles = True
		self.mergelines = False
		self.pytivo_metadata = None

		if config.has_section('vidmgr'):
			for opt, value in config.items('vidmgr'):
				if opt == 'exts':
					goodexts = value.split()
				elif opt == 'metaignore':
					metaIgnore = value.split()
				elif opt == 'metafirst':
					metaFirst = value.split()
				elif opt == 'metaspace' or opt == 'metaspaceafter':
					metaSpaceAfter = value.split()
				elif opt == 'metaspacebefore':
					metaSpaceBefore = value.split()
				elif opt == 'metamergefiles':
					if value.lower() == "false":
						self.mergefiles = False
				elif opt == 'metamergelines':
					if value.lower() == "true":
						self.mergelines = True
				elif opt == 'descsize':
					self.descsize = int(value)
				elif opt == 'infolabelpercent':
					n = int(value)
					if n < 10 or n > 70:
						print "Error in config - infolabelpercent must be between 10 and 70"
					else:
						infoLabelPercent = n
				elif opt == 'inforightmargin':
					n = int(value)
					if n < 0 or n > 100:
						print "Error in config - inforightmargin must be between 0 and 100"
					else:
						infoRightMargin = n
				elif opt == 'skin':
					self.skin = value
				elif opt == 'deleteallowed':
					if value.lower() == "false":
						self.deleteallowed = False
				elif opt == 'thumbjustify':
					if value.lower() == 'center':
						thumbFlag = RSRC_HALIGN_CENTER
					elif value.lower() == 'right':
						thumbFlag = RSRC_HALIGN_RIGHT
				elif opt == 'display':
					if (value == 'episodetitle'):
						self.dispopt = DISP_EPTITLE
					elif (value == 'episodenumtitle'):
						self.dispopt = DISP_EPNUMTITLE
					elif (value == 'file'):
						self.dispopt = DISP_FILE
					elif (value == 'normal'):
						pass
					else:
						print "Invalid display option - assuming default value"
				elif opt == 'sort':
					if (value == 'episodenumber'):
						self.sortopt = SORT_EPNUM
					elif (value == 'file'):
						self.sortopt = SORT_FILE
					elif (value == 'normal'):
						pass
					else:
						print "Invalid sort option - assuming default value"

		self.res = RES_SD
		# adjust the description height to be a multiple of the font size
		for i in [ RES_SD, RES_HD ]:
			n = int(detailDescHeight[i]/self.descsize)
			detailDescHeight[i] = n * self.descsize
			
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
		
	def cleanup(self):
		tc.saveCache()
		
	def handle_active(self):
		# initialize our image and font resources, put up the screen background	and the title
		self.myimages = Images(self)
		self.myfonts = Fonts(self)
		
		self.addShareIcons()

		self.root.set_resource(self.myimages.Background)
		self.TitleView = View(self, height=30, width=screenWidth[self.res], ypos=titleYPos[self.res])
		self.SubTitleView= View(self, height=20, width=screenWidth[self.res], ypos=subTitleYPos[self.res])
		self.TitleView.set_text(TITLE, font=self.myfonts.fnt30, colornum=0xffffff, flags=RSRC_VALIGN_BOTTOM)
		
		# attributes for shares screen
		self.sharetype = 0
		self.shareSelection = 0
		self.shareOffset = 0
		
		# attributes for listing page
		self.listSize = listSize[self.res]
		self.listOffset = 0
		self.listSelection = 0
		self.currentDir = ""
		self.listing = []
		self.directoryStack = []
		# now create the listing page (and shares page) views
		self.createListingViews()
		
		# attributes for the details page		
		self.indexDetail = 0
		self.detailMenuSelection = MENU_PUSH
		self.detailMode = MODE_INFO
		self.subMenuSelection = 0
		self.subMenuOffset = 0
		self.subMenuSize = subMenuSize[self.res]
		# now create the details page views
		self.createDetailsViews()
		
		self.vwPleaseWait = View(self, visible=False, height=66, width=66, xpos=screenWidth[self.res]/2-33, ypos=screenHeight[self.res]/2-33)
		self.vwPleaseWait.set_resource(self.myimages.PleaseWait)
		xoff = (screenWidth[self.res]-infoWidth[self.res])/2
		yoff = (screenHeight[self.res]-infoHeight[self.res])/2
		self.vwInfo = InfoView(self, infoWidth[self.res], infoHeight[self.res],
							xoff, yoff, self.myfonts.infofont)
		# get things started - set up the first page
		# if there is only 1 share - jump right to it - otherwise, put up a page of the shares
		if len(self.share) == 1:
			self.currentPage = PAGE_LIST
			self.sharetype = self.share[0]['type']
			self.createListing()		
			self.drawScreen()
		else:
			self.currentPage = PAGE_SHARES;
			self.drawScreen()
			
	def handle_font_info(self, font):
		self.vwInfo.setinfogeometry(font)

			
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
		index = self.listOffset + self.listSelection;
		snd = 'updown'
		if len(self.listing) == 0 and keynum not in [ KEY_LEFT, KEY_TIVO ]:
			snd = 'bonk'
		else:
			# if they press the info button then we can turn on the info (metadata)
			# display, but only if the current selection is NOT
			# a directory AND the info display is not already up
			if (keynum == KEY_INFO and not self.vwInfo.isVisible and self.listing[index]['hasinfo']):
				meta = self.listing[index]['meta']
				self.vwInfo.loadmetadata(meta)
				self.vwInfo.show()
				
			# if the info display is up, clear the info
			# display when the clear or left keys are hit
			elif keynum in [ KEY_LEFT, KEY_CLEAR, KEY_INFO ] and self.vwInfo.isVisible:
				self.vwInfo.hide()
				
			# if the info display is up, allow paging
			elif keynum in [ KEY_DOWN, KEY_CHANNELDOWN ] and self.vwInfo.isVisible:
				if not self.vwInfo.pagedown():
					snd = 'bonk'
					
			elif keynum in [ KEY_UP, KEY_CHANNELUP ] and self.vwInfo.isVisible:
				if not self.vwInfo.pageup():
					snd = 'bonk'
					
			# otherwise if the info display is up, they hit an invalid key
			elif self.vwInfo.isVisible:
				snd = 'bonk'
				
			# the info diaplay is not up - handle normal navigation
			elif keynum == KEY_DOWN:
				if not self.ListCursorForward():
					snd = 'bonk'
						
			elif keynum == KEY_UP:
				if not self.ListCursorBackward():
					snd = 'bonk'
					
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
					
			elif keynum in keymap:
				pct = keymap[keynum]
				self.listOffset = int(pct * len(self.listing) / 100.0)
				self.listSelection = 0
					
			elif keynum == KEY_REPLAY:
				self.listSelection = 0
				self.listOffset = 0
				
			elif keynum in [ KEY_ADVANCE, KEY_NUM0 ]:
				if self.listOffset + self.listSelection >= len(self.listing) - 1:
					self.listSelection = 0
					self.listOffset = 0
				else:
					self.listOffset = len(self.listing) - self.listSize
					if self.listOffset < 0:
						self.listOffset = 0
						self.listSelection = len(self.listing)-1
					else:
						self.listSelection = self.listSize - 1
					
			elif keynum in [KEY_SELECT, KEY_RIGHT]:
				if self.listing[index]['dir']:
					# recurse into the next directory
					self.directoryStack.append({'dir': self.currentDir, 'selection' : self.listSelection, 'offset': self.listOffset})
					self.currentDir = self.listing[index]['path']
					self.listSelection = 0
					self.listOffset = 0
					self.vwPleaseWait.set_visible(True)
					self.send_key(KEY_TIVO, 0)
					# return here so the pleasewait can be displayed.  The KEY_TIVO
					# will bring us back below
					return
				else:
					# bring up the details about the selected video
					if self.res == RES_SD:
						self.vwList.set_visible(False)
						self.vwDetail.set_visible(True)
					self.indexDetail = index
					self.currentPage = PAGE_DETAIL
					self.detailMode = MODE_MENU
					self.detailMenuSelection = MENU_PUSH
					
			# this is where we return to after the please wait icon is displayed.  We 
			# perform the long running task and then remove the pleasewait icon
			elif keynum == KEY_TIVO and rawcode == 0:
				self.createListing()
				self.vwPleaseWait.set_visible(False)
				
			elif keynum == KEY_LEFT:
				if len(self.directoryStack) == 0:
					# no more level to pop out from - either bring up
					# the shares page, or if there is only i share, exit
					if len(self.share) == 1:
						self.active = False
						snd = None
					else:
						self.currentPage = PAGE_SHARES
						self.detailMode = MODE_INFO

				else:
					# pop back one directory level
					s = self.directoryStack.pop()
					self.currentDir = s['dir']
					self.listSelection = s['selection']
					self.listOffset = s['offset']
					self.vwPleaseWait.set_visible(True)
					self.send_key(KEY_TIVO, 0)
					return
				
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
			
		elif keynum in [ KEY_ADVANCE, KEY_NUM0 ]:
			if self.shareOffset + self.shareSelection >= len(self.share) - 1:
				self.shareSelection = 0
				self.shareOffset = 0
			else:
				self.shareOffset = len(self.share) - self.listSize
				if self.shareOffset < 0:
					self.shareOffset = 0
					self.shareSelection = len(self.share)-1
				else:
					self.shareSelection = self.listSize - 1

		# jump into the chosen directory			
		elif keynum in [KEY_SELECT, KEY_RIGHT]:
			self.currentDir = ""
			x = self.shareOffset + self.shareSelection
			self.sharetype = self.share[x]['type']
			self.listSelection = 0
			self.listOffset = 0
			self.vwPleaseWait.set_visible(True)
			self.send_key(KEY_TIVO, 0)
			return
			
		elif keynum == KEY_TIVO:
			self.createListing()
			self.currentPage = PAGE_LIST
			self.detailMode = MODE_INFO
			self.vwPleaseWait.set_visible(False)

			
		elif keynum == KEY_LEFT:
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
	# a fourth mode - MODE_INFO - is when the list view is actually in control	
	def handle_key_pressDetail(self, keynum, rawcode):
		snd = 'updown'	
		if self.detailMode == MODE_DELCONFIRM:	
			# in this mode, all we are trying to do is see if they really want to delete
			# a file.  SInce this is a long running operation, we need to put up the
			# display and then send outselves a message so we can actually perform the
			# delete
			if keynum == KEY_THUMBSUP:
				self.vwPleaseWait.set_visible(True)
				self.send_key(KEY_TIVO, 0)
				return
			
			elif keynum == KEY_TIVO:				
				self.delVideo(self.indexDetail)
				self.sleep(2);
				self.createListing();
				self.vwPleaseWait.set_visible(False)
				
				self.detailMode = MODE_MENU
				if (self.indexDetail >= len(self.listing)):
					if self.ListCursorPrevVideo():
						self.indexDetail = self.listOffset + self.listSelection	
					else :
						self.listOffset = 0
						self.listSelection = 0
						if self.res == RES_SD:
							self.vwDetail.set_visible(False)
							self.vwList.set_visible(True)
						self.currentPage = PAGE_LIST
						self.detailMode = MODE_INFO
					
			else:
				# not a thumbs up - back to MODE_MENU
				self.detailMode = MODE_MENU
				
		elif self.detailMode == MODE_TIVOMENU:
			# in this mode, they have chosen push and now we need to decide which tivo
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
				if self.subMenuOffset + self.subMenuSelection >= len(self.tivo) - 1:
					self.subMenuSelection = 0
					self.subMenuOffset = 0
				else :
					self.subMenuOffset = len(self.tivo) - self.subMenuSize
					if self.subMenuOffset < 0:
						self.subMenuOffset = 0
						self.subMenuSelection = len(self.tivo)-1
					else:
						self.subMenuSelection = self.subMenuSize - 1
					
			elif keynum in [ KEY_RIGHT, KEY_SELECT ]:
				# push the video and then back to MODE_MENU
				self.vwPleaseWait.set_visible(True)
				self.send_key(KEY_TIVO, 0)
				return
			
			elif keynum == KEY_TIVO and rawcode == 0:
				self.pushVideo(self.indexDetail, self.subMenuSelection, self.shareSelection+self.shareOffset)
				self.detailMode = MODE_PUSHCONFIRM
				self.vwPleaseWait.set_visible(False)
				snd = 'alert'
			else:
				snd = 'bonk'
				
		elif self.detailMode == MODE_PUSHCONFIRM:
			# in this mode, a push operation is complete - we just want them to press ant
			# key to desmiss the message
			self.detailMode = MODE_MENU
				
		else: #MODE_MENU
			# this is the default details screen mode - basically they are choosing
			# between PUSH and DELETE
			
			# first, if they press the info display and it is not already up, display it
			if keynum == KEY_INFO and not self.vwInfo.isVisible:
				i = self.listOffset + self.listSelection	
				meta = self.listing[i]['meta']
				self.vwInfo.loadmetadata(meta)
				self.vwInfo.show()
					
			# if the info display is up and they press clear or left - remove it
			elif keynum in [ KEY_LEFT, KEY_CLEAR ] and self.vwInfo.isVisible:
				self.vwInfo.hide()
				
			# pagination through the info screens
			elif keynum in [ KEY_DOWN, KEY_CHANNELDOWN ] and self.vwInfo.isVisible:
				if not self.vwInfo.pagedown():
					snd = 'bonk'
					
			elif keynum in [ KEY_UP, KEY_CHANNELUP ] and self.vwInfo.isVisible:
				if not self.vwInfo.pageup():
					snd = 'bonk'
					
			# otherwise if the info display is up, they've pressed an invalid key
			elif self.vwInfo.isVisible:
				snd = 'bonk'
				
			# normal details screen
			elif keynum == KEY_CHANNELUP:
				if self.ListCursorPrevVideo():
					self.indexDetail = self.listOffset + self.listSelection	
				else:
					snd = 'bonk'
			
			elif keynum == KEY_CHANNELDOWN:
				if self.ListCursorNextVideo():
					self.indexDetail = self.listOffset + self.listSelection	
				else:
					snd = 'bonk'
					
			elif keynum == KEY_LEFT:
				if self.res == RES_SD:
					self.vwDetail.set_visible(False)
					self.vwList.set_visible(True)
				self.currentPage = PAGE_LIST
				self.detailMode = MODE_INFO
				
			elif keynum in [KEY_UP, KEY_DOWN]:
				if self.deleteallowed and (self.sharetype == SHARE_VIDEO):
					self.detailMenuSelection = 1 - self.detailMenuSelection
				else:
					snd = 'bonk'
					
			elif keynum in [KEY_RIGHT, KEY_SELECT]:
				# act on their choice - either go into MODE_DELCONFIRM or MODE_TIVOMENU
				# if there is only 1 tivo, bypass the tivo menu and just push it
				if self.detailMenuSelection == MENU_DELETE:
					self.detailMode = MODE_DELCONFIRM
					snd = 'alert'
				else: # MENU_PUSH
					if len(self.tivo) == 1:
						self.vwPleaseWait.set_visible(True)
						self.send_key(KEY_TIVO, 1)
						return
					else:
						self.detailMode = MODE_TIVOMENU
						self.subMenuSelection = 0
						self.subMenuOffset = 0
						
			elif keynum == KEY_TIVO and rawcode == 1:
				self.pushVideo(self.indexDetail, 0, self.shareSelection+self.shareOffset)
				self.detailMode = MODE_PUSHCONFIRM
				self.vwPleaseWait.set_visible(False)
				snd = 'alert'
									
			else:
				snd = 'bonk'
		
		if snd: self.sound(snd)		
		self.drawScreen()

	# paint the screen - first determine which screen we are painting		
	def drawScreen(self):
		if self.currentPage == PAGE_LIST:
			self.drawScreenList()
			if self.res == RES_HD:
				self.detailMode = MODE_INFO
				self.drawScreenDetail()
				self.vwDetail.set_visible(True)
		elif self.currentPage == PAGE_DETAIL:
			if self.res == RES_HD:
				self.drawScreenList()
			self.drawScreenDetail()
		else: # PAGE_SHARES
			self.drawScreenShares()
			if self.res == RES_HD:
				self.detailMode = MODE_INFO
				self.drawScreenDetail()
				self.vwDetail.set_visible(True)

	# draw the listing screen - this is the main screen that the user will be interacting with - this
	# allows browsing through the directories	
	def drawScreenList(self):
		off = self.listOffset
		self.SubTitleView.set_text(self.share[self.shareSelection+self.shareOffset]['name'] + ":" + self.currentDir,
								font=self.myfonts.fnt20,
								colornum=0xffffff, flags=RSRC_VALIGN_BOTTOM)
		
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
			self.vwListText[3].set_text('No videos in this folder - press LEFT to continue', font=self.myfonts.fnt20,
									colornum=0xffffff, flags=RSRC_HALIGN_LEFT);
			self.vwListCue[3].set_resource(self.myimages.CueLeft)
		
		else:
			self.vwListCueTop.clear_resource();
			if self.listSelection == 0 and off != 0:
				self.vwListCueTop.set_resource(self.myimages.CueUp)
				
			self.vwListCueBot.clear_resource();
			if (self.listSelection == self.listSize-1) and (self.listSelection+self.listOffset < len(self.listing)-1):
				self.vwListCueBot.set_resource(self.myimages.CueDown)
			
			for i in range(self.listSize):
				self.vwListBkg[i].clear_resource()
				self.vwListCue[i].clear_resource()
				sx = i + off
				if (sx < len(self.listing)):
					if i == self.listSelection:
						self.vwListBkg[i].set_resource(self.myimages.HiLite)
						self.vwListCue[i].set_resource(self.myimages.CueLeft)
					if i == self.listSelection-1:
						self.vwListCue[i].set_resource(self.myimages.CueUp)
					if i == self.listSelection+1:
						self.vwListCue[i].set_resource(self.myimages.CueDown)
					self.vwListText[i].set_text(self.listing[sx]['disptext'], font=self.myfonts.fnt24,
										colornum=0xffffff, flags=RSRC_HALIGN_LEFT)
					if self.listing[sx]['icon'] == None:
						self.vwListIcon[i].clear_resource()
					else:
						self.vwListIcon[i].set_resource(self.listing[sx]['icon'])
				else:
					self.vwListText[i].clear_resource()
					self.vwListIcon[i].clear_resource()
		
		if self.vwInfo.isVisible and self.res == RES_SD:
			self.vwInfo.paint()

					
	# paint the shares screen - this is much like the listing screen above except that 1) it lists shares only, 
	# and 2) we don't have to worry about it being empty because if it was empty we would have exited by now
	def drawScreenShares(self):
		self.SubTitleView.set_text("Shares", font=self.myfonts.fnt20,
									colornum=0xffffff)
		
		self.updateShares()
		
		off = self.shareOffset
		self.vwListCueTop.clear_resource();
		if self.shareSelection == 0 and off != 0:
			self.vwListCueTop.set_resource(self.myimages.CueUp)
			
		self.vwListCueBot.clear_resource();
		if (self.shareSelection == self.listSize-1) and (self.shareSelection+off < len(self.share)-1):
			self.vwListCueBot.set_resource(self.myimages.CueDown)		
		
		for i in range(self.listSize):
			self.vwListBkg[i].clear_resource()
			self.vwListCue[i].clear_resource()
			sx = i + off
			if (sx < len(self.share)):
				if i == self.shareSelection:
					self.vwListBkg[i].set_resource(self.myimages.HiLite)
					self.vwListCue[i].set_resource(self.myimages.CueLeft)
				if i == self.shareSelection-1:
					self.vwListCue[i].set_resource(self.myimages.CueUp)
				if i == self.shareSelection+1:
					self.vwListCue[i].set_resource(self.myimages.CueDown)
				self.vwListText[i].set_text(self.share[sx]['dispname'], font=self.myfonts.fnt24,
									colornum=0xffffff, flags=RSRC_HALIGN_LEFT)
				if self.share[sx]['icon'] == None:
					self.vwListIcon[i].clear_resource()
				else:
					self.vwListIcon[i].set_resource(self.share[sx]['icon'])
			else:
				self.vwListText[i].clear_resource()
				self.vwListIcon[i].clear_resource()

	# paint the detail screen
	# this is the most detailed of all of the screens - in addition to the detail
	# about the current video, it needs to paing the action menu and if in push mode, the
	# submenu of tivos
	def drawScreenDetail(self):	
		self.indexDetail = self.listOffset + self.listSelection	
	
		if ((self.FirstVideo()) or
					(self.detailMode in [ MODE_DELCONFIRM, MODE_PUSHCONFIRM, MODE_TIVOMENU, MODE_INFO ])):
			self.vwDetailCueTop.clear_resource()
		else:
			self.vwDetailCueTop.set_resource(self.myimages.CueUp)
			
		if ((self.LastVideo()) or
					(self.detailMode in [ MODE_DELCONFIRM, MODE_PUSHCONFIRM, MODE_TIVOMENU, MODE_INFO ])):
			self.vwDetailCueBot.clear_resource()
		else:
			self.vwDetailCueBot.set_resource(self.myimages.CueDown)
			
		if self.currentPage == PAGE_SHARES:
			self.vwDetailTitle.set_text("")
			self.vwDetailSubTitle.set_text("")
			if self.res == RES_HD:
				sx = self.shareOffset + self.shareSelection

				meta = self.share[sx]['meta']
				if 'description' in meta:
					self.vwDetailDescription.set_text(meta['description'], font=self.myfonts.descfont,
										colornum=0xffffff,
										flags=RSRC_TEXT_WRAP + RSRC_HALIGN_LEFT + RSRC_VALIGN_TOP)
				else:
					self.vwDetailDescription.set_text("")
				
				if 'thumb' not in self.share[sx]:
					self.share[sx]['thumb'] = self.getDirThumb(self.share[sx]['path'])
					
				if self.share[sx]['thumb']:
					self.vwDetailThumb.set_visible(True)
					self.vwDetailThumb.set_resource(self.share[sx]['thumb'], flags=RSRC_VALIGN_TOP+thumbFlag)
				else:
					self.vwDetailThumb.set_visible(False)
			else:
				self.vwDetailDescription.set_text("")

					
		elif len(self.listing) == 0:
			self.vwDetailTitle.set_text("")
			self.vwDetailSubTitle.set_text("")
			self.vwDetailDescription.set_text("")
			self.vwDetailThumb.set_visible(False)
			
		elif self.listing[self.indexDetail]['dir']:
			meta = self.listing[self.indexDetail]['meta']
			self.vwDetailTitle.set_text("")
			self.vwDetailSubTitle.set_text("")

			if self.res == RES_HD:
				if 'description' in meta:
					self.vwDetailDescription.set_text(meta['description'], font=self.myfonts.descfont,
										colornum=0xffffff,
										flags=RSRC_TEXT_WRAP + RSRC_HALIGN_LEFT + RSRC_VALIGN_TOP)
				else:
					self.vwDetailDescription.set_text("")
					
				if 'thumb' not in self.listing[self.indexDetail]:
					self.listing[self.indexDetail]['thumb'] = self.getDirThumb(self.listing[self.indexDetail]['fullpath'])
					
				if self.listing[self.indexDetail]['thumb']:
					self.vwDetailThumb.set_visible(True)
					self.vwDetailThumb.set_resource(self.listing[self.indexDetail]['thumb'], flags=RSRC_VALIGN_TOP+thumbFlag)
				else:
					self.vwDetailThumb.set_visible(False)
			else:
				self.vwDetailDescription.set_text("")
					
		else:
			meta = self.listing[self.indexDetail]['meta']
			
			if self.res == RES_SD:
				self.SubTitleView.set_text("", font=self.myfonts.fnt20, colornum=0xffffff)
				self.vwDetailTitle.set_text(meta['title'], font=self.myfonts.fnt30,
										colornum=0xffffff, flags=RSRC_HALIGN_LEFT)
				if 'episodeTitle' in meta:
					self.vwDetailSubTitle.set_text(meta['episodeTitle'], font=self.myfonts.fnt24,
										colornum=0xffffff, flags=RSRC_HALIGN_LEFT)
				else:
					self.vwDetailSubTitle.set_text("")
			else:
				self.vwDetailTitle.set_text("")
				self.vwDetailSubTitle.set_text("")
				if 'thumb' not in self.listing[self.indexDetail]:
					self.listing[self.indexDetail]['thumb'] = self.getThumb(
							self.listing[self.indexDetail]['fullpath'],
							self.listing[self.indexDetail]['fulldir'],
							self.listing[self.indexDetail]['name'])

				if self.listing[self.indexDetail]['thumb']:
					self.vwDetailThumb.set_visible(True)
					self.vwDetailThumb.set_resource(self.listing[self.indexDetail]['thumb'], flags=RSRC_VALIGN_TOP+thumbFlag)
				else:
					self.vwDetailThumb.set_visible(False)
					
			if 'description' in meta:
				self.vwDetailDescription.set_text(meta['description'], font=self.myfonts.descfont,
									colornum=0xffffff,
									flags=RSRC_TEXT_WRAP + RSRC_HALIGN_LEFT + RSRC_VALIGN_TOP)
			else:
				self.vwDetailDescription.set_text("")

		self.vwDetailSubMenuCueTop.clear_resource()
		self.vwDetailSubMenuCueBot.clear_resource()
		
		if self.vwInfo.isVisible:
			self.vwInfo.paint()
			
		if self.deleteallowed and (self.sharetype == SHARE_VIDEO):
			deldim = 0.75
			delbrite = 0
		else:
			deldim = 1
			delbrite = 1
		
		if self.detailMode == MODE_MENU:			
			for i in range(self.subMenuSize):
				self.vwDetailSubMenuBkg[i].set_transparency(1) 
			if self.detailMenuSelection == MENU_PUSH:
				self.vwDetailMenuBkg[MENU_PUSH].set_transparency(0)
				self.vwDetailMenuBkg[MENU_DELETE].set_transparency(deldim)
				self.vwDetailMenuBkg[MENU_CONFIRM].set_transparency(1)
			else:
				self.vwDetailMenuBkg[MENU_PUSH].set_transparency(0.75)
				self.vwDetailMenuBkg[MENU_DELETE].set_transparency(delbrite)
				self.vwDetailMenuBkg[MENU_CONFIRM].set_transparency(1)
				
		elif self.detailMode == MODE_DELCONFIRM:
			self.vwDetailMenuBkg[MENU_PUSH].set_transparency(0.75)
			self.vwDetailMenuBkg[MENU_DELETE].set_transparency(deldim)
			self.vwDetailMenuText[MENU_CONFIRM].set_text('Press Thumbs-Up to Confirm',
									font=self.myfonts.fnt20,
									colornum=0xffffff,
									flags=RSRC_HALIGN_LEFT)
			self.vwDetailMenuBkg[MENU_CONFIRM].set_transparency(0)
			
		elif self.detailMode == MODE_PUSHCONFIRM:
			for i in range(self.subMenuSize):
				self.vwDetailSubMenuBkg[i].set_transparency(1) 
			self.vwDetailMenuBkg[MENU_PUSH].set_transparency(0.75)
			self.vwDetailMenuBkg[MENU_DELETE].set_transparency(deldim)
			self.vwDetailMenuText[MENU_CONFIRM].set_text(self.pushText,
									font=self.myfonts.fnt16,
									colornum=0xffffff,
									flags=RSRC_HALIGN_LEFT)
			self.vwDetailMenuBkg[MENU_CONFIRM].set_transparency(0)
			
		elif self.detailMode == MODE_INFO:			
			for i in range(self.subMenuSize):
				self.vwDetailSubMenuBkg[i].set_transparency(1) 
			self.vwDetailMenuBkg[MENU_PUSH].set_transparency(1)
			self.vwDetailMenuBkg[MENU_DELETE].set_transparency(1)
			self.vwDetailMenuBkg[MENU_CONFIRM].set_transparency(1)
			
		else: # MODE_TIVOMENU
			if self.subMenuOffset != 0:
				self.vwDetailSubMenuCueTop.set_resource(self.myimages.CueUp);
			if self.subMenuOffset + self.subMenuSize < len(self.tivo):
				self.vwDetailSubMenuCueBot.set_resource(self.myimages.CueDown);
				
			for i in range(self.subMenuSize):
				tx = i + self.subMenuOffset
				if tx < len(self.tivo):
					self.vwDetailSubMenuText[i].set_text(self.tivo[tx]['name'],
												font=self.myfonts.fnt20,
												colornum=0xffffff,
												flags=RSRC_HALIGN_LEFT)
					if i == self.subMenuSelection:
						trans = 0
					else:
						trans = 0.75
				else:
					trans = 1
				self.vwDetailSubMenuBkg[i].set_transparency(trans)

	# create all the views for the listing screen and the shares screen
	def createListingViews(self):
		self.vwList = View(self, width=listViewWidth[self.res])
		self.vwListText = []
		self.vwListBkg = []
		self.vwListIcon = []
		self.vwListCue = []
		for i in range(self.listSize):
			yval = listYStart[self.res] + (i*listHeight[self.res])
			bkg = View(self, height=40, width=listViewWidth[self.res], ypos=yval, parent=self.vwList)
			self.vwListBkg.append(bkg)
			self.vwListText.append(View(self, height=40, width=listViewWidth[self.res]-listXText[self.res]-10,
									ypos=0, xpos=listXText[self.res], parent=bkg))
			self.vwListIcon.append(View(self, height=32, width=32, ypos=4, xpos=listXIcon[self.res], parent=bkg))
			self.vwListCue.append(View(self, height=32, width=32, ypos=4, xpos=listXCue[self.res], parent=bkg))
			
		self.vwListCueTop = View(self, height=32, width=32, ypos=listYStart[self.res]-listHeight[self.res]+3,
								xpos=listXCue[self.res], parent=self.vwList)
		self.vwListCueBot = View(self, height=32, width=32, ypos=listYStart[self.res]+listHeight[self.res]*self.listSize,
								xpos=listXCue[self.res], parent=self.vwList)

	# create the views for the details screen		
	def createDetailsViews(self):
		self.vwDetail = View(self, width=detailViewWidth[self.res], xpos = detailViewXPos[self.res], visible=False)
		self.vwDetailTitle = View(self, height=40, ypos=81, xpos=60, parent=self.vwDetail)
		self.vwDetailSubTitle = View(self, height=24, ypos=121, xpos=60, parent=self.vwDetail)
		self.vwDetailDescription = View(self, height=detailDescHeight[self.res], width=detailDescWidth[self.res],
									ypos=detailDescYPos[self.res], xpos=detailDescXPos[self.res], parent=self.vwDetail)
		self.vwDetailMenuBkg = []
		self.vwDetailMenuText = []
		self.vwDetailSubMenuBkg = []
		self.vwDetailSubMenuText = []
		
		if self.res == RES_HD:
			self.vwDetailThumb = View(self, width=ThumbNailWidth, height=ThumbNailHeight, xpos=10, ypos=270, parent=self.vwDetail)

		startymenu = detailMenuYPos[self.res]
		xmenu = detailMenuXPos[self.res]
		startysubmenu = detailSubMenuYPos[self.res]
		xsubmenu = detailSubMenuXPos[self.res]

		for i in range(self.subMenuSize):
			ymenu = startymenu + (i*32)
			bkg = View(self, height=30, width=240, xpos=xmenu, ypos=ymenu, parent=self.vwDetail)
			txt = View(self, height=30, width=220, xpos=20, parent=bkg)
			bkg.set_resource(self.myimages.MenuBkg)
			self.vwDetailMenuBkg.append(bkg)
			self.vwDetailMenuText.append(txt)
			
			ysubmenu = startysubmenu + (i*32)
			bkg = View(self, height=30, width=240, xpos=xsubmenu, ypos=ysubmenu, parent=self.vwDetail)
			txt = View(self, height=30, width=220, xpos=20, parent=bkg)
			bkg.set_resource(self.myimages.MenuBkg)
			self.vwDetailSubMenuBkg.append(bkg)
			self.vwDetailSubMenuText.append(txt)
			if i < len(self.tivo):
				self.vwDetailSubMenuText[i].set_text(self.tivo[i]['name'], font=self.myfonts.fnt20,
										colornum=0xffffff, flags=RSRC_HALIGN_LEFT)

		self.vwDetailSubMenuCueTop = View(self, height=32, width=32, ypos=detailSubCueTopY[self.res],
										xpos=detailSubCueXPos[self.res], parent=self.vwDetail)
		self.vwDetailSubMenuCueBot = View(self, height=32, width=32, ypos=detailSubCueBotY[self.res],
										xpos=detailSubCueXPos[self.res], parent=self.vwDetail)

		self.vwDetailCueTop = View(self, height=32, width=32, ypos=45, xpos=480, parent=self.vwDetail)
		self.vwDetailCueBot = View(self, height=32, width=32, ypos=screenHeight[self.res]-80, xpos=480, parent=self.vwDetail)
		
		self.vwDetailMenuBkg[2].set_transparency(1) # unused for now
		self.vwDetailMenuBkg[MENU_CONFIRM].set_transparency(1)
		self.vwDetailMenuText[MENU_PUSH].set_text('Push Video', font=self.myfonts.fnt20,
									colornum=0xffffff,
									flags=RSRC_HALIGN_LEFT)
		self.vwDetailMenuText[MENU_DELETE].set_text('Delete Video', font=self.myfonts.fnt20,
									colornum=0xffffff,
									flags=RSRC_HALIGN_LEFT)
	
	def ListCursorForward(self):
		if self.listSelection+self.listOffset < len(self.listing)-1:
			if self.listSelection < self.listSize-1:
				self.listSelection = self.listSelection + 1
			else:
				self.listOffset = self.listOffset + 1
			return True
		else:
			return False
		
	def ListCursorBackward(self):
		if self.listSelection == 0:
			if self.listOffset == 0:
				return False
			else:
				self.listOffset = self.listOffset - 1
		else:
			self.listSelection = self.listSelection - 1
		return True
	
	def FirstVideo(self):
		i = self.listOffset + self.listSelection - 1
		if i >= len(self.listing): return True
		
		while (i >= 0):
			if not self.listing[i]['dir']:
				return False
			
			i = i - 1
			
		return True
		
	def LastVideo(self):
		i = self.listOffset + self.listSelection + 1
		while (i < len(self.listing)):
			if not self.listing[i]['dir']:
				return False
			
			i = i + 1
			
		return True
	
	def ListCursorPrevVideo(self):
		saveOffset = self.listOffset
		saveSel = self.listSelection
		while (True):
			if not self.ListCursorBackward():
				self.listOffset = saveOffset
				self.listSelection = saveSel
				return False
			if not self.listing[self.listOffset + self.listSelection]['dir']:
				return True
	
	def ListCursorNextVideo(self):
		saveOffset = self.listOffset
		saveSel = self.listSelection
		while (True):
			if not self.ListCursorForward():
				self.listOffset = saveOffset
				self.listSelection = saveSel
				return False
			if not self.listing[self.listOffset + self.listSelection]['dir']:
				return True

	# load up tivo information from the config file
	def loadTivos(self, cfg):
		def cmptivo (left, right):
			if (left['name'] == right['name']): return 0
			if (left['name'] < right['name']): return -1
			return 0
		
		tlist = []
		section = 'tivos'
		
		allchars = maketrans('', '')
		if cfg.has_section(section):
			i = 0
			while (True):
				i = i + 1
				namekey = 'tivo' + str(i) + '.name'
				tsnkey = 'tivo' + str(i) +  '.tsn'
				if cfg.has_option(section, namekey) and cfg.has_option(section, tsnkey):
					tlist.append({'name' : cfg.get(section, namekey),
									'tsn' : cfg.get(section, tsnkey).translate(allchars, '-')})
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

				self.setupMetadataImport(os.path.dirname(cfgfile))
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
					metaname = os.path.join(path, "folder")
					meta = self.metadata_from_text(metaname)
					self.share.append({'name' : section,
						'type' : SHARE_VIDEO,
						'ip' : ip,
						'port' : port,
						'path' : path,
						'sep' : sep,
						'meta' : meta})
				elif (pyconfig.has_option(section, "type") and pyconfig.get(section, "type") == "dvdvideo" and 
					pyconfig.has_option(section, 'path')):
					path = pyconfig.get(section, 'path')
					metaname = os.path.join(path, "folder")
					meta = self.metadata_from_text(metaname)
					self.share.append({'name' : section,
						'type' : SHARE_DVDVIDEO,
						'ip' : ip,
						'port' : port,
						'path' : path,
						'sep' : sep,
						'meta' : meta})

	def setupMetadataImport(self, pytivo_directory):
		if self.pytivo_metadata: return
		import imp, sys
		sys.path.append(pytivo_directory)
		self.pytivo_metadata = imp.load_source('pytivo_metadata', os.path.join(pytivo_directory, 'metadata.py'))

	def metadata_from_text(self, full_path):
		if self.pytivo_metadata:
			md = self.pytivo_metadata.from_text(full_path)
		else:
			md = metadata.from_text(self, full_path, self.mergefiles, self.mergelines)
		return md

	def metadata_basic(self, full_path):
		if self.pytivo_metadata:
			md = self.pytivo_metadata.basic(full_path)
		else:
			md = metadata.basic(full_path)
		return md

	def addShareIcons(self):
		for share in self.share:
			if (share['type'] == SHARE_VIDEO):
				share['icon'] = self.myimages.IconFolder
			elif (share['type'] == SHARE_DVDVIDEO):
				share['icon'] = self.myimages.IconDVD
				
	def updateShares(self):
		for share in self.share:
			if (share['type'] == SHARE_VIDEO):
				path = share['path']
				dispname = share['name'] + ' (' + str(self.countFiles(path)) + ')'
				share['dispname'] = dispname
			elif (share['type'] == SHARE_DVDVIDEO):
				path = share['path']
				dispname = share['name'] + ' (' + str(self.countDirs(path)) + ')'
				share['dispname'] = dispname
			
	# delete the video and it's associated metadata file		
	def delVideo(self, index):
		curdir = os.path.join(self.share[self.shareSelection+self.shareOffset]['path'], self.currentDir)
		name = self.listing[index]['name']
		fqFileName = os.path.join(self.share[self.shareSelection+self.shareOffset]['path'], self.listing[index]['path'])
		try:
			pass
			os.remove(fqFileName)
		except:
			self.sound('bonk')
		
		for metapath in [ fqFileName + '.txt', 
						os.path.join(curdir, '.meta', name + '.txt') ]:
			if os.path.exists(metapath):
				try:
					os.remove(metapath)
				except:
					self.sound('bonk')
					
		for tnpath in [ fqFileName + '.jpg', 
						os.path.join(curdir, '.meta', name + '.jpg') ]:
			if os.path.exists(tnpath):
				try:
					os.remove(tnpath)
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
				if (left['sorttext'] < right['sorttext']): return -1
				if (left['sorttext'] > right['sorttext']): return 1
				return 0
			elif (left['dir']): return -1
			else: return 1
			
		self.listing = []
		llist = []

		if (self.sharetype == SHARE_DVDVIDEO):
			llist = self.createListingDVDVideo();
		else:
			llist = self.createListingVideo();

		self.listing = sorted(llist, cmp=cmplist)

	def createListingVideo(self):
		llist = []

		root = self.share[self.shareSelection+self.shareOffset]['path']
		fulldir = os.path.join(root, self.currentDir)
		names = os.listdir(fulldir)
		for name in names:
			relpath = os.path.join(self.currentDir, name)
			fullpath = os.path.join(fulldir, name)
			if os.path.isdir(fullpath):
				if name.startswith('.'): continue
				metaname = os.path.join(fullpath, "folder")
				meta = self.metadata_from_text(metaname)
				if len(meta) == 0:
					hasinfo = False
				else:
					hasinfo = True
				dispname = name + ' (' + str(self.countFiles(fullpath)) + ')'
				llist.append({'sorttext': name, 'disptext': dispname,
								'icon': self.myimages.IconFolder, 
								'meta': meta,
								'path': relpath,
								'fullpath': fullpath,
								'hasinfo': hasinfo,
								'dir': True})
			else:
				if os.path.splitext(name)[1].lower() in goodexts:
					meta = self.metadata_from_text(fullpath)
					if not 'title' in meta:
						meta = self.metadata_basic(fullpath)
						
					(sorttext, disptext) = self.formatTitles(meta, name)
	
					llist.append({'sorttext': sorttext,
									'disptext': disptext,
									'meta': meta,
									'fullpath': fullpath,
									'fulldir': fulldir,
									'name': name,
									'icon': self.myimages.IconVideo,
									'path': relpath,
									'hasinfo': True,
									'dir': False})
		return llist

	def createListingDVDVideo(self):
		llist = []

		root = self.share[self.shareSelection+self.shareOffset]['path']
		fulldir = os.path.join(root, self.currentDir)
		if self.isDvdDir(fulldir):
			path, deftitle = os.path.split(fulldir)
			meta, names = self.loadDvdMeta(fulldir, "default", deftitle, False)
			for (title, file) in names:
				relpath = os.path.join(self.currentDir, file)
				fullpath = os.path.join(fulldir, file)
				meta, nm = self.loadDvdMeta(fulldir, file, title, True)
				meta['title'] = title
				llist.append({'sorttext': file, 'disptext': title,
					'icon': self.myimages.IconVideo,
					'meta': meta,
					'path': relpath,
					'name': file,
					'fullpath': fullpath,
					'fulldir': fulldir,
					'hasinfo': True,
					'dir': False})

		else:
			names = os.listdir(fulldir)
			for name in names:
				relpath = os.path.join(self.currentDir, name)
				fullpath = os.path.join(fulldir, name)
				if os.path.isdir(fullpath):
					if name.startswith('.'): continue
					if (self.isDvdDir(fullpath)):
						meta, tnames = self.loadDvdMeta(fullpath, "default", name, False)
						dispname = name + ' (' + str(len(tnames)) + ')'
						llist.append({'sorttext': name, 'disptext': dispname,
									'icon': self.myimages.IconDVD, 
									'meta': meta,
									'path': relpath,
									'fullpath': fullpath,
									'fulldir': fulldir,
									'hasinfo': True,
									'dir': True})
					else:
						metaname = os.path.join(fullpath, "folder")
						meta = self.metadata_from_text(metaname)
						dispname = name + ' (' + str(self.countFiles(fullpath)) + ')'
						llist.append({'sorttext': name, 'disptext': dispname,
									'icon': self.myimages.IconFolder, 
									'meta': meta,
									'path': relpath,
									'fullpath': fullpath,
									'fulldir': fulldir,
									'hasinfo': False,
									'dir': True})
			
		return llist

	def isDvdDir(self, dir):
		dvddir = os.path.join(dir, "VIDEO_TS")
		return os.path.isdir(dvddir)

	def loadDvdMeta(self, metadir, basefn, deftitle, singleDVDtitle):
		metapath = os.path.join(metadir, basefn)
		meta = self.metadata_from_text(metapath)
		if (not 'title' in meta) or (meta['title'] == basefn):
			meta['title'] = deftitle

		titles = []
		kl = meta.keys()
		for k in kl:
			x = regex.search(k)
			if x:
				tn = int(x.group(1))
				if not meta[k].lower().startswith("ignore"):
					filename = "__T%02d.mpg" % tn
					titles.append((meta[k], filename))

				if (singleDVDtitle):
					del(meta[k])

		if len(titles) == 0:
			titles.append((meta['title'], "__T00.mpg"))
			
		return (meta, titles)

	def countFiles(self, dir):
		tally = 0
		names = os.listdir(dir)
		for name in names:
			fullpath = os.path.join(dir, name)
			if os.path.isdir(fullpath):
				if not name.startswith('.'): tally = tally + 1
			else:
				if os.path.splitext(name)[1].lower() in goodexts:
					tally = tally + 1
		return(tally)

	def countDirs(self, dir):
		tally = 0
		names = os.listdir(dir)
		for name in names:
			fullpath = os.path.join(dir, name)
			if os.path.isdir(fullpath):
				if not name.startswith('.'): tally = tally + 1
		return(tally)

	def formatTitles(self, meta, filename):
		if self.sortopt == SORT_FILE:
			sorttext = filename
		else:
			usedEpisodeNum = False
			if self.sortopt == SORT_EPNUM:
				if 'episodeNumber' in meta:
					usedEpisodeNum = True
					if 'title' in meta:
						sorttext = meta['title'] + ':' + meta['episodeNumber']
					else:
						sorttext = meta['episodeNumber']
			if not usedEpisodeNum:			
				if 'episodeTitle' in meta:
					if 'title' in meta:
						sorttext = meta['title'] + ':' + meta['episodeTitle']
					else:
						sorttext = meta['episodeTitle']
				elif 'title' in meta:
					sorttext = meta['title']
				else:
					sorttext = filename
	
		if self.dispopt == DISP_FILE:
			disptext = filename
		else:
			if 'episodeTitle' in meta:
				if self.dispopt == DISP_EPTITLE or self.dispopt == DISP_EPNUMTITLE:
					if 'episodeNumber' in meta and self.dispopt == DISP_EPNUMTITLE:
						disptext = meta['episodeNumber'] + '-' + meta['episodeTitle']
					else:
						disptext = meta['episodeTitle']
				else:
					if 'title' in meta:
						disptext = meta['title'] + ':' + meta['episodeTitle']
					else:
						disptext = meta['episodeTitle']
			elif 'title' in meta:
				disptext = meta['title']
			else:
				disptext = filename
		
		return (sorttext, disptext)
		
	def getThumb(self, fn, dir, name):
		if self.res == RES_SD:
			return None
		
		thumb = None
		for tfn in [ fn + '.jpg',
				os.path.join(dir, '.meta', name + '.jpg'),
				os.path.join(dir, 'folder.jpg'),
				os.path.join(dir, '.meta', 'folder.jpg') ]:
			data = tc.getImageData(tfn)
			if data:
				thumb = Image(self, tfn, data=data)
				break

		return thumb
	
	def getDirThumb(self, fn):
		if self.res == RES_SD:
			return None
		
		thumb = None
		for tfn in [ os.path.join(fn, 'folder.jpg'),
				os.path.join(fn, '.meta', 'folder.jpg') ]:
			data = tc.getImageData(tfn)
			if data:
				thumb = Image(self, tfn, data=data)
				break
			
		return thumb
	
class InfoView(View):
	def __init__(self, app, width, height, xpos, ypos, font):
		View.__init__(self, app, width=width, height=height, xpos=xpos, ypos=ypos, visible=False)
		self.set_resource(app.myimages.Info)
		self.labelView = []
		self.dataView = []
		self.linesPerPage = 0
		self.displayOffset = 0
		self.height = height
		self.width = width
		self.font = font
		self.app = app
		self.hide()
		
	def setinfogeometry(self, fontinfo):
		self.fi = fontinfo
		self.lineHeight = int(fontinfo.height)
		self.linesPerPage = 0
		lblwidth = int(self.width * infoLabelPercent / 100.0)
		self.datawidth = int(self.width * (100.0-infoLabelPercent) / 100.0) - infoRightMargin
		y = 10
		while (y + self.lineHeight <= self.height - 2):
			lbl = View(self.app, parent=self, width=lblwidth, height=self.lineHeight, xpos=10, ypos=y)
			data = View(self.app, parent=self, width=self.datawidth, height=self.lineHeight, xpos=10+lblwidth, ypos=y)
			self.labelView.append(lbl)
			self.dataView.append(data)
			y = y + self.lineHeight
			self.linesPerPage = self.linesPerPage + 1
		self.vwUp = View(self.app, parent=self, width=32, height=16, xpos=lblwidth-24, ypos=2)
		self.vwUp.set_resource(self.app.myimages.InfoUp)
		self.vwDown = View(self.app, parent=self, width=32, height=16, xpos=lblwidth-24, ypos=self.height-18)
		self.vwDown.set_resource(self.app.myimages.InfoDown)

		self.clear()
	
	def show(self):
		self.isVisible = True
		self.set_visible(True)
		
	def hide(self):
		self.isVisible = False
		self.set_visible(False)
		
	def clear(self):
		self.dataContent = []
		self.labelContent = []
		self.lineCount = 0;
		self.displayOffset = 0;
		
	def addline(self, label, data):
		if label in metaXlate:
			lbl = metaXlate[label]
		else:
			lbl = label
	
		if type(data) is str or type(data) is unicode:
			dstring = data
		elif type(data) is list:
			dstring = ', '.join(data)
		else:
			dstring = str(data)
			
		if label in metaSpaceBefore and not self.lastLineBlank:
			self.labelContent.append("")
			self.dataContent.append("")
			self.lineCount = self.lineCount + 1

		spacewidth = self.measure(" ")
		newstring = ""
		nslength = 0
		for w in dstring.split(' '):
			wlen = self.measure(w)
			if nslength != 0:
				wslen = wlen + spacewidth
			else:
				wslen = wlen
			if (nslength + wslen) < self.datawidth:
				if nslength != 0:
					newstring = newstring + " "
				newstring = newstring + w
				nslength = nslength + wslen
			else:
				self.labelContent.append(lbl)
				self.dataContent.append(newstring)
				self.lineCount = self.lineCount + 1
				self.lastLineBlank = False
				newstring = w
				nslength = wlen
				lbl = ""
		if nslength != 0:
			self.labelContent.append(lbl)
			self.dataContent.append(newstring)
			self.lineCount = self.lineCount + 1
			self.lastLineBlank = False
			
		if label in metaSpaceAfter:
			self.labelContent.append("")
			self.dataContent.append("")
			self.lineCount = self.lineCount + 1
			self.lastLineBlank = True
		
	def measure(self, string):
		if len(string) == 0: return(0)
		
		fi = self.fi
		width = 0
		for c in string:
			info = fi.glyphs.get(c, (0, 0))
			width += info[0]	# advance
		if info[1] > info[0]:   # bounding
			width += (info[1] - info[0])
		return int(width)

	def loadmetadata(self, meta):
		def cmpTitle(a, b):
			xa = regex.search(a)
			xb = regex.search(b)
			if xa and xb:
				return cmp(int(xa.group(1)), int(xb.group(1)))
			else:
				if a in metaXlate:
					sa = metaXlate[a]
				else:
					sa = a
				if b in metaXlate:
					sb = metaXlate[b]
				else:
					sb = b

				return cmp(sa, sb)

		self.clear()
		self.lastLineBlank = True
		if meta == None: return
		
		for m in metaFirst:
			if m in meta:
				self.addline(m, meta[m])

		skeys = sorted(meta.keys(), cmpTitle)
		for m in skeys:
			if m not in metaFirst and m not in metaIgnore:
				self.addline(m, meta[m])
		
	def paint(self):
		if self.displayOffset == 0:
			self.vwUp.set_visible(False)
		else:
			self.vwUp.set_visible(True)
			
		if self.displayOffset + self.linesPerPage >= self.lineCount:
			self.vwDown.set_visible(False)
		else:
			self.vwDown.set_visible(True)
			
		i = 0
		while i < self.linesPerPage:
			n = self.displayOffset + i
			if n >= self.lineCount:
				self.labelView[i].set_text("")
				self.dataView[i].set_text("")
			else:
				self.labelView[i].set_text(self.labelContent[n],
					font=self.font,
					colornum=0xffffff,
					flags=RSRC_HALIGN_LEFT)
				self.dataView[i].set_text(self.dataContent[n],
					font=self.font,
					colornum=0xffffff,
					flags=RSRC_HALIGN_LEFT)
			i = i + 1
	
	def pagedown(self):
		if self.displayOffset + self.linesPerPage >= self.lineCount:
			return False
		
		self.displayOffset = self.displayOffset + self.linesPerPage
		if self.displayOffset + self.linesPerPage > self.lineCount:
			self.displayOffset = self.lineCount - self.linesPerPage
		self.paint()
		return True
	
	def pageup(self):
		if self.displayOffset == 0:
			return False;
		
		self.displayOffset = self.displayOffset - self.linesPerPage
		if self.displayOffset < 0:
			self.displayOffset = 0
		self.paint()
		return True
		

