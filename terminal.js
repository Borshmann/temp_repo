const terminal = new Terminal({
    cursorBlink: true,
    convertEol: true,
    theme: {
        background: 'black',
        foreground: 'lightgray'
    }
});
terminal.open(document.getElementById('terminal'));

const socket = io();

socket.on('connect', () => {
    console.log('Connected to server');
});

document.getElementById('connectButton').addEventListener('click', () => {
    const host = document.getElementById('host').value;
    const port = document.getElementById('port').value;
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    socket.emit('ssh_connect_request', {
        host: host,
        port: port,
        username: username,
        password: password
    });
    document.getElementById('terminal').classList.remove("before");
    document.getElementById('terminal').classList.add("after");
});

socket.on('ssh_connect', (data) => {
    terminal.write(data.data);
});

socket.on('output', (data) => {
    terminal.write(data);
});

terminal.onData((data) => {
    socket.emit('input', data);
});

socket.on('connect_error', (error) => {
    terminal.write("Connection error: " + error);
});

socket.on('disconnect', () => {
    terminal.write("Disconnected from server.\r\n");
});