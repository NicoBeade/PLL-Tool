/*
  Teoría de Circuitos II (25.14)
  Laboratorio de Electrónica II (25.16)

  Modulador FSK (Audio Frequency Shift Keying)

  Autores: Nicolás Beade y Javier Petrucci
  -------------------------------------------------------------
  Convierte texto recibido por Serial (USB) a audio FSK.
  
  Especificaciones:
  - Frecuencia 0 (Space): 1200 Hz
  - Frecuencia 1 (Mark):  2400 Hz
  - Estado Reposo (Idle): Tono Mark continuo (2400 Hz)
  - Velocidad de transmisión: ~300 Baudios
  - Protocolo UART simulado: 8 bits de datos, Sin paridad, 1 bit de Stop (8N1)
  
  Conexión:
  - Pin 9: Salida
*/

// --- Configuración ---
const int PIN_AUDIO = 9;  // Salida
const int LED_IND = 13;   // LED integrado parpadea al transmitir

// --- Tiempos para FSK ---
// Para 300 baudios, un bit dura 1/300 = 3333 microsegundos.
// 1200Hz: Periodo = 833us. 3333 / 833 = 4 ciclos por bit.
// 2400Hz: Periodo = 416us. 3333 / 416 = 8 ciclos por bit.

const unsigned long HALF_PERIOD_1200 = 417; // us (para el 0)
const unsigned long HALF_PERIOD_2400 = 208; // us (para el 1)

void setup() {
  pinMode(PIN_AUDIO, OUTPUT);
  pinMode(LED_IND, OUTPUT);
  
  Serial.begin(9600); // PC1 -> Arduino
  
  Serial.println(F("--- Modulador FSK Iniciado ---"));
  Serial.println(F("Velocidad: 300 Baudios"));
  Serial.println(F("Estado Reposo: Tono continuo 2400Hz"));
}

void loop() {
  // Verificamos si hay datos desde la PC
  if (Serial.available() > 0) {
    char caracter = Serial.read();
    
    // Encendemos LED para indicar transmisión
    digitalWrite(LED_IND, HIGH);
    
    // Serial feedback
    Serial.print(F("Enviando: "));
    Serial.println(caracter);
    
    // Modulamos el caracter en FSK
    enviarByteComoFSK(caracter);
    
    digitalWrite(LED_IND, LOW);
  } 
  else {
    // --- ESTADO DE REPOSO (IDLE) ---
    // Mantenemos la línea en Mark (1 lógico / 2400 Hz).
    // Generamos ciclo a ciclo para poder interrumpir rápido si llega un dato.
    digitalWrite(PIN_AUDIO, HIGH);
    delayMicroseconds(HALF_PERIOD_2400);
    digitalWrite(PIN_AUDIO, LOW);
    delayMicroseconds(HALF_PERIOD_2400);
  }
}

// --- Función para descomponer un byte en protocolo UART y modularlo ---
void enviarByteComoFSK(byte dato) {
  // Protocolo Serial estándar (8N1):
  // Bit start --> 0
  enviarBitFSK(0);
  
  // 8 bits de datos
  for (int i = 0; i < 8; i++) {
    bool bitActual = bitRead(dato, i);
    enviarBitFSK(bitActual);
  }
  
  // Stop bit --> 1
  enviarBitFSK(1);
}

// --- Función que genera la onda cuadrada de audio por la duración de un bit ---
void enviarBitFSK(bool bitVal) {
  /* A 300 baudios, el tiempo de bit es aprox 3333us. */
  
  if (bitVal == 0) {
    // Generar 1200 Hz (4 ciclos completos en ~3333us)
    for (int i = 0; i < 4; i++) {
      digitalWrite(PIN_AUDIO, HIGH);
      delayMicroseconds(HALF_PERIOD_1200);
      digitalWrite(PIN_AUDIO, LOW);
      delayMicroseconds(HALF_PERIOD_1200);
    }
  } 
  else {
    // Generar 2400 Hz (8 ciclos completos en ~3333us)
    for (int i = 0; i < 8; i++) {
      digitalWrite(PIN_AUDIO, HIGH);
      delayMicroseconds(HALF_PERIOD_2400);
      digitalWrite(PIN_AUDIO, LOW);
      delayMicroseconds(HALF_PERIOD_2400);
    }
  }
}