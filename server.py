import logging
import time
import copy
import json
import os
from datetime import timedelta, datetime
import math

import Image
import numpy as np
from flask import Flask, request, jsonify, make_response, current_app, render_template, url_for, redirect, send_from_directory, Response
from flask.ext.compress import Compress

__author__ = "Zack Scholl"
__copyright__ = "Copyright 2015, FIND"
__credits__ = ["Zack Scholl", "Stefan Safranek"]
__license__ = "MIT"
__version__ = "0.14"
__maintainer__ = "Zack Scholl"
__email__ = "zack.scholl@gmail.com"
__status__ = "Development"

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
    datefmt='%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler()])

    
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
# Patch because basestring doesn't work for crossdomain()
# https://github.com/oxplot/fysom/issues/1
try:
    unicode = unicode
except NameError:
    # 'unicode' is undefined, must be Python 3
    str = str
    unicode = str
    bytes = bytes
    basestring = (str, bytes)
else:
    # 'unicode' exists, must be Python 2
    str = str
    unicode = unicode
    bytes = str
    basestring = basestring


app = Flask(__name__)
Compress(app)
app.config['COMPRESS_MIMETYPES'] = ['text/html', 'text/css', 'text/xml', 'application/json','application/javascript','image/jpeg']

def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    """ Decorator for the HTTP access control

    From http://flask.pocoo.org/snippets/56/

    Cross-site HTTP requests are HTTP requests for resources from a different domain 
    than the domain of the resource making the request. For instance, a resource loaded from 
    Domain A makes a request for a resource on Domain B. The way this is implemented in 
    modern browsers is by using HTTP Access Control headers: Documentation on developer.mozilla.org.
    """
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator


@app.route("/")
def landing():
    act = []
    with open('activity.txt','r') as f:
        for line in f:
            act.append(float(line)) 
            num = float(line)
            nums = [-3,2,1,0,1,2,3]
            times = [1,2,4,5,4,2,1]
            for i in range(len(nums)):
                newNum = num-nums[i]
                if newNum > 0 and newNum < 24:
                    for j in range(times[i]):
                        act.append(newNum)
            
                

    numActions = len(act)
    act = np.array(act)

    previous = 0
    hours = []
    nums = []
    for i in range(1,24*4+1,1):
        j = float(i)/4.0
        smaller = list(np.where(act<j)[0])
        larger = list(np.where(act>previous)[0])
        both = list(set(smaller) & set(larger))
        hours.append(str(j))
        nums.append(str(100.0*len(both)/numActions))
        previous = j


    data = {}
    for i in range(len(hours)):
        if '.0' in hours[i]:
            hourNum = int(math.floor(float(hours[i])))
            if hourNum == 0:
                hours[i] = str(hourNum+12) + ' AM'
            elif hourNum <= 12:
                hours[i] = str(hourNum) + ' AM'
            else:
                hours[i] = str(hourNum-12) + ' PM'
        elif '.5' in hours[i]:
            hourNum = int(math.floor(float(hours[i])))
            if hourNum == 0:
                hours[i] = str(hourNum+12) + ':30 AM'
            elif hourNum < 12:
                hours[i] = str(hourNum) + ':30 AM'
            elif hourNum == 12:
                hours[i] = str(hourNum) + ':30 PM'
            else:
                hours[i] = str(hourNum-12) + ':30 PM'
        elif '.75' in hours[i]:
            hourNum = int(math.floor(float(hours[i])))
            if hourNum == 0:
                hours[i] = str(hourNum+12) + ':45 AM'
            elif hourNum < 12:
                hours[i] = str(hourNum) + ':45 AM'
            elif hourNum == 12:
                hours[i] = str(hourNum) + ':45 PM'
            else:
                hours[i] = str(hourNum-12) + ':45 PM'
        elif '.25' in hours[i]:
            hourNum = int(math.floor(float(hours[i])))
            if hourNum == 0:
                hours[i] = str(hourNum+12) + ':15 AM'
            elif hourNum < 12:
                hours[i] = str(hourNum) + ':15 AM'
            elif hourNum == 12:
                hours[i] = str(hourNum) + ':15 PM'
            else:
                hours[i] = str(hourNum-12) + ':15 PM'
        else:
            hours[i] = ' a'

    data['hours'] = "'" + "', '".join(hours) + "'"
    data['vals'] = ','.join(nums)

    return render_template('index.html', data = data)


connected = {}
lastSeen = time.time()
lastSeenCount = 0

@app.route("/img", methods=['GET'])
def imageserve():
    global lastSeen, lastSeenCount
    os.system('cp ./static/new.jpg ./static/test.jpg')
    img_size = os.path.getsize('./static/test.jpg')
    new = False

    try:
        uuid = request.args.get('uuid')
        connected[uuid] = time.time()
    except:
        pass
    
    for key in connected.keys():
        if time.time()-connected[key] > 2:
            del connected[key]

    
    
    if img_size > 0.5*(640*480):
        im1 = Image.open('./static/test.jpg')
        im2 = Image.open('./static/image_stream.jpg')
        imarray1 = np.array(im1)
        imarray2 = np.array(im2)
        diff = np.sum(np.square(imarray1.astype(int)-imarray2.astype(int)))
        if diff > 500*(640*480):
            print('new image!')
            os.system('cp ./static/test.jpg ./static/image_stream.jpg')
            new = True
            with open('activity.txt','a') as f:
                hour = float(datetime.now().hour) + float(datetime.now().minute)/60.0 + float(datetime.now().second)/(60.0*60.0)
                f.write(str(hour))
                f.write('\n')
            lastSeenCount += 1
            if lastSeenCount > 10:
                lastSeen = time.time()
                lastSeenCount = 0
    
    lastSeenTime = time.time()-lastSeen
    if lastSeenTime < 60:
        lastSeenTime = " less than a minute ago."
    elif lastSeenTime < 60*60:
        lastSeenTime = str(int(lastSeenTime/60)) + " minutes ago."
    elif lastSeenTime < 60*60*24:
        lastSeenTime = str(int(lastSeenTime/(60*60))) + " hours ago."
    else:
        lastSeenTime = str(int(lastSeenTime/(60*60*24))) + " days ago."
    
    payload = {'src':'/static/image_stream.jpg?foo='+str(int(time.time())),'time':time.time(),'newimage':new,'connected':len(connected.keys()),'lastSeen':lastSeenTime}
    return jsonify(result=payload)
    
if __name__ == "__main__":
    """Main app

    Uses the Flask internals
    """
    app.run(host='0.0.0.0', port=3000)
    # app.run()
