#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2015-01-27 19:58:48
# @Author  : yml_bright@163.com

import os 
import cStringIO
#import magic
from time import localtime, strftime
from logger import LOGGER, CustomLoggingLevel
import struct

class FileObject():
    # init with filepath or bytes
    def __init__(self, stream):
        try:
            safeIsFile = os.path.isfile(stream)
        except:
            safeIsFile = False

        if safeIsFile:
            try:
                self.fileHandler = open(stream, 'rb')
            except IOError:
                self.fileHandler = 0
                LOGGER.error("Can't open file %s"%stream)
            self.filePath = stream
            stat = os.stat(stream)
            self.accessTime = strftime("%Y-%m-%d %H:%M:%S",localtime(stat.st_atime))
            self.editTime = strftime("%Y-%m-%d %H:%M:%S",localtime(stat.st_mtime))
            self.createTime = strftime("%Y-%m-%d %H:%M:%S",localtime(stat.st_ctime))
            self.size = stat.st_size
        else:
            self.fileHandler = cStringIO.StringIO(stream)
            self.filePath = ""
            self.accessTime = "-"
            self.editTime = "-"
            self.createTime = "-"
            self.size = len(stream)

        self.streamCur = 0
        self.markBit = 31
        self.redundancyMark = []
        self.bitMap = [0, 1]
        for i in range(2, self.markBit+1):
            self.bitMap.append(self.bitMap[i-1] + 2**(i-1))
        for i in range(0, self.size+1, self.markBit):
            self.redundancyMark.append(0)

    def __del__(self):
        if self.fileHandler:
            self.fileHandler.close()

    # read [length] bytes from [start]
    # if [start] is -1, read data from current position
    def read(self, length, start = -1):
        if self.fileHandler:
            if start >= 0:
                self.streamCur = start
            if self.streamCur+length > self.size:
                length = self.size - self.streamCur
            self.fileHandler.seek(self.streamCur)
            self.domark(self.streamCur, length)
            self.streamCur += length
            return self.fileHandler.read(length)

    # return current file pointer
    def cur(self):
        return self.streamCur

    # change current file pointer
    def change_cur(self, cur):
        self.streamCur = cur

    # guess file MIME type return an ascii string
    def type(self):
        if self.filePath != '':
            t = os.popen("file %s"%self.filePath)
        else:
            with open('tmp.tmp', 'wb') as f:
                self.fileHandler.seek(0)
                f.write(self.fileHandler.read())
            t = os.popen("file tmp.tmp")
        return t.read()[9:-1]
        #return magic.from_buffer(self.read(1024, 0))

    # mark the data which are read
    def domark(self, start, length):
        bit = start % self.markBit
        index = start / self.markBit
        if length>(self.markBit-bit):
            self.redundancyMark[index] |= self.bitMap[-1] - self.bitMap[bit]
        else:
            self.redundancyMark[index] |= self.bitMap[length+bit] - self.bitMap[bit]
            return
        length -= self.markBit - bit
        index += 1
        while length>self.markBit:
            self.redundancyMark[index] |= self.bitMap[-1]
            index += 1
            length -= self.markBit
        if length>0:
            self.redundancyMark[index] |= self.bitMap[length] 

    # get data which are unread and split it by whick are not continuation
    def redundancy(self):
        if self.fileHandler:
            data = []
            start = 0
            length = 0
            buffFlag = False
            for index in range(len(self.redundancyMark)):
                for i in range(self.markBit):
                    if buffFlag:
                        if self.redundancyMark[index] & (1<<i) != 0:
                            buffFlag = False
                            self.fileHandler.seek(start)
                            data.append({'start' :start, 'data' :self.fileHandler.read(length+1)})
                        else:
                            length += 1
                    else:
                        if self.redundancyMark[index] & (1<<i) == 0:
                            buffFlag = True
                            start = index*self.markBit + i
                            length = 0
            if buffFlag and start < self.size:
                self.fileHandler.seek(start)
                data.append({'start' :start, 'data' :self.fileHandler.read(length)})
            return data

    def __str__(self):
        return "<FileObject: accessTime=%s, editTime=%s, createTime=%s, size=%s, fileHandler=%s>"%(
                self.accessTime, self.editTime, self.createTime, self.size, self.fileHandler)

    def read_uint8(self, start=-1):
        return struct.unpack("B", self.read(1, start))[0]

    def read_uint16(self, start=-1):
        return struct.unpack("H", self.read(2, start))[0]

    def read_uint32(self, start=-1):
        return struct.unpack("l", self.read(4, start))[0]



if __name__ == '__main__':
    x = FileObject('0123456789')
    print x.read(1)
    print x.read(1)
    print x.read(2,3)
    print bin(x.redundancyMark[0])
    print x.redundancy()
    print x.type()
    print x.size