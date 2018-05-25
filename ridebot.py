import re
import shelve

from astropy import units as u
from astropy import time

driving_to = re.compile('driving to (rotunda|muller)(?: in)?(.*)')
need_ride = re.compile('need ride to (rotunda|muller)(?: in)?(.*)')

shelf = shelve.open('ridebot.shelf')  # NEVER DO THIS.  should not use global variables to store db-like objects
shelf = {} # HACKHACK!

DEFAULT_TIMESPAN = 15*u.min

def parse_time(time_str):
    try:
        when_time = time.Time(time_str)
    except:
        try:
            dt = u.Quantity(time_str)
            when_time = time.Time.now() + dt
        except:
            raise
    return when_time

def message_from_main_channel(msg, username):
    """
    Inputs: `msg` is the message from the main ridesharing channel,
    `username` is the name of the user that sent the message

    Returns: A message the bot should respond with, *or* if None, don't send a message
    """
    msg = msg.lower()
    message_to_respond_with = None

    drive = driving_to.match(msg)
    if drive:
        which_building = drive.group(1)
        when_str = drive.group(2)

        try:
            when_time = parse_time(when_str)
        except:
            raise
            when_time = None
            message_to_respond_with = "Sorry, I didn't understand the timeframe " + when_str

        if when_time is not None:
            send_to_calendar(username, which_building, when_time, DEFAULT_TIMESPAN)
            message_to_respond_with = 'OK {}, thanks for signing up! :kittens-rideshare:'.format(username)

    else:
        need = need_ride.match(msg)
        if need:
            which_building = need.group(1)
            when_str = need.group(2)
            matched_user = check_if_in_calendar(which_building, parse_time(when_str))
            if matched_user is None:

                message_to_respond_with = ('I\'m afraid I can\'t do that, Dave/{}. '
                                           'You\'ll have to walk.  But on the '
                                           'plus side, our insurance premiums '
                                           'will all go down!'.format(username))
            else:
                message_to_respond_with = ('No problem {}, {} is also going '
                                           'there'.format(username, matched_user))

    return message_to_respond_with

def send_to_calendar(username, destination, leave_time, timespan):
    if destination not in shelf:
        shelf[destination] = []
    shelf[destination].append((leave_time, timespan, username))

def check_if_in_calendar(destination, leave_time):
    matched_user = None
    if destination in shelf:
        for cal_leave_time, timespan, cal_username in shelf[destination]:
            dtime = (cal_leave_time - leave_time)
            if (dtime.jd > 0) and (dtime < timespan):
                matched_user = cal_username
    return matched_user
