#!/usr/bin/env python3
"""
MQTT Broadcaster (Publisher)
============================
This script publishes messages to an MQTT broker.
It works together with mqtt-listener.py which subscribes to the same topic.

MQTT Publish/Subscribe Pattern:
- Broadcaster (this file): Sends messages to a topic on the broker
- Listener (mqtt-listener.py): Subscribes to the topic and receives messages
- Broker (mosquitto): Routes messages from publishers to subscribers

Usage:
    python mqtt-broadcaster.py
    Then type messages and press Enter to publish them.
    Type 'quit' or press Ctrl-C to exit.

See also: mqtt-listener.py for the subscriber side of this demo.
"""
import sys
import time
import paho.mqtt.client as mqtt  # Paho MQTT client library for Python

# MQTT Broker configuration (must match mqtt-listener.py)
BROKER_HOST = "192.168.2.100"  # Broker IP address
BROKER_PORT = 1883              # Standard MQTT port (unencrypted)
TOPIC = "chat/demo"             # Topic to publish to (listeners subscribe to this)
CLIENT_ID = f"broadcaster-{int(time.time())}"  # Unique client ID using timestamp

def on_connect(client, userdata, flags, reason_code, properties=None):
    """
    Callback triggered when connection to MQTT broker is established.
    Unlike the listener, the broadcaster doesn't need to subscribe to any topic.
    
    Args:
        client: The MQTT client instance
        userdata: User data set in Client() (not used here)
        flags: Response flags from the broker
        reason_code: 0 = success, other values = error codes
        properties: MQTT v5 properties (optional)
    """
    if reason_code == 0:
        print(f"[mqtt-broadcaster] connected to {BROKER_HOST}:{BROKER_PORT}")
    else:
        print(f"[mqtt-broadcaster] connect failed rc={reason_code}")

def main():
    """
    Main function: Creates MQTT client, connects to broker, and publishes user input.
    
    The published messages will be received by mqtt-listener.py (or any client
    subscribed to the same topic 'chat/demo').
    """
    # Create MQTT client with unique ID and protocol version 3.1.1
    client = mqtt.Client(client_id=CLIENT_ID, protocol=mqtt.MQTTv311)
    client.on_connect = on_connect  # Register connection callback

    # Connect to broker (same settings as mqtt-listener.py)
    client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
    
    # Start background thread for network traffic
    # Note: Listener uses loop_forever() instead, which blocks
    client.loop_start()

    print(f"[mqtt-broadcaster] publishing to topic '{TOPIC}'")
    print("[mqtt-broadcaster] type messages; 'quit' to exit; Ctrl-C to exit")

    try:
        # Main input loop - read user input and publish to broker
        while True:
            try:
                line = input("> ")
            except EOFError:
                break

            if line.strip().lower() == "quit":
                break

            # Publish message to the topic
            # QoS 0 = "fire and forget" (no delivery guarantee)
            # retain=False = don't store message for new subscribers
            payload = line
            info = client.publish(TOPIC, payload=payload, qos=0, retain=False)
            info.wait_for_publish()  # Wait for message to be sent
    except KeyboardInterrupt:
        pass
    finally:
        print("\n[mqtt-broadcaster] bye")
        client.loop_stop()   # Stop background network thread
        client.disconnect()  # Disconnect from broker


if __name__ == "__main__":
    main()
