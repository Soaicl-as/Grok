document.addEventListener('DOMContentLoaded', function() {
    var socket = io();
    var logDiv = document.getElementById('logs');

    socket.on('log', function(msg) {
        var p = document.createElement('p');
        p.textContent = msg;
        logDiv.appendChild(p);
        logDiv.scrollTop = logDiv.scrollHeight;
    });
});
