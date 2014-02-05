# Logging, standard library
import logging
# OS, standard library
import os

# ConfigParser, MIT, read and write ini files, standard library
import ConfigParser
# Watchdog, Apache 2, watch file for changes, pip install watchdog
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# constants
user_ini_file = '~/.yotta/config'
ini_files     = [user_ini_file, '/usr/local/etc/yottaconfig', '/etc/yottaconfig']

# private state
parser = None

# private API
def _iniFiles():
    for x in ini_files:
        yield os.path.expanduser(x)

def _ensureParser():
    global parser
    if not parser:
        parser = ConfigParser.SafeConfigParser()
        # set up handlers to re-load settings whenever they change
        class ReloadHandler(FileSystemEventHandler):
            def on_deleted(self, event):
                logging.debug('settings: file deleted, will reload all files, event: %s', event)
                self.on_modified(event);
            def on_modified(self, event):
                global parser
                logging.debug('settings: file changed, will reload all files, event: %s', event)
                p = ConfigParser.SafeConfigParser()
                p.read(_iniFiles())
                parser = p
        for filepath in _iniFiles():
            if os.path.exists(filepath):
                logging.debug('will watch settings file "%s" for changes', filepath)
                o = Observer()
                o.schedule(ReloadHandler(), filepath, recursive=False)
                o.start()
        parser.read(_iniFiles())

# public API
def getProperty(section, name):
    _ensureParser()
    try:
        return parser.get(section, name)
    except ConfigParser.NoSectionError:
        return None

def setProperty(section, name, value):
    # use a local parser instance so that we don't copy system-wide settings
    # into the user config file
    p = ConfigParser.SafeConfigParser()
    full_ini_path = os.path.expanduser(user_ini_file)
    ini_directory = os.path.dirname(full_ini_path)
    if not os.path.exists(ini_directory):
        os.makedirs(ini_directory)
    with open(full_ini_path, 'r+') as f:
        p.readfp(f)
        f.seek(0)
        if not p.has_section(section):
            p.add_section(section)
        p.set(section, name, value)
        p.write(f)
        f.truncate()
    # also update the in-memory settings:
    if parser is not None:
        if not parser.has_section(section):
            parser.add_section(section)
        parser.set(section, name, value)

