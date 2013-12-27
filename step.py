#!/usr/bin/python

# A simple Python command line tool to control a stepper motor
# attached to an MCP23017 I2C IO Expander
# By Thomas Hoeser http://thomas.hoeser-medien.de
# GNU GPL V3

import smbus
import sys
import time     # for sleep timer
import argparse # analyze command line arguments
 
bus = smbus.SMBus(1) # smbus.SMBus(1) for revision 2

I2C_address = 0x20 # I2C address of MCP23017
BankA   =0x00
BankB   =0x01

RegisterB = 0x13 # BankB
RegisterA = 0x12 # BankA

degree_rate = 510.0 / 360.0 # convert degree into steps; 510 steps = 360 degree
# ------------------------------------------------------------------
def usage():
   print 'Usage: step.py -h | -d <degrees> [-r -v [level] -n -s -t [time]]'
   print "Examples"
   print "step.py -d 360          # turn 360 degrees"
   print "step.py -d 360 -r       # turn 360 degrees into reverse direction"
   print "step.py -d 360 -s       # turn 360 degrees using 8 step sequence"
   print "step.py -d 360 -t 0.01  # turn 360 degrees wit delay of 0.01 seconds"
   print "step.py -d 360 -n  -v2  # simulate and print debug messages"
   


# define default settings
verbose_level = 0
simulate_flag = 0
direction_flag = 0
sleep_time = 0.006

# 4 step sequence is faster but the torque is lower
StepCount4 = 4
Seq4 = []
Seq4 = range(0, StepCount4)
Seq4[0] = int('00010001',2)
Seq4[1] = int('00100010',2)
Seq4[2] = int('01000100',2)
Seq4[3] = int('10001000',2)

# 8 step sequence is slower but the torque is higher
StepCount8 = 8
Seq8 = []
Seq8 = range(0, StepCount8)
Seq8[0] = int('00000001',2)
Seq8[1] = int('00000011',2)
Seq8[2] = int('00000010',2)
Seq8[3] = int('00000110',2)
Seq8[4] = int('00000100',2)
Seq8[5] = int('00001100',2)
Seq8[6] = int('00001000',2)
Seq8[7] = int('00001001',2)

# ------------------------------------------------------------------
def gpio_setup():
  if verbose_level >0: print "prepare smbus: ",  I2C_address , BankA, BankB
  bus.write_byte_data(I2C_address,BankA,0x00) # Set all of bank A to outputs
  # bus.write_byte_data(I2C_address,BankB,0x00) # Set all of bank B to outputs
  return

# ------------------------------------------------------------------
def gpio_read(register):

  if simulate_flag ==0:
    value = bus.read_byte_data(I2C_address,register)
  if verbose_level >3:
     print "Read : Address 0x%02x  Register 0x%02x / Value 0x%02X = %s" % (I2C_address, register, value,bin(value))
  return

# ------------------------------------------------------------------
def gpio_write(register,value):

  if verbose_level >2:
     print "Set  : Address 0x%02x  Register 0x%02x / Value 0x%02X = %s" % (I2C_address,   register, value,bin(value)) 

  if simulate_flag ==0:
    bus.write_byte_data(I2C_address,register,value)

  if verbose_level >3: gpio_read(register)
  return  

# ------------------------------------------------------------------
 
def step_main(Register,Seg,Stepcount,Cycles,sleep_time): 

  print "----- %d steps using %s sequence, delay %.3f ----- " % (Cycles,Stepcount,sleep_time)

  if direction_flag >0:
    if verbose_level >1: print "turn ->"
    for cyc in range (0,Cycles):
      for value in range (0,Stepcount):
       gpio_write(Register,Seg[value])
       time.sleep(sleep_time)
  else:
    if verbose_level >1: print "turn <-"
    for cyc in range (0,Cycles):
      for value in range (Stepcount-1,-1,-1):
       gpio_write(Register,Seg[value])
       time.sleep(sleep_time)
     
  return

# ------------------------------------------------------------------

def main():

  global verbose_level
  global sleep_time
  global simulate_flag
  global direction_flag
    
  parser = argparse.ArgumentParser(description="write to I2C interface to control stepper motor")
  parser.add_argument("-d", "--degree", help="turn [degree]", type=int)
  parser.add_argument("-s", "--strong", action='store_const', dest='strong', const='value-to-store',help="use 8 step sequence with strong torque",)
  parser.add_argument("-t", "--time", help="sleep [TIME] seconds; default 0.006", type=float)
  parser.add_argument("-n", "--nowrite", action='store_const', dest='nowrite', const='value-to-store',help="no write, just simulate",)
  parser.add_argument("-r", "--reverse", action='store_const', dest='reverse', const='value-to-store',help="reverse direction",)
  parser.add_argument("-v", "--verbose", default=False, 
                    dest='verbose', help="increase output verbosity", type=int)
  parser.add_argument('--version', action='version', version='%(prog)s 0.1')
  
  args = parser.parse_args()
  if args.verbose:  verbose_level = args.verbose
  

  if args.degree: 
    loops = int(args.degree * degree_rate)
    print "turn %d degrees %d steps " % (args.degree,loops)

    if args.time:
      sleep_time = args.time
      if verbose_level >0: print "sleep time ", sleep_time

    if args.nowrite:
      simulate_flag = 1
      if verbose_level >0: print "simulating, no output to device"

    if args.reverse:
      direction_flag = 1
      if verbose_level >0: print "reverse direction"
            
    gpio_setup()  # prepare smbus
    if args.strong:
      if verbose_level >0: print "using Sequence 1"
      step_main(RegisterA, Seq8,StepCount8,loops,sleep_time)
    else:
      if verbose_level >0: print "using Sequence 2"
      step_main(RegisterA, Seq4,StepCount4,loops,sleep_time)

    gpio_write(RegisterA,0) # set all outputs to 0
    sys.exit(0)

  else:
    print "Error! need to provide cycles, e.g. 360 degrees: -c 510"
    usage()
    sys.exit(1)
    
if __name__ == "__main__":
   main() 


