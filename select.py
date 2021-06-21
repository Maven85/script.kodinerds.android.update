#     Copyright (C) 2020 Team-Kodi
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# -*- coding: utf-8 -*-

from traceback import format_exc as traceback_format_exc
from xbmc import log as xbmc_log, LOGDEBUG as xbmc_LOGDEBUG, LOGERROR as xbmc_LOGERROR
from xbmcaddon import Addon as xbmcaddon_Addon
from xbmcgui import Dialog as xbmcgui_Dialog
from xbmcvfs import listdir as xbmcvfs_listdir

# Plugin Info
ADDON_ID      = 'script.kodinerds.android.update'
REAL_SETTINGS = xbmcaddon_Addon(id=ADDON_ID)
ADDON_NAME    = REAL_SETTINGS.getAddonInfo('name')
ADDON_VERSION = REAL_SETTINGS.getAddonInfo('version')
ICON          = REAL_SETTINGS.getAddonInfo('icon')
LANGUAGE      = REAL_SETTINGS.getLocalizedString

## GLOBALS ##
DEBUG         = REAL_SETTINGS.getSetting('Enable_Debugging') == 'true'
CUSTOM        = REAL_SETTINGS.getSetting('Custom_Manager')

def log(msg, level=xbmc_LOGDEBUG):
    if DEBUG == False and level != xbmc_LOGERROR: return
    if level == xbmc_LOGERROR: msg += ', {0}'.format(traceback_format_exc())
    xbmc_log('[{0}-{1}] {2}'.format(ADDON_ID, ADDON_VERSION, msg), level)

def selectDialog(label, items, pselect=-1, uDetails=False):
    select = xbmcgui_Dialog().select(label, items, preselect=pselect, useDetails=uDetails)
    if select >= 0: return select
    return None
    
class Select(object):
    def __init__(self):
        items  = xbmcvfs_listdir('androidapp://sources/apps/')[1]
        select = selectDialog(LANGUAGE(30020),items)
        if select is None or select < 0: return #return on cancel.
        REAL_SETTINGS.setSetting('Custom_Manager', '{0}'.format(items[select]))

if __name__ == '__main__': Select()