# arbeitszeit.py
Keep track of your working hours the UNIX way - using plain text files.
Date and time period format is [ISO8601](https://en.wikipedia.org/wiki/ISO8601).

## Requirements
The [dateutil](https://github.com/dateutil/dateutil) module: `pacman -S python-dateutil`.

## Invocation
```
./arbeitszeit.py [inputfile1 inputfile2...]
```
If no input files are given, stdin is read.

## Example
```python
# /tmp/example
# Define working schedule
for 2019 #if no year is given assume 2019
#employment started on 2019-01-14
#4 hours on workdays (MO-FR)
schedule PT4H valid=--01-14/--03-31
#on April 1st working hours were reduced to 3 hours from MO to TH
schedule PT3H valid=--04-01/2021-01-31 byweekday=MO,TU,WE,TH

for 2019-01
work 14T09:00/12:15 #on 2019-01-14 we worked from 09:00 to 12:15
work 14T13:15/13:55 #and from 13:15 to 13:55
work 15T09:00/11:50
work 16T09:00/11:50
work 17T10:20/11:45
work 21T11:25/11:45
work 22T09:00/09:30
work 22T10:00/11:50
work 23T11:30/11:55
#let's take a 30 minute lunch break
work 24T12:30/14:00 lunch=PT30M
work 28T09:10/09:25
work 29T10:00/10:50
work 30T10:00/11:45
work 30T14:50/15:45
work 31T09:50/13:55
```
Calling `arbeitszeit.py` on this input file will output one line for each day of our employment
keeping track of how much work was scheduled for this day (`SOLL`), how much work was actually done (`IST`)
and the running total of the difference (`AKT`).
```bash
$ ./arbeitszeit.py /tmp/example | grep 2019-01
2019-01-14: SOLL 04:00 IST 03:55 AKT -00:05
2019-01-15: SOLL 04:00 IST 02:50 AKT -01:15
2019-01-16: SOLL 04:00 IST 02:50 AKT -02:25
2019-01-17: SOLL 04:00 IST 01:25 AKT -05:00
2019-01-18: SOLL 04:00 IST 00:00 AKT -09:00
2019-01-19: SOLL 00:00 IST 00:00 AKT -09:00
2019-01-20: SOLL 00:00 IST 00:00 AKT -09:00
2019-01-21: SOLL 04:00 IST 00:20 AKT -12:40
```
Seems like we are not hitting our target hours. Ouch.

## Input syntax reference
### `for <date>`
For all following commands: If a date string without year, month, ... is encountered, fill in the omitted values from `date`.
### `schedule <period> valid=<interval> [byweekday=MO,TU,WE,TH,FR]`
Use to specify your working hours.
Work for `period` amount of time on weekdays given by `byweekday` (Default: Monday to Friday).
You must specify the start and end date of this schedule.
`arbeitszeit.py` will output one line per day starting from the earliest start day of all validity intervals
and ending with the latest end date. At least one `schedule` line must be present.

### `holiday <date|byeaster=n>`
Use to specify yearly public holidays. No working hours will be scheduled for holidays.
If the date is dependent on Easter use `byeaster=n` with `n` being the offset from Easter Sunday in days.
The national holidays of Austria can be found in the file `holidays-at`. Remember to include this file in your input files or paste into your input file.
Pull requests for other countries are welcome.
* `holiday --05-01 #Staatsfeiertag`
* `holiday byeaster=50 #Monday after Pentecost`

### `vacation <interval>` or `sick <interval>`
When you take off work. No working hours will be scheduled for the days in `interval`.
* `vacation 08-08/08-14`
* `vacation 2020-06-16/2020-07-09`

### `work <interval> [lunch=period]`
Records working hours. The time period given in `lunch` will be subtracted.
Use with `for` to avoid repeating the year and month in each line.
**Note:** If the end time is not on the same date as the start time (you work around midnight) you must include the new date.
* `work 22T06:10/11:35`
* `work 09T21:00/10T00:30`
* `work 2019-01-24T07:30/17:00 lunch=PT1H30M`
