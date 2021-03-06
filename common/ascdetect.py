from common.logger import LOGGER, CustomLoggingLevel
from common.fileobject import FileObject
import logging


def asc_detect(filename, min_length=5):
    LOGGER.log(CustomLoggingLevel.OTHER_DATA,
               "--- ascii detect start --- ")
    
    def is_readable(c):
        readable_chars = "abcdefghijklmnopqrstuvwxyz" + \
                         "ABCDEFGHIJKLMNOPQRSTUVWXYZ" + \
                         "0123456789" + \
                         "`~!@#$%^&*()_+[]\{}|;':\",./<>" + \
                         " "+'\n'+'\t'+'\r'

        return c < 128 and chr(c) in readable_chars
    # LOGGER.addHandler(logging.StreamHandler())
    file_object = FileObject(filename)
    pre = -1
    data = ""
    for i in xrange(file_object.size):
        byte = file_object.read_uint8()
        if not is_readable(byte):
            length = i - pre - 1
            pre = i
            if length >= min_length:
                LOGGER.log(CustomLoggingLevel.ASCII_DATA,
                           "[ascii] at pos 0x%x:\n" % i +data)
            data = ""
        else:
            data += chr(byte)
    LOGGER.log(CustomLoggingLevel.OTHER_DATA,
               "--- ascii detect finished --- ")


if __name__ == '__main__':
    asc_detect("../!index.jpg", 10)