// app.js - Web Serial API logic for FSK Terminal

// Elements
const unsupportedWarning = document.getElementById('unsupported-warning');
const appContainer = document.getElementById('app-container');
const btnSender = document.getElementById('btn-sender');
const btnReceiver = document.getElementById('btn-receiver');
const baudSenderContainer = document.getElementById('baud-sender-container');
const baudReceiverContainer = document.getElementById('baud-receiver-container');
const baudSelect = document.getElementById('baud-select');
const connectBtn = document.getElementById('connect-btn');
const connectionStatus = document.getElementById('connection-status');

// UIs
const senderUi = document.getElementById('sender-ui');
const receiverUi = document.getElementById('receiver-ui');

// Sender Elements
const msgInput = document.getElementById('msg-input');
const sendBtn = document.getElementById('send-btn');
const txLog = document.getElementById('tx-log');
const rxDebugLog = document.getElementById('rx-debug-log');

// Receiver Elements
const clearBtn = document.getElementById('clear-btn');
const rxMainLog = document.getElementById('rx-main-log');

// Serial State
let port = null;
let reader = null;
let inputDone = null;
let outputStream = null;
let outputDone = null;
let isConnected = false;
let currentRole = 'sender';

// Check Support
if (!("serial" in navigator)) {
    unsupportedWarning.classList.remove('hidden');
    appContainer.classList.add('hidden');
}

// Role Selection Logic
function getRole() {
    return currentRole;
}

function updateUiForRole(role) {
    currentRole = role;
    if (role === 'sender') {
        btnSender.classList.add('is-success');
        btnReceiver.classList.remove('is-success');
        senderUi.classList.add('active-ui');
        senderUi.classList.remove('hidden');
        receiverUi.classList.add('hidden');
        receiverUi.classList.remove('active-ui');
        baudSenderContainer.classList.remove('hidden');
        baudReceiverContainer.classList.add('hidden');
    } else {
        btnReceiver.classList.add('is-success');
        btnSender.classList.remove('is-success');
        receiverUi.classList.add('active-ui');
        receiverUi.classList.remove('hidden');
        senderUi.classList.add('hidden');
        senderUi.classList.remove('active-ui');
        baudSenderContainer.classList.add('hidden');
        baudReceiverContainer.classList.remove('hidden');
    }
}

btnSender.addEventListener('click', () => updateUiForRole('sender'));
btnReceiver.addEventListener('click', () => updateUiForRole('receiver'));

// Utility to append text to logs and scroll
function appendLog(element, text) {
    element.innerHTML += text;
    element.scrollTop = element.scrollHeight;
}

function appendLogLine(element, text) {
    const time = new Date().toLocaleTimeString('en-US', { hour12: false });
    element.innerHTML += `[${time}] ${text}<br>`;
    element.scrollTop = element.scrollHeight;
}

// Serial Connection
async function connect() {
    try {
        port = await navigator.serial.requestPort();
        const role = getRole();
        const baudRate = role === 'sender' ? 9600 : parseInt(baudSelect.value, 10);
        
        await port.open({ baudRate: baudRate });
        
        // This is crucial for Arduinos: assert DTR and RTS to initiate connection
        await port.setSignals({ dataTerminalReady: true, requestToSend: true });
        
        isConnected = true;
        connectBtn.innerText = "DISCONNECT";
        connectBtn.classList.replace('is-primary', 'is-error');
        connectionStatus.innerText = "CONNECTED";
        connectionStatus.className = "status-connected";

        if (role === 'sender') {
            appendLogLine(txLog, `--- CONNECTED TO PORT @ ${baudRate} BAUD ---`);
        } else {
            appendLogLine(rxMainLog, `<span style="color: #f1c40f;">--- CONNECTED @ ${baudRate} BAUD ---</span><br>`);
        }

        // Disable role selection and baud rate choice while connected
        btnSender.disabled = true;
        btnReceiver.disabled = true;
        baudSelect.disabled = true;

        // Setup Output stream for sending
        const encoder = new TextEncoderStream();
        outputDone = encoder.readable.pipeTo(port.writable);
        outputStream = encoder.writable;

        // Start reading loop
        readLoop();

    } catch (e) {
        console.error(e);
        alert("Failed to connect: " + e.message);
    }
}

async function disconnect() {
    if (reader) {
        await reader.cancel();
    }
    if (outputStream) {
        await outputStream.getWriter().close();
    }
    
    // Wait for the stream to be closed completely
    if (port) {
        try {
            await port.close();
        } catch (e) {
            console.error("Error closing port", e);
        }
    }
    
    isConnected = false;
    connectBtn.innerText = "CONNECT PORT";
    connectBtn.classList.replace('is-error', 'is-primary');
    connectionStatus.innerText = "DISCONNECTED";
    connectionStatus.className = "status-disconnected";
    btnSender.disabled = false;
    btnReceiver.disabled = false;
    baudSelect.disabled = false;
    
    const role = getRole();
    if (role === 'sender') {
        appendLogLine(txLog, "--- DISCONNECTED ---");
    } else {
        appendLogLine(rxMainLog, `<span style="color: #e74c3c;">--- DISCONNECTED ---</span><br>`);
    }
}

connectBtn.addEventListener('click', () => {
    if (isConnected) {
        disconnect();
    } else {
        connect();
    }
});

// Read Loop
async function readLoop() {
    const decoder = new TextDecoderStream('utf-8');
    inputDone = port.readable.pipeTo(decoder.writable);
    reader = decoder.readable.getReader();

    const role = getRole();

    try {
        while (true) {
            const { value, done } = await reader.read();
            if (value) {
                if (role === 'sender') {
                    // Arduino debug output
                    // Convert newlines to <br> for HTML display
                    const formatted = value.replace(/\n/g, '<br>').replace(/\r/g, '');
                    appendLog(rxDebugLog, formatted);
                } else {
                    // Receiver raw text
                    const formatted = value.replace(/\n/g, '<br>').replace(/\r/g, '');
                    appendLog(rxMainLog, formatted);
                }
            }
            if (done) {
                break;
            }
        }
    } catch (error) {
        console.error("Read error:", error);
    } finally {
        reader.releaseLock();
    }
}

// Send Data
async function sendMessage() {
    if (!isConnected) {
        alert("Not connected to any port!");
        return;
    }
    
    const msg = msgInput.value;
    if (!msg) return;

    try {
        const writer = outputStream.getWriter();
        await writer.write(msg); // Send the text
        writer.releaseLock();

        appendLogLine(txLog, `> ${msg}`);
        msgInput.value = ''; // clear input
    } catch (e) {
        console.error("Write error:", e);
        alert("Error sending data.");
    }
}

sendBtn.addEventListener('click', sendMessage);
msgInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});

// Receiver clear screen
clearBtn.addEventListener('click', () => {
    rxMainLog.innerHTML = '';
});
