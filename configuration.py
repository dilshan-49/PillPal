import network
import socket
import ure
import time
import ujson


ap_ssid = "PillPal"
ap_password = "12345678"
ap_authmode = 3  # WPA2


wlan_ap = network.WLAN(network.AP_IF)
wlan_sta = network.WLAN(network.STA_IF)

server_socket = None

def send_header(client, status_code=200, content_length=None ):
    client.sendall("HTTP/1.0 {} OK\r\n".format(status_code))
    client.sendall("Content-Type: text/html\r\n")
    if content_length is not None:
      client.sendall("Content-Length: {}\r\n".format(content_length))
    client.sendall("\r\n")
    
def send_response(client, payload, status_code=200):
    content_length = len(payload)
    send_header(client, status_code, content_length)
    if content_length > 0:
        client.sendall(payload)
    client.close()

def handle_root(client):
    send_header(client)
    client.sendall('<html><body>'.encode('utf-8'))
    client.sendall('<h1>Welcome</h1>'.encode('utf-8'))
    client.sendall('<p>Select the configuration page:</p>'.encode('utf-8'))
    client.sendall('<form action="/user"><input type="submit" value="User Configuration"></form>'.encode('utf-8'))
    client.sendall('<form action="/wifi"><input type="submit" value="WiFi Configuration"></form>'.encode('utf-8'))
    client.sendall('</body></html>'.encode('utf-8'))

def handle_user_credentials(client):
    send_header(client)
    client.sendall('<html><body>'.encode('utf-8'))
    client.sendall('<h1>User Configuration</h1>'.encode('utf-8'))
    client.sendall('<form action="/configure_user" method="POST">'.encode('utf-8'))
    client.sendall('<label for="email">Email:</label><br>'.encode('utf-8'))
    client.sendall('<input type="text" id="email" name="email"><br>'.encode('utf-8'))
    client.sendall('<label for="password">Password:</label><br>'.encode('utf-8'))
    client.sendall('<input type="password" id="password" name="password"><br>'.encode('utf-8'))
    client.sendall('<label for="api">API Key:</label><br>'.encode('utf-8'))
    client.sendall('<input type="text" id="api" name="api"><br>'.encode('utf-8'))
    client.sendall('<input type="submit" value="Submit">'.encode('utf-8'))
    client.sendall('</form></body></html>'.encode('utf-8'))


def handle_wifi_credentials(client):
    wlan_sta.active(True)
    ssids = sorted(ssid.decode('utf-8') for ssid, *_ in wlan_sta.scan())
    send_header(client)
    client.sendall('<html><body>'.encode('utf-8'))
    client.sendall('<h1>WiFi Configuration</h1>'.encode('utf-8'))
    client.sendall('<form action="/configure_wifi" method="POST">'.encode('utf-8'))
    client.sendall('<label for="ssid">WiFi SSID:</label><br>'.encode('utf-8'))
    client.sendall('<select id="ssid" name="ssid">'.encode('utf-8'))

    for ssid in ssids:
        client.sendall('<option value="{}">{}</option>'.format(ssid, ssid).encode('utf-8'))

    client.sendall('</select><br><br>'.encode('utf-8'))
    client.sendall('<label for="wifi_password">WiFi Password:</label><br>'.encode('utf-8'))
    client.sendall('<input type="password" id="wifi_password" name="wifi_password"><br>'.encode('utf-8'))
    client.sendall('<input type="submit" value="Submit">'.encode('utf-8'))
    client.sendall('</form></body></html>'.encode('utf-8'))

def handle_configure_user(client, request):
    match = ure.search("email=([^&]*)&password=([^&]*)&api=(.*)", request)
    print(match)
    
    if match:
        email = match.group(1).decode("utf-8").replace("%3F", "?").replace("%21", "!").replace("%40","@")
        password = match.group(2).decode("utf-8").replace("%3F", "?").replace("%21", "!").replace("%40","@")
        api = match.group(3).decode("utf-8")
        with open("USER_CRED.txt","w") as f:
            f.write("{%s:%s:%s}"%(email,password,api))
        client.sendall('<html><body><h1>User Configuration saved</h1></body></html>'.encode('utf-8'))
    else:
        send_response(client,'<html><body><h1>Invalid configuration</h1></body></html>'.encode('utf-8'), status_code=400)

    client.close()

def handle_configure_wifi(client, request):
    match = ure.search("ssid=([^&]*)&wifi_password=(.*)", request)
    if match:
        wifi_ssid = match.group(1).decode("utf-8").replace("%3F", "?").replace("%21", "!")
        wifi_password = match.group(2).decode("utf-8").replace("%3F", "?").replace("%21", "!").replace("%20"," ")
        with open("WIFI_CRED.txt","w") as f:
            f.write("{%s:%s}"%(wifi_ssid,wifi_password))
        client.sendall('<html><body><h1>WiFi Configuration saved</h1></body></html>'.encode('utf-8'))
    else:
        send_response(client,'<html><body><h1>Invalid configuration</h1></body></html>'.encode('utf-8'), status_code=400)

    client.close()

    
def handle_not_found(client, url):
    send_response(client, "Path not found: {}".format(url), status_code=404)
    

def stop():
    global server_socket

    if server_socket:
        server_socket.close()
        server_socket = None
        
def start(port=80):
    global server_socket

    addr = socket.getaddrinfo('0.0.0.0', port)[0][-1]

    stop()

    wlan_sta.active(True)
    wlan_ap.active(True)

    wlan_ap.config(essid=ap_ssid, password=ap_password, authmode=ap_authmode)

    server_socket = socket.socket()
    server_socket.bind(addr)
    server_socket.listen(1)
    
    while True:
        client, addr = server_socket.accept()
        print('client connected from', addr)
        
        try:
            client.settimeout(5.0)

            request = b""
            try:
                while "\r\n\r\n" not in request:
                    request += client.recv(512)
            except OSError:
                pass

            # Handle form data from Safari on macOS and iOS; it sends \r\n\r\nssid=<ssid>&password=<password>
            try:
                request += client.recv(1024)
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
                handle_user_credentials(client)
            elif path == 'wifi':
                handle_wifi_credentials(client)
            elif path == 'configure_user':
                handle_configure_user(client, request)
            elif path == 'configure_wifi':
                handle_configure_wifi(client, request)
            else :
                handle_root(client)

        except Exception as e:
            print(e)
                
        finally:
            client.close()
                
        
