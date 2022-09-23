from devices.PSU import PSU0, PSU1

PSU0.Instance().off()
PSU1.Instance().off()

print(PSU0.Instance().is_on())
print(PSU1.Instance().is_on())

PSU0.Instance().on()
PSU1.Instance().on()

print(PSU0.Instance().is_on())
print(PSU1.Instance().is_on())
