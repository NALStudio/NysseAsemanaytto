import datetime

def local2utc(dt: datetime.datetime) -> datetime.datetime:
    return dt.astimezone(datetime.timezone.utc)

def utc2local(dt: datetime.datetime) -> datetime.datetime:
    return dt.astimezone(tz=None)

def time_after_midnight(t: datetime.time) -> datetime.timedelta:
    return datetime.timedelta(hours=t.hour, minutes=t.minute, seconds=t.second, microseconds=t.microsecond)
