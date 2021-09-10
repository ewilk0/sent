from pytrends.request import TrendReq
import pandas as pd
import datetime, time
from bitmex import bitmex
import sys, subprocess
import smtplib, ssl

api_key = 'xxx'
api_secret = 'xxx'
client = bitmex(test=False, api_key=api_key, api_secret=api_secret)
port = 465
password = "xxx"
context = ssl.create_default_context()
global now, next_hour # dangerous but necessary; these need to be aligned across entire script

def initialWait():
	delta = datetime.timedelta(hours=1)
	now = datetime.datetime.now()
	next_hour = (now + delta).replace(microsecond=0, second=0, minute=0)
	wait_seconds = (next_hour - now).seconds
	print("The time is: " + str(now))
	print("We're waiting for the next hour in... " + str(wait_seconds) + " seconds.")
	time.sleep(wait_seconds + 1)
	monitorDataframe()

def monitorDataframe():
	pytrends = TrendReq(hl='en-US', tz=420)
	kw_list = ["buy bitcoin", "sell bitcoin"]
	pytrends.build_payload(kw_list, cat=0, timeframe='now 7-d', geo='US')
	df = pytrends.interest_over_time()

	if(df.iloc[166]['buy bitcoin'] > df.iloc[165]['buy bitcoin'] and df.iloc[166]['sell bitcoin'] < df.iloc[165]['sell bitcoin']):
		priceBought = float((client.Instrument.Instrument_get(symbol="XBTUSD").result())[0][0]["askPrice"])
		balance = ((client.User.User_getMargin().result())[0]['marginBalance'])
		balance = balance * 0.00000001
		quantity = balance * 0.95 * priceBought
		client.Order.Order_new(symbol="XBTUSD", orderQty=int(quantity)).result()
		print("Last close on buy: " + str(df.iloc[166]['buy bitcoin']))
		print("Last close on short: " + str(df.iloc[166]['sell bitcoin']))
		print("Last last close on buy: " + str(df.iloc[165]['buy bitcoin']))
		print("Last last close on short: " + str(df.iloc[165]['sell bitcoin']))
		try:
			# sending an email notification to user
			with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
				server.login("xxx", password)
				server.sendmail("xxx", "xxx", "Bought bitcoin.")
		except:
			pass
		monitorTrade(1, priceBought, quantity)
	elif(df.iloc[166]['buy bitcoin'] < df.iloc[165]['buy bitcoin'] and df.iloc[166]['sell bitcoin'] > df.iloc[165]['sell bitcoin']):
		priceBought = float((client.Instrument.Instrument_get(symbol="XBTUSD").result())[0][0]["askPrice"])
		balance = ((client.User.User_getMargin().result())[0]['marginBalance'])
		balance = balance * 0.00000001
		quantity = balance * 0.95 * priceBought
		client.Order.Order_new(symbol="XBTUSD", orderQty=-int(quantity)).result()
		print("Last close on buy: " + str(df.iloc[166]['buy bitcoin']))
		print("Last close on short: " + str(df.iloc[166]['sell bitcoin']))
		print("Last last close on buy: " + str(df.iloc[165]['buy bitcoin']))
		print("Last last close on short: " + str(df.iloc[165]['sell bitcoin']))
		monitorTrade(2, priceBought, quantity)
	else:
		print("Waiting for the next hour...")
		subprocess.Popen(["python3", "sentiment2.py"])
		sys.exit(0)

def monitorTrade(conVal, priceBought, quantityBought):
	delta = datetime.timedelta(hours=1)
	now = datetime.datetime.now()
	next_hour = (now + delta).replace(microsecond=0, second=0, minute=0)
	while(True):
		delta = datetime.timedelta(hours=1)
		now = datetime.datetime.now()

		if conVal == 1:
			if now >= next_hour:
				client.Order.Order_new(symbol="XBTUSD", orderQty=int(quantityBought)).result()
				print("Released.")
				break
			elif(currentPrice/priceBought < 0.997):
				client.Order.Order_new(symbol="XBTUSD", orderQty=-int(quantityBought)).result()
				print("Released.")
				break
			time.sleep(1)

		elif conVal == 2:
			if now >= next_hour:
				client.Order.Order_new(symbol="XBTUSD", orderQty=int(quantityBought)).result()
				print("Purchased.")
				break
			elif(currentPrice/priceBought < 1.003):
				client.Order.Order_new(symbol="XBTUSD", orderQty=int(quantityBought)).result()
				print("Purchased.")
				break
			time.sleep(1)

	subprocess.Popen(["python3", "sentiment2.py"])
	sys.exit(0)

initialWait()