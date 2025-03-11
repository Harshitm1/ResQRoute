import time

# 🚦 Traffic Light States
TRAFFIC_LIGHT = "RED"  # Default state

# 🚑 Critical Health Thresholds
CRITICAL_BP1 = 80 
CRITICAL_BP2 = 150      # Low BP threshold (Systolic)
CRITICAL_SPO2 = 90     # Low Oxygen saturation
CRITICAL_HR1 = 50 
CRITICAL_HR2 = 130      # Low Heart Rate

# Function to simulate IoT device checking patient vitals
def check_vital_signs(bp, spo2, hr):
    global TRAFFIC_LIGHT  # Modify global traffic light state

    print("\n🔎 Checking Patient Vitals...")
    print(f"📌 BP: {bp} mmHg | SpO2: {spo2}% | HR: {hr} bpm")

    if bp < CRITICAL_BP1 or bp > CRITICAL_BP2 or spo2 < CRITICAL_SPO2 or hr < CRITICAL_HR1 or hr > CRITICAL_HR2:
        print("\n🚨 EMERGENCY DETECTED! 🚑")
        print("🔄 Turning Traffic Light GREEN for ambulance!\n")
        TRAFFIC_LIGHT = "GREEN"
    else:
        print("\n✅ Patient is stable. No emergency detected.")
        TRAFFIC_LIGHT = "RED"

# Function to simulate traffic light system
def traffic_light_control():
    global TRAFFIC_LIGHT

    print("\n🚦 Traffic Light Simulation Started...")
    time.sleep(1)

    if TRAFFIC_LIGHT == "GREEN":
        print("🔵 Current Light: 🟢 GREEN - Ambulance Priority Granted!\n")
    else:
        print("🔴 Current Light: 🔴 RED - Normal Traffic Flow.\n")

# 🏥 Simulation Loop
while True:
    print("\n=============================")
    print("🏥 ENTER PATIENT VITALS (or type 'exit' to quit)")

    try:
        bp = input("🔹 Enter Blood Pressure (Systolic): ")
        if bp.lower() == "exit":
            break
        spo2 = input("🔹 Enter Blood Oxygen (SpO2 %): ")
        if spo2.lower() == "exit":
            break
        hr = input("🔹 Enter Heart Rate (BPM): ")
        if hr.lower() == "exit":
            break

        # Convert inputs to integers
        bp, spo2, hr = int(bp), int(spo2), int(hr)

        # Run health check
        check_vital_signs(bp, spo2, hr)

        # Simulate traffic light control
        traffic_light_control()

        # Simulate a delay before next input
        time.sleep(3)

    except ValueError:
        print("⚠️ Invalid input! Please enter numeric values.")

print("\n🔚 Simulation Ended.")
