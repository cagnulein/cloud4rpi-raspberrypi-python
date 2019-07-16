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

def line_voltage():
	try:
		p = subprocess.Popen(["apcaccess"], stdout = subprocess.PIPE)
		timestr = re.compile("LINEV    : [0-9]+\.[0-9]+ Volts").findall(str(p.communicate()[0]))
		volts = float(timestr[0][11:].split(' ')[0])
	except:
		volts = 0
	return volts

def main():

    # Put variable declarations here
    # Available types: 'bool', 'numeric', 'string'
    variables = {
        'CPU Temp': {
            'type': 'numeric',
            'bind': rpi.cpu_temp
        },
        'Network Latency': {
            'type': 'numeric',
            'bind': network_latency
        },
        'Hosts Up': {
            'type': 'numeric',
            'bind': hosts_up
        },
        'Line Voltage': {
            'type': 'numeric',
            'bind': line_voltage
        },
    }

    diagnostics = {
        'CPU Temp': rpi.cpu_temp,
        'IP Address': rpi.ip_address,
        'Host': rpi.host_name,
        'Operating System': rpi.os_name
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
