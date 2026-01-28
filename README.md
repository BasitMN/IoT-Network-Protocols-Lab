# MQTT Broadcaster & Listener Demo

## Varför jag skapade denna instruktion

Jag har tagit fram denna instruktion för att **MQTT publish/subscribe-mönstret är en grundläggande byggsten i IoT-processkedjan**. Inom IoT är förståelsen för hur sensorer, enheter och tjänster kommunicerar med varandra avgörande för att kunna bygga fungerande IoT-system.

I en typisk IoT-arkitektur behöver jag kunna:
- **Samla in data** från sensorer (publisher)
- **Distribuera data** via en meddelandebroker
- **Reagera på data** i mottagande tjänster (subscriber)

Genom att skapa denna steg-för-steg-guide ville jag dokumentera min egen inlärningsprocess och samtidigt ha en referens jag kan återvända till. MQTT är det protokoll som används i allt från smarta hem till industriella IoT-lösningar, så att behärska detta är en viktig kompetens.

---

## Översikt

Denna demo visar **MQTT Publish/Subscribe-mönstret** med två Python-skript:

| Fil | Roll | Beskrivning |
|-----|------|-------------|
| `mqtt-broadcaster.py` | **Publisher** | Skickar meddelanden till brokern |
| `mqtt-listener.py` | **Subscriber** | Tar emot meddelanden från brokern |


---

## Steg-för-steg förlopp

### Steg 1: Konfiguration (gemensam för båda)

Båda skripten använder **samma konfiguration** för att kunna kommunicera:

**mqtt-broadcaster.py:**
```python
BROKER_HOST = "192.168.2.100"  # Broker IP address
BROKER_PORT = 1883              # Standard MQTT port (unencrypted)
TOPIC = "chat/demo"             # Topic to publish to
```

**mqtt-listener.py:**
```python
BROKER_HOST = "192.168.2.100"  # Broker IP address
BROKER_PORT = 1883              # Standard MQTT port (unencrypted)
TOPIC = "chat/demo"             # Topic to subscribe to
```

> ⚠️ **Viktigt:** `TOPIC` måste vara identiskt i båda filerna för att kommunikationen ska fungera!

---

### Steg 2: Skapa MQTT-klient

Båda skripten skapar en MQTT-klient med unikt ID:

**mqtt-broadcaster.py:**
```python
CLIENT_ID = f"broadcaster-{int(time.time())}"
client = mqtt.Client(client_id=CLIENT_ID, protocol=mqtt.MQTTv311)
client.on_connect = on_connect
```

**mqtt-listener.py:**
```python
CLIENT_ID = f"listener-{int(time.time())}"
client = mqtt.Client(client_id=CLIENT_ID, protocol=mqtt.MQTTv311)
client.on_connect = on_connect
client.on_message = on_message  # ← Endast listener behöver denna!
```

> 📝 **Notera:** Listener registrerar en extra callback (`on_message`) för att hantera inkommande meddelanden.

---

### Steg 3: Anslut till brokern

Båda skripten ansluter till samma broker:

```python
client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
```

När anslutningen lyckas triggas `on_connect` callback:

**mqtt-broadcaster.py** - Bara loggar anslutningen:
```python
def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        print(f"[mqtt-broadcaster] connected to {BROKER_HOST}:{BROKER_PORT}")
```

**mqtt-listener.py** - Prenumererar på topic:
```python
def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        print(f"[mqtt-listener] connected to {BROKER_HOST}:{BROKER_PORT}")
        client.subscribe(TOPIC, qos=0)  # ← Prenumerera på topic!
```

---

### Steg 4: Nätverksloop (olika strategier)

**mqtt-broadcaster.py** - Bakgrundsloop + interaktiv input:
```python
client.loop_start()  # Starta bakgrundstråd

while True:
    line = input("> ")       # Vänta på användarinput
    if line.strip().lower() == "quit":
        break
    # ... publicera meddelande
```

**mqtt-listener.py** - Blockerande loop:
```python
client.loop_forever()  # Blockerar och väntar på meddelanden
```

> 💡 **Varför olika?**
> - Broadcaster behöver läsa input → använder `loop_start()` (icke-blockerande)
> - Listener bara väntar på meddelanden → använder `loop_forever()` (blockerande)

---

### Steg 5: Publicera meddelande (Broadcaster)

När användaren skriver ett meddelande:

```python
payload = line
info = client.publish(TOPIC, payload=payload, qos=0, retain=False)
info.wait_for_publish()
```

| Parameter | Värde | Betydelse |
|-----------|-------|-----------|
| `TOPIC` | `"chat/demo"` | Vilken kanal meddelandet skickas till |
| `payload` | Användarens text | Själva meddelandet |
| `qos` | `0` | "Fire and forget" - ingen leveransgaranti |
| `retain` | `False` | Spara inte meddelandet för nya prenumeranter |

---

### Steg 6: Ta emot meddelande (Listener)

När ett meddelande anländer till topic som listener prenumererar på:

```python
def on_message(client, userdata, msg):
    text = msg.payload.decode("utf-8", errors="replace")
    print(f"[mqtt-listener] {msg.topic}: {text}")
```

| Attribut | Beskrivning |
|----------|-------------|
| `msg.topic` | Vilken topic meddelandet kom från |
| `msg.payload` | Meddelandet som bytes |
| `.decode()` | Konverterar bytes → sträng |

---

### Steg 7: Avsluta

**mqtt-broadcaster.py:**
```python
client.loop_stop()   # Stoppa bakgrundstråd
client.disconnect()  # Koppla från broker
```

**mqtt-listener.py:**
```python
# Ctrl-C avbryter loop_forever()
client.disconnect()  # Koppla från broker
```

---

## Komplett flödesdiagram

```
 BROADCASTER                    BROKER                     LISTENER
     │                            │                            │
     │ 1. connect()               │                            │
     │ ─────────────────────────► │                            │
     │                            │     1. connect()           │
     │                            │ ◄───────────────────────── │
     │                            │                            │
     │ 2. on_connect callback     │     2. on_connect callback │
     │    (bara loggar)           │        + subscribe(TOPIC)  │
     │                            │ ◄───────────────────────── │
     │                            │                            │
     │ 3. loop_start()            │     3. loop_forever()      │
     │    + input loop            │        (väntar)            │
     │                            │                            │
     │ 4. publish("Hej!")         │                            │
     │ ─────────────────────────► │                            │
     │                            │ 5. deliver("Hej!")         │
     │                            │ ──────────────────────────►│
     │                            │                            │
     │                            │     6. on_message callback │
     │                            │        → print("Hej!")     │
     │                            │                            │
     │ 7. disconnect()            │     7. disconnect()        │
     │ ─────────────────────────► │ ◄───────────────────────── │
     ▼                            ▼                            ▼
```

---

## Köra demo

### Terminal 1 - Starta listener först:
```bash
python mqtt-listener.py
```

### Terminal 2 - Starta broadcaster:
```bash
python mqtt-broadcaster.py
```

### Testa:
1. Skriv ett meddelande i broadcaster-terminalen
2. Se meddelandet dyka upp i listener-terminalen
3. Skriv `quit` eller tryck `Ctrl-C` för att avsluta

---

## Krav

- Python 3.x
- `paho-mqtt` bibliotek: `pip install paho-mqtt`
- MQTT Broker (t.ex. Mosquitto) på `192.168.2.100:1883`


___________________________________________

# edu-python-in-docker Setup Instructions

> 🐳 **Docker-baserad labbmiljö för IoT-nätverksprotokoll**

---

## 📋 Innehåll

1. [Förberedelser](#1-förberedelser)
2. [Starta Docker-miljön](#2-starta-docker-miljön)
3. [Kontrollera IP-adresser](#3-kontrollera-ip-adresser)
4. [Logga in på Listeners (Klient 1 & 2)](#4-logga-in-på-listeners-klient-1--2)
5. [Logga in på Broadcaster](#5-logga-in-på-broadcaster)
6. [Bygga om maskinerna](#6-bygga-om-maskinerna)

---

## 1. Förberedelser

Klona repot och byt till rätt branch:

```bash
cd ~
cd ws
git clone https://github.com/miwashi-edu/edu-python-in-docker.git
cd edu-python-in-docker
git checkout level-2
```

---

## 2. Starta Docker-miljön

Starta alla containers i bakgrunden:

```bash
docker compose up -d
```

Verifiera att alla containers körs:

```bash
docker ps
```

Du bör se tre containers igång (client1, client2, broadcaster + mosquitto broker).

---

## 3. Kontrollera IP-adresser

Inspektera nätverket för att hitta IP-adresser:

```bash
docker inspect iotnet
```

> 📝 **Tips:** Läs JSON-outputen för att hitta IP-adresserna till respektive container.

---

## 4. Logga in på Listeners (Klient 1 & 2)

### Klient 1 (Listener)

```bash
ssh -p 2223 dev@localhost
```

| Fält | Värde |
|------|-------|
| **Port** | 2223 |
| **Användare** | dev |
| **Lösenord** | dev |

När du är inloggad:

```bash
cd ~/src
pip install paho-mqtt
python mqtt-listener.py
```

---

### Klient 2 (Listener)

Öppna en **ny terminal** och kör:

```bash
ssh -p 2224 dev@localhost
```

| Fält | Värde |
|------|-------|
| **Port** | 2224 |
| **Användare** | dev |
| **Lösenord** | dev |

När du är inloggad:

```bash
cd ~/src
pip install paho-mqtt
python mqtt-listener.py
```

---

## 5. Logga in på Broadcaster

Öppna en **ny terminal** och kör:

```bash
ssh -p 2222 dev@localhost
```

| Fält | Värde |
|------|-------|
| **Port** | 2222 |
| **Användare** | dev |
| **Lösenord** | dev |

När du är inloggad:

```bash
cd ~/src
pip install paho-mqtt
python mqtt-broadcaster.py
```

> ✅ **Nu kan du skriva meddelanden i broadcaster-terminalen och se dem dyka upp i båda listener-terminalerna!**

---

## 6. Bygga om maskinerna

### Alternativ 1: Snabb rebuild

```bash
docker compose up -d --build
```

### Alternativ 2: Full rebuild (utan cache)

```bash
docker compose build --no-cache
docker compose up -d
```

---

## 🔧 Snabbreferens: SSH-portar

| Container | Port | Användare | Lösenord | Roll |
|-----------|------|-----------|----------|------|
| Broadcaster | 2222 | dev | dev | Publisher |
| Client 1 | 2223 | dev | dev | Listener/Subscriber |
| Client 2 | 2224 | dev | dev | Listener/Subscriber |

---

## 🛑 Stoppa miljön

```bash
docker compose down
```

Ta bort allt (inklusive volymer):

```bash
docker compose down -v
```


docker compose build --no-cache
docker compose up -d
