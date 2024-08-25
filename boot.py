from machine import RTC,Pin,reset_cause,wake_reason,deepsleep
from esp32 import wake_on_ext0,wake_on_ext1,WAKEUP_ANY_HIGH
from os import stat
import gc
import ntptime
from utime import sleep,localtime,time
from main_func import *

but_pressed=False

def pressed(pin):
    global but_pressed
    but_pressed=True




wake_on_ext1((update_button,),WAKEUP_ANY_HIGH)
update_button.irq(trigger=Pin.IRQ_RISING, handler=put_to_deepsleep)
lcd.clear()
lcd.putstr("Initializing...")
print("Initializing")
try:
    stat('USER_CRED.txt')
    stat('WIFI_CRED.txt')
except OSError:
    lcd.clear()
    lcd.putstr("Please Configure \nUser Credentials and\n Wi-Fi Credentials")
    print("Please Configure User Credentials and\n Wi-Fi Credentials")
    sleep(2)
    config.start()

with open('USER_CRED.txt', 'r') as f:
    credentials=ujson.load(f)
    user_email=credentials['email']
    user_password=credentials['password']
    del credentials

rtc = RTC()
update_data=False
if reset_cause() == 4:
    print("Deepsleep Reset")
    if wake_reason()==2:
        print("User Button Pressed")
        but_pressed=True
    elif wake_reason()==3:
        print("Update Button Pressed")
        update_data=True
    else:
        print("Woke up from the Timer")
        

lcd.clear()
lcd.putstr("Initializing...")
sleep(1)
if not but_pressed:
    if connect_to_wifi() :
        try:
            if update_data : 
                print("Update Button Pressed")      
                sleep(2)
                retrieve_data(user_email,user_password)
                lcd.clear()
                lcd.putstr('Opening containers')
                open_containers()
                update_button.irq(trigger=Pin.IRQ_RISING, handler=pressed)
                lcd.putstr('\nPress update button after refilling')
                while not but_pressed:
                    sleep(1)
                update_button.irq(handler=None)
                but_pressed=False
                close_containers()
                lcd.putstr('closing containers')
                sleep(0.5)
                stop_motor()
                lcd.clear()
                lcd.putstr("Device will sleep for 30 minutes.Press user button to take medicine")
                wake_on_ext0(user_button, WAKEUP_ANY_HIGH)
                sleep(10)
                deepsleep(1800*60)

            ntptime.settime()
            timezone_sec = 5.5 * 3600
            sec = int(time() + timezone_sec)
            (year, month, day, hours, minutes, seconds, weekday, yearday) = localtime(sec)
            rtc.datetime((year, month, day, 0, hours, minutes, seconds, 0))

            if stat('records.txt')[6]!= 0:
                print('Records available')
                with open('records.txt', 'r') as f:
                    data = [ujson.loads(line) for line in f]
                for record in data:
                    for path,x in record.items():
                        if firebase.FIREBASE_GLOBAL_VAR.ACCESS_TOKEN is None:
                            auth=FirebaseAuth(firebase.FIREBASE_GLOBAL_VAR.API)
                            auth.sign_in(user_email,user_password)
                            access_token=(auth.session.access_token)
                            firebase.FIREBASE_GLOBAL_VAR.UID=auth.user["uid"]
                            firebase.set_access_token(access_token)
                        json_data=ujson.dumps({"fields":x})
                        firebase.create(json_data,path)
            else:
                print("File is empty")
        except AuthError:
            lcd.clear()
            lcd.putstr("Invalid User Credentials")
            config.start()
            if update_data :       
                print("Update Button Pressed")      
                sleep(2)
                retrieve_data(user_email,user_password)
                open_containers()
                lcd.putstr('Opening containers')
                update_button.irq(trigger=Pin.IRQ_RISING, handler=pressed)
                lcd.putstr('\nPress update button after refilling')
                while not but_pressed():
                    sleep(1)
                update_button.irq(handler=None)
                but_pressed=False
                lcd.clear()
                lcd.putstr('Closing Containers')
                close_containers()
                lcd.clear()
                lcd.putstr("Device will sleep for 30 minutes.Press user button to take medicine")
                wake_on_ext0(user_button, WAKEUP_ANY_HIGH)
                sleep(10)
                deepsleep(1800*60)

            ntptime.settime()
            timezone_sec = 5.5 * 3600
            sec = int(time() + timezone_sec)
            (year, month, day, hours, minutes, seconds, weekday, yearday) = localtime(sec)
            rtc.datetime((year, month, day, 0, hours, minutes, seconds, 0))

            if stat('records.txt').st_size != 0:
                with open('records.txt', 'r') as f:
                    data = [ujson.loads(line) for line in f]
                for record in data:
                    if firebase.FIREBASE_GLOBAL_VAR.ACCESS_TOKEN is None:
                        auth=FirebaseAuth(firebase.FIREBASE_GLOBAL_VAR.API)
                        auth.sign_in(email,password)
                        access_token=(auth.session.access_token)
                        firebase.FIREBASE_GLOBAL_VAR.UID=auth.user["uid"]
                        firebase.set_access_token(access_token)
                    firebase.create(record)
                    del data
            else:
                print("File is empty")

    else:
        while True:
            lcd.clear()
            lcd.putstr("Please check your connection and reboot device! Contact Service for Help.")
            sleep(2)
            lcd.clear()
            lcd.putstr("Press User Button for configurations.")
            sleep(2)
            user_button.irq(trigger=Pin.IRQ_RISING, handler=pressed)
            if but_pressed:
                user_button.irq(handler=None)
                but_pressed=False
                config.start()
                lcd.clear()
                lcd.putstr("Reboot device")
                print("Reboot device")
                while True:
                    sleep(10)




gc.collect()



        