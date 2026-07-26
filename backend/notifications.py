from datetime import datetime

def generate_notifications(traffic_data):
    notifications = []
    
    for route in traffic_data:
        now = datetime.now().strftime("%H:%M:%S")
        cong = route["congestion_index"]
        name = route["route"]
        
        if cong >= 8:
            notif = {
                "type": "alert",
                "title": f"🔴 URGENT — {name}",
                "message": f"Congestion index {cong}/10. Avoid this route immediately.",
                "time": now
            }
        elif cong >= 5:
            notif = {
                "type": "warn", 
                "title": f"🟠 WARNING — {name}",
                "message": f"Congestion index {cong}/10. Expect delays.",
                "time": now
            }
        else:
            notif = {
                "type": "info",
                "title": f"🟡 INFO — {name}",
                "message": f"Congestion index {cong}/10. Moderate traffic.",
                "time": now
            }
        
        notifications.append(notif)
    
    return notifications


# Test
if __name__ == "__main__":
    traffic_data = [
        {"route": "Satellite → Maninagar", "congestion_index": 4.1},
        {"route": "Bopal → CG Road", "congestion_index": 7.8},
        {"route": "Naroda → ISCON", "congestion_index": 9.1}
    ]
    
    print("=== FlowAI Notifications ===\n")
    notifs = generate_notifications(traffic_data)
    
    for n in notifs:
        print(f"[{n['time']}] {n['title']}")
        print(f"  {n['message']}\n")