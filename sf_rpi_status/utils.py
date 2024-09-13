
def human2bytes(s: str):
    symbols = ('B', 'K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
    if s[-1] not in symbols:
        return int(s)
    prefix = s[-1]
    value = float(s[:-1])
    for i, sym in enumerate(symbols):
        if sym == prefix:
            break
    else:
        i = 0
    return int(value * (1024 ** i))
