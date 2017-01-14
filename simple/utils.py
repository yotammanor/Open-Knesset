import os
import subprocess
from logging import getLogger

local_logger = getLogger(__name__)


def doc_to_xml(filename, logger=None):
    if not logger:
        logger = local_logger
    cmd = 'antiword -x db ' + filename + ' > ' + filename + '.awdb.xml'
    logger.debug('Generated antiword command %s' % cmd)
    output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
    logger.debug('Antiword output: %s' % output)
    with open(filename + '.awdb.xml', 'r') as f:
        xmldata = f.read()

    logger.debug('len(xmldata) = ' + str(len(xmldata)))
    os.remove(filename + '.awdb.xml')
    return xmldata
