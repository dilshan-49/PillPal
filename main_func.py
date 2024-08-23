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
user_button=Pin(35, Pin.IN, Pin.PULL_DOWN)
motor_button=Pin(15, Pin.IN, Pin.PULL_DOWN)

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

##############################################################################

def put_to_deepsleep(pin):
    deepsleep()



#####################################################

def open_containers():
    m1o.value(1)
    sleep(1.7)
    m1o.value(0)
    sleep(0.3)
    m2o.value(1)
    sleep(1.7)
    m2o.value(0)
    sleep(0.3)
    m3o.value(1)
    sleep(1.7)
    m3o.value(0)
    sleep(0.3)
    m4o.value(1)
    sleep(1.7)
    m4o.value(0)
    sleep(0.3)
   
def close_containers():
    m1c.value(1)
    sleep(1.7)
    m1c.value(0)
    m1o.value(1)
    sleep(0.3)
    m1o.value(0)
    m2c.value(1)
    sleep(1.7)
    m2c.value(0)
    m2o.value(1)
    sleep(0.3)
    m2o.value(0)
    m3c.value(1)
    sleep(1.7)
    m3c.value(0)
    m3o.value(1)
    sleep(0.3)
    m3o.value(0)
    m4c.value(1)
    sleep(1.7)
    m4c.value(0)
    m4o.value(1)
    sleep(0.3)
    m4o.value(0)


def stop_motor():
    m1o.value(0)
    m1c.value(0)
    m2o.value(0)
    m2c.value(0)
    m3o.value(0)
    m3c.value(0)
    m4o.value(0)
    m4c.value(0)

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
    fields=["slot1","slot2","slot3","slot4","times"]
    for field in fields:
        data[field]=firebase.get(field)
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
    
################# User Configurations ###############################################
class Configure:
    def __init__(self) :
        self.ap_ssid = "PillPal"
        self.ap_password = "12345678"
        self.ap_authmode = 3  # WPA2

        self.wlan_ap = network.WLAN(network.AP_IF)
        self.wlan_sta = network.WLAN(network.STA_IF)

        self.server_socket = None


    def send_response(self, client, content, status_code=200):
        status_line = "HTTP/1.1 {} {}\r\n".format(status_code, "OK" if status_code == 200 else "Bad Request")
        headers = "Content-Type: text/html\r\n"
        headers += "Content-Length: {}\r\n".format(len(content))
        response = status_line + headers + "\r\n" + content

        client.sendall(response.encode('utf-8'))
        client.close()
    
    def send_file(self, client, file_path,data=None):
        try:
            with open(file_path, 'r') as file:
                content = file.read()
            if data:
                content = content.replace('{{ ssid_options }}', data)
            self.send_response(client, content)
            content=None
            data=None
        except OSError:
            # File not found, or other error, send a 404 response
            self.send_response(client, "404: File Not Found", status_code=404)


    def handle_root(self,client):
        self.send_file(client, 'web/index.html')

    def handle_user_credentials(self,client):
        self.send_file(client, 'web/user.html')


    def handle_wifi_credentials(self,client):
        self.wlan_sta.active(True)
        ssids = sorted(ssid.decode('utf-8') for ssid, *_ in self.wlan_sta.scan())
        ssid_options = ''
        for ssid in ssids:
            ssid_options += '<option value="{}">{}</option>'.format(ssid, ssid)
        self.send_file(client, 'web/wifi.html', ssid_options)

    def handle_configure_user(self,client, request):
        match = ure.search("email=([^&]*)&password=([^&]*)&mobile=([^&]*)&api=(.*)", request)
        print(match)
        
        if match:
            email = match.group(1).decode("utf-8").replace("%3F", "?").replace("%21", "!").replace("%40","@")
            password = match.group(2).decode("utf-8").replace("%3F", "?").replace("%21", "!").replace("%40","@")
            mobile=match.group(3).decode("utf-8").replace("%2B","+")
            api = match.group(4).decode("utf-8")

            if api=='' and mobile=='':
                with open("USER_CRED.txt","r+") as f:
                    data=ujson.load(f)
                    data['email']=email
                    data['password']=password

            elif api=='':
                with open("USER_CRED.txt","r+") as f:
                    data=ujson.load(f)
                    data['email']=email
                    data['password']=password
                    data['mobile']=mobile

            elif mobile=='':
                with open("USER_CRED.txt","r+") as f:
                    data=ujson.load(f)
                    data['email']=email
                    data['password']=password
                    data['api']=api
            else:
                data={"email":email,"password":password,"api":api,"mobile":mobile}
                
            with open("USER_CRED.txt","w") as f:
                ujson.dump(data,f)
            lcd.clear()
            lcd.putstr("Successfully saved User Data")
            html_content = """
                            <html>
                            <head>
                                <meta charset="UTF-8">
                                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                                <title>Success</title>
                                <style>
                                    body {
                                        font-family: Georgia, serif;
                                        background-color: #e6e6fa;
                                        color: #333;
                                        display: flex;
                                        flex-direction: column;
                                        align-items: center;
                                        justify-content: center;
                                        height: 100vh;
                                        margin: 0;
                                        padding: 20px;
                                        box-sizing: border-box;
                                    }
                                    h1 {
                                        color: #6a5acd;
                                        text-align: center;
                                        font-size: 24px;
                                    }
                                    h2 {
                                        text-align: center;
                                        font-size: 24px;
                                    }
                                </style>
                            </head>
                            <body>
                                <h1>Success</h1>
                                <h2>User Credentials saved. Reboot the device if both Configurations done!</h2>
                            </body>
                            </html>
                        """
            self.send_response(client, html_content)

        else:
            html_content="""
                                <head>
                                    <title>Error</title>
                                    <style>
                                        body {
                                            font-family: Georgia, serif;
                                            background-color: #e6e6fa;
                                            color: #333;
                                            display: flex;
                                            flex-direction: column;
                                            align-items: center;
                                            justify-content: center;
                                            height: 100vh;
                                            margin: 0;
                                            padding: 20px;
                                            box-sizing: border-box;
                                        }
                                        h1 {
                                            color: #6a5acd;
                                            text-align: center;
                                            font-size: 32px;
                                        }
                                        h2 {
                                            text-align: center;
                                            font-size: 28px;                                        
                                        }
                                    </style>
                                </head>
                                <body>
                                    <h1>Failure</h1>
                                    <h2>Some problems were encountered while trying to save data.Please try again</h2>
                                </body>
                                </html>
                                """
            self.send_response(client,html_content, status_code=400)
            lcd.clear()
            lcd.putstr("Failed to Save User Credentials")

        sleep(2)
        lcd.clear

    def handle_configure_wifi(self,client, request):
        match = ure.search("ssid=([^&]*)&wifi_password=(.*)", request)
        if match:
            print(match)
            wifi_ssid = match.group(1).decode("utf-8").replace("%3F", "?").replace("%21", "!").replace("%40","@").replace("%20"," ").replace("%27","'").replace("%2D","-").replace("+"," ")
            wifi_password = match.group(2).decode("utf-8").replace("%3F", "?").replace("%21", "!").replace("%20"," ").replace("%40","@").replace("%2D","-")
            try:
                with open("WIFI_CRED.txt","r+") as f:
                    data = ujson.load(f)
                    data[wifi_ssid] = wifi_password
                    f.seek(0)
                    ujson.dump(data,f)
            except OSError:
                data={}
                data[wifi_ssid]=wifi_password
                with open("WIFI_CRED.txt","w") as f:
                    ujson.dump(data,f)
                    del request,match,data
                    gc.collect()

            html_content = """
                            <html>
                            <head>
                                <meta charset="UTF-8">
                                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                                <title>Success</title>
                                <style>
                                    body {
                                        font-family: Georgia, serif;
                                        background-color: #e6e6fa;
                                        color: #333;
                                        display: flex;
                                        flex-direction: column;
                                        align-items: center;
                                        justify-content: center;
                                        height: 100vh;
                                        margin: 0;
                                        padding: 20px;
                                        box-sizing: border-box;
                                    }
                                    h1 {
                                        color: #6a5acd;
                                        text-align: center;
                                        font-size: 24px;
                                    }
                                    h2 {
                                        text-align: center;
                                        font-size: 24px;
                                    }
                                </style>
                            </head>
                            <body>
                                <h1>Success</h1>
                                <h2>Wifi Configuration saved. Reboot the device if both Configurations done!</h2>
                            </body>
                            </html>
                        """

            self.send_response(client, html_content)
            lcd.clear()
            lcd.putstr("Succesfully Saved\nWi-Fi Credentials")

        else:
            html_content="""
                                <head>
                                    <title>Error</title>
                                    <style>
                                        body {
                                            font-family: Georgia, serif;
                                            background-color: #e6e6fa;
                                            color: #333;
                                            display: flex;
                                            flex-direction: column;
                                            align-items: center;
                                            justify-content: center;
                                            height: 100vh;
                                            margin: 0;
                                            padding: 20px;
                                            box-sizing: border-box;
                                        }
                                        h1 {
                                            color: #6a5acd;
                                            text-align: center;
                                            font-size: 32px;
                                        }
                                        h2 {
                                            text-align: center;
                                            font-size: 28px;                                        
                                        }
                                    </style>
                                </head>
                                <body>
                                    <h1>Failure</h1>
                                    <h2>Some problems were encountered while trying to save data.Please try again</h2>
                                </body>
                                </html>
                                """
            self.send_response(client,html_content, status_code=400)
            lcd.clear()
            lcd.putstr("Failed to Save Wi-Fi Credentials")
        del html_content
        gc.collect()
        sleep(2)
        lcd.clear

        
    def handle_not_found(self, client, url):
        self.send_response(client, "Path not found: {}".format(url), status_code=404)
        

    def stop(self):
        if self.server_socket:
            self.server_socket.close()
            del self.server_socket
            
    def start(self,port=80):

        addr = socket.getaddrinfo('0.0.0.0', port)[0][-1]

        self.stop()

        self.wlan_sta.active(True)
        self.wlan_ap.active(True)

        self.wlan_ap.config(essid=self.ap_ssid, password=self.ap_password, authmode=self.ap_authmode)

        lcd.clear()
        lcd.putstr("Connect to PillPal  from your Device")
        self.server_socket = socket.socket()
        self.server_socket.bind(addr)
        self.server_socket.listen(1)
        
        
        x=True
        while True:
            client, addr = self.server_socket.accept()
            print('client connected from', addr)
            if x:
                lcd.clear()
                lcd.putstr("Open PillPall and go to Configure")
                sleep(5)
                x=False
            lcd.clear()
            lcd.putstr("Once Configuration  is Done, Reboot the device")
            try:
                client.settimeout(7.0)
                
                request = b""
                try:
                    while "\r\n\r\n" not in request:
                        request += client.recv(1024)
                except OSError:
                    pass

                # Handle form data from Safari on macOS and iOS; it sends \r\n\r\nssid=<ssid>&password=<password>
                try:
                    request += client.recv(1024)
                    print(client.recv(1024))
                    print("Received form data after \\r\\n\\r\\n(i.e. from Safari on macOS or iOS)")
                except OSError:
                    pass

                print("Request is: {}".format(request))
                
                match = ure.search("(GET|POST) /(.*?)(?:\\?.*?)? HTTP", request)
                if match:
                    path = match.group(2)
                    try:
                        path=match.group(2).decode("utf-8").rstrip("/")
                    except Exception:
                        path=match.group(2).rstrip("/")
                print("URL is {}".format(path))

                
                if path == 'user':
                    self.handle_user_credentials(client)
                elif path == 'wifi':
                    self.handle_wifi_credentials(client)
                elif path == 'configure_user':
                    self.handle_configure_user(client, request)
                elif path == 'configure_wifi':
                    self.handle_configure_wifi(client, request)
                elif path =="" :
                    self.handle_root(client)
                else:
                    self.handle_not_found(client, path)

            except Exception as e:
                print(e)
                lcd.putstr("Error Occured.Reboot and Try again")
                    
            finally:
                client.close()
                gc.collect()

config=Configure()