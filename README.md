# commute
analyze traffic for possible commutes

## result
 ![commute_example](https://github.com/user-attachments/assets/f295e268-b9e5-4fb1-9394-05b8e7621dce)

## usage
* add mapbox token:
  * create a mapbox account: https://www.mapbox.com/
  * get access token: https://console.mapbox.com/account/access-tokens/
  * create token with access to directions api, or use default public token
  * create new file `mapbox_token.txt` containing token
* configure:
  * edit `config.json`
  * gps coordinates are formatted as `[LON, LAT]`
  * fill in work destination and possible starting positions
  * check if timezone and hours/days are correct
* install requirements:
  * `pip install -r requirements.txt`
* test program:
  * `./main.py --test`
* set up recurring run:
  * easiest is using cronjob, through `crontab -e`, add line:
    * `*/15 * * * * /usr/bin/python /home/USER/commute/main.py 2>> /home/USER/commute/out/err.log`
    * this will run the script every 15 minutes
* wait for a while to gather data
* analyze data using analyze script
  * `./analyze.py`
