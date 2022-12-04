from kivy.config import Config
Config.set('graphics', 'resizable', '0')
import kivy	
from kivy.core.window import Window
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivy.clock import mainthread, Clock
from kivy.factory import Factory
from functools import partial
from datetime import *
from csv import reader, writer
from ast import literal_eval
import pickle

Window.size = (800, 600)

tasks = [
]

notes = [
]

data = [tasks, notes]

username = ''
FORM_24H = '%H:%M'
FORM_12H = '%I:%M %p'
FORM_MDY = '%m/%d/%Y'
FORM_MLDY = '%B %d, %Y'
FORM_DMY = '%d/%m/%Y'
FORM_YMD = '%Y/%m/%d'
FORM_YDM = '%Y/%d/%m'
time_formats = {1:FORM_24H, 2:FORM_12H}
date_formats = {
	1:FORM_MDY,
	2:FORM_MLDY,
	3:FORM_DMY,
	4:FORM_YMD,
	5:FORM_YDM
}

user_name = 'New User'
time_pref = FORM_12H
date_pref = FORM_MDY
date_pref_ny = '%m/%d %I:%M %p'
date_pref_hint = 'MM/DD/YYYY'
time_pref_hint = 'HH/MM AM-PM'
res_setting = (800, 600)

C_TIME = datetime(1,1,1)

def load_settings():
	'''Reads the config.dat file and loads the user preferences
	contained within. If config.dat does not exist, does
	nothing.

	If invalid settings for time preference or date preference are
	loaded from config.dat, they will be reset to default values.

	The Resolution setting specifically is checked to ensure that
	the length of the user's setting is not excessively long. This
	is done to prevent uneccesary CPU load caused by calling the
	literal_eval() function to parse the setting back into a tuple.

	Typically one would not call literal_eval on a string generated
	by user input for safety reasons; this is simply a fringe case in
	which it is the most effecient way to recall the setting.'''
	global user_name, time_pref, date_pref, res_setting, date_pref_ny, date_pref_hint, time_pref_hint
	try:
		with open('config.dat', 'r') as file:
			csvreader = reader(file)
			for row in csvreader:
				if row[0] == 'Setting':
					pass
				elif row[0] == 'Date Setting':
					if row[1] not in ['%m/%d/%Y','%B %d, %Y','%d/%m/%Y','%Y/%m/%d','%Y/%d/%m']:
						date_pref = '%m/%d/%Y'
					else:
						date_pref = row[1]
				elif row[0] == 'Time Setting':
					if row[1] not in ['%H:%M','%I:%M %p']:
						time_pref = '%I:%M %p'
					else:
						time_pref = row[1]
				elif row[0] == 'Username':
					user_name = row[1]
				elif row[0] == 'Resolution':
					if len(row[1]) < 14:
						if type(literal_eval(row[1])) == tuple:
							Window.size = literal_eval(row[1])
						else:
							Window.size = (800, 600)
					else:
						Window.size = (800, 600)
				elif row[0] == 'Short Date Setting':
					date_pref_ny = row[1]
				elif row[0] == 'Date HInt':
					date_pref_hint = row[1]
				elif row[0] == 'Time Hint':
					time_pref_hint = row[1]
	except FileNotFoundError:
		return None

def save_events_list():
	global data, tasks, notes
	data = [tasks, notes]
	with open('userevents.dat', 'wb') as file:
		pickle.dump(data, file)

def load_events():
	global data, tasks, notes
	try:
		with open('userevents.dat', 'rb') as file:
			data = pickle.load(file)
			tasks = data[0]
			notes = data[1]
	except FileNotFoundError:
		pass

def sort_tasks():
	global tasks
	tasks.sort(key = lambda x: x['date'])

class AlignButton(Factory.Button):
	def on_size(self, _, size):
		self.text_size = size

class TopMenu(Widget):
	title = StringProperty('')
	description = StringProperty('')
	str_time = StringProperty(str(datetime.today().strftime(time_pref)))
	str_date = StringProperty(str(datetime.today().strftime(date_pref)))
	day = StringProperty(str(datetime.today().strftime('%A')))
	uname = StringProperty(user_name)
	uname_2 = user_name
	greet = StringProperty('')
	alert = StringProperty('TEST')
	refresh = False
	timer = 0

	def __init__(self, **kwargs):
		super(TopMenu, self).__init__(**kwargs)
		self.check_upcoming_tasks()


	def update(self, dt):

		if self.timer == 0:
			self.str_date = str(datetime.today().strftime(f'{date_pref}'))
			self.str_time = str(datetime.today().strftime(f'{time_pref}'))
			self.day = str(datetime.today().strftime('%A'))
			self.uname = user_name
			self.uname_2=user_name
			self.timer = 1
		if self.uname_2 != 'New User':
			if datetime.today().hour < 11:
				self.greet = f'Good morning, {self.uname_2}.'
			elif datetime.today().hour > 15:
				self.greet = f'Good evening, {self.uname_2}.'
			else:
				self.greet = f'Good day, {self.uname_2}.'
		else:
			self.greet = f'Greetings, new user! You can set what\nI call you in the \'Preferences\' menu.'
		self.check_upcoming_tasks()
		self.timer += 1
		if self.timer >5:
			self.timer = 0

	def clean_tasks(self):
		global tasks
		DeleteOldTasks.old_tasks = [t for t in tasks if t['date'].date() < datetime.today().date()]
		DeleteOldTasks.warning_msg = f'By pressing the "Delete" button below, all events scheduled for past dates will be deleted. This will delete {len(DeleteOldTasks.old_tasks)} events. Proceed?'
		pop = DeleteOldTasks()
		pop.open()

	def check_upcoming_tasks(self):
		global tasks
		new_alert = ''
		upcoming_tasks = []
		upcoming_tasks_d = []
		upcoming_tasks = [t for t in tasks if (t['date'].date() - datetime.today().date()) <= timedelta(7) and (t['date'].date() - datetime.today().date())>= timedelta()]
		if upcoming_tasks:
			if len(upcoming_tasks) == 1:
				new_alert += f'You have 1 event scheduled for the next seven days.\n\n'
			else:
				new_alert += f'You have {len(upcoming_tasks)} events scheduled for the next seven days.\n\n'
		upcoming_tasks_d = [t for t in tasks if (t['date'].date() - datetime.today().date()) == timedelta()]
		if upcoming_tasks_d:
			if len(upcoming_tasks_d) ==1:
				new_alert += f'You have 1 event scheduled for today.\n\n'
			else:
				new_alert += f'You have {len(upcoming_tasks_d)} events scheduled for today.\n\n'
		self.alert = new_alert


class DeleteOldTasks(Popup):
	old_tasks = []
	warning_msg = StringProperty('')

	def del_events(self):
		global tasks 
		tasks = [t for t in tasks if t not in self.old_tasks]
		TopMenu.refresh = True
		save_events_list()
		self.dismiss()

class EventCalendar(Popup):
	c_month = datetime.today().month
	c_year = datetime.today().year
	sel_date = StringProperty(str(datetime.strftime(datetime.today(), '%B %Y')))
	p_month = datetime.today().month
	p_year = datetime.today().year 
	day = 1
	def __init__(self, **kwargs):
		super(EventCalendar, self).__init__(**kwargs)
		self.add_dates()
		Clock.schedule_interval(self.update, 10.0/60.0)

	@mainthread
	def add_dates(self, *args):
		global tasks
		blanks = 0
		halt = False
		self.day = 1
		days = ['Sun','Mon','Tue','Wed','Thur','Fri','Sat']
		sort_tasks()
		self.ids.calendar_grid.clear_widgets()
		month_tasks = [t for t in tasks if t['date'].month == self.c_month]
		blanks = int(datetime.strftime(datetime(self.c_year, self.c_month, 1), '%w'))

		back_button = Button(text='Prev.', font_size=20)
		back_button.bind(on_release=self.back_month)
		self.ids.calendar_grid.add_widget(back_button)

		for x in range(5):
			label = Label(text='')
			self.ids.calendar_grid.add_widget(label)

		next_button = Button(text='Next', font_size=20)
		next_button.bind(on_release=self.forward_month)
		self.ids.calendar_grid.add_widget(next_button)

		for x in days:
			label = Label(text = x, font_size=20)
			self.ids.calendar_grid.add_widget(label)
		while blanks:
			filler = Label(text = '')
			self.ids.calendar_grid.add_widget(filler)
			blanks -= 1
		# while self.day < 32 and not halt:
		# 	try:
		# 		button = AlignButton(text=(' '+str(self.day)), halign='left', valign='top', font_size=20)
		# 		self.ids.calendar_grid.add_widget(button)
		# 		self.day += 1
		# 	except ValueError:
		# 		halt = True
		while True:
			try:
				datetime(2022, self.c_month, self.day)
			except ValueError:
				break
			button = AlignButton(text=(' '+str(self.day)), halign='left', valign='top', font_size=20)
			button.bind(on_release=partial(self.pressed, self.c_year, self.c_month, self.day))
			self.ids.calendar_grid.add_widget(button)
			self.day += 1

	def pressed(self, year, month, day, instance):
		DateEventView.date = datetime(year, month, day)
		DateEventView.str_date = str(datetime(year, month, day))
		pop = DateEventView()
		pop.open()

	def update(self, dt):
		if self.c_month != self.p_month or self.c_year != self.p_year:
			self.p_month = self.c_month 
			self.p_year = self.c_year
			self.date_string = str(self.c_month) + ' ' + str(self.c_year)
			self.sel_date = str(datetime.strftime(datetime.strptime(self.date_string, '%m %Y'), '%B %Y'))
			self.ids.calendar_grid.clear_widgets()
			self.add_dates()

	def when_closed(self):
		Clock.unschedule(self.update)

	def back_month(self, *args):	
		self.c_month -=1
		if self.c_month < 1:
			self.c_year -= 1
			self.c_month = 12
		if self.c_year < 1:
			self.c_year = 1
		elif self.c_year > 9999:
			self.year = 9999

	def forward_month(self, *args):
		self.c_month += 1
		if self.c_month > 12:
			self.c_month = 1 
			self.c_year += 1
		if self.c_year < 1:
			self.c_year = 1
		elif self.c_year > 9999:
			self.year = 9999

class DateEventView(Popup):
	date = datetime(1, 1, 1)
	str_date = str(datetime(1,1,1))

	def __init__(self, **kwargs):
		super(DateEventView, self).__init__(**kwargs)
		self.add_buttons()

	@mainthread
	def add_buttons(self, *args):
		global tasks
		sort_tasks()
		day_tasks = [t for t in tasks if t['date'].strftime('%m/%d/%Y') == self.date.strftime('%m/%d/%Y')]
		for i in day_tasks:
			button = Button(text=(i['date'].strftime(date_pref_ny) + ' ' + i['title']), font_size=25)
			button.bind(on_release=partial(self.pressed, i['title'], i['description'], i['date'].strftime(f'{(date_pref+" "+time_pref)}')))
			self.ids.daily_task_grid.add_widget(button)

	def pressed(self, t, d, w, instance):
		TaskDetails.t = t
		TaskDetails.d = d
		TaskDetails.w = w
		show_task_popup()




class TaskView(Popup):
	mon = datetime.today().month
	year = datetime.today().year
	sel_date = StringProperty(str(datetime.strftime(datetime.today(), '%B %Y')))
	p_mon = datetime.today().month 
	p_year = datetime.today().year
	def __init__(self, **kwargs):
		super(TaskView, self).__init__(**kwargs)
		self.add_buttons()
		Clock.schedule_interval(self.update, 10.0/60.0)
	
	@mainthread
	def add_buttons(self, *args):
		global tasks
		sort_tasks()
		month_tasks = [t for t in tasks if t['date'].month == self.mon and t['date'].year == self.year]
		for i in month_tasks:
			button = Button(text=(i['date'].strftime(date_pref_ny) + ' ' + i['title']), font_size=25)
			button.bind(on_release=partial(self.pressed, i['title'], i['description'], i['date'].strftime(f'{(date_pref+" "+time_pref)}')))
			self.ids.taskgrid.add_widget(button)

	def update(self, dt):
		if self.mon != self.p_mon or self.year != self.p_year:
			self.p_mon = self.mon
			self.p_year = self.year
			self.date_string = str(self.mon) + ' ' + str(self.year) 
			self.sel_date = str(datetime.strftime(datetime.strptime(self.date_string, '%m %Y'), '%B %Y'))
			self.ids.taskgrid.clear_widgets()
			self.add_buttons()

	def change_month(self, direction):
		if direction == '+':
			self.mon += 1
			if self.mon > 12:
				self.mon = 1
				self.year += 1
		else:
			self.mon -= 1
			if self.mon < 1:
				self.mon = 12
				self.year -= 1
		if self.year < 1:
			self.year = 1
		elif self.year > 9999:
			self.year = 9999

	def pressed(self, t, d, w, instance):
		TaskDetails.t = t
		TaskDetails.d = d
		TaskDetails.w = w
		show_task_popup()

	def when_closed(self):
		Clock.unschedule(self.update)

class TaskDetails(GridLayout):
	t = StringProperty('')
	d = StringProperty('')
	w = StringProperty('')


def show_task_popup():
	show = TaskDetails()
	taskwindow = Popup(title=TaskDetails.t, title_size = 20,title_align='center', content=show, size_hint=(0.8,0.8))
	taskwindow.open()

class NoteView(Popup):
	def __init__(self, **kwargs):
		super(NoteView, self).__init__(**kwargs)
		self.add_buttons()	
	
	@mainthread
	def add_buttons(self, *args):
		global notes
		for i in notes:
			button = Button(text=str(i['title']), font_size=25)
			button.bind(on_release=partial(self.pressed, i['title'], i['contents'] ))
			self.ids.notegrid.add_widget(button)

	def pressed(self, t, d, instance):
		NoteDetails.t = t
		NoteDetails.d = d
		show_note_popup()

class NoteDetails(GridLayout):
	t = StringProperty('')
	d = StringProperty('')


def show_note_popup():
	show = NoteDetails()
	notewindow = Popup(title=NoteDetails.t, title_size=20, title_align='center', content=show, size_hint=(0.8,0.8))
	notewindow.open()

class AddNoteWindow(Popup):
	titled = False
	described = False
	t = ''
	d = ''

	def process_text(self, field):
		if field == 'title':
			self.t = self.ids.title_input.text
			self.titled = True
		else:
			self.d = self.ids.description.text 
			self.described = True

	def save_note(self):
		if self.titled and self.described:
			notes.append({'title': self.t, 'contents': self.d})
			save_events_list()
			self.dismiss()

class DeleteNoteWindow(Popup):
	but_count = 0
	def __init__(self, **kwargs):
		super(DeleteNoteWindow, self).__init__(**kwargs)
		self.add_buttons()
		Clock.schedule_interval(self.update, 15.0/60.0)
	
	@mainthread
	def add_buttons(self, *args):
		global notes
		self.but_count = 0
		sort_tasks()
		for i in notes:
			button = Button(text=str(i['title']), font_size=25)
			button.bind(on_release=partial(self.pressed,
				i['title'],
				i['contents'],
				notes.index(i)))
			self.ids.notegrid.add_widget(button)
			self.but_count+=1

	def update(self, dt):
		global notes
		if self.but_count != len(notes):
			self.ids.notegrid.clear_widgets()
			self.add_buttons()

	def pressed(self, t, d, idx, instance):
		NoteRemove.t = t
		NoteRemove.d = d
		NoteRemove.ix = idx
		self.show_deletenote_popup()

	def show_deletenote_popup(self):
		show = NoteRemove()
		show.open()

	def when_closed(self):
		Clock.unschedule(self.update)


class NoteRemove(Popup):
	t = StringProperty('')
	d = StringProperty('')
	ix = None
	removed = False

	def delete_note(self):
		global notes
		try:
			notes.pop(self.ix)
			save_events_list()
			self.dismiss()
			DeleteNoteWindow.but_count -= 1
		except ValueError:
			pass
		except IndexError:
			pass


class AddEventWindow(Popup):
	valid_date = False
	valid_time = False
	titled = False
	described = False
	date_hint = StringProperty(date_pref_hint)
	time_hint = StringProperty(time_pref_hint)
	d = ''
	t = ''
	dt = ''
	tl = ''
	dsc = ''

	def __init__(self, **kwargs):
		global date_pref_hint, time_pref_hint
		super(AddEventWindow, self).__init__(**kwargs)
		self.date_hint = date_pref_hint
		self.time_hint = time_pref_hint
	
	def process_text(self, field):
		if field == 'title':
			self.tl = self.ids.title_input.text
			self.titled = True
		elif field == 'date':
			try:
				self.d = datetime.strptime(self.ids.date_input.text, date_pref)
				self.valid_date = True
			except ValueError:
				self.valid_date = False
		elif field == 'time':
			try:
				self.t = datetime.strptime(self.ids.time_input.text, time_pref)
				self.valid_time = True
			except ValueError:
				self.valid_time = False		
		elif field == 'details':
			self.dsc = self.ids.detail_input.text
			self.described = True

		if self.valid_date and self.valid_time:
			self.dt = self.ids.date_input.text+' '+self.ids.time_input.text
			tf = date_pref + ' ' + time_pref
			self.dt = datetime.strptime((self.ids.date_input.text+' '+self.ids.time_input.text), (date_pref + ' ' + time_pref))

	def save_event(self):
		if self.valid_date and self.valid_time and self.described and self.titled:
			tasks.append({'title': self.tl, 'date': self.dt, 'description': self.dsc})
			save_events_list()
			TopMenu.refresh = True
			self.dismiss()


class DeleteEventWindow(Popup):
	but_count = 0
	def __init__(self, **kwargs):
		super(DeleteEventWindow, self).__init__(**kwargs)
		self.add_buttons()
		Clock.schedule_interval(self.update, 15.0/60.0)	
	
	@mainthread
	def add_buttons(self, *args):
		global tasks
		self.but_count = 0
		for i in tasks:
			button = Button(text=str(i['title']), font_size=25)
			button.bind(on_release=partial(
				self.pressed,
				i['title'],
				i['description'],
				i['date'].strftime(f'{(date_pref+" "+time_pref)}'),
				tasks.index(i)))
			self.ids.taskgrid.add_widget(button)
			self.but_count += 1

	def update(self, dt):
		global tasks
		if self.but_count != len(tasks):
			self.ids.taskgrid.clear_widgets()
			self.add_buttons()

	def pressed(self, t, d, w, idx, instance):
		TaskRemove.t = t
		TaskRemove.d = d
		TaskRemove.w = w 
		TaskRemove.ix = idx
		show_delete_popup()

	def when_closed(self):
		Clock.unschedule(self.update)



class TaskRemove(Popup):
	t = StringProperty('')
	d = StringProperty('')
	w = StringProperty('')
	ix = None

	def delete_task(self):
		global tasks
		try:
			tasks.pop(self.ix)
			save_events_list()
			TopMenu.refresh = True	
			self.dismiss()
		except ValueError:
			pass
		except IndexError:
			pass
			

def show_delete_popup():
	show = TaskRemove()
	show.open()


	


class UserSettings(Popup):
	date = datetime.today()
	str_time = StringProperty(str(datetime.today().strftime(time_pref)))
	str_date = StringProperty(str(datetime.today().strftime(date_pref)))
	c_res = StringProperty(
		str(Window.size[0]) + 'x' + str(Window.size[1])
		)
	uname = StringProperty(user_name)

	def save_prefs(self):
		'''Saves user settings to the config.dat csv file.
		Parameters saved:
		"Date Preference"
		"Time Preference"
		"Username"
		"Resolution"'''
		global date_pref, time_pref, user_name, res_setting, date_pref_ny, date_pref_hint, time_pref_hint
		with open('config.dat', 'w', newline = '') as file:
			csvwriter = writer(file)
			csvwriter.writerow(['Setting', 'Value'])
			csvwriter.writerow(['Date Setting',date_pref])
			csvwriter.writerow(['Time Setting',time_pref])
			csvwriter.writerow(['Username',user_name])
			csvwriter.writerow(['Resolution',res_setting])
			csvwriter.writerow(['Short Date Setting', date_pref_ny])
			csvwriter.writerow(['Date Hint', date_pref_hint])
			csvwriter.writerow(['Time Hint', time_pref_hint])

	def change_date_prefs(self, new_date=None, new_date_ny=None, new_date_hint=None):
		global date_pref, time_pref, date_pref_ny, date_pref_hint
		date_pref = new_date
		date_pref_ny = new_date_ny + ' ' + time_pref + ':'
		date_pref_hint = new_date_hint

	def change_time_prefs(self, new_time=None, new_time_hint=None):
		global time_pref, time_pref_hint, date_pref, date_pref_ny
		time_pref = new_time
		time_pref_hint = new_time_hint
		date_pref_ny = date_pref[:5] + ' ' + time_pref + ':'

	def set_resolution(self, x, y):
		global res_setting
		Window.size = (x,y)
		res_setting = (x,y)
		self.c_res = str(x) + 'x' + str(y)

	def set_user_name(self, username):
		global user_name
		user_name = username
		self.uname = user_name

class Planbook(App):

	def build(self):
		load_settings()
		load_events()
		prog = TopMenu()
		Clock.schedule_interval(prog.update, 15.0/60.0)
		return prog

if __name__ == '__main__':
	Planbook().run()