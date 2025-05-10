# commute
analyze traffic for possible commutes

## usage
* add mapbox token:
  * create a mapbox account: https://www.mapbox.com/
  * create access token: https://console.mapbox.com/account/access-tokens/
  * create token with access to directions api, or use default public token
  * copy token to `mapbox_token.txt`
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
  * `./analyze.py
