import requests
import json

base_url = "http://localhost:8000/sensors/read"

def test_sensor(addr):
    payload = {
        "addr": addr,
        "samples": 1,
        "avg": 1
    }
    try:
        response = requests.post(base_url, json=payload)
        response.raise_for_status()
        data = response.json()
        print(f"Address {hex(addr)}: {data['readings'][0]['voltages']}")
        return data['readings'][0]['voltages']
    except Exception as e:
        print(f"Error reading {hex(addr)}: {e}")
        return None

if __name__ == "__main__":
    v1 = test_sensor(0x48)
    v2 = test_sensor(0x49)
    
    if v1 and v2:
        if v1 != v2:
            print("\nSUCCESS: Sensor readings are different!")
        else:
            print("\nFAILURE: Sensor readings are identical!")
    else:
        print("\nFAILURE: Could not get readings from one or both sensors. Is the backend running?")
