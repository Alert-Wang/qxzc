## qxzc

### Introduction

A network crawler from https://www.sge.com.cn

there 2 runner in this project:
- meta: for crawling the relatioship between date and url.
- main: from downloading the data from the specific url in meta.

init/hist/live mode share same cmd, and recovery mode would need -f in some time as ypu need.

DELAY=1 Day

### Setup
python3.6+  
for python dependency run `pip install -r requirements.txt`

### Operation

the program will store the meta data into csv first
then the main worker read the meta data, select the dates from user end input
the main worker will download the final data on the page.

worker.py is your entry points   
use `python worker.py -h` to get more help.

**init/live**   
only meta worker: `python worker.py -r meta`  
only main worker: `python worker.py -r main`   or `python worker.py -r main -s 20220101 -e 20220120`  
all worker: `python worker.py [-f] [-s START_DATE] [-e END_DATE] [-r RUNNER]`   

note:
1. -s/-e only work in main runner.
2. -f only work in meta runner.
3. when you not specify -r, the above -f, -s/-e working scope still be avalible.
4. the python program should be run under qxzc folder.
5. worker.py is the only entry piont.

**recovery**  
same cmd with above, better sepcify -s/-e.
should add `-f` option when you operate. it will scan on all of the pages, and save the data
into meta if there any missing.

