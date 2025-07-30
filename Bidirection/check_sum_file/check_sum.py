

class ASTM:
    ENQ = 5
    ACK = 6
    NAK = 21
    EOT = 4
    ETX = 3
    ETB = 23
    STX = 2
    NEWLINE = 10

def get_checksum_value(frame: str) -> str:
    """
    Reads checksum of an ASTM frame. Calculates characters after STX,
    up to and including the ETX or ETB.
    
    :param frame: Frame of ASTM data to evaluate
    :return: String containing the checksum
    """
    sum_of_chars = 0
    complete = False

    for char in frame:
        byte_val = ord(char)  
        
        if byte_val == ASTM.STX:
            sum_of_chars = 0  
        elif byte_val in {ASTM.ETX, ASTM.ETB}:
            sum_of_chars += byte_val
            complete = True
            break
        else:
            sum_of_chars += byte_val

    if complete and sum_of_chars > 0:
        checksum = hex(sum_of_chars % 256)[2:].upper()
        return checksum.zfill(2)

    return "00"

frame = """\x021H|\^&|||H7600^1|||||host|TSREQ^REAL|P|1\rQ|1|^^               G31 - S^0^50021^021^^S0^||ALL||||||||A\rL|1|N\r\x03"""
checksum = get_checksum_value(frame)
print("Checksum:", checksum)
