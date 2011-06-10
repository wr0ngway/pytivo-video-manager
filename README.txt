PyTivo Video Manager

version 0.4

Added an info page that pops up when you press the info button and displays all the metadata about the current video

version 0.3c

Fixed bug when navigating OUT of an empty directory and bug where share list was not being updated when a video is deleted

version 0.3b

Added 1) share and directory listings show the number of videos and directories contained within them, and 2) added a "Please Wait" icon
during length operations - currently this includes:  building a directory listing, pushing a video, and deleting a video.

version 0.3a

Removed the clear key - it no longer exits the app. 
Removed calls to unicode from metadata.py
Added functionality to advance key - if pressed while at the end of a list, it will move to the start of the list.

version 0.3

Allow various sorting and display options:
display=file - only display the file name
       =episodetitle - only display the episode name
       =episodenumtitle = display both the episode number and name
if not specified (or if an invalid option is specified) then it will display title+episode title
If you specify metadata that does not exist, vidmgr will use the title and/or the file name in order to display something

sort=file - sort the screen listing based on the file name only
    =episodenumber - sort based on the episode number (if present) - NOTE - this is a character string comparison - not numeric
If not specified (or if an invalid option is specified) sorting will be based on title and/or file name
Again, if the specified meta data does not exist, a sort key will be built from whatever is available using title and/or filename

Also in version 0.3 - fixed the issue reported by reneg where shares on the second and subsequent pages of the shares listing were wrong


version 0.2g 

When deleting a video, if the meta file was in the .meta directory, it was not
deleted.  Also, the jpg artwork file was not deleted either.  Both of these 
have been fixed

version 0.2f

Version 0.2f properly implements what 0.2e was supposed to do

Change with 0.2e

Allow artwork to be placed in the .meta subdirectory

version 0.2d

Changes with 0.2d

Ignore directories beginning with . - this allows .meta directories for holding pytivo meta data

Changes with 0.2c

Added descsize option to alter size of description font

Changes with 0.2b

Added logic to metadata.py to strip non-ascii chars from meta data

Changes with version 0.2

Support HD resolution - this allows addition of screen capture/art work.  Also, tried to pay more
attention to TV safe area - although this is hard for HD since the simulator doesn't support HD.
Added exts option to config file.






what it is
==========

PyTivo video manager (vidmgr) is an HME application that allows you to request that videos in your 
library be "Pushed" to your tivo instead of the normal pull.  SInce it's an HME app, this request
can be made from your easy chair with your tivo remote.  Pushing allows videos that are in a
compatible MP4 format to be transferred as is - saving time and space - instead of the transcoding
that a pull will always cause.  vidmgr can also be used to delete videos from your library.

vidmgr is a TiVo HME application designed to operate under wmcbrine's pyhme
framework.  It is NOT a stand-alone application.  Please install the pyhme package and make sure it
is running before you install vidmgr.

Vidmgr is designed to operate in conjunction with the PyTivo transcoding server - If you are not 
using pytivo, then there is no point in installing vidmgr.  I have tested vidmgr with the mcbrine
fork of pytivo.  I am not familiar with the other forks to know whether or not it will run there.

====================================================================================================

installation/setup
==================

If you've gotten this far, you must want to really install this.  It's very simple:

1. Go to the directory where you have pyhme installed.  There should be a lot of subdirectories here,
one per application.  Create a new directroy here named "vidmgr"

2. Copy the contents of the vidmgr directory from this package into this new directory.  This should
include __init__.py and a bunch of .png files

3. Copy metadata.py and config.merge from this package into the pyhme main directory.  BTW - metadata.py
is an extract of the same named file that is part of pytivo.  I can't take the credit for this code.

4. Configure - you will need to merge the config.merge file that was delivered with this package with
your config.ini file that you are currently using.  There are three areas you need to pay attention to:  

	a) You may or may not have an "apps" line under the heading [hmeserver].  If you do not, then
the hmeserver will start all apps that it finds.  If you do, then it will only start the named apps.
So if you do have this line and you do want to run vidmgr, add the word "vidmgr" to this line - no quotes
or commas or other punctuation.

	b) you can specify various vidmgr options:  specify the file extensions that vidmgr will pay
attention to with the exts option.  By default this is .mpg, .mp4, .wmv, and .avi.  You can also
specify the size of the font used for descriptive text - by default 16.  All of this is done by
putting entries in the [vidmgr] section of the config.ini as follows:
[vidmgr]
exts=.mpg .mp4 .avi .wmv .m4v
descsize=16


	c) You need to tell vidmgr about your Tivos.  For each tivo, you need to specify the name and
the TSN.  The format for this is:
[tivos]
tivo1.name=Family Room
tivo1.tsn=TSN1
tivo2.name=Master Bedroom
tivo2.tsn=TSN2

You can have an arbitrary number of Tivos, but as soon as vidmgr detects a gap in the numbering
sequence it will stop parsing.  Make sure the TSN's are accurate as this is how pytivo knows which
tivo to push to.

	d) You need to tell vidmgr about your PyTivo instances.  There are 4 possible pytivo parameters:
		- config is mandatory and is the fully qualified name of the pytivo config file. 
vidmgr reads this file to determine the share names and locations.  
		- You may specify an ip address for the machine on which this instance of pytivo is running.
If you do not specify one, the local IP address is used.
		- If the pytivo config file names a port in the server section, then vidmgr will
use that port number.  Otherwise you need to specify the port number here.
		-Finally, if your hme server is running in a different host environment than this
instance of pytivo, then you need to specify the directory separator character for the pytivo environment.

format for specifying pytivo information:
[pytivos]
pytivo1.config=/usr/local/pytivo/pyTivo.conf
pytivo1.ip=192.168.1.201
pytivo1.port=9032
pytivo1.sep=/

You can have an arbitrary number of pytivos, but as soon as vidmgr detects a gap in the numbering
sequence it will stop parsing.

A note about the separator:  If you are running both vidmgr and pytivo on the same machine, then this
is not required.  However, if (as was happening while I was developing) you are running vidmgr
in a Windows environment (where the directory separator is unfortunately a backslash '\') and 
you are running pytivo in a linux environment (where the separator is a forward slash '/') then
you need to specify "pytivox.sep=/".  Otherwise, vidmgr will happily send its requests to 
pytivo using a backslash in the paths and this will cause pytivo to choke.

=======================================================================================================

Usage
=====

Vidmgr presents a directory tree to you.  You can step into and out of directories using the normal
tivo navigation keys.  The directory tree is rooted at ths list of shares, unless there is only 1 share
in which case it is rooted at the topmost directory of that share.

In HD mode, vidmgr will also show video artwork on the right hand side of the screen.  Vidmgr looks for
the following file:  <full-video-file-name-including-extension>.jpg or, if this doesn't exist, folder.jpg.
The view into which this graphic is placed is 320 pixels wide by 44 pixels high.  If your graphic exceeds
those dimensions it will be cropped.

Once you choose a video file, you will be shown some of the metadata associated with that file,
and then have two options - push or delete.  In HD mode, this detail will be on the right side of the 
screen as you navigate through the directories - it is not on a separate screen

If you choose delete, you will be asked to press thumbs-up to confirm and when you do, the file and
its associated metadata file will be deleted.  If you press ANYTHING other than thumbs-up, the
delete is cancelled.

If you choose push and you only have 1 tivo, then it will simply initiate a push to that tivo and
give you a confirmation message.  If you have multiple tivos, you need to choose the one you want to
push to from the provided list.  After choosing, vidmgr will initiate the push and give you the
confirmation message.  The confirmation message can be dismissed with ANY keypress
