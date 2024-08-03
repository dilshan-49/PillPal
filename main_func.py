from machine import Pin, PWM, deepsleep
from utime import sleep
import urequests
import ujson
from esp32_gpio_lcd import GpioLcd
import myfirebase as firebase
from firebase_auth import FirebaseAuth,AuthError
import socket
import ure
import network
import gc

update_button=Pin(34, Pin.IN, Pin.PULL_DOWN)

#############################################################################
lcd = GpioLcd(rs_pin=Pin(32),
            enable_pin=Pin(33),
            d4_pin=Pin(25),
            d5_pin=Pin(26),
            d6_pin=Pin(27),
            d7_pin=Pin(14),
            backlight_pin=Pin(12),
            num_lines=4, num_columns=20)

##############################################################################

############## Motor Pins ###########################
m1o=Pin(23,Pin.OUT)
m1c=Pin(22,Pin.OUT)
m2o=Pin(21,Pin.OUT)
m2c=Pin(19,Pin.OUT)
m3o=Pin(18,Pin.OUT)
m3c=Pin(17,Pin.OUT)
m4o=Pin(16,Pin.OUT)
m4c=Pin(4,Pin.OUT)

def open_container():
    print("Opening Containers")
    m1o.value(1)
    m2o.value(1)
    m3o.value(1)
    m4o.value(1)

def close_container():
    print('closing Containers')
    m1c.value(1)
    m2c.value(1)
    m3c.value(1)
    m4c.value(1)


def stop_motor():
    m1o.value(0)
    m1c.value(0)
    m2o.value(0)
    m2c.value(0)
    m3o.value(0)
    m3c.value(0)
    m4o.value(0)
    m4c.value(0)
####################################################

#########Setting times ############
morning_1=(0,30)
morning_2=(9,00)

afternoon_1=(12,30)
afternoon_2=(14,30)

night_1=(18,00)
night_2=(23,30)   

####################################
class Button:
    def __init__(self, pin,name):
        self.name = name
        self.button = Pin(pin, Pin.IN, Pin.PULL_DOWN)
        self.pressed = False
        self.button.irq(trigger=Pin.IRQ_RISING, handler=self.button_pressed)


    def button_pressed(self,pin):
        self.pressed = True
        print('Pressed',self.name)
        lcd.clear()

    def is_pressed(self):
        if self.pressed:
            self.pressed = False
            return True
        return False
##############################################################################

def put_to_deepsleep(pin):
    deepsleep()


##############################################################################
buzzer = PWM(Pin(13)) 



# Play the melody
def ring():
    C6 = 1109
    E5 = 659
    C5 = 554
    G6 = 1661
    B5 = 988
    G5 = 830
    E6=1318
    # Define the melody
    melody = [E5,G5,B5,C6,E6,C6,B5,G5]
    for note in melody:
        buzzer.freq(note)  # Set the frequency of the buzzer
        buzzer.duty(512)  # Turn on the buzzer
        sleep(0.2)  # Wait for a while
        buzzer.duty(0)  # Turn off the buzzer
        sleep(0.075)  # Wait for a while

#################################################################################

def url_encode(string):

        encoded_string = ""

        for character in string:
           if character.isalpha() or character.isdigit():
               encoded_string += character
           else:
               encoded_string += f"%{ord(character):x}"

        return encoded_string
##################################################################################

def retrieve_data(email,password):
    lcd.clear()
    lcd.putstr('Updating data')
    print('Updating Data')
    if firebase.FIREBASE_GLOBAL_VAR.ACCESS_TOKEN is None:
        auth=FirebaseAuth(firebase.FIREBASE_GLOBAL_VAR.API)
        auth.sign_in(email,password)
        access_token=(auth.session.access_token)
        firebase.set_access_token(access_token)
        firebase.FIREBASE_GLOBAL_VAR.UID=auth.user['uid']
    data={}
    slots=["slot1","slot2","slot3","slot4"]
    for slot in slots:
        data[slot]=firebase.get(slot)
    with open('data.txt', 'w') as f:
        ujson.dump(data,f)
    del data
    gc.collect()
    print("Successfully Updated Data")

    

##################################################################################

def send_message(phone_number, api_key, message):
    encoded_msg=url_encode(message)
  #set your host URL
    url = 'https://api.callmebot.com/whatsapp.php?phone='+phone_number+'&text='+encoded_msg+'&apikey='+api_key

  #make the request
    if connect_to_wifi():
        response = urequests.get(url)
    #check if it was successful
        if response.status_code == 200:
            print('Success!')
        else:
            print('Error')
            print(response.text)
        del response
        del encoded_msg
        gc.collect()
    else:
        lcd.putstr('Network Error')

####################################################################################

user_button=Button(35,'user')

motor_button=Button(2,'motor')

#####################    Connect to Wi-Fi     #######################################

def connect_to_wifi():
    wlan = network.WLAN(network.STA_IF)
    if wlan.isconnected():
        return True
    else:
        wlan.active(True)
        with open('WIFI_CRED.txt') as f:
            wifi_credentials=ujson.load(f)
        # Scan for available networks
        available_networks = wlan.scan()

        # Convert list of tuples to list of SSIDs
        available_ssids = [str(ssid[0], 'utf-8') for ssid in available_networks]
        for ssid, password in wifi_credentials.items():
            if ssid in available_ssids:
                print('Trying to connect to:', ssid)
                wlan.connect(ssid, password)

                # Check for successful connection
                for _ in range(10):
                    if wlan.isconnected():
                        lcd.clear()
                        lcd.putstr('Connected to:'+ssid)
                        print('Connected to:', ssid)
                        del available_ssids,wifi_credentials
                        gc.collect()
                        return True
                    sleep(1)
        lcd.clear()
        lcd.putstr('Could not connect to any network')
        print('Could not connect to any network')
        return False
    
