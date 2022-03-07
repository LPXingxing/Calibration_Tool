import configparser

config=configparser.ConfigParser()
config.read("config.ini",encoding="utf-8")
val = config.get('MTF', 'middle_threshold')
print(val)
