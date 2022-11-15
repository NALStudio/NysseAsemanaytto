import datetime

def local2utc(dt: datetime.datetime) -> datetime.datetime:
    return dt.astimezone(datetime.timezone.utc)

def utc2local(dt: datetime.datetime) -> datetime.datetime:
    return dt.astimezone(tz=None)
