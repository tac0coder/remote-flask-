import argparse
import asyncio
import json
import logging
import os
import platform
import ssl,PIL.ImageGrab
from av import VideoFrame
import pyautogui
import pydirectinput,math
from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription,VideoStreamTrack
from aiortc.contrib.media import MediaPlayer, MediaRelay
from aiortc.rtcrtpsender import RTCRtpSender

pyautogui.FAILSAFE =False
ROOT = os.path.dirname(__file__)

directions = {'w':False,'a':False,'d':False,'s':False,' ':False}
mine = False
relay = None
webcam = None

class VideoTransformTrack(VideoStreamTrack):
    """
    takes frames from ur screen
    """

    kind = "video"

    def __init__(self):
        super().__init__()  # don't forget this! 


    async def recv(self):
        pts, time_base = await self.next_timestamp()
        im=PIL.ImageGrab.grab()
        im = im.resize((int(im.size[0]/2),int(im.size[1]/2)),PIL.Image.Resampling.LANCZOS)
        im = VideoFrame.from_image(im)
        im.pts = pts
        im.time_base = time_base
        return im




async def index(request):
    content = open(os.path.join(ROOT, "index.html"), "r").read()
    return web.Response(content_type="text/html", text=content)


async def javascript(request):
    content = open(os.path.join(ROOT, "client.js"), "r").read()
    return web.Response(content_type="application/javascript", text=content)


async def offer(request):
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()
    pcs.add(pc)

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        print("Connection state is %s" % pc.connectionState)
        if pc.connectionState == "failed":
            await pc.close()
            pcs.discard(pc)
    
    @pc.on("datachannel")
    def on_datachannel(channel):
        @channel.on("message")
        def on_message(message): 
            print(message)
            if isinstance(message, str) and message.startswith("mousemove"):
                args = message.split(' ')[1:]
                locs = [math.floor(float(args[0])),math.floor(float(args[1]))]
                pyautogui.moveTo(locs[0],locs[1])
            elif isinstance(message, str) and message.startswith("mouseclick"):
                args = message.split(' ')[1:]
                button = int(args[0])
                if button == 0:
                    pydirectinput.click()
                elif button == 2:
                    pydirectinput.rightClick()
                elif button == 1:
                    pydirectinput.middleClick()
            elif isinstance(message, str) and message.startswith("keyboard"):
                args = message.split(' ')[1:]
                button = args[0]
                pydirectinput.press(button.lower() if not 'Arrow' in button else button[5:].lower())
            elif isinstance(message, str) and message.startswith("mine"):
                global mine
                mine = not mine
                if mine:
                    pydirectinput.mouseDown()
                else:
                    pydirectinput.mouseUp()
            elif isinstance(message, str) and message.startswith("scroll"):
                args = message.split(' ')
                pyautogui.scroll(int(args[1]))
            elif isinstance(message, str) and message.startswith("movement"):
                global directions
                direction = message.split(' ')[1]
                direction = direction if not direction == 'space' else ' '
                directions[direction] = not directions[direction]
                print(directions)
                if directions[direction]:
                    pydirectinput.keyDown(direction)
                else: 
                    pydirectinput.keyUp(direction)


    video_sender = pc.addTrack(VideoTransformTrack())


    await pc.setRemoteDescription(offer)

    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return web.Response(
        content_type="application/json",
        text=json.dumps(
            {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
        ),
    )


pcs = set()


async def on_shutdown(app):
    # close peer connections
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros)
    pcs.clear()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WebRTC webcam demo")
    parser.add_argument("--cert-file", help="SSL certificate file (for HTTPS)")
    parser.add_argument("--key-file", help="SSL key file (for HTTPS)")
    parser.add_argument("--play-from", help="Read the media from a file and sent it.")
    parser.add_argument(
        "--play-without-decoding",
        help=(
            "Read the media without decoding it (experimental). "
            "For now it only works with an MPEGTS container with only H.264 video."
        ),
        action="store_true",
    )
    parser.add_argument(
        "--host", default="0.0.0.0", help="Host for HTTP server (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", type=int, default=8080, help="Port for HTTP server (default: 8080)"
    )
    parser.add_argument("--verbose", "-v", action="count")
    parser.add_argument(
        "--audio-codec", help="Force a specific audio codec (e.g. audio/opus)"
    )
    parser.add_argument(
        "--video-codec", help="Force a specific video codec (e.g. video/H264)"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    if args.cert_file:
        ssl_context = ssl.SSLContext()
        ssl_context.load_cert_chain(args.cert_file, args.key_file)
    else:
        ssl_context = None

    app = web.Application()
    app.on_shutdown.append(on_shutdown)
    app.router.add_get("/", index)
    app.router.add_get("/client.js", javascript)
    app.router.add_post("/offer", offer)
    web.run_app(app, host=args.host, port=args.port, ssl_context=ssl_context)
