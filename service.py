# -*- coding: utf-8 -*-

from json import dumps as json_dumps, loads as json_loads
from platform import machine as platform_machine
from traceback import format_exc as traceback_format_exc
from xbmc import executeJSONRPC as xbmc_executeJSONRPC, getInfoLabel as xbmc_getInfoLabel, log as xbmc_log, \
    LOGDEBUG as xbmc_LOGDEBUG, LOGERROR as xbmc_LOGERROR, Monitor as xbmc_Monitor
from xbmcaddon import Addon as xbmcaddon_Addon
from xbmcgui import Dialog as xbmcgui_Dialog
from xbmcvfs import delete as xbmcvfs_delete, exists as xbmcvfs_exists

# Plugin Info
ADDON_ID = 'script.kodinerds.android.update'
REAL_SETTINGS = xbmcaddon_Addon(id=ADDON_ID)
ADDON_NAME = REAL_SETTINGS.getAddonInfo('name')
ADDON_VERSION = REAL_SETTINGS.getAddonInfo('version')
ICON = REAL_SETTINGS.getAddonInfo('icon')
LANGUAGE = REAL_SETTINGS.getLocalizedString

# # GLOBALS ##
DEBUG = REAL_SETTINGS.getSetting('Enable_Debugging') == 'true'
CLEAN = REAL_SETTINGS.getSetting('Disable_Maintenance') == 'false'
CACHE = REAL_SETTINGS.getSetting('Disable_Cache') == 'false'
VER_QUERY = '{"jsonrpc":"2.0","method":"Application.GetProperties","params":{"properties":["version"]},"id":1}'


def log(msg, level=xbmc_LOGDEBUG):
    if DEBUG == False and level != xbmc_LOGERROR: return
    if level == xbmc_LOGERROR: msg += ', {0}'.format(traceback_format_exc())
    xbmc_log('[{0}-{1}] {2}'.format(ADDON_ID, ADDON_VERSION, msg), level)


class Service(object):


    def __init__(self):
        self.myMonitor = xbmc_Monitor()
        self.setSettings()
        lastPath = REAL_SETTINGS.getSetting("LastPath")  # CACHE = Keep last download, CLEAN = Remove all downloads
        if not CACHE and CLEAN and xbmcvfs_exists(lastPath): self.deleteLast(lastPath)


    def deleteLast(self, lastPath):
        log('deleteLast')
        try:
            xbmcvfs_delete(lastPath)
            xbmcgui_Dialog().notification(ADDON_NAME, LANGUAGE(30007), ICON, 4000)
        except Exception as e: log('deleteLast Failed! {0}'.format(e), xbmc_LOGERROR)


    def setSettings(self):
        log('setSettings')
        [func() for func in [self.getBuild, self.getPlatform, self.getVersion]]


    def getBuild(self):
        log('getBuild')
        REAL_SETTINGS.setSetting('Build', json_dumps(json_loads(xbmc_executeJSONRPC(VER_QUERY) or '').get('result', {}).get('version', {})))


    def getPlatform(self):
        log('getPlatform')
        count = 0
        try:
            while not self.myMonitor.abortRequested() and count < 15:
                count += 1
                if self.myMonitor.waitForAbort(1): return
                build = platform_machine()
                if len(build) > 0: return REAL_SETTINGS.setSetting("Platform", build)
        except Exception as e: log('getVersion Failed! {0}'.format(e), xbmc_LOGERROR)


    def getVersion(self):
        log('getVersion')
        count = 0
        try:
            while not self.myMonitor.abortRequested() and count < 15:
                count += 1
                if self.myMonitor.waitForAbort(1): return
                build = (xbmc_getInfoLabel('System.OSVersionInfo') or 'busy')
                if build.lower() != 'busy': return REAL_SETTINGS.setSetting("Version", str(build))
        except Exception as e: log('getVersion Failed! {0}'.format(e), xbmc_LOGERROR)


if __name__ == '__main__': Service()
