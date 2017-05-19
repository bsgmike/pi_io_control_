import time
from tkinter import *  # get a widget object
from tkinter.messagebox import *  # get standard dialogs
from threading import Timer, Thread, Event
from ScrolledText import *
from time import gmtime, strftime

import pifacedigitalio

mycolor2 = '#F6D153'

powerupinprogress = False
starttime = 0
NumberOfRelayTransitions = 0
AlarmState = False

class ThemedButton(Button):
    def __init__(self, parent=None, **configs):
        Button.__init__(self, parent, **configs)
        self.pack()
        self.config(fg='red', bg=mycolor2, font=('courier', 12), relief=RAISED, bd=5)


#Reference example of repeating timer
#Don't delete.....
class RepeatingTimer(object):
    def __init__(self, interval, f, *args, **kwargs):
        self.interval = interval
        self.f = f
        self.args = args
        self.kwargs = kwargs
        self.timer = None

    def callback(self):
        self.f(*self.args, **self.kwargs)
        self.start()

    def cancel(self):
        reportmsg('Repeat timer cancelled', 2)
        self.timer.cancel()

    def start(self):
        reportmsg('Repeat timer started', 2)
        self.timer = Timer(self.interval, self.callback)
        self.timer.start()



class PowerUpTimer(object):
    def __init__(self, *args, **kwargs):
        self.interval = 60
        self.f = self.PowerUpComplete
        self.args = args
        self.kwargs = kwargs
        self.timer = None

    def PowerUpComplete(self):
        global waitforalarm
        global powerupinprogress
        reportmsg('Power up complete - now waiting for alarm to turn on', 2)
        powerupinprogress = False
        waitforalarm.start()

    def callback(self):
        self.f(*self.args, **self.kwargs)
        #self.start()

    def cancel(self):
        # reportmsg('Power up timer cancelled', 2)
        if self.timer:
            self.timer.cancel()

    def start(self):
        global powerupinprogress
        reportmsg('Power up timer started', 2)
        powerupinprogress = True
        self.timer = Timer(self.interval, self.PowerUpComplete)
        self.timer.start()


# class RecycleTimer(object):
#     def __init__(self, *args, **kwargs):
#         self.interval = 15
#         self.timer = None
#         self.cycleno = 0
#
#     def callback(self):
#         global nglControl
#         global offtimer
#         global NumberOfRelayTransitions
#         global powerupinprogress
#         reportmsg('Cycle ' + repr(self.cycleno) + ':   No of relay transitions seen = ' + repr(NumberOfRelayTransitions), 1)
#         self.cycleno += 1
#         NumberOfRelayTransitions = 0
#         powerupinprogress = True
#         nglControl.TurnOff()
#         offtimer.start()
#
#     def cancel(self):
#         reportmsg('Recycle timer cancelled', 2)
#         if self.timer:
#             self.timer.cancel()
#
#     def start(self):
#         reportmsg('Recycle timer started', 2)
#         self.powerupcomplete = True
#         self.timer = Timer(self.interval, self.callback)
#         self.timer.start()

class WaitForAlarm(object):
    def __init__(self, *args, **kwargs):
        self.interval = 2
        self.timer = None
        self.cycleno = 0

    def callback(self):
        global nglControl
        global delayBeforePowerDown
        global AlarmState
        global powerupinprogress

        if(AlarmState == True):
            reportmsg(strftime("%Y-%m-%d %H:%M:%S", gmtime()) + '   Saw alarm turn on - repowering' + '  - cycle ' + repr(self.cycleno))
            self.cycleno += 1
            delayBeforePowerDown.start()
        else:
            self.start()

    def cancel(self):
        reportmsg('WaitForAlarm timer cancelled', 2)
        if self.timer:
            self.timer.cancel()

    def start(self):
        # reportmsg('Now waiting for alarm', 2)
        self.powerupcomplete = True
        self.timer = Timer(self.interval, self.callback)
        self.timer.start()

class OffTimer(object):
    def __init__(self, *args, **kwargs):
        self.interval = 60
        self.timer = None

    def callback(self):
        global nglControl
        reportmsg('60 second Off period complete', 2)
        nglControl.TurnOn()

    def cancel(self):
        reportmsg('Off timer cancelled', 2)
        if self.timer:
            self.timer.cancel()

    def start(self):
        reportmsg('60 second Off period started',2)
        self.timer = Timer(self.interval, self.callback)
        self.timer.start()

class DelayBeforePowerDown(object):
    def __init__(self, *args, **kwargs):
        self.interval = 30
        self.timer = None

    def callback(self):
        global nglControl
        global offtimer
        reportmsg('30 second delay before power down complete', 2)
        nglControl.TurnOff()
        offtimer.start()

    def cancel(self):
        reportmsg('DelayBeforePowerDown timer cancelled', 2)
        if self.timer:
            self.timer.cancel()

    def start(self):
        reportmsg('Applying 30 scond delay before powering down', 2)
        self.timer = Timer(self.interval, self.callback)
        self.timer.start()

class MyLabel(Frame):
    def __init__(self, parent=Frame, titletext = 'Legend'):
        Frame.__init__(self, parent)
        self.config(bg='white', padx=0)
        self.labelfont = ('arial', 12, 'normal')
        self.bgColor = '#97FFF2'
        self.fgColor = '#A61D39'
        self.legend = titletext
        self.value = Label(self, text='OFF')
        self.make_widgets()

    def make_widgets(self):
        titlebar = Label(self, text=self.legend, justify=RIGHT)
        titlebar.pack(side=LEFT, anchor="w",  padx=0, pady=0)
        titlebar.config(font=self.labelfont)
        titlebar.config(bg=self.bgColor, fg=self.fgColor, width=20)

        self.value.pack(side=RIGHT, anchor="e", padx=10, pady=0)
        self.value.config(font=self.labelfont)
        self.value.config(bg='white', fg=self.fgColor)

    def changevalue(self, newvalue):
        self.value.config(text=newvalue)


class NglControls(Frame):
    def __init__(self, parent=Frame):
        Frame.__init__(self, parent)
        self.config(bg='beige', padx=30)
        self.data = 42
        self.NglState = False
        self.pfd = pifacedigitalio.PiFaceDigital()
        self.labelfont = ('arial', 12, 'normal')
        self.bgColor = '#F6D153'
        self.fgColor = '#720C7e'


        self.make_widgets()

    def make_widgets(self):
        titlebar = Label(self, text='---   NGL Controls   ---')
        titlebar.pack(side=TOP,  anchor="nw", padx=0, pady=0)
        titlebar.config(font=self.labelfont)
        titlebar.config(bg=self.bgColor, fg=self.fgColor)

        TurnOnButton = Button(self, text='Turn On NGL', command=self.TurnOn)
        TurnOnButton.pack(side=TOP, anchor="nw")

        TurnOffButton = Button(self, text='Turn Off NGL', command=self.TurnOff)
        TurnOffButton.pack(side=TOP, anchor="nw")

        ToggleButton = Button(self, text='Toggle NGL', command=self.Toggle)
        ToggleButton.pack(side=TOP, anchor="nw")

        self.QuitButton = Button(self, text='Quit', command=self.quit)
        self.QuitButton.pack(side=TOP, anchor="nw")

    # def message(self):
    #     self.data += 1
    #     print('Hello frame world %s!' % self.data)

    def TurnOn(self):
        global starttime
        global putimer

        reportmsg('TurnOn NGL', 2)
        # putimer.start()
        self.pfd.relays[0].value = 1
        self.NglState = True

    def TurnOff(self):
        # global putimer
        # putimer.cancel()
        reportmsg('TurnOff NGL', 2)
        self.pfd.relays[0].value = 0
        self.NglState = False

    def Toggle(self):
        reportmsg('Toggle NGL', 2)
        if self.NglState == True:
            # putimer.cancel()
            # offtimer.cancel()
            # delayBeforePowerDown.cancel()
            # waitforalarm.cancel()
            reportmsg('TurnOff NGL', 2)
            self.pfd.relays[0].value = 0
            self.NglState = False
        else:
            reportmsg('TurnOn NGL', 2)
            self.pfd.relays[0].value = 1
            self.NglState = True

    def quit(self):
        reportmsg('NGL controls quitting', 2)
        nglMonitor.quit()
        sys.exit()

    def TestMsg(self):
        print('Just testing')


class NglMonitor(Frame):
    def __init__(self, parent=Frame):
        Frame.__init__(self, parent)
        self.config(bg='beige', padx=30)
        self.data = 42
        self.NglState = False

        self.pfd = pifacedigitalio.PiFaceDigital()
        self.listener=pifacedigitalio.InputEventListener(chip=self.pfd)

        self.relay1Label = MyLabel(self, 'Option Board Relay 1')
        self.relay2Label = MyLabel(self, 'Option Board Relay 2')
        self.relay3Label = MyLabel(self, 'Main Board Relay')
        self.relay4Label = MyLabel(self, 'Unused')

        self.labelcallbacks = [self.relay1Label.changevalue,
                          self.relay2Label.changevalue,
                          self.relay3Label.changevalue,
                          self.relay4Label.changevalue]



        for i in range(4):
            self.listener.register(i, pifacedigitalio.IODIR_ON, self.relay_closed)
            self.listener.register(i, pifacedigitalio.IODIR_OFF, self.relay_opened)
        self.listener.activate()

        self.labelfont = ('arial', 14, 'bold')
        self.bgColor = '#F6D153'
        self.fgColor = '#720C7e'

        self.titlebar = Label(self, text='---   Relay Monitor   ---')
        self.titlebar.pack(side=TOP, anchor="nw", padx=0, pady=0)
        self.titlebar.config(font=self.labelfont)
        self.titlebar.config(bg=self.bgColor, fg=self.fgColor)

        self.inputstate = Label(self, text='RELAY STATE')
        self.inputstate.pack(side=TOP, anchor="nw", padx=0, pady=10)
        self.inputstate.config(font=self.labelfont, width=20)
        self.inputstate.config(bg='white', fg=self.fgColor)

        # self.QuitButton = Button(self, text='Quit', command=self.quit)
        # self.QuitButton.pack(side=TOP, anchor="nw")


        self.relay1Label.pack(side=TOP, anchor="nw")
        self.relay2Label.pack(side=TOP, anchor="nw")
        self.relay3Label.pack(side=TOP, anchor="nw")
        self.relay4Label.pack(side=TOP, anchor="nw")

        self.labelcallbacks[3]('not used')

    def message(self):
        self.data += 1
        print('Hello frame world %s!' % self.data)


    def relay_closed(self, event):
        global powerupinprogress
        global NumberOfRelayTransitions
        global AlarmState
        event.chip.output_pins[event.pin_num].turn_on()
        self.inputstate.config(text='ON')
        print('relay_closed. pin = ' + repr(event.pin_num))
        self.labelcallbacks[event.pin_num]('Closed')
        AlarmState = True
        reportmsg('Alarm On detected. NGL power up must have been successful')

        # if not powerupinprogress:
        #     NumberOfRelayTransitions += 1
        # else:
        #     reportmsg('Power up in progress - relay transition discarded', 2)

    def relay_opened(self, event):
        global powerupinprogress
        global NumberOfRelayTransitions
        global AlarmState
        event.chip.output_pins[event.pin_num].turn_off()
        print('relay_opened. pin = ' + repr(event.pin_num))
        self.inputstate.config(text='OFF')
        self.labelcallbacks[event.pin_num]('Open')
        AlarmState = False
        # reportmsg('Alarm Off')


    def quit(self):
        global putimer
        global offtimer
        global recycletimer

        reportmsg('Got to go now', 1)
        self.listener.deactivate()
        for i in range(4):
            self.listener.deregister(i, pifacedigitalio.IODIR_ON)
            self.listener.deregister(i, pifacedigitalio.IODIR_OFF)
        # putimer.cancel()
        # offtimer.cancel()
        # waitforalarm.cancel()
        st.quit()
        sys.exit()

class NglControlsContainer(Frame):
    def __init__(self, parent=None):
        Frame.__init__(self, parent)
        self.pack(side=LEFT)

        self.makeWidgets()

    def makeWidgets(self):
        NglControls(self)  # .pack(side=TOP, fill=X)
        Button(self, text='Attach', command=self.quit).pack(side=TOP, fill=X)


class NglControlsExtender(NglControls):
    def make_widgets(self):  # override the make_widgets() function
        self.bgColor = 'green'
        NglControls.make_widgets(self)  # call the base class version
        Button(self, text='Extend', command=self.new_message).pack(side=LEFT, fill=X)  # and add a new button

    def message(self):
        print('This is the overriden button in NglControl class extender')

    def new_message(self):
        print('This is the new button in NglControl class extender')


def Menu_Quit():
    print('Menu exit selected')
    sys.exit()


def notdone():
    showerror('Not Implemented', 'Not yet available')


def makemenu(win):
    top = Menu(win)
    win.config(menu=top)

    file = Menu(top)
    file.add_command(label='New...', command=notdone, underline=0)
    file.add_command(label='Open...', command=notdone, underline=0)
    file.add_command(label='Quit', command=Menu_Quit, underline=0)
    top.add_cascade(label='File', menu=file, underline=0)

    edit = Menu(top, tearoff=False)
    edit.add_command(label='Cut', command=notdone, underline=0)
    edit.add_command(label='Paste', command=notdone, underline=0)
    edit.add_separator()
    top.add_cascade(label='Edit', menu=edit, underline=0)

    submenu = Menu(edit, tearoff=True)
    submenu.add_command(label='Spam', command=win.quit, underline=0)
    submenu.add_command(label='Eggs', command=notdone, underline=0)
    edit.add_cascade(label='Stuff', menu=submenu, underline=0)

def reportmsg(text='', level=2):
    global currentreportinglevel
    if level <= currentreportinglevel:
        print(text)
        st.inserttext(text + '\n')

if __name__ == '__main__':
    root = Tk()
    root.title('menu_win')
    root.config(bg='beige')
    makemenu(root)

    st = ScrolledTextClass(text='Start up\n')
    st.pack(side=RIGHT, expand=YES, fill=Y, anchor="ne")

    nglControl = NglControls(root)  # Hello class
    nglControl.pack(side=TOP, pady='10', anchor="w")

    nglMonitor = NglMonitor(root)  # Hello class
    nglMonitor.pack(side=TOP, pady='30', anchor="w")

    # putimer = PowerUpTimer()
    # recycletimer = RecycleTimer()
    # waitforalarm = WaitForAlarm()
    # offtimer = OffTimer()
    # delayBeforePowerDown = DelayBeforePowerDown()

    currentreportinglevel = 2


    if __name__ == '__main__': root.mainloop()
    #
    # sys.exit()

