# from pymodbus.client.sync import ModbusTcpClient
# from concurrent.futures import ThreadPoolExecutor, as_completed
# import time


# # ---------PLC FUNCTIONS Modbus address -----------
# # D512 ---> Machine On/off (1/0)
# MACHINE_ADDRESS = 512
# # D525 ---> Count 1- 4 cops , 0- no signal 
# COUNT_ADDRESS = 525
# # D528 ---> Bad not eject 1-alaram on , 0-no signal
# ALARAM_ADDRESS = 528
# # D530 ---> auto and manuel mode 1-manuel on , 0-auto
# AUTO_MANUEL_MODE = 530
# # D515 ---> Up down not working 
# GRIPPER_UP_DOWN = 515
# # D516 ---> Forword reverse not working
# GRIPPER_FORWORD_REVERSE = 516
# # D521 ---> Gripper one 0-good, 1-bad
# G1_ADDRESS=521
# # D522 ---> Gripper two 0-good, 1-bad
# G2_ADDRESS=522
# # D523 ---> Gripper three 0-good, 1-bad
# G3_ADDRESS=523
# # D524 ---> Gripper four 0-good, 1-bad
# G4_ADDRESS=524


# # ---------- PLC SETTINGS ----------
# PLC_IP = "192.168.3.250"     # change this to your PLC IP
# PLC_PORT = 502
# D0_ADDRESS = 0             # D0   => Modbus address 0
# UNIT_ID = 1                # Delta PLC usually unit 1
# LENGTH_FILE = "length.txt"
# # ----------------------------------


# client = ModbusTcpClient(PLC_IP, port=PLC_PORT)   # seconds ,timeout=2

# if not client.connect():
#     print("PLC not connected")
# else:
#     print("PLC connected")


# def plc_connection():
#     if client.connect():
#         return True
#     else:
#         return False

# # def read_register(client, address):
# #     """Read 1 holding register from given address.
# #        Returns integer value, or None if error.
# #     """
# #     try:
# #         response = client.read_holding_registers(address, 1, unit=UNIT_ID)

# #         if response.isError():
# #             return None

# #         return response.registers[0]

# #     except Exception as e:
# #         # You can print(e) for debug if needed
# #         return None

# def read_register(address):
#     try:
#         if not client.connect():
#             return False

#         resp = client.read_holding_registers(address, 1, unit=UNIT_ID)
#         if resp.isError():
#             return False

#         return resp.registers[0]

#     except:
#         return False


# def machine_status():
#     #return 1
#     try:
#         value = read_register(MACHINE_ADDRESS)

#         if value is None:
#             print("Machine Not Connected")
#             return False

#         # else:
#             # if value == 1:
#             #     print("Machine on")
                
#             # elif value == 0:
#             #     print("Machine off")

#         return value
    
#     except Exception as e:
#         # You can print(e) for debug if needed
#         return False

# import random

# checking = [0, 1, 0, 0]

# def count_status():
#    # return random.choice(checking)
#     try:
#         value = read_register(COUNT_ADDRESS)

#         if value is None:
#             return False

#         if value == 1:
#             print("Count added")
#             time.sleep(0.2)
            
#         return value

#     except Exception as e:
#         print(f"Error reading register: {e}")
#         return False
    

# # machine_status()
# # count_status()
# # data = True
# # while data:
# #     val = count_status()
# #     # import time
# #     # time.sleep(0.2)
# #     # if val == 1:
# #     #     data = False

# def alaram_status():
#     try:
#         value = read_register(ALARAM_ADDRESS) 

#         if value is None:
#             print("Not Connected")
#             return False
#         else:
#             if value == 1:
#                 print("Alaram ON")
#             elif value == 0:
#                 print("waiting for next count")
#             return value
#     except Exception as e:
#         # You can print(e) for debug if needed
#         return False
    
# def mode_status():
#     try:
#         value = read_register(AUTO_MANUEL_MODE)

#         if value is None:
#             print("Mode issue")
#             return False

#         else:
#             if value == 1:
#                 print("Manuel Mode")
                
#             elif value == 0:
#                 print("Auto Mode")

#         return value
        
#     except Exception as e:
#         # You can print(e) for debug if needed
#         return False

# def gripper_up_down_status():
#     try:
#         value = read_register(GRIPPER_UP_DOWN) 

#         if value is None:
#             print("Not Connected")
#             return False
#         else:
#             if value == 1:
#                 print("count added 4")
#             elif value == 0:
#                 print("waiting for next count")
#         return value
    
#     except Exception as e:
#         # You can print(e) for debug if needed
#         return False
    

# def gripper_forward_reverse_status():
#     try:
#         value = read_register(GRIPPER_FORWORD_REVERSE) 

#         if value is None:
#             print("Not Connected")
#             return False
#         else:
#             if value == 1:
#                 print("Gripper Forward Reverse done")
#             elif value == 0:
#                 print("waiting for next count")
#         return value
#     except Exception as e:
#         # You can print(e) for debug if needed
#         return False


# def write_register(ADDRESS,value):
#     try:
#         response = client.write_register(ADDRESS,value)
#         if response.isError():
#             return False
#         # if value == 1:
#         #     print("defect capture sent (D521 = 1)")

#         # else:
#         #     print(f"D521 written with value {value}")
#         return True

#     except Exception as e:
#         print(f"Error writing {ADDRESS}:", e)
#         return False
    

# # def gripper_function(values: list):
# #     try:
# #         addresses = [G1_ADDRESS, G2_ADDRESS, G3_ADDRESS, G4_ADDRESS]

# #         with ThreadPoolExecutor(max_workers=4) as executor:
# #             futures = [executor.submit(write_register, addr, val) for addr, val in zip(addresses, values)]
# #             results = [f.result() for f in futures]   # ✅ wait + collect

# #         return all(results)  # optional: depends write_register returns True/False
# #     except Exception as e:
# #         print("Gripper Function -", e)
# #         return False
    
# # def gripper_function(values: list):
# #     """
# #     values: list of 4 ints, e.g. [0,1,0,1]
# #     """
# #     try:
# #         if not isinstance(values, (list, tuple)) or len(values) != 4:
# #             print("❌ Invalid gripper values:", values)
# #             return False

# #         addresses = [G1_ADDRESS, G2_ADDRESS, G3_ADDRESS, G4_ADDRESS]

# #         # ===== 1️⃣ SET GRIPPER VALUES =====
# #         with ThreadPoolExecutor(max_workers=4) as executor:
# #             futures = [
# #                 executor.submit(write_register, addr, val)
# #                 for addr, val in zip(addresses, values)
# #             ]
# #             results = [f.result() for f in futures]

# #         # optional: small ON time for PLC to latch
# #         time.sleep(0.5)   # 500 ms (tune if needed)

# #         # ===== 2️⃣ RESET GRIPPER VALUES (0000) =====
# #         reset_values = [0, 0, 0, 0]
# #         with ThreadPoolExecutor(max_workers=4) as executor:
# #             futures = [
# #                 executor.submit(write_register, addr, val)
# #                 for addr, val in zip(addresses, reset_values)
# #             ]
# #             reset_results = [f.result() for f in futures]

# #         return all(results) and all(reset_results)

# #     except Exception as e:
# #         print("Gripper Function -", e)
# #         return False
    

# def gripper_function(values):
#     if len(values) != 4:
#         return False

#     addresses = [G1_ADDRESS, G2_ADDRESS, G3_ADDRESS, G4_ADDRESS]

#     # SET
#     for addr, val in zip(addresses, values):
#         write_register(addr, val)

#     time.sleep(0.2)   # small latch delay

#     # RESET
#     for addr in addresses:
#         write_register(addr, 0)

#     return True
    

# # values = [0, 0, 0, 0]
# # gripper_function(values)

# # print(machine_status())







from pymodbus.client.sync import ModbusTcpClient
import time
import random

# ---------------- PLC ADDRESSES ----------------

MACHINE_ADDRESS = 512
COUNT_ADDRESS = 525
ALARAM_ADDRESS = 528
AUTO_MANUEL_MODE = 530

GRIPPER_UP_DOWN = 515
GRIPPER_FORWORD_REVERSE = 516

G1_ADDRESS = 521
G2_ADDRESS = 522
G3_ADDRESS = 523
G4_ADDRESS = 524

# ---------------- PLC SETTINGS ----------------

PLC_IP = "192.168.3.250"
PLC_PORT = 502
UNIT_ID = 1

# ---------------- CONNECT PLC ----------------

client = ModbusTcpClient(PLC_IP, port=PLC_PORT)

if client.connect():
    print("PLC connected")
else:
    print("PLC not connected")


# ---------------- READ REGISTER ----------------

def read_register(address):
    try:
        resp = client.read_holding_registers(address, 1, unit=UNIT_ID)

        if resp.isError():
            return None

        return resp.registers[0]

    except Exception as e:
        print("PLC read error:", e)
        return None


# ---------------- MACHINE STATUS ----------------

def machine_status():

    # TEMP TEST MODE
    return 1

    value = read_register(MACHINE_ADDRESS)

    if value is None:
        print("Machine not connected")

    return value


# ---------------- COUNT SIGNAL ----------------

checking = [0, 1, 0, 0]

def count_status():

    # TEMP TEST MODE
    return random.choice(checking)

    value = read_register(COUNT_ADDRESS)

    if value == 1:
        print("Count signal received")

    return value


# ---------------- ALARM ----------------

def alarm_status():

    value = read_register(ALARAM_ADDRESS)

    if value == 1:
        print("Alarm ON")

    return value


# ---------------- MODE ----------------

def mode_status():

    value = read_register(AUTO_MANUEL_MODE)

    if value == 1:
        print("Manual Mode")

    if value == 0:
        print("Auto Mode")

    return value


# ---------------- WRITE REGISTER ----------------

def write_register(address, value):

    try:
        resp = client.write_register(address, value)

        if resp.isError():
            return False

        return True

    except Exception as e:
        print("PLC write error:", e)
        return False


# ---------------- GRIPPER CONTROL ----------------

def gripper_function(values):

    if len(values) != 4:
        return False

    addresses = [G1_ADDRESS, G2_ADDRESS, G3_ADDRESS, G4_ADDRESS]

    # send values
    for addr, val in zip(addresses, values):
        write_register(addr, val)

    time.sleep(0.2)

    # reset
    for addr in addresses:
        write_register(addr, 0)

    return True