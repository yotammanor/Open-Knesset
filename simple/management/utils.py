import os
import subprocess

def antiword(filename, logger=None):
    cmd='antiword -x db '+filename+' > '+filename+'.awdb.xml'
    if logger: logger.debug(cmd)
    output = subprocess.check_output(cmd,stderr=subprocess.STDOUT,shell=True)
    if logger: logger.debug(output)
    with open(filename+'.awdb.xml','r') as f:
        xmldata=f.read()
    if logger: logger.debug('len(xmldata) = '+str(len(xmldata)))
    os.remove(filename+'.awdb.xml')
    return xmldata
