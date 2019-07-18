# -*- coding: utf-8 -*-

from time import sleep
import sys
import random
import cloud4rpi
import rpi
import re
import subprocess
import traceback
from huawei_lte_api.Client import Client
from huawei_lte_api.AuthorizedConnection import AuthorizedConnection
from huawei_lte_api.Connection import Connection

router_url = 'http://admin:password@192.168.0.254/'         # CHANGE ME

# Put your device token here. To get the token,
# sign up at https://cloud4rpi.io and create a device.
DEVICE_TOKEN = ''                                           # CHANGE ME
DATA_SENDING_INTERVAL = 30 # sec
DIAG_SENDING_INTERVAL = 60 # sec
POLL_INTERVAL = 0.5 # sec

connection = AuthorizedConnection(router_url)
client = Client(connection)

_gsm_band = 0
_gsm_mode = ''
_gsm_rssi = 0
_gsm_rsrq = 0 
_gsm_rsrp = 0
_gsm_signal = 0
_gsm_reading_status = 'KO'

_loadpct = 0
_line_voltage = 0
_xonbatt = ""
_xoffbatt = ""
_lastxfer = ""

################################## NET #########################################

def network_latency():
	try:
		p = subprocess.Popen(["ping","-c1","8.8.8.8"], stdout = subprocess.PIPE)
		timestr = re.compile("time=[0-9]+\.[0-9]+").findall(str(p.communicate()[0]))
		network_latency = float(timestr[0][5:])
	except:
        print(traceback.format_exc())
		network_latency = 0.0
	return network_latency

def localnet_latency():
    try:
        p = subprocess.Popen(["ping","-c1","192.168.0.254"], stdout = subprocess.PIPE)
        timestr = re.compile("time=[0-9]+\.[0-9]+").findall(str(p.communicate()[0]))
        localnet_latency = float(timestr[0][5:])
    except:
        print(traceback.format_exc())
        localnet_latency = 0.0
    return localnet_latency

def hosts_up():
	try:
		p = subprocess.Popen(["nmap","-sP","192.168.0.1/24"], stdout = subprocess.PIPE)
		timestr = re.compile("\([0-9]+ hosts up").findall(str(p.communicate()[0]))
		hosts = int(timestr[0][1:].split(' ')[0])
	except:
        print(traceback.format_exc())
		hosts = 0
	return hosts

################################## UPS #########################################

def apcaccess():
	global _loadpct
	global _line_voltage
	global _xonbatt
	global _xoffbatt
    global _lastxfer

	try:
        	p = subprocess.Popen(["apcaccess"], stdout = subprocess.PIPE)
        	out = p.communicate()[0]
        	timestr = re.compile("LINEV    : [0-9]+\.[0-9]+ Volts").findall(str(out))
        	_line_voltage = float(timestr[0][11:].split(' ')[0])
        	timestr = re.compile("LOADPCT  : [0-9]+\.[0-9]+ Percent").findall(str(out))
        	_loadpct = float(timestr[0][11:].split(' ')[0])
        	timestr = re.compile("XONBATT  : .+").findall(str(out))
        	_xonbatt = str(timestr[0][11:]).split('+0000')[0]
        	timestr = re.compile("XOFFBATT : .+").findall(str(out))
        	_xoffbatt = str(timestr[0][11:]).split('+0000')[0]
            timestr = re.compile("LASTXFER : .+").findall(str(out))
            _lastxfer = str(timestr[0][11:]).split('+0000')[0]            
	except:
		print(traceback.format_exc())
		_loadpct = 0
		_line_voltage = 0
		_xonbatt = ""
		_xoffbatt = ""
        _lastxfer = ""     

def line_voltage():
	return _line_voltage

def loadpct():
    return _loadpct

def xonbatt():
    return _xonbatt

def xoffbatt():
    return _xoffbatt

def lastxfer():
    return _lastxfer

################################## GSM #########################################

def update_gsm():
	global _gsm_band
	global _gsm_mode
	global _gsm_rssi
	global _gsm_rsrq
	global _gsm_rsrp
	global _gsm_signal
	global client
	global connection
    global _gsm_reading_status

	try:
		signal = client.device.signal()
		info = client.device.information()
		status = client.monitoring.status()
		_gsm_mode = info['workmode']
		_gsm_band = int(signal['band'])
		_gsm_rssi = int(signal['rssi'].split('dBm')[0])
		_gsm_rsrq = int(signal['rsrq'].split('dB')[0])
		_gsm_rsrp = int(signal['rsrp'].split('dBm')[0])
		_gsm_signal = int(status['SignalIcon'])
        _gsm_reading_status = 'OK'
	except:
		print(traceback.format_exc())
        _gsm_reading_status = 'KO'
		connection = AuthorizedConnection(router_url)
		client = Client(connection)

def gsm_band():
    return _gsm_band

def gsm_mode():
    return _gsm_mode

def gsm_rssi():
    return _gsm_rssi

def gsm_rsrq():
    return _gsm_rsrq

def gsm_rsrp():
    return _gsm_rsrp

def gsm_signal():
    return _gsm_signal

def gsm_status():
    return _gsm_reading_status

#################################################################################

def main():

    # Put variable declarations here
    # Available types: 'bool', 'numeric', 'string'
    variables = {

        ##### RASP PI ######
        'CPU Temp': {
            'type': 'numeric',
            'bind': rpi.cpu_temp
        },

        ##### NETWORK ######
        'Network Latency': {
            'type': 'numeric',
            'bind': network_latency
        },
        'Localnet Latency': {
            'type': 'numeric',
            'bind': localnet_latency
        },        
        'Hosts Up': {
            'type': 'numeric',
            'bind': hosts_up
        },

        ##### UPS ######
        'Line Voltage': {
            'type': 'numeric',
            'bind': line_voltage
        },
        'LoadPCT': {
            'type': 'numeric',
            'bind': loadpct
        },        
        'UPS Last On Battery': {
            'type': 'string',
            'bind': xonbatt
        },        
        'UPS Last Off Battery': {
            'type': 'string',
            'bind': xoffbatt
        },
        'UPS Last Transfer': {
            'type': 'string',
            'bind': lastxfer
        },

        ##### 4G ROUTER ######
        'GSM Rssi': {
            'type': 'numeric',
            'bind': gsm_rssi
        },
        'GSM Rsrq': {
            'type': 'numeric',
            'bind': gsm_rsrq
        },
        'GSM Rsrp': {
            'type': 'numeric',
            'bind': gsm_rsrp
        },
        'GSM Band': {
            'type': 'numeric',
            'bind': gsm_band
        },
        'GSM Signal': {
            'type': 'numeric',
            'bind': gsm_signal
        },
        'GSM Mode': {
            'type': 'string',
            'bind': gsm_mode
        },
        'GSM Status': {
            'type': 'string',
            'bind': gsm_status
        },        
    }

    diagnostics = {
        'IP Address': rpi.ip_address,
        'Host': rpi.host_name,
        'Operating System': rpi.os_name,
    }

    tls = {
        'ca_certs': '/etc/ssl/certs/ca-certificates.crt'
    }
    device = cloud4rpi.connect(DEVICE_TOKEN, tls_config=tls)

    try:
        device.declare(variables)
        device.declare_diag(diagnostics)

        device.publish_config()

        # Adds a 1 second delay to ensure device variables are created
        sleep(1)

        data_timer = 0
        diag_timer = 0

        while True:
            if data_timer <= 0:
                update_gsm()
                apcaccess()
                device.publish_data()
                data_timer = DATA_SENDING_INTERVAL

            if diag_timer <= 0:
                device.publish_diag()
                diag_timer = DIAG_SENDING_INTERVAL

            sleep(POLL_INTERVAL)
            diag_timer -= POLL_INTERVAL
            data_timer -= POLL_INTERVAL

    except KeyboardInterrupt:
        cloud4rpi.log.info('Keyboard interrupt received. Stopping...')

    except Exception as e:
        error = cloud4rpi.get_error_message(e)
        cloud4rpi.log.exception("ERROR! %s %s", error, sys.exc_info()[0])

    finally:
        sys.exit(0)


if __name__ == '__main__':
    main()
