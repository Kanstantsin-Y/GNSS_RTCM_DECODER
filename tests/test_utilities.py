"""
    Author: Kanstantsin Yuryeu
    Mail: konstantin.yuriev83@gmail.com

    All kinds af utility functions/classes required for tests or test data generation.
"""



def make_1029():

    # an example from the standard spec.
    bts = [ 0xD3, 0x00, 0x27, 0x40, 0x50, 0x17, 0x00, 0x84,
            0x73, 0x6E, 0x15, 0x1E, 0x55, 0x54, 0x46, 0x2D,
            0x38, 0x20, 0xD0, 0xBF, 0xD1, 0x80, 0xD0, 0xBE,
            0xD0, 0xB2, 0xD0, 0xB5, 0xD1, 0x80, 0xD0, 0xBA,
            0xD0, 0xB0, 0x20, 0x77, 0xC3, 0xB6, 0x72, 0x74,
            0x65, 0x72, 0xED, 0xA3, 0x3B ]

    bts = bytes(bts)
    f = open('msg1029.rtcm3','wb')
    f.write(bts)
    f.close()


class TestDataGrabber():

    def __init__(self):
        self.eph_scenario = {
            1019: {'fname':'msg1019.rtcm3', 'cnt':3, 'fp':None},
            1020: {'fname':'msg1020.rtcm3', 'cnt':3, 'fp':None},
            1041: {'fname':'msg1041.rtcm3', 'cnt':3, 'fp':None},
            1042: {'fname':'msg1042.rtcm3', 'cnt':3, 'fp':None},
            1044: {'fname':'msg1044.rtcm3', 'cnt':3, 'fp':None},
            1045: {'fname':'msg1045.rtcm3', 'cnt':3, 'fp':None},
            1046: {'fname':'msg1046.rtcm3', 'cnt':3, 'fp':None}
        }
        self.base_scenario = {
            1005: {'fname':'msg1005.rtcm3', 'cnt':1, 'fp':None},
            1007: {'fname':'msg1007.rtcm3', 'cnt':1, 'fp':None},
            1230: {'fname':'msg1230.rtcm3', 'cnt':1, 'fp':None},
            1006: {'fname':'msg1006.rtcm3', 'cnt':1, 'fp':None},
            1033: {'fname':'msg1033.rtcm3', 'cnt':1, 'fp':None}
        }
        

    def save(self, mNum:int, msg:bytes, set:str = 'EPH'):
        """Save a messages from the input flow to file."""

        if set == 'EPH':
            s = self.eph_scenario.get(mNum)
        elif set == 'BASE':
            s = self.base_scenario.get(mNum)

        if not s:
            return
        
        if s['cnt'] == 0:
            return
        
        if s['fp'] == None:
            s['fp'] = open(s['fname'],'wb')

        s['fp'].write(msg)
        s['fp'].flush()
        s['cnt'] -= 1
        
        if s['cnt'] == 0:
            s['fp'].close()

        


def save_some_fancy_test_data(msg_list):
    '''Utility function. Accepts a bunch or RTCM messages.
        Makes some test files.'''

    f = open('reference-3msg.rtcm3','wb')
    f.write(b''.join([msg_list[0], msg_list[1], msg_list[2]]))
    f.close()

    f = open('reference-3msg-interleaved.rtcm3','wb')
    f.write(b'-'.join([msg_list[0], msg_list[1], msg_list[2]]))
    f.close()

    f = open('reference-3msg-noiseBefore.rtcm3','wb')
    f.write(b''.join([b'abra-cadabra', msg_list[0], msg_list[1], msg_list[2]]))
    f.close()

    f = open('reference-3msg-noiseAfter.rtcm3','wb')
    f.write(b''.join([msg_list[0], msg_list[1], msg_list[2], b'abra-cadabra']))
    f.close()
    
    f = open('reference-3msg-1brokenCRC.rtcm3','wb')
    a = bytearray(msg_list[0])
    a[-1:] = b'0'
    a[-2:-1] = b'0'
    f.write(b''.join([a,msg_list[1],msg_list[2]]))
    f.close()
    
    f = open('reference-3msg-2brokenCRC.rtcm3','wb')
    a = bytearray(msg_list[0])
    a[-1:] = b'0'
    a[-2:-1] = b'0'
    b = bytearray(msg_list[1])
    b[-5:-4] = b'0'
    b[-6:-5] = b'0'
    f.write(b''.join([a,b,msg_list[2]]))
    f.close()