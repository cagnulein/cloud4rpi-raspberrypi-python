# -*- coding: utf-8 -*-

from time import sleep
import sys
import random
import cloud4rpi
import rpi
import re
import subprocess

# Put your device token here. To get the token,
# sign up at https://cloud4rpi.io and create a device.
DEVICE_TOKEN = ''
DATA_SENDING_INTERVAL = 30 # sec
DIAG_SENDING_INTERVAL = 60 # sec
POLL_INTERVAL = 0.5 # sec

_gsm_band = 0
_gsm_mode = ''
_gsm_rssi = 0
_gsm_rsrq = 0 
_gsm_rsrp = 0
_gsm_signal = 0

_loadpct = 0
_line_voltage = 0
_xonbatt = ""
_xoffbatt = ""

################################## NET #########################################

def network_latency():
	try:
		p = subprocess.Popen(["ping","-c1","8.8.8.8"], stdout = subprocess.PIPE)
		timestr = re.compile("time=[0-9]+\.[0-9]+").findall(str(p.communicate()[0]))
		network_latency = float(timestr[0][5:])
	except:
		network_latency = 0.0
	return network_latency

def hosts_up():
	try:
		p = subprocess.Popen(["nmap","-sP","172.31.53.1/24"], stdout = subprocess.PIPE)
		timestr = re.compile("\([0-9]+ hosts up").findall(str(p.communicate()[0]))
		hosts = int(timestr[0][1:].split(' ')[0])
	except:
		hosts = 0
	return hosts

################################## UPS #########################################

def apcaccess():
    try:
        p = subprocess.Popen(["apcaccess"], stdout = subprocess.PIPE)
        out = p.communicate()[0]
        timestr = re.compile("LINEV    : [0-9]+\.[0-9]+ Volts").findall(str(out))
        _line_voltage = float(timestr[0][11:].split(' ')[0])
        timestr = re.compile("LOADPCT  : [0-9]+\.[0-9]+ Percent").findall(str(p.communicate()[0]))
        _loadpct = float(timestr[0][11:].split(' ')[0])
        timestr = re.compile("XONBATT  : .+").findall(str(p.communicate()[0]))
        _xonbatt = str(timestr[0][11:])        
        timestr = re.compile("XOFFBATT : .+").findall(str(p.communicate()[0]))
        _xoffbatt = str(timestr[0][11:])        
    except:
        _loadpct = 0
        _line_voltage = 0
        _xonbatt = ""
        _xoffbatt = ""        
    return volts

def line_voltage():
	return _line_voltage

def loadpct():
    return _loadpct

def xonbatt():
    return _xonbatt

def xoffbatt():
    return _xoffbatt

################################## GSM #########################################

def update_gsm():
	try:
		p = subprocess.Popen(["python3", "router.py"], stdout = subprocess.PIPE)
		out = p.communicate()[0]
		timestr = re.compile("Rssi: \-[0-9]+dBm").findall(str(out))
		_gsm_rssi = int(timestr[0][6:].split('dBm')[0])
		timestr = re.compile("Rsrq: \-[0-9]+dBm").findall(str(out))
		_gsm_rsrq = int(timestr[0][6:].split('dBm')[0])
		timestr = re.compile("Rsrp: \-[0-9]+dBm").findall(str(out))
		_gsm_rsrp = int(timestr[0][6:].split('dBm')[0])
		timestr = re.compile("Mode:.+").findall(str(out))
		_gsm_mode = str(timestr[0][6:])
		timestr = re.compile("Band: [0-9]+").findall(str(out))
		_gsm_band = int(timestr[0][6:])
		timestr = re.compile("Signal: [0-9]").findall(str(out))
		_gsm_signal = int(timestr[0][8:])		
	except:
		_gsm_band = 0
		_gsm_mode = ''
		_gsm_rssi = 0
		_gsm_rsrq = 0 
		_gsm_rsrp = 0
		_gsm_signal = 0

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
    }

    diagnostics = {
        'IP Address': rpi.ip_address,
        'Host': rpi.host_name,
        'Operating System': rpi.os_name,
        'UPS Last On Battery': xonbatt,
        'UPS Last Off Battery': xoffbatt,
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
