import datetime

def get_date_in_yyyymmdd():
  """Returns the current date in YYYYMMDD format."""
  now = datetime.datetime.now()
  return now.strftime("%Y%m%d")

def format_date():
  """Returns the current date in YYYYMMDD format."""
  now = datetime.datetime.now()
  return now.strftime("%Y%m%d%H")

def get_time_in_mmddss():
  """Returns the current time in mmddss format."""
  now = datetime.datetime.now()
  return now.strftime("%H%M%S")

def get_date_in_all():
  """Returns the current time in mmddss format."""
  return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

if __name__ == "__main__":
    print(get_date_in_yyyymmdd())
    print(get_time_in_mmddss())  