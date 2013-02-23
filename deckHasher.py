import base64

'''
const unsigned short ID2BASE64(const UINT Id)
{
	_ASSERT(Id < 0xFFF);
#define EncodeBase64(x) (x < 26) ? (x + 'A') : ((x < 52) ? (x + 'a' - 26) : ((x < 62) ? (x + '0' - 52) : ((x == 62) ? ('+') : ('/'))))	
	// please keep in mind that any integer type has swapped hi and lo bytes
	// i have swapped them here so we will have correct 2 byte string in const char* GetID64 function
	return ((EncodeBase64(((Id >> 6) & 63)))/* << 8*/) + ((EncodeBase64((Id & 63))) << 8); // so many baneli... parenthesis!
}
#define BASE64ID	BASE642ID // alias
const UINT BASE642ID(const unsigned short base64)
{
#define DecodeBase64(x) (((x >= 'A') && (x <= 'Z')) ? (x - 'A') : (((x >= 'a') && (x <= 'z')) ? (x - 'a' + 26) : (((x >= '0') && (x <= '9')) ? (x - '0' + 52) : ((x == '+') ? (62) : (63)))))
	// same stuff as with ID2BASE64, hi and lo swapped
	return DecodeBase64((base64 & 0xFF)) + DecodeBase64((base64 >> 8)) * 64;
}
'''

# return DecodeBase64((base64 & 0xFF)) + DecodeBase64((base64 >> 8)) * 64;
def hashToDeck(hashString):
    encodedString = hashString
    decodedString = []
    lastId = -1
    while(len(encodedString) > 0):
        isOver4000 = False
        if(encodedString[0] == "-"):
            isOver4000 = True
            encodedString = encodedString[1:]

        id = decodeBase64(encodedString[:1]) * 64
        id += decodeBase64(encodedString[1:2])
        encodedString = encodedString[2:]
        if(id > 4000):
            for i in range(0,id - 4000 - 1):
                decodedString.append(lastId)
        else:
            if(isOver4000):
                id += 4000
            decodedString.append(id)
        lastId = id
    return decodedString

# return ((EncodeBase64(((Id >> 6) & 63)))/* << 8*/) + ((EncodeBase64((Id & 63))) << 8); // so many baneli... parenthesis!
def deckToHash(idList, sort = False):

    encodedString = ''

    # prep the vars and setup the initial encoding
    lastId = -1
    lastCount = 1

    if(sort):
        temp = list(idList)
        idList = sorted(temp[1:])
        idList.insert(0, temp[0])

    for i in range(0, len(idList)):
        id = idList[i]
        if(lastId == id):
            lastCount += 1
            continue
        elif(lastCount > 1):
            lastCount += 4000
            encodedString += encodeBase64((lastCount >> 6) & 63)
            encodedString += encodeBase64((lastCount & 63))
            lastCount = 1

        lastId = id
        if(id > 4000):
            encodedString += "-"
            id -= 4000
        encodedString += encodeBase64((id >> 6) & 63)
        encodedString += encodeBase64((id & 63))

    # need to encode any duplicate ids leftover from the loop
    if(lastCount > 1):
        lastId = 4000 + lastCount
        encodedString += encodeBase64((lastId >> 6) & 63)
        encodedString += encodeBase64((lastId & 63))
    return encodedString
    
# DecodeBase64(x) (((x >= 'A') && (x <= 'Z')) ? (x - 'A') : (((x >= 'a') && (x <= 'z')) ? (x - 'a' + 26) : (((x >= '0') && (x <= '9')) ? (x - '0' + 52) : ((x == '+') ? (62) : (63)))))
def decodeBase64(x):
    if (x == '.'):
        x = '/' # workaround for azure not liking '/'

    if (x >= 'A' and x <= 'Z') : return ord(x) - ord('A')
    if (x >= 'a' and x <= 'z') : return ord(x) - ord('a') + 26
    if (x >= '0' and x <= '9') : return ord(x) - ord('0') + 52
    if (x == '+'): return 62
    return 63

# EncodeBase64(x) (x < 26) ? (x + 'A') : ((x < 52) ? (x + 'a' - 26) : ((x < 62) ? (x + '0' - 52) : ((x == 62) ? ('+') : ('/'))))	
def encodeBase64(x):
    if (x < 26) : return chr(x + ord('A'))
    if (x < 52) : return chr(x + ord('a') - 26)
    if (x < 62) : return chr(x + ord('0') - 52)
    if (x == 62) : return "+"
    return "/"

def idListToOutputString(ids):
    output = ""
    lastId = -1
    rangeStart = -1
    for id in sorted(ids):
        if(id != lastId + 1):
            if(rangeStart != -1):
                if(rangeStart != lastId):
                    output += str(rangeStart) + ", " + str(lastId) + "\n"
                else:
                    output += str(rangeStart) + "\n"
            rangeStart = id
        lastId = id
    output += str(rangeStart) + ", " + str(lastId) + "\n"
    return output
