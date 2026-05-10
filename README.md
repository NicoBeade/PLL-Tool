# FSK Communicator Web Tool

This repository contains a unified Web Serial application for FSK (Frequency Shift Keying) transmission and reception, replacing the older Python desktop tools. 

The web app uses the **Web Serial API** and runs directly from Google Chrome, Edge, or Opera. It features a retro, videogame-inspired interface.

## 🚀 Live Demo
You can host this `docs/` folder on GitHub Pages to access it from anywhere!
*(Once GitHub pages is enabled for the `docs/` directory or root, insert the link here).*

> **Note:** Safari, Firefox, and mobile browsers do not support the Web Serial API.

---

## 🔌 Hardware Connection Guide

To successfully transmit text via audio using FSK, you need to connect the hardware precisely as shown below.

### Block Diagram

```mermaid
flowchart TD
    subgraph SENDER ["Sender Side (PC 1)"]
        A[Web App - Sender Mode<br>Baud: 9600]
        B[Arduino Uno<br>Modulator]
    end
    
    subgraph CHANNEL ["Audio / Signal Channel"]
        C((FSK Audio Signal<br>Space: 1200 Hz<br>Mark: 2400 Hz))
    end
    
    subgraph RECEIVER ["Receiver Side (PC 2)"]
        D[PLL FSK Circuit<br>Demodulator]
        E[UART-USB Converter<br>CH340/FTDI]
        F[Web App - Receiver Mode<br>Baud: 300]
    end
    
    A -- USB --> B
    B -- "Pin 9 & GND" --> C
    C -- "Audio In" --> D
    D -- "Digital Out (TX)" --> E
    E -- USB --> F

    style A fill:#2b2b2b,stroke:#4ade80,color:#fff
    style F fill:#2b2b2b,stroke:#4ade80,color:#fff
    style B fill:#00878F,stroke:#000,color:#fff
    style D fill:#FFA500,stroke:#000,color:#000
    style E fill:#e74c3c,stroke:#000,color:#fff
```

### Wiring Steps

1. **PC1 (Sender) Setup:**
   - Connect the **Arduino Uno** to PC1 via USB.
   - Upload the `TC2-PLL-FSK/TC2-PLL-FSK.ino` sketch to the Arduino.
   - Open the web app on PC1, select **[ SENDER ]**, and click **CONNECT PORT**. Select the Arduino's COM port.
   - *Note: The Sender connects at 9600 baud automatically.*

2. **Audio Link:**
   - Connect Arduino **Pin 9** (Audio Out) to the input of your **PLL FSK Demodulator Circuit**.
   - Connect the Arduino's **GND** to the PLL Circuit's **GND**.

3. **PC2 (Receiver) Setup:**
   - Connect the output of the **PLL FSK Demodulator** to the `RX` pin of a **UART-USB converter**.
   - Ensure the PLL Circuit and the UART-USB converter share a common **GND**.
   - Plug the UART-USB converter into PC2.
   - Open the web app on PC2, select **[ RECEIVER ]**, and click **CONNECT PORT**. Select the UART-USB's COM port.
   - *Note: The Receiver connects at 300 baud automatically (the true data rate of the FSK transmission).*

### Testing
Type a message on the Sender app and hit `Send`. The Arduino will modulate the text into audio tones (1200 Hz / 2400 Hz) at 300 baud. The PLL circuit will demodulate these tones back into digital 1s and 0s, passing them through the UART converter to PC2, where the Receiver app will display the decoded text.

---

**Authors:** Nicolás Beade & Javier Petrucci
**Course:** Laboratorio de Electrónica II (25.16)
