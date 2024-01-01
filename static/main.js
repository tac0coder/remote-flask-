socket = io();

directions = {'w':false,'a':false,'s':false,'d':false,' ':false}

image = document.getElementById('image')
scale = 1920/image.width
document.getElementById('up').onclick =function(){
    socket.emit('scroll',3)
}
document.getElementById('down').onclick =function(){
    socket.emit('scroll',-3)
}
image.addEventListener('mousemove',function(e){
    scale = 1920/image.width
    console.log((e.clientX*scale,e.clientY*scale))
    socket.emit('mousemove',[e.clientX*scale,e.clientY*scale])
})

image.addEventListener('mousedown',function(e){
    e.preventDefault();
    scale = 1920/image.width
    socket.emit('mouseclick',[e.clientX*scale,e.clientY*scale],e.button)
})

window.addEventListener('keydown',function(e){
    if (!(e.key in directions)){
        socket.emit('keyboard',e.key)
    }else if(directions[e.key]==false){
        socket.emit('movement',e.key)
        directions[e.key] = true
    }
})

window.addEventListener('keyup',function(e){
    if (e.key in directions){
        socket.emit('movement',e.key)
        directions[e.key] = false
    }
})

document.getElementById('escape').onclick = function(){
    socket.emit('keyboard', 'esc')
}
document.getElementById('mine').onclick = function(){
    socket.emit('mine')
}
