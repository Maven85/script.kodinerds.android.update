# -*- coding: utf-8 -*-

from datetime import timedelta as datetime_timedelta
from json import dumps as json_dumps, loads as json_loads
from os.path import join as os_path_join, sep as os_path_sep
from re import compile as re_compile, findall as re_findall
from simplecache import SimpleCache
from six import PY2
from six.moves import urllib
from socket import setdefaulttimeout as socket_setdefaulttimeout
from time import time as time_time
from traceback import format_exc as traceback_format_exc
from xbmc import executebuiltin as xbmc_executebuiltin, executeJSONRPC as xbmc_executeJSONRPC, log as xbmc_log, \
    LOGDEBUG as xbmc_LOGDEBUG, LOGERROR as xbmc_LOGERROR, Monitor as xbmc_Monitor
from xbmcaddon import Addon as xbmcaddon_Addon
from xbmcgui import Dialog as xbmcgui_Dialog, DialogProgress as xbmcgui_DialogProgress, ListItem as xbmcgui_ListItem
from xbmcvfs import delete as xbmcvfs_delete, exists as xbmcvfs_exists, mkdir as xbmcvfs_mkdir

if PY2:
    from xbmc import translatePath as xbmcvfs_translatePath
else:
    from xbmcvfs import translatePath as xbmcvfs_translatePath

# Plugin Info
ADDON_ID = 'script.kodinerds.android.update'
REAL_SETTINGS = xbmcaddon_Addon(id=ADDON_ID)
ADDON_NAME = REAL_SETTINGS.getAddonInfo('name')
ADDON_PATH = REAL_SETTINGS.getAddonInfo('path')
ADDON_VERSION = REAL_SETTINGS.getAddonInfo('version')
ICON = REAL_SETTINGS.getAddonInfo('icon')
LANGUAGE = REAL_SETTINGS.getLocalizedString

# # GLOBALS ##
TIMEOUT = 15
MIN_VER = 5  # Minimum Android Version Compatible with Kodi
BASE_URL = 'https://repo.kodinerds.net/index.php'
MAIN = [
    {'label': 'Matrix', 'url': '{}?action=list&scope=all&version=matrix/'.format(BASE_URL), 'regex': 'download=(.*net\.kodinerds\.maven\.kodi\.arm.*)"'},
    {'label': 'Matrix-FireTV', 'url': '{}?action=list&scope=all&version=matrix/'.format(BASE_URL), 'regex': 'download=(.*net\.kodinerds\.maven\.kodi\.firetv\.arm.*)"'},
    {'label': 'Nexus', 'url': '{}?action=list&scope=all&version=nexus/'.format(BASE_URL), 'regex': 'download=(.*net\.kodinerds\.maven\.kodi20\.arm.*)"'},
    {'label': 'Nexus-FireTV', 'url': '{}?action=list&scope=all&version=nexus/'.format(BASE_URL), 'regex': 'download=(.*net\.kodinerds\.maven\.kodi20\.firetv\.arm.*)"'},
    {'label': 'Omega', 'url': '{}?action=list&scope=all&version=omega/'.format(BASE_URL), 'regex': 'download=(.*net\.kodinerds\.maven\.kodi21\.arm.*)"'},
    {'label': 'Omega-FireTV', 'url': '{}?action=list&scope=all&version=omega/'.format(BASE_URL), 'regex': 'download=(.*net\.kodinerds\.maven\.kodi21\.firetv\.arm.*)"'},
    {'label': 'Piers', 'url': '{}?action=list&scope=all&version=piers/'.format(BASE_URL), 'regex': 'download=(.*net\.kodinerds\.maven\.kodi22\.arm.*)"'},
]
DEBUG = REAL_SETTINGS.getSetting('Enable_Debugging') == 'true'
CLEAN = REAL_SETTINGS.getSetting('Disable_Maintenance') == 'false'
VERSION = REAL_SETTINGS.getSetting('Version')
CUSTOM = (REAL_SETTINGS.getSetting('Custom_Manager') or 'com.android.documentsui')
FMANAGER = {0:'com.android.documentsui', 1:CUSTOM}[int(REAL_SETTINGS.getSetting('File_Manager'))]
DOWNLOAD_FOLDER = REAL_SETTINGS.getSetting('Download_Folder')


def log(msg, level=xbmc_LOGDEBUG):
    if DEBUG == False and level != xbmc_LOGERROR: return
    if level == xbmc_LOGERROR: msg += ', {0}'.format(traceback_format_exc())
    xbmc_log('[{0}-{1}] {2}'.format(ADDON_ID, ADDON_VERSION, msg), level)


def selectDialog(label, items, pselect=-1, uDetails=True):
    select = xbmcgui_Dialog().select(label, items, preselect=pselect, useDetails=uDetails)
    if select >= 0: return select
    return None


socket_setdefaulttimeout(TIMEOUT)


class Installer(object):


    def __init__(self):
        self.myMonitor = xbmc_Monitor()
        self.cache = SimpleCache()
        if not self.chkVersion(): return
        self.buildMain('')


    def disable(self, build):
        xbmcgui_Dialog().notification(ADDON_NAME, VERSION, ICON, 8000)
        if not xbmcgui_Dialog().yesno(ADDON_NAME, LANGUAGE(30011).format(build), LANGUAGE(30012)): return False
        xbmc_executeJSONRPC('{"jsonrpc": "2.0", "method":"Addons.SetAddonEnabled","params":{"addonid":"{0}","enabled":false}, "id": 1}'.format(ADDON_ID))
        xbmcgui_Dialog().notification(ADDON_NAME, LANGUAGE(30009), ICON, 4000)
        return False


    def chkVersion(self):
        try:
            build = int(re_compile('Android (\d+)').findall(VERSION)[0])
        except: build = MIN_VER
        if build >= MIN_VER: return True
        else: return self.disable(build)


    def getAPKs(self, url):
        log('getAPKs: path = {0}'.format(url))
        try:
            cacheResponse = self.cache.get('{0}.openURL, url = {1}'.format(ADDON_NAME, url))
            if not cacheResponse:
                cacheResponse = dict(entries=list())
                if url == '':
                    for item in MAIN:
                        entry = dict()
                        entry.update(dict(tag='folder'))
                        entry.update(dict(name=item.get('label')))
                        entry.update(dict(url=item.get('url')))
                        entry.update(dict(regex=item.get('regex')))
                        cacheResponse.get('entries').append(entry)
                else:
                    regex = url.rsplit('/', 1)[1].split('=', 1)[1]
                    if regex:
                        request = urllib.request.Request(url)
                        response = urllib.request.urlopen(request, timeout=TIMEOUT)
                        cookie = response.info().get_all('Set-Cookie')
                        request.add_header("Cookie", cookie[0])
                        html = urllib.request.urlopen(request, timeout=TIMEOUT).read().decode('utf-8')
                        matches = re_findall(regex, html)
                        if matches:
                            for match in matches:
                                entry = dict()
                                entry.update(dict(tag='file'))
                                entry.update(dict(name=match.rsplit('/', 1)[1]))
                                entry.update(dict(date=match.rsplit('/', 1)[1].split('-')[2]))
                                entry.update(dict(url=BASE_URL))
                                entry.update(dict(data='{{"c_item[]": "download={}"}}'.format(match)))
                                cacheResponse.get('entries').append(entry)
                            cacheResponse.update(dict(entries=sorted(cacheResponse.get('entries'), key=lambda k: k['name'].split('-', 2)[2], reverse=True)))

                self.cache.set('{0}.openURL, url = {1}'.format(ADDON_NAME, url), cacheResponse, expiration=datetime_timedelta(minutes=5))
            return cacheResponse
        except Exception as e:
            log('openURL Failed! {0}'.format(e), xbmc_LOGERROR)
            xbmcgui_Dialog().notification(ADDON_NAME, LANGUAGE(30001), ICON, 4000)
            return None


    def buildItems(self, path):
        entries = self.getAPKs(path).get('entries', {})
        if entries is None or len(entries) == 0: return
        for entry in entries:
            if entry.get('tag') == 'file' and entry.get('name').endswith('.apk'):
                label = entry.get('name')
                label2 = '{}-{}-{}'.format(entry.get('date')[:4], entry.get('date')[4:6], (entry.get('date')[6:] if len(entry.get('date')) == 8 else entry.get('date')[6:8]))
                if len(entry.get('date')) > 8:
                    time = entry.get('date')[8:]
                    if len(time) == 3:
                        label2 = '{} 0{}:{}'.format(label2, time[:1], time[1:])
                    else:
                        label2 = '{} {}:{}'.format(label2, time[:2], time[2:])
                li = xbmcgui_ListItem(label, label2, path=entry.get('url'))
                li.setProperty('data', entry.get('data'))
                li.setArt({'icon': ICON})
                yield (li)
            elif entry.get('tag') == 'folder':
                label = entry.get('name')
                li = xbmcgui_ListItem(label, path='{}&regex={}'.format(entry.get('url'), entry.get('regex')))
                li.setArt({'icon': ICON})
                yield (li)


    def buildMain(self, path):
        log('buildMain')
        items = list(self.buildItems(path))
        if len(items) == 0: return
        else: select = selectDialog(ADDON_NAME, items)
        if select is None or select < 0: return  # return on cancel.
        if items[select].getProperty('data'):
            if not xbmcvfs_exists(DOWNLOAD_FOLDER): xbmcvfs_mkdir(DOWNLOAD_FOLDER)
            dest = xbmcvfs_translatePath(os_path_join(DOWNLOAD_FOLDER, items[select].getLabel()))
            REAL_SETTINGS.setSetting("LastPath", dest)
            return self.downloadAPK(items[select].getPath(), dest, items[select].getProperty('data'))
        else:
            self.buildMain(items[select].getPath())


    def fileExists(self, dest):
        if xbmcvfs_exists(dest):
            if not xbmcgui_Dialog().yesno(ADDON_NAME, '{0}: {1}'.format(LANGUAGE(30004), dest.rsplit(os_path_sep, 1)[-1]), nolabel=LANGUAGE(30005), yeslabel=LANGUAGE(30006)): return True
        elif CLEAN and xbmcvfs_exists(dest): self.deleleAPK(dest)
        return False


    def deleleAPK(self, path):
        count = 0
        # some file systems don't release the file lock instantly.
        while not self.myMonitor.abortRequested() and count < 3:
            count += 1
            if self.myMonitor.waitForAbort(1): return
            try:
                if xbmcvfs_delete(path): return
            except: pass


    def downloadAPK(self, url, dest, data):
        if self.fileExists(dest): return self.installAPK(dest)
        start_time = time_time()
        dia = xbmcgui_DialogProgress()
        fle = dest.rsplit(os_path_sep, 1)[1]
        dia.create(ADDON_NAME, LANGUAGE(30002).format(fle))
        data = urllib.parse.urlencode(json_loads(data)).encode()
        try: urllib.request.urlretrieve(url, dest, lambda nb, bs, fs: self.pbhook(nb, bs, fs, dia, start_time, fle), data)
        except Exception as e:
            dia.close()
            xbmcgui_Dialog().notification(ADDON_NAME, LANGUAGE(30001), ICON, 4000)
            log('downloadAPK, Failed! ({0}) {1}'.format(url, e), xbmc_LOGERROR)
            return self.deleleAPK(dest)
        dia.close()
        return self.installAPK(dest)


    def pbhook(self, numblocks, blocksize, filesize, dia, start_time, fle):
        try:
            percent = min(numblocks * blocksize * 100 / filesize, 100)
            currently_downloaded = float(numblocks) * blocksize / (1024 * 1024)
            kbps_speed = numblocks * blocksize / (time_time() - start_time)
            if kbps_speed > 0: eta = int((filesize - numblocks * blocksize) / kbps_speed)
            else: eta = 0
            kbps_speed = kbps_speed / 1024
            if eta < 0: eta = divmod(0, 60)
            else: eta = divmod(eta, 60)
            total = (float(filesize) / (1024 * 1024))
            label = '[B]Downloading: [/B] {0}'.format(os_path_join(DOWNLOAD_FOLDER, fle))
            label2 = '{0:.02f} MB of {1:.02f} MB'.format(currently_downloaded, total)
            label2 += ' | [B]Speed:[/B] {0:.02f} Kb/s'.format(kbps_speed)
            label2 += ' | [B]ETA:[/B] {0:02d}:{1:02d}'.format(eta[0], eta[1])
            dia.update(int(percent), '{0} {1}'.format(label, label2.replace('.', ',')))
        except Exception('Download Failed'): dia.update(100)
        if dia.iscanceled(): raise Exception('Download Canceled')


    def installAPK(self, apkfile):
        xbmc_executebuiltin('StartAndroidActivity({0},,,"content://{1}")'.format(FMANAGER, apkfile))


if __name__ == '__main__': Installer()
