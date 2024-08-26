##########Importing required Modules###############
from machine import Pin,deepsleep,soft_reset,wake_reason
from esp32 import wake_on_ext0,wake_on_ext1,WAKEUP_ANY_HIGH
from utime import localtime
import gc
import ujson
from pill_container import Container
from main_func import *

update_button=Pin(34, Pin.IN, Pin.PULL_DOWN)
wake_on_ext1((update_button,),WAKEUP_ANY_HIGH)
update_button.irq(trigger=Pin.IRQ_RISING, handler=put_to_deepsleep)


release=False
if wake_reason()==2:
    release=True
############################################
    
def pressed(pin):
    global release
    led.value(1)
    release=True
    
#########Initializing Display ############
    
lcd.clear()
lcd.putstr("Hello!")

##########################################

with open('USER_CRED.txt', 'r') as f:
    credetials=ujson.load(f)
    user_email=credetials['email']
    user_password=credetials['password']
    api_key=credetials['api']
    mobile=credetials['mobile']

##########Setiing up Slots##########
    
S1=Container('slot1',user_button,lcd,m1o,m1c,motor_button)
S2=Container('slot2',user_button,lcd,m2o,m2c,motor_button)
S3=Container('slot3',user_button,lcd,m3o,m3c,motor_button)
S4=Container('slot4',user_button,lcd,m4o,m4c,motor_button)

##################################################

lcd.clear()
try:
    # Try to open the file
    with open('data.txt', 'r') as f:
        data=ujson.load(f)
    msg=''
    for name,val in data.items():        
        if name=="times":
            continue
        if int(val["pill_count"])<5:
            msg=val["pill_name"]+', '
    if msg:
        msg+='need to be refilled'
        send_message(mobile,api_key,msg)
    gc.collect()
            
        
except OSError:
    lcd.putstr('Update Required.\nPress Update button to continue')
    while True:
        sleep(10)


##################################################
S1.update(data['slot1'])
S2.update(data['slot2'])
S3.update(data['slot3'])
S4.update(data['slot4'])
times=data['times']

morning_1=tuple(map(int, times['morning'].split(":")))
morning_2=(morning_1[0]+1,morning_1[1])
afternoon_1=tuple(map(int, times['afternoon'].split(":")))
afternoon_2=(afternoon_1[0]+1,afternoon_1[1])
night_1=tuple(map(int, times['night'].split(":")))
night_2=(night_1[0]+1,night_1[1])

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
        
        if release:
            update_button.irq(handler=None)
            sleep(0.5)
            lcd.clear()
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
                msg="Morning medication was taken by the patient"
            elif time_period==2:
                path=date+"/Afternoon"
                doc[S1.pill]={"integerValue":S1.afternoon}
                doc[S2.pill]={"integerValue":S2.afternoon}
                doc[S3.pill]={"integerValue":S3.afternoon}
                doc[S4.pill]={"integerValue":S4.afternoon}
                msg="Afternoon medication was taken by the patient"
            else:
                path=date+"/Night"
                doc[S1.pill]={"integerValue":S1.night}
                doc[S2.pill]={"integerValue":S2.night}
                doc[S3.pill]={"integerValue":S3.night}
                doc[S4.pill]={"integerValue":S4.night}
                msg="Night medication was taken by the patient"
                
            doc["time"]={"timestampValue":date+"T{:02d}:{:02d}:{:02d}Z".format(now[3], now[4], now[5])}
            doc["taken"]={"booleanValue":True}
            json_doc=ujson.dumps({"fields":doc})
            
 
        
            if connect_to_wifi():
                del doc
                gc.collect()
                lcd.clear()
                lcd.putstr('Sending message and Updating data')
                send_message(mobile,api_key,msg)
                
                gc.collect()
                if firebase.FIREBASE_GLOBAL_VAR.ACCESS_TOKEN is None:
                    auth=FirebaseAuth(firebase.FIREBASE_GLOBAL_VAR.API)
                    auth.sign_in(user_email,user_password)
                    access_token=(auth.session.access_token)
                    firebase.FIREBASE_GLOBAL_VAR.UID=auth.user["uid"]
                    firebase.set_access_token(access_token)                   
                for slot in (S1,S2,S3,S4):
                    firebase.update(slot.name,slot.count)
                    gc.collect()
                firebase.create(json_doc, path)
                gc.collect()
                lcd.clear()
                lcd.putstr("Successfully Updated Data")
                sleep(3)


            else:
                lcd.clear()
                lcd.putstr('Connection Issue! \nSaving records locally.')
                print('Connection Issue Saving records locally')
                with open('records.txt', 'a+') as f:
                    file={path:doc}
                    ujson.dump(file,f)
                    f.write('\n')
                del doc
                del file
                sleep(1)


            ##############################################################
            lcd.clear()
            lcd.putstr("Have a nice day")
            sleep(3)
            lcd.backlight_off()
            lcd.clear()
            gc.collect()
            secs=0
            now=localtime()[3:5]
            if now<morning_1:
                secs=(morning_1[0]-now[0])*3600+(morning_1[1]-now[1])*60
                print('sleep till morning')
            elif now<afternoon_1:
                print('sleep till afternoon')
                secs=(afternoon_1[0]-now[0])*3600+(afternoon_1[1]-now[1])*60
            elif now<night_1:
                print('sleep till night')
                secs=(night_1[0]-now[0])*3600+(night_1[1]-now[1])*60
            else:
                print('sleep till morning overnight')
                secs=(morning_1[0]-now[0]+24)*3600+(morning_1[1]-now[1])*60

            deepsleep(secs*1000)

        elif should_ring:
            lcd.putstr("Time for medicine")
            ring()
            ring()
            user_button.irq(trigger=Pin.IRQ_RISING, handler=pressed)
            for _ in range(300):
                if release:
                    user_button.irq(handler=None)
                    led.value(0)
                    break
                sleep(1)
        else:
            gc.collect()
            try:
                if connect_to_wifi():
                    send_message(mobile,api_key,'Patient seems to have forgot to take medicine')
            except:
                pass
            finally:
                print('Times up! Going to sleep')
                wake_on_ext0(user_button, WAKEUP_ANY_HIGH)
                lcd.backlight_off()
                lcd.clear()
                deepsleep(3600*1000)
    
    else:
        lcd.clear()
        lcd.putstr('No Medicine to take.Have a nice day')
        sleep(5)
        lcd.backlight_off()
        lcd.clear()
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
