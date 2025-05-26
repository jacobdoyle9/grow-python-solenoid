import atexit
import threading
import time

import RPi.GPIO as GPIO

VALVE_1_PIN = 17
VALVE_2_PIN = 27
VALVE_3_PIN = 22


global_lock = threading.Lock()


class Valve(object):
    """Grow valve driver."""

    def __init__(self, channel=1):
        """Create a new valve.

        Uses soft PWM to drive a Grow valve.

        :param channel: One of 1, 2 or 3.

        """

        self._gpio_pin = [VALVE_1_PIN, VALVE_2_PIN, VALVE_3_PIN][channel - 1]

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self._gpio_pin, GPIO.OUT, initial=GPIO.LOW)

        self._timeout = None

        atexit.register(self._cleanup)

    def _cleanup(self):
        """Clean up GPIO on exit."""
        self.off()
        GPIO.setup(self._gpio_pin, GPIO.IN)

    def on(self):
        """Turn the valve ON (energize solenoid)."""
        GPIO.output(self._gpio_pin, GPIO.HIGH)

    def off(self):
        """Turn the valve OFF (de-energize solenoid)."""
        GPIO.output(self._gpio_pin, GPIO.LOW)

    def stop(self):
        """Alias for turning the valve off and cancelling timers."""
        if self._timeout is not None:
            self._timeout.cancel()
            self._timeout = None
        self.off()

    def dose(self, timeout=1.0, blocking=True, force=False):
        """Open the valve for a fixed time.

        :param timeout: Time in seconds to keep the valve open.
        :param blocking: If True, waits for the valve to close.
        :param force: If True, overrides previous dose timer.
        :return: True if activated, False otherwise.
        """
        if blocking:
            self.on()
            time.sleep(timeout)
            self.off()
            return True
        else:
            if self._timeout is not None and self._timeout.is_alive():
                if force:
                    self._timeout.cancel()
                else:
                    return False  # Already running and not forced

            self.on()
            self._timeout = threading.Timer(timeout, self.off)
            self._timeout.start()
            return True