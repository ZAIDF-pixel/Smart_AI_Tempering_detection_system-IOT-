#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// ---------- WIFI SETTINGS ----------
const char* ssid = "A15";
const char* password = "123456789";

// Laptop server address
const char* serverURL = "http://10.127.136.251:8000/sensor";

// ---------- PIN CONFIGURATION ----------
#define VIBRATION_PIN 27
#define DOOR_PIN 26

#define RED_LED 19
#define GREEN_LED 18
#define BUZZER_PIN 25

#define SDA_PIN 21
#define SCL_PIN 22

// ---------- SENSOR LOGIC ----------
#define DOOR_OPEN_LEVEL HIGH
#define VIBRATION_ACTIVE HIGH

// ---------- OLED SETTINGS ----------
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1

Adafruit_SSD1306 display(
  SCREEN_WIDTH,
  SCREEN_HEIGHT,
  &Wire,
  OLED_RESET
);

// ---------- VARIABLES ----------
int vibration = 0;
int door = 0;
int alarmValue = 0;

int previousAlarm = -1;

unsigned long lastSendTime = 0;
unsigned long lastWiFiCheck = 0;
unsigned long lastVibrationTime = 0;
unsigned long lastOledVibrationTime = 0;

const unsigned long sendInterval = 250;
const unsigned long wifiCheckInterval = 10000;
const unsigned long alarmHoldTime = 1000;
const unsigned long oledHoldTime = 5000;

// ---------- WIFI CONNECTION ----------
void connectWiFi() {
  Serial.println();
  Serial.println("Connecting to WiFi...");

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  unsigned long startTime = millis();

  while (WiFi.status() != WL_CONNECTED &&
         millis() - startTime < 20000) {
    delay(500);
    Serial.print(".");
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println();
    Serial.println("WiFi Connected!");
    Serial.print("ESP32 IP Address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println();
    Serial.println("WiFi Connection Failed!");
  }
}

// ---------- OLED DISPLAY ----------
void showDisplay(int vibrationValue, int doorValue) {
  display.clearDisplay();

  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);

  display.setCursor(0, 0);
  display.println("ATM SECURITY SYSTEM");

  display.drawLine(0, 12, 128, 12, SSD1306_WHITE);

  display.setCursor(0, 20);
  display.print("Vibration: ");
  display.println(vibrationValue);

  display.setCursor(0, 32);
  display.print("Door: ");
  display.println(doorValue == 1 ? "OPEN" : "CLOSED");

  display.setCursor(0, 46);

  // OLED warning depends ONLY on vibration
  if (lastOledVibrationTime != 0 &&
      millis() - lastOledVibrationTime < oledHoldTime) {
    display.println("WARNING: TAMPERING!");
  } else {
    display.println("STATUS: NORMAL");
  }

  display.display();
}

// ---------- OUTPUT CONTROL ----------
// Original LED and buzzer logic unchanged
void controlOutputs(int alarmStatus) {
  if (alarmStatus == 1) {
    digitalWrite(RED_LED, HIGH);
    digitalWrite(GREEN_LED, LOW);
    digitalWrite(BUZZER_PIN, HIGH);
  } else {
    digitalWrite(RED_LED, LOW);
    digitalWrite(GREEN_LED, HIGH);
    digitalWrite(BUZZER_PIN, LOW);
  }
}

// ---------- SEND DATA TO PYTHON SERVER ----------
void sendSensorData(int vibrationValue, int doorValue, int alarmStatus) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected. Data not sent.");
    return;
  }

  HTTPClient http;

  http.setConnectTimeout(300);
  http.setTimeout(300);

  http.begin(serverURL);
  http.addHeader("Content-Type", "application/json");

  String json = "{";
  json += "\"vibration\":" + String(vibrationValue);
  json += ",\"door\":" + String(doorValue);
  json += ",\"alarm\":" + String(alarmStatus);
  json += "}";

  int httpResponseCode = http.POST(json);

  Serial.print("HTTP Response: ");
  Serial.println(httpResponseCode);

  if (httpResponseCode > 0) {
    Serial.println("Data sent successfully.");
  } else {
    Serial.println("Error sending data.");
  }

  http.end();
}

// ---------- SETUP ----------
void setup() {
  Serial.begin(115200);

  pinMode(VIBRATION_PIN, INPUT_PULLUP);
  pinMode(DOOR_PIN, INPUT_PULLUP);

  pinMode(RED_LED, OUTPUT);
  pinMode(GREEN_LED, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);

  digitalWrite(RED_LED, LOW);
  digitalWrite(GREEN_LED, HIGH);
  digitalWrite(BUZZER_PIN, LOW);

  Wire.begin(SDA_PIN, SCL_PIN);

  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println("OLED initialization failed!");
  } else {
    display.clearDisplay();
    display.setTextSize(1);
    display.setTextColor(SSD1306_WHITE);
    display.setCursor(0, 20);
    display.println("ATM SECURITY SYSTEM");
    display.println("Starting...");
    display.display();
  }

  connectWiFi();
}

// ---------- MAIN LOOP ----------
void loop() {
  int vibrationRaw = digitalRead(VIBRATION_PIN);
  int doorRaw = digitalRead(DOOR_PIN);

  vibration = (vibrationRaw == VIBRATION_ACTIVE) ? 1 : 0;
  door = (doorRaw == DOOR_OPEN_LEVEL) ? 1 : 0;

  // Update timers whenever vibration is detected
  if (vibration == 1) {
    lastVibrationTime = millis();
    lastOledVibrationTime = millis();
  }

  bool vibrationAlarm =
    (lastVibrationTime != 0 &&
     millis() - lastVibrationTime <= alarmHoldTime);

  // Original LED and buzzer alarm calculation unchanged
  bool doorAlarm = (door == 1);
  alarmValue = (vibrationAlarm || doorAlarm) ? 1 : 0;

  // Control LEDs and buzzer using original alarm logic
  controlOutputs(alarmValue);

  // OLED uses its separate 5-second vibration timer
  showDisplay(vibration, door);

  if (alarmValue != previousAlarm) {
    Serial.println("--------------------------");

    Serial.print("Vibration: ");
    Serial.println(vibration);

    Serial.print("Door: ");
    Serial.println(door);

    Serial.print("Alarm: ");
    Serial.println(alarmValue);

    if (alarmValue == 1) {
      Serial.println("WARNING: SUSPICIOUS ACTIVITY!");
    } else {
      Serial.println("ATM STATUS: NORMAL");
    }

    previousAlarm = alarmValue;
  }

  // Send data every second
  // Send sensor data every 250 milliseconds
if (millis() - lastSendTime >= sendInterval) {
  lastSendTime = millis();
  sendSensorData(vibration, door, alarmValue);
}

  // Reconnect WiFi if disconnected
  if (WiFi.status() != WL_CONNECTED &&
      millis() - lastWiFiCheck >= wifiCheckInterval) {
    lastWiFiCheck = millis();

    Serial.println("Reconnecting WiFi...");

    WiFi.disconnect();
    WiFi.begin(ssid, password);
  }

  delay(50);
}