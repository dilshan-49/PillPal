from time import sleep
from machine import Pin
from main_func import led

pressed=False

def handler(pin):
    global pressed
    print('handled')
    led.value(1)
    pressed=True
    
def check():
    global pressed
    print('checking')
    if pressed:
        print('checked')
        pressed=False
        led.value(0)
        return True
    else:
        return False

class Container:
    def __init__(self,name,button,lcd,m_o,m_c,m_in):
        self.name = name
        self.button=button
        self.lcd=lcd
        self.motor_open=m_o
        self.motor_close=m_c
        self.motor_button=m_in    
        self.reset()

    def reset(self):
        self.pill=None
        self.morning=0
        self.afternoon=0
        self.night=0
        self.count=0    


    def update(self,slot_data):
        self.pill=slot_data['medicine_name']
        if slot_data['morning_dose']:
            self.morning=int(slot_data['tablet_count'])
        if slot_data['afternoon_dose']:
            self.afternoon=int(slot_data['tablet_count'])
        if slot_data['night_dose']:
            self.night=int(slot_data['tablet_count'])
        self.count=int(slot_data['pill_count'])

        

    def release(self, time):
        global pressed
        pressed = False
        self.lcd.clear()
        if time==1:
            if self.morning==0:
                self.lcd.putstr('No pills from '+self.name)
                print('No pills from '+self.name)
                sleep(2)
                return
            else:
                self.lcd.putstr('Take '+str(self.morning)+' pills. \nPress Button to \ncontinue.')
                print('Take '+str(self.morning)+' pills \nPress Button to \ncontinue')
                self.motor_open.value(1)
                self.count-=self.morning
        elif time==2:
            if self.afternoon==0:
                self.lcd.putstr('No pills from '+self.name)
                print('No pills from '+self.name)
                sleep(2)
                return
            else:
                self.lcd.putstr('Take '+str(self.afternoon)+' pills. \nPress Button to \ncontinue.')
                print('Take '+str(self.afternoon)+' pill')
                self.motor_open.value(1)
                self.count-=self.afternoon
        elif time==3:
            if self.night==0:
                self.lcd.putstr('No pills from '+self.name)
                print('No pills from '+self.name)
                sleep(2)
                return
            else:
                self.motor_open.value(1)
                self.lcd.putstr('Take '+str(self.night)+' pills. \nPress Button to \ncontinue.')
                print('Take '+str(self.night)+' pill')
                self.count-=self.night
        sleep(0.5)
        while not self.motor_button.value():
            sleep(0.05)
        self.motor_open.value(0)
        self.button.irq(trigger=Pin.IRQ_RISING, handler=handler)
        while not check():
            sleep(0.05)
        self.lcd.clear()
        self.button.irq(handler=None)
        self.motor_close.value(1)
        sleep(0.5)
        led.value(0)
        pressed=False
        while not self.motor_button.value():
            sleep(0.05)
        self.motor_close.value(0)
        sleep(0.5)
        self.motor_open.value(1)
        sleep(0.2)
        self.motor_open.value(0)
        print(self.name+' closed')
        sleep(1)

