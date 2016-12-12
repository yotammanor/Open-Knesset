import os
import subprocess
from logging import getLogger

local_logger = getLogger(__name__)


def antiword(filename, logger=None):
    if not logger:
        logger = local_logger
    cmd = 'antiword -x db ' + filename + ' > ' + filename + '.awdb.xml'
    logger.debug(cmd)
    output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
    logger.debug(output)
    with open(filename + '.awdb.xml', 'r') as f:
        xmldata = f.read()

    logger.debug('len(xmldata) = ' + str(len(xmldata)))
    os.remove(filename + '.awdb.xml')
    return xmldata
