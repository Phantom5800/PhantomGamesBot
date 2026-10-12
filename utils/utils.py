# standard libraries
import os, random, re

debugPrintEnabled = False

def debugPrint(value: str):
    if debugPrintEnabled:
        print(value)

def tryParseInt(value: str, default: int = 0) -> int:
    try:
        return int(value)
    except ValueError:
        return default
    
def getenv(key: str, default: str = None) -> str:
    return os.environ.get(key, default)

def getenv_int(key: str, default: int = 0) -> int:
    value = os.environ.get(key)
    if value is None:
        return default
    else:
        return tryParseInt(value, default)

async def replace_vars_generic(message: str) -> str:
    '''Generic variable replacement that does not depend on any platform specific features.'''
    out_str = message

    # generate a random number in a range
    if "$randnum" in out_str:
        regex = r"(.*)\W*((?i:)\$randnum\((?-i:))\W*([0-9]*),([0-9]*)\)(.*)"
        matches = re.match(regex, out_str)
        if matches is not None:
            match_groups = matches.groups()
            minimum = tryParseInt(match_groups[2], 0)
            maximum = tryParseInt(match_groups[3], 100)
            rand = random.randint(minimum, maximum)

            start = len(matches.groups()[0])
            end = len(matches.groups()[0]) + len(matches.groups()[1]) + len(matches.groups()[2]) + len(matches.groups()[3]) + 2
            out_str = f"{out_str[:start]}{rand}{out_str[end:]}"
        else:
            out_str = out_str.replace("$randnum", "[$randnum must have a minimum and maximum: example \"$randnum(10,50)\"]")

    return out_str
