# -*- coding: utf-8 -*-

from time import sleep
import sys
import random
import cloud4rpi
import rpi
import re
import subprocess
import traceback

############################### GSM ###########################################
from huawei_lte_api.Client import Client
from huawei_lte_api.AuthorizedConnection import AuthorizedConnection
from huawei_lte_api.Connection import Connection
router_url = 'http://admin:ROUTER_PASSWORD_HERE@192.168.0.254/'         # CHANGE ME

############################### ARLO ##########################################
import arlo # pip install arlo
ARLO_USERNAME = 'ARLO_USERNAME_HERE'
ARLO_PASSWORD = 'ARLO_PASSWORD_HERE'

import pywemo # https://github.com/pavoni/pywemo

try:
    arlo = arlo.Arlo(ARLO_USERNAME, ARLO_PASSWORD)
    arlo_basestation = arlo.GetDevices('basestation')
except Exception as e:
    print(e)

# Put your device token here. To get the token,
# sign up at https://cloud4rpi.io and create a device.
DEVICE_TOKEN = 'DEVICE_TOKEN_HERE'                                           # CHANGE ME
DATA_SENDING_INTERVAL = 600 # sec
DIAG_SENDING_INTERVAL = 600 # sec
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

wemo_devices = None

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
		_lastxfer = str(timestr[0][11:]).split('\\n')[0]            
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
	
################################## WEMO #########################################

def update_wemo():
	global wemo_devices
	wemo_devices = pywemo.discover_devices()
	
def wemo_online():
	global wemo_devices
	return len(wemo_devices)
	
def wemo_status():
	global wemo_devices
	return wemo_devices[0].get_state()

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

#################################### ARLO #######################################
def arlo_updatecamerasstate():
    global arlo_basestation
    global arlo    
    global arlo_cameras
    try:
        arlo_cameras = arlo.GetCameraState(arlo_basestation[0])
    except Exception as e:
        print(e)

def arlo_basestationstatus():
    global arlo_basestation
    global arlo
    try:
        base = arlo.GetBaseStationState(arlo_basestation[0])
        return base['properties']['connectivity'][0]['connected']
    except Exception as e:
        print(e)
        return 0

def arlo_camera_0_connectionstate():
    global arlo_cameras
    if(arlo_cameras['properties'][0]['connectionState'] == 'available'):
        return True
    else:
        return False

def arlo_camera_0_batterylevel():
    global arlo_cameras
    return arlo_cameras['properties'][0]['batteryLevel']

def arlo_camera_0_signalstrength():
    global arlo_cameras
    return arlo_cameras['properties'][0]['signalStrength']

def arlo_camera_1_connectionstate():
    global arlo_cameras
    if(arlo_cameras['properties'][1]['connectionState'] == 'available'):
        return True
    else:
        return False

def arlo_camera_1_batterylevel():
    global arlo_cameras
    return arlo_cameras['properties'][1]['batteryLevel']

def arlo_camera_1_signalstrength():
    global arlo_cameras
    return arlo_cameras['properties'][1]['signalStrength']

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

		##### WEMO ######
        'WEMO Online': {
            'type': 'numeric',
            'bind': wemo_online
        },
        'UPS State': {
            'type': 'bool',
            'bind': wemo_status
        },		

        ##### UPS ######
        'UPS Line Voltage': {
            'type': 'numeric',
            'bind': line_voltage
        },
        'UPS LoadPCT': {
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

        ####### ARLO ########
        'Arlo Base Station Status': {
            'type': 'bool',
            'bind': arlo_basestationstatus
        },

        'Arlo Camera 0 Status': {
            'type': 'bool',
            'bind': arlo_camera_0_connectionstate
        },
        'Arlo Camera 0 Battery Level': {
            'type': 'numeric',
            'bind': arlo_camera_0_batterylevel
        },
        'Arlo Camera 0 Signal Strength': {
            'type': 'numeric',
            'bind': arlo_camera_0_signalstrength
        },

        'Arlo Camera 1 Status': {
            'type': 'bool',
            'bind': arlo_camera_1_connectionstate
        },
        'Arlo Camera 1 Battery Level': {
            'type': 'numeric',
            'bind': arlo_camera_1_batterylevel
        },
        'Arlo Camera 1 Signal Strength': {
            'type': 'numeric',
            'bind': arlo_camera_1_signalstrength
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
                arlo_updatecamerasstate()
				update_wemo()
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
