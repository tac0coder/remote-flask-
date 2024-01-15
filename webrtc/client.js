var pc = null;

function negotiate() {
    pc.addTransceiver('video', {direction: 'recvonly'});
    pc.addTransceiver('audio', {direction: 'recvonly'});
    return pc.createOffer().then(function(offer) {
        return pc.setLocalDescription(offer);
    }).then(function() {
        // wait for ICE gathering to complete
        return new Promise(function(resolve) {
            if (pc.iceGatheringState === 'complete') {
                resolve();
            } else {
                function checkState() {
                    if (pc.iceGatheringState === 'complete') {
                        pc.removeEventListener('icegatheringstatechange', checkState);
                        resolve();
                    }
                }
                pc.addEventListener('icegatheringstatechange', checkState);
            }
        });
    }).then(function() {
        var offer = pc.localDescription;
        return fetch('/offer', {
            body: JSON.stringify({
                sdp: offer.sdp,
                type: offer.type,
            }),
            headers: {
                'Content-Type': 'application/json'
            },
            method: 'POST'
        });
    }).then(function(response) {
        return response.json();
    }).then(function(answer) {
        return pc.setRemoteDescription(answer);
    }).catch(function(e) {
        alert(e);
    });
}

function start() {
    var config = {
        sdpSemantics: 'unified-plan'
    };

    if (document.getElementById('use-stun').checked) {
        config.iceServers = [{urls: ['stun:stun.l.google.com:19302']}];
    }

    pc = new RTCPeerConnection(config);

    // connect audio / video
    pc.addEventListener('track', function(evt) {
        if (evt.track.kind == 'video') {
            document.getElementById('video').srcObject = evt.streams[0];
        } else {
            document.getElementById('audio').srcObject = evt.streams[0];
        }
    });
    
    dc = pc.createDataChannel('events', {"ordered": true});
    function sendData(type,args){
        data = type
        for(i in args){
            data += ` ${args[i]}`
        }
        dc.send(data)
    }
    directions = {'w':false,'a':false,'s':false,'d':false,' ':false}
    
    image = document.getElementById('video')
    scale = 1
    
    document.getElementById('up').onclick =function(){
        sendData('scroll',[3])
    }
    document.getElementById('down').onclick =function(){
        sendData('scroll',[-3])
    }
    image.addEventListener('mousemove',function(e){
        scale = 1
        console.log(e)
        //sendData('mousemove',[e.clientX*scale,e.clientY*scale])
    })
    
    image.addEventListener('mousedown',function(e){
        e.preventDefault();
        sendData('mouseclick',[e.button])
    })
    
    window.addEventListener('keydown',function(e){
        if (!(e.key in directions)){
            sendData('keyboard',[e.key])
        }else if(directions[e.key]==false){
            if (e.key != ' '){
            sendData('movement',[e.key])
            }else{
                sendData('movement',['space'])
            }
            directions[e.key] = true
        }
    })
    
    window.addEventListener('keyup',function(e){
        if (e.key in directions){
            if (e.key != ' '){
                sendData('movement',[e.key])
                }else{
                    sendData('movement',['space'])
                }
            directions[e.key] = false
        }
    })
    
    document.getElementById('escape').onclick = function(){
        sendData('keyboard', 'esc')
    }
    document.getElementById('mine').onclick = function(){
        sendData('mine')
    }

    document.getElementById('start').style.display = 'none';
    negotiate();
    document.getElementById('stop').style.display = 'inline-block';
}

function stop() {
    document.getElementById('stop').style.display = 'none';

    // close peer connection
    setTimeout(function() {
        pc.close();
    }, 500);
}
