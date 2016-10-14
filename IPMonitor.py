#!/usr/bin/env python3





'''
Monitor current IP.

Needs GSettings schema installing.

Requires 'curl'
'''

## TODO:
# Do the subsitution and restart? (nginx, etc.)
# Hide on start
# full history of drop/disconnect
## Consider:
# Ping
# Server PID


import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import subprocess
from time import sleep
from gi.repository import Gio, GLib

from datetime import datetime, date, time





#################
### User Data ###
#################

# Test time in secs
# A pro setup might test every few seconds or something
# But we only need to know a rough frame. 20 mins? 
#TESTINTERVAL=20*60*60
TESTINTERVAL=5

GSCHEMA = "uk.co.archaicgroves.server.monitor"
IP_KEY = 'ip'
IP_FAIL_KEY = 'ip-fail-time'

ipProvider = "icanhazip.com"
    
    
    
    
############
# Internal #
############         



        
       
class MyWindow(Gtk.Window):

    def vField(self, label, field):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        box.pack_start(label, False, True, 0)
        box.pack_start(field, False, True, 0)
        return box
        
        
    def __init__(self):
        Gtk.Window.__init__(self, title="Server Monitor")
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.box.set_homogeneous(False)
        self.add(self.box)
        
        approvedIPlabel = Gtk.Label()
        approvedIPlabel.set_markup("<b>Approved IP:</b>")
        # Use to test IP as failure
        #gsettings.set_string(IP_KEY, 'goop')
        self.approvedIPDisplay = Gtk.Label(gsettings.get_string(IP_KEY))
        self.box.pack_start(
            self.vField(approvedIPlabel,self.approvedIPDisplay),
            True, True, 0
            )
     
        self.currentIPlabel = Gtk.Label()
        self.currentIPlabel.set_markup("<b>Current IP:</b>")
        self.currentIPDisplay = Gtk.Label('Unloaded')
        self.box.pack_start(
            self.vField(self.currentIPlabel, self.currentIPDisplay),
            True, True, 0
            )
        
        self.IPFailtimelabel = Gtk.Label()
        self.IPFailtimelabel.set_markup("<b>IP Fail Time:</b>")
        self.IPFailtimeDisplay = Gtk.Label('Unloaded')
        self.box.pack_start(
            self.vField(self.IPFailtimelabel, self.IPFailtimeDisplay),
            True, True, 0
            )
            
        self.img = Gtk.Image()
        self.img.set_from_icon_name("gtk-no", Gtk.IconSize.DND)

        self.spinner = Gtk.Spinner()
        self.box.pack_start(self.spinner, True, True, 0)
        
        self.box.pack_start(self.img, True, True, 0)

        self.button1 = Gtk.Button(label="Approve current IP")
        self.button1.connect("clicked", self.approve_current_ip)
        self.box.pack_start(self.button1, True, True, 0)

        # interval test
        GLib.timeout_add_seconds(TESTINTERVAL, self.testIP)
        # Kickstart, as timeout waits.
        self.testIP()
        
        
        
    def _get_ip(self, ipProvider):
        self.spinner.start()

        cmd = ["/usr/bin/curl", "-s", ipProvider]
        ret = b''
        
        try:
            ret = subprocess.check_output(cmd)
        except:
            ret = b''
            
        self.spinner.stop()

        ipStr = ret.decode('UTF-8')
        return ipStr
    
    def showFailIPInfo(self, ipStr, failTimeStr):
        self.currentIPDisplay.set_markup(ipStr)
        self.currentIPlabel.show()
        self.currentIPDisplay.show()
        self.IPFailtimeDisplay.set_text(failTimeStr)
        self.IPFailtimelabel.show()
        self.IPFailtimeDisplay.show()
        
    def hideFailIPInfo(self):
        self.currentIPlabel.hide()
        self.currentIPDisplay.hide()
        self.IPFailtimelabel.hide()
        self.IPFailtimeDisplay.hide()

    def failtimeToString(self, ft):
        if (ft):
            return ft.strftime("%a/%d/%b/%Y %I:%M%p")
        else:
            return 'Nothing verified'

    def setToConnectionWarning(self):
        failTimeStr = gsettings.get_string(IP_FAIL_KEY)
        self.showFailIPInfo(
            '<span foreground="red">No Access</span>',
            failTimeStr
            )
        self.img.set_from_icon_name("dialog-warning", Gtk.IconSize.DND)
        
    def testIP(self):
        #print("test...")
        provedIP = gsettings.get_string(IP_KEY)
        currentIP = self._get_ip(ipProvider)
        if(currentIP):
            if(provedIP == currentIP):
                # If by any chance ip switches back, kill the fail time
                gsettings.set_string(IP_FAIL_KEY, '')
                # Usually an assert....
                self.hideFailIPInfo()
                self.approvedIPDisplay.set_text(currentIP)
                self.img.set_from_icon_name("gtk-yes", Gtk.IconSize.DND)
            else:
                # Only set failtime if empty
                failTimeStr = gsettings.get_string(IP_FAIL_KEY)
                if(not failTimeStr):
                    failTimeStr = self.failtimeToString(datetime.now())
                    gsettings.set_string(IP_FAIL_KEY, failTimeStr)
                self.showFailIPInfo(
                    currentIP,
                    failTimeStr
                    )
                self.img.set_from_icon_name("gtk-no", Gtk.IconSize.DND)
        else:
            self.setToConnectionWarning()
        return True




    def approve_current_ip(self, widget):
        currentIP = self._get_ip(ipProvider)
        if(currentIP):
            # both gSettings
            gsettings.set_string(IP_KEY, currentIP)
            gsettings.set_string(IP_FAIL_KEY, '')
            # display
            self.approvedIPDisplay.set_text(currentIP)
            self.hideFailIPInfo()
            self.img.set_from_icon_name("gtk-yes", Gtk.IconSize.DND)
        else:
            self.setToConnectionWarning()

        
# get proved IP
gsettings = Gio.Settings.new(GSCHEMA)

win = MyWindow()
win.connect("delete-event", Gtk.main_quit)
win.show_all()
Gtk.main()
