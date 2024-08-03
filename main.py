##########Importing required Modules###############
from machine import Pin,deepsleep,soft_reset
from esp32 import wake_on_ext0,wake_on_ext1,WAKEUP_ANY_HIGH
from utime import localtime
import gc
import ujson
from pill_container import Container
from main_func import *

update_button=Pin(34, Pin.IN, Pin.PULL_DOWN)
wake_on_ext1((update_button,),WAKEUP_ANY_HIGH)
update_button.irq(trigger=Pin.IRQ_RISING, handler=put_to_deepsleep)

#########Initializing Display ############
lcd.clear()
lcd.putstr("Hello!")
print('Hello')
##########################################
with open('USER_CRED.txt', 'r') as f:
    credetials=ujson.load(f)
    user_email=credetials['email']
    user_password=credetials['password']
    api_key=credetials['api']
    mobile=credetials['mobile']

##########Setiing up Slots##########
S1=Container('Slot 1',user_button,lcd,m1o,m1c,motor_button)
S2=Container('Slot 2',user_button,lcd,m2o,m2c,motor_button)
S3=Container('Slot 3',user_button,lcd,m3o,m3c,motor_button)
S4=Container('Slot 4',user_button,lcd,m4o,m4c,motor_button)

##################################################
now=localtime()[3:5]
print(now)
lcd.clear()
try:
    # Try to open the file
    with open('data.txt', 'r') as f:
        data=ujson.load(f)
        print(data)
    for name,val in data.items:
        msg=''
        if val["pill_count"]<5:
            msg=val["pill_name"]+', '
    if msg:
        msg+='need to be refilled'
        send_message(mobile,api_key,msg)
    gc.collect()
            
        
except OSError:
    lcd.putstr('Press Update button to Update data')
    print('Please Update Data')
    update_button=Button(34,'update')
    while True:
        if update_button.is_pressed():
            deepsleep()
        sleep(1)

##################################################
S1.update(data['slot1'])
S2.update(data['slot2'])
S3.update(data['slot3'])
S4.update(data['slot4'])

while True:
    now=localtime()[3:5]
    if night_1<= now or now <= morning_1:
        time_period=3
        pills=S1.night+S2.night+S3.night+S4.night
    elif afternoon_1 <= now:
        time_period=2
        pills=S1.afternoon+S2.afternoon+S3.afternoon+S4.afternoon
    else :
        time_period=1
        pills=S1.morning+S2.morning+S3.morning+S4.morning
    
    
    should_ring=night_1<=now<=night_2 or morning_1<=now<=morning_2 or afternoon_1<=now<=afternoon_2

    if pills>0:
        print(pills,'Pills')
        del pills
        
        if user_button.is_pressed():
            S1.release(time_period)
            S2.release(time_period)
            S3.release(time_period)
            S4.release(time_period)
            gc.collect()

            #update local data file
            data['slot1']['count']=S1.count
            data['slot2']['count']=S2.count
            data['slot3']['count']=S3.count
            data['slot4']['count']=S4.count
            with open('data.txt', 'w') as f:
                ujson.dump(data, f)
                del data
        


            #update database
            now=localtime()
            doc={}
            date = "{:04d}-{:02d}-{:02d}".format(now[0], now[1], now[2])
            if time_period==1:
                path=date+"/Morning"
                doc[S1.pill]={"integerValue":S1.morning}
                doc[S2.pill]={"integerValue":S2.morning}
                doc[S3.pill]={"integerValue":S3.morning}
                doc[S4.pill]={"integerValue":S4.morning}
            elif time_period==2:
                path=date+"/Afternoon"
                doc[S1.pill]={"integerValue":S1.afternoon}
                doc[S2.pill]={"integerValue":S2.afternoon}
                doc[S3.pill]={"integerValue":S3.afternoon}
                doc[S4.pill]={"integerValue":S4.afternoon}
            else:
                path=date+"/Night"
                doc[S1.pill]={"integerValue":S1.night}
                doc[S2.pill]={"integerValue":S2.night}
                doc[S3.pill]={"integerValue":S3.night}
                doc[S4.pill]={"integerValue":S4.night}
                
            doc["time"]={"timestampValue":date+"T{:02d}:{:02d}:{:02d}Z".format(now[3], now[4], now[5])}
            json_doc=ujson.dumps({"fields":doc})
            del doc
            
            '''
        
            if connect_to_wifi():
                gc.collect()
                print('Sendind message and Updating data')
                send_message(mobile,api_key,'hto beth biwwa')
                gc.collect()
                if firebase.FIREBASE_GLOBAL_VAR.ACCESS_TOKEN is None:
                    auth=FirebaseAuth(firebase.FIREBASE_GLOBAL_VAR.API)
                    auth.sign_in(user_email,user_password)
                    access_token=(auth.session.access_token)
                    firebase.FIREBASE_GLOBAL_VAR.UID=auth.user["uid"]
                    firebase.set_access_token(access_token)
                firebase.create(json_doc, path)
                gc.collect()
                for slot in (S1,S2,S3,S4):
                    firebase.update(slot.name,slot.count)
                
                gc.collect()
                gc.mem_free()
            else:
                lcd.putstr('Connection Issue!   Saving records locally.')
                print('Connection Issue Saving records locally')
                with open('records.txt', 'a+') as f:
                    ujson.dump(doc,f)
                    f.write('\n')

            '''


            ##############################################################
            with open('records.txt', 'a+') as f:
                ujson.dump(doc,f)
                f.write('\n')
            lcd.backlight_off()
            lcd.clear()
            gc.collect()
            global secs
            if now<morning_1:
                secs=(morning_1[0]-now[3])*3600+(morning_1[1]-now[4])*60
                print('sleep till morning')
                deepsleep(secs*1000)
            elif morning_1<=now<afternoon_1:
                print('sleep till afternoon')
                secs=(afternoon_1[0]-now[3])*3600+(afternoon_1[1]-now[4])*60
                deepsleep(secs*1000)
            elif afternoon_1<=now<night_1:
                print('sleep till night')
                secs=(night_1[0]-now[3])*3600+(night_1[1]-now[4])*60
                deepsleep(secs*1000)
            else:
                print('sleep till morning overnight')
                secs=(morning_1[0]-now[3]+24)*3600+(morning_1[1]-now[4])*60
                deepsleep(secs*1000)
                
        elif should_ring:
            print('ringing')
            ring()
            ring()
            ring()
            ####configure loop correctly to ring once 5 minutes for 1 hour
            for _ in range(60):
                if user_button.pressed:
                    print('User pressed.Bre4akng loop')
                    break
                sleep(5)
        else:
            print('Times up! Going to sleep')
            wake_on_ext0(Pin(35,Pin.IN), WAKEUP_ANY_HIGH)
            lcd.backlight_off()
            deepsleep(3600*1000)
    
    else:
        lcd.clear()
        lcd.putstr('No Medicine to take')
        print('No Medicine to take')
        sleep(5)
        lcd.backlight_off()
        print('Going to sleep. Reboot to interrupt')
        gc.collect()
        if now<morning_1:
            secs=(morning_1[0]-now[0])*3600+(morning_1[1]-now[1])*60
            deepsleep(secs*1000)
        elif morning_1<=now<afternoon_1:
            secs=(afternoon_1[0]-now[0])*3600+(afternoon_1[1]-now[1])*60
            deepsleep(secs*1000)
        elif afternoon_1<=now<night_1:
            secs=(night_1[0]-now[0])*3600+(night_1[1]-now[1])*60
            deepsleep(secs*1000)
        else:
            secs=(morning_1[0]-now[0]+24)*3600+(morning_1[1]-now[1])*60
            deepsleep(secs*1000)
