#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Sep 21 11:47:10 2019

@author: vramirez
"""

from lxml import html
import requests
import decimal
from datetime import datetime
import  boto3
from time import sleep
from random import randint

def getBookId(url):
    vec=iter(str.split(url,"/"))
    for pos in vec:
        if pos == "dp" :
            return next(vec)
        if pos =="product":
            return str.split(next(vec),"?")[0]
    return None
        
def parse(url):
    vec=[]
    vec.append('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36' )
    vec.append('Mozilla/5.0 (Macintosh; Intel Mac OS X x.y; rv:42.0) Gecko/20100101 Firefox/42.0')
    vec.append('Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0')
    vec.append('Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:69.0) Gecko/20100101 Firefox/69.0')
    vec.append('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) snap Chromium/77.0.3865.90 Chrome/77.0.3865.90 Safari/537.36')
    vec.append('Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:71.0) Gecko/20100101 Firefox/71.0')
    vec.append('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) snap Chromium/78.0.3904.108 Chrome/78.0.3904.108 Safari/537.36')
    
    try:
        # Retrying for failed requests
        for i in range(50):
            headers = {
                'User-Agent': vec[randint(0,len(vec)-1)]
            }
            # Generating random delays
            sleep(randint(1,5))
            # Adding verify=False to avold ssl related issues
            response = requests.get(url, headers=headers, verify=True)

            if response.status_code == 200: 
                doc = html.fromstring(response.content)
                XPATH_SALE_PRICE = '//input[@name="displayedPrice"]/@value'
                XPATH_ORIGINAL_PRICE = '//td[contains(text(),"Digital List Price")]/following-sibling::td/text()'
                RAW_SALE_PRICE = doc.xpath(XPATH_SALE_PRICE)
                RAW_ORIGINAL_PRICE = doc.xpath(XPATH_ORIGINAL_PRICE)
                
                SALE_PRICE = RAW_SALE_PRICE[0] if RAW_SALE_PRICE else None
                ORIGINAL_PRICE = ''.join(RAW_ORIGINAL_PRICE).strip()[1:] if RAW_ORIGINAL_PRICE else None
                
                if not ORIGINAL_PRICE:
                    ORIGINAL_PRICE = SALE_PRICE
                # retrying in case of captcha
                if not SALE_PRICE:
                    print('captcha')
                    continue

                data = {
                    'SALE_PRICE': SALE_PRICE,
                    'ORIGINAL_PRICE': ORIGINAL_PRICE,
                    'URL': url,
                }
                return data
            
            elif response.status_code==404:
                break
    



        
    except Exception as e:
        print(e)


def generateItem(url, email):
    #
    obj={}
    obj['ebookid']=getBookId(url)
    obj['userid']=email
    obj['url']=url
    obj['timestamp']=datetime.now().isoformat()
    obj['price']=decimal.Decimal(parse(url)['SALE_PRICE'])
    return obj

def writeItem(item):
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('ebooks')
    response = table.put_item(Item=item)
    return response

def deleteEbook(ebookid,userid):
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('ebooks')
    response = table.delete_item(Key={'ebookid':ebookid,'userid':userid})
    return response
#def get    