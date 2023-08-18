import machine
import time
import binascii
import utime
import binascii
from machine import Timer

def pullup_pin(num):
    return machine.Pin(num,machine.Pin.PULL_UP)

#pullup_pin = lambda num : machine.Pin(num,machine.Pin.PULL_UP)

# --- setup ---
print('setup...')
#tim = Timer(period=5000, mode=Timer.ONE_SHOT, callback=lambda t:print(1))
#tim.init(period=2000, mode=Timer.PERIODIC, callback=lambda t:print(2))

#setup on-board led put high
led = machine.Pin(25, machine.Pin.OUT)

#setup I2C channel 0
i2c0 = machine.I2C(0,sda=pullup_pin(12),scl=pullup_pin(13), freq=1000)

#setup I2C channel 1
#i2c1 = machine.I2C(1,sda=pullup_pin(6), scl=pullup_pin(7), freq=10000)

#scan for debug-trace
print(i2c0.scan())
#print(i2c1.scan())
while True:
    res = i2c0.scan()
    if len(res)==0:
        time.sleep(0.1)
    else:
        print(res)
        if 0x40 in res:
            print('htu found')
        break

utime.sleep_us(100*1000)

#ads addr, htu addr
addr = 72
addr_htu = 64

#led blink decorator 1
def withled(LedPin=25):
    def inner_function(fn):
        _led = machine.Pin(LedPin, machine.Pin.OUT)
        def wrapper(*args):
            _led.high()
            retval = fn(*args)
            _led.low()
            return retval
        return wrapper
    return inner_function

def htu_restart(i2cdev,htuaddr):
    try:
        #res = i2cdev.readfrom_mem(htuaddr,0xFE,0)
        res = i2cdev.writeto(htuaddr,bytes([0xFE]))
        #res = i2cdev.writeto_mem(htuaddr,1,bytes([0xFE]))
        print(res)
    except Exception as e:
        print(e)

#led blink decorator 2
def withpicoled(fn):
    return withled(25)(fn)

@withled(LedPin=15)
@withpicoled
def htu_read(i2c,alarmnfo=None):
    #print('mainloop',alarmnfo)
    htu_addr = 0x40
    while True:
        try:
            #set temp capture (hold master mode)
            rv = i2c.readfrom_mem(htu_addr,0xE3,3)
            #conversion into 14-bit value
            sen_temp_val = ((rv[0] << 8) | ((rv[1] >> 2) << 2))
            Temp = (-46.85 + 175.72*sen_temp_val/(1<<16))
            time.sleep(0.01)

            #read humidity
            rv = i2c.readfrom_mem(htu_addr,0xE5,3)
            sen_hum_val = ((rv[0] <<8) | ((rv[1]>>2)<<2))
            RH = (-6.0 + 125.0*(sen_hum_val / (1<<16)))
                       
            return (Temp,RH)            
        except OSError as ose:
            print(type(ose),ose)
            print('restarting module')
            htu_restart(i2c,htu_addr)
            utime.sleep_ms(1000)
            continue
        finally:
            pass
    return

def dtinfo():
    z = time.gmtime()
    return "{}/{}/{}-{}:{}:{}".format(z[0],z[1],z[2],z[3],z[4],z[5])
    #return "{}-{}-{}/{}:{}:{}".format(z[0:6])


htu_restart(i2c0,0x40)
while True:
    print(dtinfo())
    (temp,hum) = htu_read(i2c0)
    print("Temperature {:.1f} C. Humidity {:.2f} %".format(temp,hum))
    if False:
        utime.sleep_ms(1000)
        lo_tresh = i2c0.readfrom_mem(addr,2,2)#regA conversion
        hi_tresh = i2c0.readfrom_mem(addr,3,2)#regA conversion
        print('tresholds',binascii.hexlify(lo_tresh), binascii.hexlify(hi_tresh))
    utime.sleep_ms(5000)
    pass
