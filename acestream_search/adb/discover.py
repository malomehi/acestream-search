import portscan

from acestream_search.log import logger


def discover_adb_devices():
    local_ip = portscan.get_local_ip()
    logger.info(f'Found local IP: {local_ip}')
    network = '.'.join(local_ip.split('.')[:-1]) + '.0/24'
    scanner = portscan.PortScan(network, '5555')
    logger.info('Discovering ADB devices...')
    open_port_discovered = scanner.run()
    all_hosts = sorted([item[0] for item in open_port_discovered])
    if all_hosts:
        logger.info(f'Found ADB hosts: {", ".join(all_hosts)}')
    else:
        logger.warning(
            'No ADB devices found. Have you enabled '
            'ADB debugging in your Android devices?'
        )
    return all_hosts
