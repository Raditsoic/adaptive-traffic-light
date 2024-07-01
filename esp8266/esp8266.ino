#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>

const char* ssid = "MI 10";
const char* password = "passwordhotspot";

ESP8266WebServer server(80);

const int R1 = 0;
const int Y1 = 2;
const int G1 = 14;

const int R2 = 4;
const int Y2 = 5;
const int G2 = 16;

const int R3 = 15;
const int Y3 = 13;
const int G3 = 12;

int trafficTimes[2];

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }

  Serial.println("Connected to WiFi");
  Serial.println(WiFi.localIP());

  pinMode(R1, OUTPUT);
  pinMode(Y1, OUTPUT);
  pinMode(G1, OUTPUT);

  pinMode(R2, OUTPUT);
  pinMode(Y2, OUTPUT);
  pinMode(G2, OUTPUT);

  pinMode(R3, OUTPUT);
  pinMode(Y3, OUTPUT);
  pinMode(G3, OUTPUT);

  server.on("/", handleRoot);
  server.begin();
  Serial.println("HTTP server started");
}

void controlTrafficLight() {
  int trafficLightIndex = trafficTimes[1];
  int greenLight = trafficTimes[0];
  if (trafficLightIndex == 1) {
    if(greenLight == 0) {

    } else {
      digitalWrite(G1, 1);
      digitalWrite(R2, 1);
      digitalWrite(R3, 1);
      countdown(greenLight, "Traffic Light 1 Green");
      digitalWrite(G1, 0);
      digitalWrite(R2, 0);
      digitalWrite(R3, 1);
      digitalWrite(Y1, 1);
      digitalWrite(Y2, 1);
      delay(1000);
      digitalWrite(Y1, 0);
      digitalWrite(Y2, 0);
    }
  } else if (trafficLightIndex == 2) {
    if(greenLight == 0) {
    
    } else {
      digitalWrite(R1, 1);
      digitalWrite(R3, 1);
      digitalWrite(G2, 1);
      countdown(greenLight, "Traffic Light 2 Green");
      digitalWrite(G2, 0);
      digitalWrite(R3, 0);
      digitalWrite(R1, 1);
      digitalWrite(Y2, 1);
      digitalWrite(Y3, 1);
      delay(1000);
      digitalWrite(Y2, 0);
      digitalWrite(Y3, 0);
    }
  } else {
    if(greenLight == 0) {
      
    } else {
      digitalWrite(R1, 1);
      digitalWrite(R2, 1);
      digitalWrite(G3, 1);
      countdown(greenLight, "Traffic Light 3 Green");
      digitalWrite(G3, 0);
      digitalWrite(R1, 0);
      digitalWrite(R2, 1);
      digitalWrite(Y1, 1);
      digitalWrite(Y3, 1);
      delay(1000);
      digitalWrite(Y1, 0);
      digitalWrite(Y3, 0);
    }
  }
  
}

void countdown(int seconds, const char* light) {
  for (int i = seconds; i > 0; i--) {
    Serial.print(light);
    Serial.print(": ");
    Serial.print(i);
    Serial.println(" seconds remaining");
    delay(1000);
  }
}

void loop() {
  server.handleClient();
}

void handleRoot() {
  if (server.hasArg("array")) {
    String arrayData = server.arg("array");
    Serial.println("Received array: " + arrayData);

    parseArray(arrayData, trafficTimes);
    server.send(200, "text/plain", "Array received");
    controlTrafficLight();
  }
}

void parseArray(String arrayStr, int values[2]) {
  int index = 0;
  int row = 0;
  String numStr = "";

  while (index < arrayStr.length()) {
    char c = arrayStr[index];
    if (c == ',') {
      values[row] = numStr.toInt();
      row++;
      numStr = "";
    } else {
      numStr += c;
    }
    index++;
  }
  values[row] = numStr.toInt();
}