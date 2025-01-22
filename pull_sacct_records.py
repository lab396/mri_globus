#!/usr/bin/env python
# coding: utf-8

# Python script to pull the prior month's SLURM accounting
# records using sacct. The resulting file can be imported into
# Excel for analysis
#
# J Nucciarone, 10/2024, RC 1

from datetime import date
import datetime
from calendar import monthrange

import subprocess
import os
import sys

def check_installation(rv):
    current_version = sys.version_info
    if current_version[0] == rv[0] and current_version[1] >= rv[1]:
        pass
    else:
        sys.stderr.write( "[%s] - Error: Your Python interpreter must be %d.%d or greater (within major version %d)\n" % (sys.argv[0], rv[0], rv[1], rv[0]) )
        sys.exit(-1)
    return 0

# Calling the 'check_installation' function checks if Python3 is >= 3.10, as str | None syntax is only supported in 3.10 or later.

required_version = (3,10)
check_installation(required_version)

# This is a bit of a silly function, as the start of the month is always the 1st.
def beginning_of_month(today: date | None = None) -> date:
    today = today or date.today()
    return date(today.year, today.month, 1)

def end_of_month(today: date | None = None) -> date:
    today = today or date.today()
    (_, num_days_in_month) = monthrange(today.year, today.month)
    return date(today.year, today.month, num_days_in_month)


# Print starting banner

print(f"--------\n{sys.argv[0]} execution starting at {datetime.datetime.now()}.\n\n")

# Get the CWD
my_cwd = os.getcwd()
#print(f"My current directory is {my_cwd}")


# Obtain the account name, and verify it exists

account = "pches"

sacctmgr_command_string = f"sacctmgr -n -P   show account {account}  format=account%30 | grep ^{account} > /dev/null"

#print(f"Command string is {sacctmgr_command_string}.\n")

result = subprocess.run([f"{sacctmgr_command_string}"], shell=True, capture_output=True, text=True)
sacctmgr_command_result_code = result.returncode

if sacctmgr_command_result_code != 0:
    sys.stderr.write(f"Error: Account {account} does not exist.\n")
    print(result.stderror)
    sys.exit(-1)
else:
    print(f"Account records will be obtained for account \"{account}\".\n")


# Obtain today's date

today_date = date.today()

my_year = today_date.year
my_month = today_date.month
my_day = today_date.day

# For testing we are going to fake a date. Uncomment these fields to set the fake date.

#my_year = int(2024)
#my_month = int(1)
#my_day = int(13)
#today_date = datetime.date(my_year, my_month, my_day)

print(f"Today's date is {today_date}.\n")


# We will use today's date to calculate the prior month and year

if my_month == 1:
    my_last_month = 12
    my_last_months_year = my_year - 1
else:
    my_last_month = my_month - 1
    my_last_months_year = my_year

print(f"Running accounting records for  {int(my_last_month)} / {int(my_last_months_year)}\n")

# As we are looking to what last month is, the day variable isn't important. Set it to 1.

date_last = datetime.date(my_last_months_year, my_last_month, 1)


# Calculate the start and end dates of last month

start_day = beginning_of_month(date_last).day
end_day = end_of_month(date_last).day
#print(f"Starting day for month {int(date_last.month)} is {int(start_day)} and the ending day is {int(end_day)}\n")


# Create strings for the start and end date of the accounting period. Base the output file name on these dates. 
# The date format requires the month be two digits, so append the leading 0 in months < October.

if my_last_month >= 10:
    start_date_str = f"{int(my_last_months_year)}-{int(my_last_month)}-{int(start_day)}"
    end_date_str = f"{int(my_last_months_year)}-{int(my_last_month)}-{int(end_day)}"
else:
    start_date_str = f"{int(my_last_months_year)}-0{int(my_last_month)}-{int(start_day)}"
    end_date_str = f"{int(my_last_months_year)}-0{int(my_last_month)}-{int(end_day)}"
    
# print(f"Start date string {start_date_str}\nEnd date string {end_date_str}\n")

output_file = f"{my_cwd}/pches_usage_{start_date_str}_{end_date_str}.csv"
print(f"sacct records will be written to file {output_file}")


# Build the sacct command string, pipe it through awk to eliminate lines where the user field is blank
    
sacct_command_string = f"`which sacct` --allusers --starttime {start_date_str} --endtime {end_date_str} --account {account} --format=User,Account,JobID,Jobname,partition,state,time,start,end,elapsed,MaxRss,MaxVMSize,nnodes,ncpus,nodelist -P --delimiter ',' | awk -F\, '$1~/\w/' >& {output_file}"

#print(f"My command string is \"{sacct_command_string}\"\n")


# Execute the sacct command

result = subprocess.run([f"{sacct_command_string}"], shell=True, capture_output=True, text=True)
command_result_code = result.returncode

if command_result_code != 0:
    print(f"Error encountered running {sacct_command_string}\n\n")
    print(result.stderror)
else:
    print(result.stdout)
    num_lines = sum(1 for _ in open(output_file))
    print(f"{num_lines - 1} records written to file {output_file}.\n")

print(f"{sys.argv[0]} execution completed at {datetime.datetime.now()}.\n--------\n")
