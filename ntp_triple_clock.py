import time
from datetime import datetime
import tm1637


def init_displays():
    try:
        d_time = tm1637.TM1637(clk=23, dio=25)
        d_secs = tm1637.TM1637(clk=24, dio=22)
        d_date = tm1637.TM1637(clk=27, dio=17)

        # Set brightness (0 to 7)
        d_time.brightness(4)
        d_secs.brightness(4)
        d_date.brightness(4)
        return d_time, d_secs, d_date
    except Exception as e:
        print(f"Hardware init error: {e}")
        time.sleep(2)
        return init_displays()


disp_time, disp_seconds, disp_date = init_displays()
print("NTP 3-Display Clock Sync Service Engaged.")

while True:
    try:
        start_time = time.time()
        now = datetime.now()

        # 1. Determine AM/PM and 12-Hour Format
        is_pm = now.hour >= 12
        ampm_char = "P" if is_pm else "A"

        hour_12 = now.hour % 12
        if hour_12 == 0:
            hour_12 = 12

        blink_state = now.second % 2 == 0

        # 2. Update Display 1: Hours & Minutes (e.g., " 2:35")
        hour_minute_str = f"{hour_12:2d}{now.minute:02d}"
        disp_time.show(hour_minute_str, blink_state)
        time.sleep(0.04)  # Bus-settling delay

        # 3. Update Display 2: Seconds + AM/PM on far right (e.g., "45 P")
        seconds_str = f"{now.second:02d} {ampm_char}"
        disp_seconds.show(seconds_str, False)
        time.sleep(0.04)  # Bus-settling delay

        # 4. Update Display 3: Date (e.g., "09:12")
        date_str = f"{now.month:02d}{now.day:02d}"
        disp_date.show(date_str, True)

        # 5. Dynamic sleep to prevent frame drift
        elapsed = time.time() - start_time
        target_delay = 0.2
        remaining_sleep = target_delay - elapsed

        if remaining_sleep > 0:
            time.sleep(remaining_sleep)

    except Exception as e:
        print(f"Bus recovery triggered: {e}")
        time.sleep(0.5)
        disp_time, disp_seconds, disp_date = init_displays()
