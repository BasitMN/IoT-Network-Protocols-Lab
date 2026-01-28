#!/usr/bin/env python3
"""
MQTT Listener (Subscriber)
==========================
This script subscribes to an MQTT topic and receives messages from the broker.
It works together with mqtt-broadcaster.py which publishes to the same topic.

MQTT Publish/Subscribe Pattern:
- Broadcaster (mqtt-broadcaster.py): Sends messages to a topic on the broker
- Listener (this file): Subscribes to the topic and receives messages
- Broker (mosquitto): Routes messages from publishers to subscribers

Usage:
    python mqtt-listener.py
    Messages published to 'chat/demo' will appear in the console.
    Press Ctrl-C to exit.

See also: mqtt-broadcaster.py for the publisher side of this demo.
"""
import time
import paho.mqtt.client as mqtt  # Paho MQTT client library for Python

# MQTT Broker configuration (must match mqtt-broadcaster.py)
BROKER_HOST = "192.168.2.100"  # Broker IP address
BROKER_PORT = 1883              # Standard MQTT port (unencrypted)
TOPIC = "chat/demo"             # Topic to subscribe to (broadcaster publishes here)
CLIENT_ID = f"listener-{int(time.time())}"  # Unique client ID using timestamp

def on_connect(client, userdata, flags, reason_code, properties=None):
    """
    Callback triggered when connection to MQTT broker is established.
    Unlike the broadcaster, the listener must subscribe to the topic here.
    
    Args:
        client: The MQTT client instance
        userdata: User data set in Client() (not used here)
        flags: Response flags from the broker
        reason_code: 0 = success, other values = error codes
        properties: MQTT v5 properties (optional)
    """
    if reason_code == 0:
        print(f"[mqtt-listener] connected to {BROKER_HOST}:{BROKER_PORT}")
        # Subscribe to the topic where mqtt-broadcaster.py publishes messages
        client.subscribe(TOPIC, qos=0)
        print(f"[mqtt-listener] subscribed to '{TOPIC}' (Ctrl-C to exit)")
    else:
        print(f"[mqtt-listener] connect failed rc={reason_code}")


def on_message(client, userdata, msg):
    """
    Callback triggered when a message is received on a subscribed topic.
    This is called whenever mqtt-broadcaster.py (or any publisher) sends
    a message to the 'chat/demo' topic.
    
    Args:
        client: The MQTT client instance
        userdata: User data set in Client() (not used here)
        msg: The received message (contains topic and payload)
    """
    # Decode the binary payload to string
    text = msg.payload.decode("utf-8", errors="replace")
    print(f"[mqtt-listener] {msg.topic}: {text}")

def main():
    """
    Main function: Creates MQTT client, connects to broker, and listens for messages.
    
    Messages published by mqtt-broadcaster.py (or any client publishing to
    the 'chat/demo' topic) will be received and printed to the console.
    """
    # Create MQTT client with unique ID and protocol version 3.1.1
    client = mqtt.Client(client_id=CLIENT_ID, protocol=mqtt.MQTTv311)
    client.on_connect = on_connect  # Register connection callback
    client.on_message = on_message  # Register message callback (not needed in broadcaster)

    # Connect to broker (same settings as mqtt-broadcaster.py)
    client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)

    try:
        # Block and process network traffic, dispatching callbacks
        # Note: Broadcaster uses loop_start() + input loop instead
        client.loop_forever()
    except KeyboardInterrupt:
        print("\n[mqtt-listener] bye")
    finally:
        client.disconnect()  # Disconnect from broker


if __name__ == "__main__":
    main()
