#!/usr/bin/python3

import sys, re
import dateutil.parser
from dateutil.rrule import *
from itertools import chain
from datetime import *

default_dt = None
def parse_dt(date_str, default=None):
    if not default:
        default = default_dt
    return dateutil.parser.parse(date_str, default=default)
def set_default_date(new_default):
    global default_dt
    default_dt = parse_dt(new_default)

def parse_interval(interval_str):
    interval_start, interval_end = interval_str.split("/", maxsplit=1)
    interval_start = parse_dt(interval_start)
    interval_end = parse_dt(interval_end, default=interval_start)
    if interval_end < interval_start:
        raise ValueError("Interval \"{0}\" ends before its starting time.".format(interval_str))
    return interval_start, interval_end

period_regex = re.compile("PT((?P<hours>\d+)H)?((?P<minutes>\d+)M)?")
def parse_period(period_string):
    if not period_string:
        return timedelta(hours=0)
    if not period_string.endswith("H") and not period_string.endswith("M"):
        raise ValueError("Period must be of format PTxHxM")
    match = period_regex.match(period_string).groupdict()
    return timedelta(hours=int(match["hours"] or 0), minutes=int(match["minutes"] or 0))

working_schedules = []
first_work_day = datetime.max
last_work_day = datetime.min
def schedule(amount, valid=None, byweekday="MO,TU,WE,TH,FR"):
    if not valid:
        raise ValueError("No \"valid\" parameter for planned working time.")
    amount = parse_period(amount)
    valid_from, valid_to = parse_interval(valid)
    byweekday = [getattr(dateutil.rrule, weekday) for weekday in byweekday.split(",")]

    global first_work_day, last_work_day
    first_work_day, last_work_day = min(first_work_day, valid_from), max(last_work_day, valid_to)
    rr = rrule(DAILY, dtstart=valid_from, until=valid_to, byweekday=byweekday)
    working_schedules.append((amount, rr))
def work_days():
    for amount, rr in working_schedules:
        for working_day in rr:
            yield working_day, amount

holiday_rrules = []
def holiday(date, byeaster=None):
    if not date:
        #Easter calculation does not work backwards, maybe bug in dateutil?
        #Set start date to some date in the past
        date = parse_dt("2018-01-01")
    else:
        date = parse_dt(date)
    if byeaster != None:
        byeaster = int(byeaster)
    
    rr = rrule(YEARLY, date, byeaster=byeaster)
    holiday_rrules.append(rr)
def is_holiday(day):
    return any(map(
        lambda rr: len(rr.between(day, day, inc=True)) > 0,
        holiday_rrules
    ))

vacations = []
def vacation(span):
    vacations.append(parse_interval(span))
def is_vacation(day):
    return any(map(
        lambda vacation: day >= vacation[0] and day <= vacation[1],
        vacations
    ))

work_times = []
def work(span, lunch=None):
    work_start, work_end = parse_interval(span)
    lunch = parse_period(lunch)

    work_times.append((work_start, work_end, lunch))

def process_command(line, linenumber):
    #ignore comments and empty lines
    line = line.split("#", maxsplit=1)[0].strip()
    if not line:
        return
    
    #parse commands and call their functions
    parts = line.split(" ")
    command = parts[0]
    main_parameter = None
    other_parameters = {}
    for part in parts[1:]:
        if "=" in part:
            key, value = part.split("=", maxsplit=1)
            other_parameters[key] = value
        else:
            main_parameter = part
    
    command_func_map = {
        "for": set_default_date,
        "schedule": schedule,
        "holiday": holiday,
        "vacation": vacation,
        "sick": vacation,
        "work": work,
        "dt": lambda x: print(parse_dt(x))
    }
    if command not in command_func_map:
        print("WARNING: On line {0}: Unknown command \"{1}\".".format(linenumber, command), file=sys.stderr)
        return
    command_func_map[command](main_parameter, **other_parameters)

def format_timedelta(td):
    sign = ""
    total_minutes, seconds = divmod(int(td.total_seconds()), 60)
    if total_minutes < 0:
        sign = "-"
        total_minutes = abs(total_minutes)
    total_hours, minutes = divmod(total_minutes, 60)
    return "{0}{1:0>2}:{2:0>2}".format(sign, total_hours, minutes)

if __name__=="__main__":
    input_files = ([open(f) for f in sys.argv[1:]] or [sys.stdin]) #read from stdin if no files given
    for linenumber, line in enumerate(chain(*input_files), 1):
        try:
            process_command(line, linenumber)
        except Exception as e:
            print("ERROR: On line {0}: {1}".format(linenumber, str(e)), file=sys.stderr)
            print("Offending line was: \"{0}\"".format(line[:-1]), file=sys.stderr)
            sys.exit(1)
    
    if len(working_schedules) == 0:
        print("ERROR: No work schedule given")
        sys.exit(1)

    all_days = rrule(DAILY, first_work_day, until=last_work_day)
    day_scheduled_map = {}
    day_worked_map = {}
    for day in all_days:
        day = day.date()
        day_scheduled_map[day] = timedelta(hours=0)
        day_worked_map[day] = timedelta(hours=0)
    
    #calculate scheduled time
    total_scheduled = timedelta(hours=0)
    for day, scheduled_time in work_days():
        if (is_holiday(day) or is_vacation(day)):
            continue

        day_scheduled_map[day.date()] += scheduled_time
        total_scheduled += scheduled_time
    
    #calculate worked time
    total_worked = timedelta(hours=0)
    out_of_schedule_worked = timedelta(hours=0)
    for work_start, work_end, lunch in work_times:
        day = work_start.date()
        worked_time = (work_end - work_start) - lunch
        if work_start < first_work_day or last_work_day < work_start:
            out_of_schedule_worked += worked_time
        else:
            day_worked_map[day] += worked_time
        total_worked += worked_time
    
    #print scheduled, worked time and difference by day
    try:
        diff = timedelta(hours=0)
        for day in all_days:
            day = day.date()
            scheduled = day_scheduled_map[day]
            worked = day_worked_map[day]
            diff += worked - scheduled
            print("{0}: SOLL {1} IST {2} AKT {3}".format(
                day,
                format_timedelta(scheduled),
                format_timedelta(worked),
                format_timedelta(diff)
            ))

        if out_of_schedule_worked.total_seconds() > 0:
            print("OUT OF SCHEDULE TIME: {0}".format(
                format_timedelta(out_of_schedule_worked)
            ))
            diff += out_of_schedule_worked
        
        #print totals
        print("TOTAL: SOLL {0} IST {1} AKT {2}".format(
            format_timedelta(total_scheduled),
            format_timedelta(total_worked),
            format_timedelta(diff)
        ))
    except IOError:
        pass
