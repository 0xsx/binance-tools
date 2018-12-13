Binance Trading Tools
=====================

Work-in-progress Python tools for collecting trading data and simulating
trade predictions with the Binance API.

### Requirements

* Python 2 or 3
* NumPy
* Tornado server
* PycURL
* A Binance account and API key
* npm
* gulp


### License
GPLv3.


### Usage

#### 1. Download the source repository.

#### 2. Build the UI.

    cd ui/
    npm install
    gulp build



#### 3. Configure the software.

Edit `config.json` and add a Binance API key and secret key, then update the
save pairs and data directory. Make sure the ui host IP and port are set.
There is currently no form of authentication to connect to the UI server.

#### 4. Run the trading bot to collect data.

Currently this doesn't do any sort of trading. It will record and save
trading data for all of the save pairs specified in the config file as gzip
compressed text.

#### 5. Run the simulator.

For arguments run the simulator with the `-h` flag.
Choose the session by the starting timestamp saved in the data directory.
The model pair is currently unused, and the simulator doesn't currently
predict anything.


