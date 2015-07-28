# Copyright 2014-2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.
#
# This is a script to install yotta. Eventually I would like to add all OS's to this script
# but for now it just works on windows. 
#
# There are some ganky hacks in place holding it together, such as opening 
# IE to get certificates that windows doesnt have. Currently the script
# just downloads the dependencies and has the user run through the click
# throughs. Eventually I would like to hack together some silent installers
# which would involve some exe brute forcing and some registry hacking. 
#

import math
import sys
import pip
import os
import subprocess

#
# Downloads to download
#
# Note that on windows the '.exe' extension is necessary to run with a subprocess
downloads = {
	"all":{
		"cmake.exe":"http://www.cmake.org/files/v3.2/cmake-3.2.1-win32-x86.exe",
		"ninja.zip":"https://github.com/martine/ninja/releases/download/v1.5.3/ninja-win.zip",
		"gcc.exe":"https://launchpad.net/gcc-arm-embedded/4.8/4.8-2014-q3-update/+download/gcc-arm-none-eabi-4_8-2014q3-20140805-win32.exe"
	},
	"64bit":{
	},
	"32bit":{
	}

}

#
# Prompt to re-install / download packages
#
def shouldInstall(binName):
	import shutil
	import shutilwhich
	question = "\n\t"+binName+" already exists on your PATH, would you like to reinstall it? (y/n): "
	choice = ""
	if shutil.which(binName):
		sys.stdout.write(question)
		choice = raw_input().lower() # check for a y for yes, all others are no
		dir(choice)
		if choice =='y':
			return True #re-install bin
		else:
			print("\n\tSkipping installation of "+binName)
			return False  #skip installation
	else:
		return True; #bin does not exist, install it

#
# Cygwin Install Script - TODO
#
def cygwin():
	print("Cygwin is not currently supported. Please install for the windows command line. See  http://docs.yottabuild.org/#installing-on-windows for details.");
	return;

#
# Linux Install Script - TODO
#
def linux():
	print("For Linux install instructions please see http://docs.yottabuild.org/#installing-on-linux");
	return;

#
# OSX Install Script - TODO
#
def osx():
	print("For OSX install instructions please see http://docs.yottabuild.org/#installing-on-osx");
	return;

#
# Windows Install Script
#
def windows():
	import wget
	import shutil
	import shutilwhich
	print("\nOpening an Internet Explorer window to launchpad.net to grab security certificate to download GCC.");
	w = subprocess.Popen(r'"C:\Program Files\Internet Explorer\iexplore.exe" https://launchpad.net/' ); #hack to get the security certificate in place so we can dowload the file.
	print("\nDownloading dependencies...");
	# Downloads for both 64bit / 32bit
	for key in downloads['all']:
		if os.path.isfile(key):
			print("\n\t" +key +" already exists in this folder. [Skipped]");
		else:
			print("\n\tDownloading " +key);
			wget.download(downloads['all'][key],key);
	w.kill(); #close the internet explorer window hack
	# 64bit Downloads
	if sys.maxsize > math.pow(2,32): 
		print("\nWindows 64bit detected");
		for key in downloads['64bit']:
			if os.path.isfile(key):
				print("\n\t" +key +" already exists in this folder.[Skipped]");
			else:
				print("\n\tDownloading " +key );
				wget.download(downloads['64bit'][key],key);

	# 32bit Downloads
	elif sys.maxsize <= math.pow(2,32): 
		print("\nWindows 32bit detected");
		for key in downloads['32bit']:
			if os.path.isfile(key):
				print("\n\t" +key +" already exists in this folder. [Skipped]");
			else:
				print("\n\tDownloading " +key);
				wget.download(downloads['32bit'][key],key);
	
	# Install the Packages
	print("\nInstalling packages: Please Follow the Click Throughs ");

	#Yotta
	if shouldInstall("yotta"):
		print("\n\tInstalling Yotta from pip ...");
		x = subprocess.call(['pip','install','-qU','yotta']);
		if x!= 0:
			print("\t[**ERROR**]: Yotta install failed. Please run 'pip install yotta -U' from the command line");
		else:
			print("\t[Installed]");

	#cmake
	if shouldInstall("cmake"):
		print("\n\tInstalling Cmake: Please allow admin permissions and check 'Add CMake to system PATH for all users' option");	
		x = subprocess.call(['cmake.exe'], shell=True);
		if x!=0:
			print("\t[**ERROR**]: Cmake install failed, Please re-run installer and give admin rights to installer");
		else:
			print("\t[Installed]");

	#gcc-arm-none-eabi
	if shouldInstall("arm-none-eabi-gcc"):
		print("\n\tInstalling gcc-none-eabi-gcc : Please allow admin permissions and check 'Add path to enviroment variable' box");
		x = subprocess.call(['gcc.exe'], shell=True);
		if x!=0:
			print("\t[**ERROR**]: gcc-none-eabi-gcc install failed, Please re-run installer and give admin rights to installer");
		else:
			print("\t[Installed]");	

	#ninja
	if shouldInstall("ninja"):
		import zipfile
		import shutil
		print("\n\tInstalling Ninja...");
		zipfile.ZipFile('ninja.zip').extract('ninja.exe');
		if not os.path.exists('c:/ninja'):
			os.makedirs('c:/ninja');
		shutil.copy2('ninja.exe','c:/ninja/ninja.exe')
		print("\t**REQUIRED:** Add c:/ninja/ to your PATH to complete ninja install")


#
# install extra packages for python
#
def bootstrap():
	# check for Pip
	try: 
		import pip
	except ImportError:
		print("\n****ERROR: Pip is not installed on this system. Please update your python install and / or install Pip, then retry***");
		sys.exit();
		return;

	#install wget if it doesnt already exist
	try: 
		import wget
	except ImportError:
		print("\nWget package missing, installing now...");
		x = subprocess.call(['pip', 'install', '-q','wget']);
		if x!= 0:
			print("\t**ERROR** wget did not install correctly!");
			sys.exit();
		else:
			print("[Installed]");

	#install shutil.which if it doesnt already exist.
	#Python 3 has this already, python 2.7 does not so we need to install it.
	try: 
		import shutilwhich
	except ImportError:
		print("\nshutilwhich package missing, installing now...");
		x = subprocess.call(['pip', 'install', '-q','shutilwhich']);
		if x!= 0:
			print("\t**ERROR** shutilwhich did not install correctly!");
			sys.exit();
		else:
			print("[Installed]");

	return;


#
# The main function figures out what OS is running and calls appropriate handler
#
def main():
	chooseOS = {
		"win32"	: windows, 	# Windows32 and 64bit
		"cygwin": cygwin, 	# cygwin on windows
		"darwin": osx, 		# Mac OSX
		"linux"	: linux		# Linux
	}
	if sys.platform in chooseOS:
		bootstrap();
		chooseOS[sys.platform]();
	else:
		print("Your OS is not supported!");

	return;


if __name__ == "__main__":
    main()
