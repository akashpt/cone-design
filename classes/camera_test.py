from arena_api.system import system

devices = system.create_device()

print("Devices found:", len(devices))

for d in devices:
    print(d)