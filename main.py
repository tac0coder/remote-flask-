from flask import Flask, render_template,Response
from flask_socketio import SocketIO
import PIL.ImageGrab
import PIL.Image
import os
import cv2
import pyautogui
import pydirectinput,math
import base64
from multiprocessing import Process
import numpy as np
app = Flask(__name__)
socketio = SocketIO(app,logger=True)
mine = False
#data:image/jpg;base64, [bytearray]

directions = {'w':False,'a':False,'d':False,'s':False,' ':False}


@socketio.on('getscreen')
def getScreen():
    global socketio

    im=PIL.ImageGrab.grab()
    r, g, b = im.split()
    tempb = b
    tempr = r
    b = tempr
    r = tempb
    im = PIL.Image.merge('RGB', (r, g, b))
    im = im.resize((int(im.size[0]/2),int(im.size[1]/2)),PIL.Image.Resampling.LANCZOS)
    im = np.asarray(im)
    #with open('large.txt','w') as s:
        #s.write(str(base64.b64encode(cv2.imencode('.jpg',im)[1].tobytes()))[2:-1])
    socketio.emit('image',str(base64.b64encode(cv2.imencode('.jpg',im)[1].tobytes()))[2:-1])


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/panic')
def panic():
    os.system("taskkill /IM python.exe /F")
    
@socketio.on('mousemove')
def mousemove(locs):
    locs = [math.floor(locs[0]),math.floor(locs[1])]
    pyautogui.moveTo(locs[0],locs[1])
    
@socketio.on('mouseclick')
def mouseclick(locs,button):
    locs = [math.floor(locs[0]),math.floor(locs[1])]
    #print(button)
    if button == 0:
        pydirectinput.click()
    elif button == 2:
        pydirectinput.rightClick()
    elif button == 1:
        pydirectinput.middleClick()


@socketio.on('keyboard')
def keyboard(button):
    pydirectinput.press(button.lower() if not 'Arrow' in button else button[5:].lower())

@socketio.on('mine')
def minefunc():
    global mine
    mine = not mine
    if mine:
        pydirectinput.mouseDown()
    else:
        pydirectinput.mouseUp()

@socketio.on('scroll')
def scroll(num):
    pyautogui.scroll(num)

@socketio.on('movement')
def move(direction):
    global directions
    directions[direction] = not directions[direction]
    print(directions)
    if directions[direction]:
        pydirectinput.keyDown(direction)
    else: 
        pydirectinput.keyUp(direction)

if __name__ == "__main__":
    socketio.run(app,host='0.0.0.0')
    
    
