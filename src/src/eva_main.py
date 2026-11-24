
"""
EVA - Empowered Vigilant Assistant
Smart Wearable Personal Safety System

Hardware:
- AI Thinker A9G GSM/GPS Module
- Emergency Push Button
- Status LED
- 3.7V Rechargeable Battery

Firmware: MicroPython
IDE: Thonny

Features:
- Emergency SMS and Voice Call
- False Alarm Cancellation
- Geofence Mode Toggle
- Periodic Location Alerts
- LED Status Indications

NOTE:
This version uses a predefined demo location.
Live GPS coordinate retrieval and geofence boundary
detection are not implemented in this firmware.
"""

import cellular
import machine
import time
from machine import Pin


# ==================================================
# 1. CONFIGURATION
# ==================================================

# Emergency contact numbers.
# Add your actual numbers locally before testing.
# Do NOT upload personal contact numbers to GitHub.

SMS_NUMBERS = []

# Hardware pin configuration
BUTTON_PIN = 29
LED_PIN = 27

# Button press duration (seconds)
TIME_EMERGENCY_MAX = 3.0
TIME_CANCEL_MIN = 3.0
TIME_CANCEL_MAX = 5.0
TIME_GEOFENCE_MIN = 5.0

# Geofence alert interval (3 minutes)
GEOFENCE_CHECK_INTERVAL = 180

# Demo location configuration.
# Replace these values locally with an appropriate
# test location before using the system.

LOCATION_NAME = "Demo Location"
LOCATION_LAT = 0.0
LOCATION_LNG = 0.0

LOCATION_MAPS_LINK = (
    "https://maps.google.com/?q={},{}".format(
        LOCATION_LAT,
        LOCATION_LNG
    )
)


# ==================================================
# 2. GLOBAL VARIABLES
# ==================================================

sms_sent_flag = False

button_press_start = 0
button_was_pressed = False
action_handled = False

GEOFENCE_ENABLED = False
geofence_last_check = 0
geofence_start_time = 0


# ==================================================
# 3. HARDWARE INITIALIZATION
# ==================================================

button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)
led = Pin(LED_PIN, Pin.OUT)


# ==================================================
# 4. SMS EVENT HANDLER
# ==================================================

def sms_handler(event):

    global sms_sent_flag

    if event == cellular.SMS_SENT:
        sms_sent_flag = True
        print("[SMS] Sent confirmation received")

    elif event == cellular.SMS_RECEIVE:
        print("[SMS] Incoming message received")


try:
    cellular.on_sms(sms_handler)
    print("[SYSTEM] SMS handler registered")

except Exception as error:
    print("[ERROR] SMS handler registration failed:", error)


# ==================================================
# 5. LED STATUS FUNCTIONS
# ==================================================

def set_led_idle():
    """Slow blink: 1 Hz - Idle mode"""

    led.value(1 if int(time.time() * 2) % 2 == 0 else 0)


def set_led_geofence_active():
    """Fast blink: 3 Hz - Geofence mode"""

    led.value(1 if int(time.time() * 6) % 2 == 0 else 0)


def set_led_sending():
    """Very fast blink: 5 Hz - SMS transmission"""

    led.value(1 if int(time.time() * 10) % 2 == 0 else 0)


# ==================================================
# 6. SMS COMMUNICATION
# ==================================================

def send_sms_to_all(message):
    """Send an SMS to all configured emergency contacts."""

    global sms_sent_flag

    if not SMS_NUMBERS:
        print("[WARNING] No emergency contacts configured")
        return

    for number in SMS_NUMBERS:

        sms_sent_flag = False

        print("[SMS] Sending message to:", number)

        try:
            cellular.SMS(number, message).send()

            # Wait for SMS confirmation (15-second timeout)
            start_wait = time.time()

            while (
                not sms_sent_flag
                and time.time() - start_wait < 15
            ):
                set_led_sending()
                time.sleep(0.1)

            if sms_sent_flag:
                print("[SMS] Successfully sent to:", number)

            else:
                print("[SMS] Confirmation timeout:", number)

        except Exception as error:
            print("[ERROR] SMS transmission failed:", error)

        time.sleep(1)


# ==================================================
# 7. EMERGENCY ALERT FUNCTIONS
# ==================================================

def send_emergency_sms():
    """Send emergency alert with configured location."""

    message = (
        "EMERGENCY! Need Help. "
        "Location: {}. Maps: {}"
    ).format(
        LOCATION_NAME,
        LOCATION_MAPS_LINK
    )

    print("[EMERGENCY] Sending emergency SMS")
    send_sms_to_all(message)


def send_cancel_sms():
    """Notify emergency contacts that the alert is cancelled."""

    message = (
        "ALERT CANCELLED. Device Safe. "
        "Location: {}. Maps: {}"
    ).format(
        LOCATION_NAME,
        LOCATION_MAPS_LINK
    )

    print("[SYSTEM] Sending cancellation SMS")
    send_sms_to_all(message)


# ==================================================
# 8. EMERGENCY VOICE CALL
# ==================================================

def make_emergency_call():
    """Initiate an emergency call to the first contact."""

    if not SMS_NUMBERS:
        print("[WARNING] No emergency contact configured")
        return

    try:
        emergency_number = SMS_NUMBERS[0]

        print("[CALL] Dialing:", emergency_number)

        cellular.dial(emergency_number)

        time.sleep(5)

        cellular.hangup()

        print("[CALL] Emergency call ended")

    except Exception as error:
        print("[ERROR] Emergency call failed:", error)


# ==================================================
# 9. GEOFENCING FUNCTIONS
# ==================================================

def send_geofence_alert():
    """
    Send periodic location alerts every 3 minutes.

    DEMO IMPLEMENTATION:
    Uses predefined coordinates and does not
    check actual GPS position or boundary crossing.
    """

    elapsed_time = int(time.time() - geofence_start_time)

    minutes = elapsed_time // 60
    seconds = elapsed_time % 60

    message = (
        "GEOFENCE UPDATE. "
        "Location: {}. "
        "Maps: {}. "
        "Active for: {}min {}sec."
    ).format(
        LOCATION_NAME,
        LOCATION_MAPS_LINK,
        minutes,
        seconds
    )

    print("[GEOFENCE] Sending periodic location update")

    send_sms_to_all(message)


def toggle_geofence():
    """Enable or disable geofence monitoring mode."""

    global GEOFENCE_ENABLED
    global geofence_last_check
    global geofence_start_time

    GEOFENCE_ENABLED = not GEOFENCE_ENABLED

    if GEOFENCE_ENABLED:

        geofence_start_time = time.time()
        geofence_last_check = time.time()

        print("[GEOFENCE] ACTIVATED")

        message = (
            "GEOFENCE ACTIVATED. "
            "Location: {}. "
            "Maps: {}. "
            "Updates every 3 minutes."
        ).format(
            LOCATION_NAME,
            LOCATION_MAPS_LINK
        )

        send_sms_to_all(message)

    else:

        print("[GEOFENCE] DEACTIVATED")

        message = (
            "GEOFENCE DEACTIVATED. "
            "Location: {}. Monitoring stopped."
        ).format(LOCATION_NAME)

        send_sms_to_all(message)


# ==================================================
# 10. SYSTEM STARTUP
# ==================================================

print("=" * 50)
print("EVA - EMPOWERED VIGILANT ASSISTANT")
print("=" * 50)

print("Hardware: A9G GSM/GPS Module")
print("Location:", LOCATION_NAME)
print("Geofence Interval: 3 Minutes")

print("-" * 50)

print("BUTTON OPERATIONS:")
print("Press < 3 seconds  : Emergency Alert")
print("Press 3-5 seconds  : Cancel Alert")
print("Press >= 5 seconds : Toggle Geofence")

print("-" * 50)

print("LED INDICATIONS:")
print("Slow Blink         : Idle")
print("Fast Blink         : Geofence Active")
print("Very Fast Blink    : Sending SMS")
print("Solid ON           : Button Pressed")

print("=" * 50)

print("[SYSTEM] Waiting for network registration...")

time.sleep(5)

print("[SYSTEM] EVA is ready!")
print("=" * 50)


# ==================================================
# 11. MAIN CONTROL LOOP
# ==================================================

while True:

    current_time = time.time()

    # Read button state
    # 0 = Pressed
    # 1 = Released

    button_value = button.value()


    # ----------------------------------------------
    # BUTTON PRESSED
    # ----------------------------------------------

    if button_value == 0:

        if not button_was_pressed:

            button_press_start = current_time

            button_was_pressed = True
            action_handled = False

            print("[INPUT] Emergency button pressed")

        duration = current_time - button_press_start

        # Solid LED while button is held
        led.value(1)

        # Check for geofence toggle
        if (
            duration >= TIME_GEOFENCE_MIN
            and not action_handled
        ):

            # Wait until the button is released
            while button.value() == 0:
                time.sleep(0.1)

            print("[INPUT] Long press detected")

            action_handled = True

            toggle_geofence()

            button_was_pressed = False
            button_press_start = 0

            led.value(0)

            time.sleep(0.5)


    # ----------------------------------------------
    # BUTTON RELEASED
    # ----------------------------------------------

    else:

        if button_was_pressed and not action_handled:

            duration = current_time - button_press_start

            print(
                "[INPUT] Button released after {:.1f}s".format(
                    duration
                )
            )

            # Emergency: less than 3 seconds
            if duration < TIME_EMERGENCY_MAX:

                print("[ACTION] EMERGENCY ACTIVATED")

                make_emergency_call()
                send_emergency_sms()

            # Cancellation: 3 to less than 5 seconds
            elif (
                TIME_CANCEL_MIN <= duration < TIME_CANCEL_MAX
            ):

                print("[ACTION] ALERT CANCELLATION")

                send_cancel_sms()

        # Reset button state
        if button_was_pressed:

            button_was_pressed = False
            button_press_start = 0
            action_handled = False

            led.value(0)

            time.sleep(0.5)


    # ----------------------------------------------
    # PERIODIC GEOFENCE ALERT
    # ----------------------------------------------

    if GEOFENCE_ENABLED:

        if (
            current_time - geofence_last_check
            >= GEOFENCE_CHECK_INTERVAL
        ):

            print("[GEOFENCE] Sending periodic alert")

            send_geofence_alert()

            geofence_last_check = time.time()


    # ----------------------------------------------
    # LED STATUS UPDATE
    # ----------------------------------------------

    if not button_was_pressed:

        if GEOFENCE_ENABLED:

            set_led_geofence_active()

        else:

            set_led_idle()


    time.sleep(0.1)
