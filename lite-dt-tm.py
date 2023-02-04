import sys
import wx
import wx.adv
import pytz
import datetime
import urllib.request, urllib.error, urllib.parse
import subprocess as sp
 

def geturldata(url):
  return_sts = 0
  return_msg = ''
  ntp_list = []
  req = urllib.request.Request(
    url,
    data=None, 
    headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'})

  try:
    response = urllib.request.urlopen(req)
  except Exception as e:
    return_sts = 1
    return_msg = "Exception Error:" + " URL failed to open"
  except urllib.error.HTTPError as err:
    return_sts = 1
    return_msg = "HTTP Error:" + err.reason + "; error_code:" + err.code
  except IOError as e: 
    return_sts = 1
    if hasattr(e, 'reason'): 
      return_msg = "Unable to reach a server. Reason: "+ e.reason
    elif hasattr(e, 'code'): 
      return_msg = "The server couldn\'t fulfill the request. Error code: "+ e.code
  except ValueError as error:
    return_sts = 1
    return_msg = "Value Error:" + error.message
  except URLError as error:
    return_sts = 1
    return_msg = "URL Error:" + error.reason.strerror

  if return_sts != 0:
    return return_sts, return_msg, ntp_list

  response_output = response.read()
  response_str  = response_output.decode('utf-8')
  response_list = response_str.splitlines()

  for i in response_list:
    """
    if      an element in the list contains data
      if    the element does not contain any of the following characters: '#', ':', '(', ')', ']'
        and the element does not start with http
        add the element to the list
    """

    if len(i):
      if i.find('#') < 0 and i.find(':') < 0 and i.find('(') < 0 and i.find(')') < 0 and i.find('/') < 0 and i.startswith('http') <= 0:
        ntp_list.append(i)
  
  return return_sts, return_msg, ntp_list
  

class DateTimeFrame(wx.Frame):
  def __init__(self):
    wx.Frame.__init__(self, parent=None, title='LITE TIME AND DATE', style= wx.SIMPLE_BORDER)
    rect = wx.GetClientDisplayRect()
    self.selectionpanel = SelectionPanel(self)
    self.buttonpanel = ButtonPanel(self)
    self.framesizer = wx.BoxSizer(wx.VERTICAL)
    self.framesizer.Add(self.selectionpanel,0, flag=wx.EXPAND)
    # Add an empty space 10 pixels high above and below the button panel
    self.framesizer.Add((0,5),0)
    self.framesizer.Add(self.buttonpanel,0, flag=wx.EXPAND)
    self.framesizer.Add((0,5),0)
    self.SetSizerAndFit(self.framesizer)
    self.Center()


  def OnClose(self, event):
    self.Close()


class SelectionPanel(wx.Panel):
  # This panel's parent is DateTimeFrame. DateTimeFrame is the top level window.
  def __init__(self, parent):
    wx.Panel.__init__(self, parent=parent)
    self.parent = parent
    self.SetBackgroundColour('light grey')
    self.return_sts = 0
    self.internet_connection_flag = 1
    self.time_zone = ""
    self.time_zone_idx = -1
    self.ntp_active_flag = 0
    self.server_name = ""
    self.server_name_idx = -1
    self.current_ntp_server = ""
    self.ntp_list = []

    # Create the list of timezones
    self.tz_list = pytz.all_timezones

    self.GetSystemData()

    # Create the title label
    self.title_lbl = wx.StaticText(self, -1, "Lite Time and Date")

    # Create the timezone selection label
    self.tz_lbl = wx.StaticText(self, -1, "Select your timezone")

    # Create the timezone drop down menu
    self.tz_menu = wx.Choice(self, -1, choices=self.tz_list)
    self.tz_menu.SetSelection(self.time_zone_idx)
    self.tz_menu.Bind(wx.EVT_CHOICE, self.OnTZMenuChoice)
    self.current_tz = self.time_zone

    # Create the sync method label
    self.sync_lbl = wx.StaticText(self, -1, "Select sync method")

    # Create two lists for the sync methods
    # The first list contains 2 sync methods because an internet connection does not exist
    # The second list contains 3 sync methods because an internet connection exists
    self.sync_method_list1 = []
    self.sync_method_list1.append("Hardware clock")
    self.sync_method_list1.append("Time Zone")
    self.sync_method_list2 = []
    self.sync_method_list2.append("Hardware clock")
    self.sync_method_list2.append("NTP server")
    self.sync_method_list2.append("Time Zone")
    self.current_sync_method_list = self.sync_method_list1
    if self.internet_connection_flag:
      self.current_sync_method_list = self.sync_method_list2
    self.current_sync_method_idx = 0
    if self.internet_connection_flag and self.ntp_active_flag:
      self.current_sync_method_idx = 1

    # Create the sync method drop down menu
    self.sync_menu = wx.Choice(self, -1, choices=self.current_sync_method_list)
    self.sync_menu.SetSelection(self.current_sync_method_idx)
    self.sync_menu.Bind(wx.EVT_CHOICE, self.OnSyncMenuChoice)

    # Create the ntp server drop down menu
    self.ntp_menu = wx.Choice(self, -1, choices=self.ntp_list)
    self.ntp_menu.SetSelection(self.server_name_idx)
    self.ntp_menu.Bind(wx.EVT_CHOICE, self.OnNtpMenuChoice)
    if not self.internet_connection_flag:
      self.ntp_menu.Enable(0)
    else:
      self.current_ntp_server = self.server_name

    # Create the date picker
    self.datepicker = wx.adv.DatePickerCtrl(self, -1)
    self.current_date = self.datepicker.GetValue().Format('%A, %B %d, %Y')
    if self.internet_connection_flag and self.ntp_active_flag:
      self.datepicker.Enable(0)

    # Create the time picker
    self.timepicker = wx.adv.TimePickerCtrl(self, -1)
    self.current_time = self.timepicker.GetValue().Format('%H:%M%p')
    if self.internet_connection_flag and self.ntp_active_flag:
      self.timepicker.Enable(0)

    # Create the output text area
    self.outputtxt = wx.StaticText(self, -1, "")

    self.selectionsizer = wx.BoxSizer(wx.VERTICAL)
    self.selectionsizer.Add((0,10),0)
    self.selectionsizer.Add(self.title_lbl,0, flag=wx.EXPAND|wx.LEFT, border = 20)
    self.selectionsizer.Add((0,60),0)
    self.selectionsizer.Add(self.tz_lbl,0, flag=wx.EXPAND)
    self.selectionsizer.Add((0,10),0)
    self.selectionsizer.Add(self.tz_menu,0, flag=wx.EXPAND)
    self.selectionsizer.Add((0,10),0)
    self.selectionsizer.Add(self.sync_lbl,0, flag=wx.EXPAND)
    self.selectionsizer.Add((0,10),0)
    self.selectionsizer.Add(self.sync_menu,0, flag=wx.EXPAND)
    self.selectionsizer.Add((0,10),0)
    self.selectionsizer.Add(self.ntp_menu,0, flag=wx.EXPAND)
    self.selectionsizer.Add((0,10),0)
    self.selectionsizer.Add(self.datepicker,0, flag=wx.EXPAND)
    self.selectionsizer.Add((0,10),0)
    self.selectionsizer.Add(self.timepicker,0, flag=wx.EXPAND)
    self.selectionsizer.Add(self.outputtxt,0, flag=wx.EXPAND|wx.ALL, border = 20)
    self.SetSizer(self.selectionsizer)

    self.SetOutputData()


  def GetSystemData(self):
    # If it is not possible to get the time zone, the application must abort with an appropriate error message
    try:
      result = sp.run(['timedatectl', 'show', '--property=Timezone'], stdout=sp.PIPE, stderr=sp.PIPE )
    except:
      self.return_sts = 1
      return
    self.time_zone = result.stdout.decode().split('\n')[0].split('=')[1]
    
    if self.time_zone not in self.tz_list:
      self.tz_list.append(self.time_zone)
      self.tz_list.sort()
    self.time_zone_idx = self.tz_list.index(self.time_zone)

    # Verify if an internet connection exists.
    # Create the list of NTP servers
    # A list of the public ntp servers is available at gist.github.com
    url = "https://gist.github.com/mutin-sa/eea1c396b1e610a2da1e5550d94b0453/raw"
    return_sts, return_msg, self.ntp_list = geturldata(url)
    if return_sts:
      self.internet_connection_flag = 0
      self.ntp_list = []
      #self.ntp_list.append("No internet connection")

    try:
      result = sp.run(['timedatectl', 'show', '--property=NTP'], stdout=sp.PIPE, stderr=sp.PIPE )
    except:
      self.return_sts = 1
      return
    if result.stdout.decode().split('\n')[0].split('=')[1] == "yes":
      self.ntp_active_flag = 1
    else:
      return
    
    try:
      result = sp.run(['timedatectl', 'show-timesync', '--property=ServerName'], stdout=sp.PIPE, stderr=sp.PIPE )
    except:
      self.return_sts = 1
      return
    self.server_name = result.stdout.decode().split('\n')[0].split('=')[1]
    if len(self.ntp_list):
      if self.server_name not in self.ntp_list:
        self.ntp_list.append(self.server_name)
        self.ntp_list.sort()
      self.server_name_idx = self.ntp_list.index(self.server_name)


  def GetReturnStatus(self):
    return self.return_sts


  def OnTZMenuChoice(self, event):
    self.tz_idx = event.GetSelection()
    self.current_tz = self.tz_list[self.tz_idx]
    # Update the time zone
    try:
      result = sp.run(['timedatectl', 'set-timezone', self.current_tz], stdout=sp.PIPE, stderr=sp.PIPE )
    except:
      pass
    today_wx = wx.DateTime.Now()
    today_dt = datetime.datetime.now()
    self.timepicker.SetValue(today_dt)
    self.current_time = self.timepicker.GetValue().Format('%H:%M%p')
    self.SetOutputData()


  def OnApplyDateTime(self):
    self.current_date = self.datepicker.GetValue().Format('%Y-%m-%d')
    self.current_time = self.timepicker.GetValue().Format('%H:%M:%S')
    self.current_date_time = self.current_date + ' ' + self.current_time
    # Update the date and time
    result = sp.run(['timedatectl', 'set-time', self.current_date_time], stdout=sp.PIPE, stderr=sp.PIPE )

    self.current_date = self.datepicker.GetValue().Format('%A, %B %d, %Y')
    self.current_time = self.timepicker.GetValue().Format('%H:%M%p')
    self.SetOutputData()


  def OnSyncMenuChoice(self, event):
    self.sync_idx = event.GetSelection()
    if self.internet_connection_flag:
      if self.sync_idx == 0:
        self.UpdateNewHardwareClockChoice()
      elif self.sync_idx == 1:
        self.UpdateNewNTPServerChoice()
      elif self.sync_idx == 2:
        self.UpdateNewTimezoneChoice()
    else:
      if self.sync_idx == 0:
        self.UpdateNewHardwareClockChoice()
      elif self.sync_idx == 1:
        self.UpdateNewTimezoneChoice()


  def OnNtpMenuChoice(self, event):
    self.ntp_idx = event.GetSelection()
    self.current_ntp_server = self.ntp_list[self.ntp_idx]
    self.SetOutputData()


  def UpdateNewHardwareClockChoice(self):
    self.ntp_menu.Enable(0)
    self.datepicker.Enable(1)
    self.timepicker.Enable(1)
    self.parent.buttonpanel.OnEnableApplyButton(1)


  def UpdateNewNTPServerChoice(self):
    self.ntp_menu.Enable(1)
    self.datepicker.Enable(0)
    self.timepicker.Enable(0)
    self.parent.buttonpanel.OnEnableApplyButton(0)


  def UpdateNewTimezoneChoice(self):
    pass


  def SetOutputData(self):
    self.outputdata = self.current_tz + "\nNTP Server: " + self.current_ntp_server + "\nCurrent Date: " + self.current_date + "\nCurrent Time: " + self.current_time
    self.outputtxt.SetLabel(self.outputdata)


  def GetNTPStatus(self):
    if self.internet_connection_flag and self.ntp_active_flag:
      return 1
    else:
      return 0


class ButtonPanel(wx.Panel):
  # This panel's parent is DateTimeFrame. DateTimeFrame is the top level window.
  def __init__(self, parent):
    wx.Panel.__init__(self, parent=parent)
    self.parent = parent
    self.parent.selectionpanel.GetNTPStatus()
    self.buttonpanelsizer = wx.BoxSizer(wx.HORIZONTAL)
    self.closebutton = wx.Button(self, label = 'Close')
    self.Bind(wx.EVT_BUTTON, self.OnClose, self.closebutton)
    self.buttonpanelsizer.AddStretchSpacer(prop=1)
    self.buttonpanelsizer.Add(self.closebutton, 0, wx.ALIGN_CENTER)
    self.applybutton = wx.Button(self, label = 'Apply')
    if self.OnNTPStatus():
      self.applybutton.Enable(0)
    self.Bind(wx.EVT_BUTTON, self.OnApply, self.applybutton)
    self.buttonpanelsizer.AddStretchSpacer(prop=1)
    self.buttonpanelsizer.Add(self.applybutton, 0, wx.ALIGN_CENTER)
    self.SetSizer(self.buttonpanelsizer)
    self.closebutton.SetFocus()


  def OnClose(self, event):
    self.parent.OnClose(event)


  def OnApply(self, event):
    self.parent.selectionpanel.OnApplyDateTime()


  def OnNTPStatus(self):
    return self.parent.selectionpanel.GetNTPStatus()


  def OnEnableApplyButton(self, status):
     self.applybutton.Enable(status)


def main():
  app = wx.App(False)
  date_time_frame = DateTimeFrame()
  if date_time_frame.selectionpanel.GetReturnStatus():
    title = "Date and Time cannot be adjusted."
    error_msg = "Contact the system administrator."
    error_dialog = wx.MessageDialog(None, error_msg, title, wx.OK, wx.DefaultPosition)
    error_dialog.ShowModal()
    error_dialog.Destroy()
    date_time_frame.Close()
  date_time_frame.Show(True)

  app.MainLoop()
  
if __name__ == '__main__':
  main()
