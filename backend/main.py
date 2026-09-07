from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import cv2
import numpy as np
from ultralytics import YOLO
import time
import datetime
import os
import asyncio

# ============================================
# GET ABSOLUTE PATHS
# ============================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ============================================
# LOAD MODELS
# ============================================
print("🔄 Loading models...")
model_person = YOLO(os.path.join(BASE_DIR, "yolo11n.pt"))
model_weapon = YOLO(os.path.join(BASE_DIR, "models", "weapon_model_final.pt"))
print("✅ Models loaded!")

# ============================================
# CONFIGURATION
# ============================================
ZONE_X1 = 450
ZONE_Y1 = 0
ZONE_X2 = 640
ZONE_Y2 = 220

PERSON_CONFIDENCE_THRESHOLD = 0.5
WEAPON_CONFIDENCE_THRESHOLD = 0.45
WEAPON_INSIDE_PERSON_THRESHOLD = 0.65
MOVEMENT_THRESHOLD = 50
ZONE_DWELL_THRESHOLD = 3.0

app = FastAPI(title="NEXUS SENTINEL")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return FileResponse("frontend/index.html")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("🔌 WebSocket client connected")
    
    # ✅ PING EVERY 5 SECONDS TO KEEP CONNECTION ALIVE
    async def send_ping():
        while True:
            await asyncio.sleep(5)
            try:
                await websocket.send_text("ping")
            except:
                break
    
    asyncio.create_task(send_ping())
    
    log_file = os.path.join(BASE_DIR, "security_events.log")
    if not os.path.exists(log_file):
        with open(log_file, "w") as f:
            f.write("=== NEXUS SENTINEL SECURITY LOG ===\n")
            f.write(f"Started: {datetime.datetime.now()}\n")
            f.write("=" * 50 + "\n\n")
    
    def log_event(event_type, message, data=None):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {event_type}: {message}"
        if data:
            log_entry += f" | Data: {data}"
        with open(log_file, "a") as f:
            f.write(log_entry + "\n")
        print(f"📝 LOG: {log_entry}")

    zone_tracker = {}
    movement_tracker = {}

    try:
        while True:
            try:
                data = await websocket.receive()
            except WebSocketDisconnect:
                print("🔌 WebSocket disconnected gracefully")
                break
            except Exception as e:
                print(f"❌ WebSocket receive error: {e}")
                break
            
            if "text" in data:
                print(f"📨 Received text: {data['text']}")
                continue
            
            elif "bytes" in data:
                try:
                    frame = data["bytes"]
                    print(f"📷 Frame received: {len(frame) / 1024:.1f} KB")
                    
                    nparr = np.frombuffer(frame, np.uint8)
                    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    
                    # ==========================================
                    # PERSON DETECTION
                    # ==========================================
                    results_person = model_person(image, verbose=False, imgsz=224)
                    
                    person_boxes = []
                    persons = []
                    person_count = 0
                    current_time = time.time()
                    zone_active = False
                    
                    for box in results_person[0].boxes:
                        class_id = int(box.cls[0])
                        confidence = float(box.conf[0])
                        
                        if model_person.names[class_id] == "person" and confidence > PERSON_CONFIDENCE_THRESHOLD:
                            person_count += 1
                            x1, y1, x2, y2 = box.xyxy[0].tolist()
                            person_boxes.append([x1, y1, x2, y2])
                            
                            center_x = (x1 + x2) / 2
                            center_y = (y1 + y2) / 2
                            
                            in_zone = (ZONE_X1 <= center_x <= ZONE_X2 and ZONE_Y1 <= center_y <= ZONE_Y2)
                            person_id = f"p{int(center_x/10)}_{int(center_y/10)}"
                            dwell_time = 0
                            prolonged = False
                            
                            if in_zone:
                                if person_id not in zone_tracker:
                                    zone_tracker[person_id] = current_time
                                    log_event("ZONE_ENTRY", f"Person {person_id} entered restricted zone")
                                dwell_time = current_time - zone_tracker[person_id]
                                if dwell_time >= ZONE_DWELL_THRESHOLD:
                                    prolonged = True
                                    zone_active = True
                                    log_event("PROLONGED_STAY", f"Person {person_id} in zone for {dwell_time:.1f}s")
                            else:
                                if person_id in zone_tracker:
                                    del zone_tracker[person_id]
                                    log_event("ZONE_EXIT", f"Person {person_id} left restricted zone")
                            
                            movement_detected = False
                            movement_distance = 0
                            movement_speed = 0
                            
                            if person_id in movement_tracker:
                                prev_pos = movement_tracker[person_id]["position"]
                                prev_time = movement_tracker[person_id]["time"]
                                distance = np.sqrt((center_x - prev_pos[0])**2 + (center_y - prev_pos[1])**2)
                                time_diff = current_time - prev_time
                                speed = distance / time_diff if time_diff > 0 else 0
                                
                                if distance > MOVEMENT_THRESHOLD:
                                    movement_detected = True
                                    movement_distance = distance
                                    movement_speed = speed
                                    log_event("MOVEMENT_ALERT", f"Person {person_id} moved {distance:.1f}px")
                                
                                movement_tracker[person_id] = {"position": [center_x, center_y], "time": current_time}
                            else:
                                movement_tracker[person_id] = {"position": [center_x, center_y], "time": current_time}
                            
                            # ✅ BBOX ADDED
                            persons.append({
                                "id": person_id,
                                "center": [center_x, center_y],
                                "bbox": [x1, y1, x2, y2],  # ✅ ADDED
                                "in_zone": in_zone,
                                "prolonged": prolonged,
                                "dwell_time": round(dwell_time, 1),
                                "movement_detected": movement_detected,
                                "movement_distance": round(movement_distance, 1),
                                "movement_speed": round(movement_speed, 1),
                                "has_weapon": False,
                                "threat_level": "safe"
                            })
                    
                    # ==========================================
                    # WEAPON DETECTION
                    # ==========================================
                    results_weapon = model_weapon(image, verbose=False, imgsz=224)
                    
                    weapon_count = 0
                    weapon_list = []
                    threat_detected = False

                    for box in results_weapon[0].boxes:
                        class_id = int(box.cls[0])
                        weapon_name = model_weapon.names[class_id]
                        confidence = float(box.conf[0])
                        
                        wx1, wy1, wx2, wy2 = box.xyxy[0].tolist()
                        weapon_area = (wx2 - wx1) * (wy2 - wy1)
                        
                        is_inside_person = False
                        matched_person_id = None
                        
                        for idx, person in enumerate(persons):
                            if idx >= len(person_boxes):
                                continue
                            px1, py1, px2, py2 = person_boxes[idx]
                            overlap_x = max(0, min(wx2, px2) - max(wx1, px1))
                            overlap_y = max(0, min(wy2, py2) - max(wy1, py1))
                            overlap_area = overlap_x * overlap_y
                            
                            if weapon_area > 0 and (overlap_area / weapon_area) > WEAPON_INSIDE_PERSON_THRESHOLD:
                                is_inside_person = True
                                matched_person_id = person["id"]
                                break
                        
                        if is_inside_person and confidence < WEAPON_CONFIDENCE_THRESHOLD:
                            continue
                        
                        if weapon_name == "knife":
                            KNIFE_THRESHOLD = 0.20
                            if confidence > KNIFE_THRESHOLD:
                                weapon_count += 1
                                # ✅ BBOX ADDED
                                weapon_list.append({
                                    "name": weapon_name,
                                    "confidence": confidence,
                                    "bbox": [wx1, wy1, wx2, wy2],  # ✅ ADDED
                                    "matched_person": matched_person_id
                                })
                                
                                if matched_person_id:
                                    for person in persons:
                                        if person["id"] == matched_person_id:
                                            person["has_weapon"] = True
                                            person["threat_level"] = "high"
                                            threat_detected = True
                                
                                print(f"🔪 KNIFE DETECTED: {weapon_name} ({confidence:.2f})")
                                log_event("WEAPON_DETECTED", f"{weapon_name} detected!")
                            else:
                                print(f"⚠️ Knife filtered: {confidence:.2f}")
                        
                        elif weapon_name == "guns":
                            GUN_THRESHOLD = 0.55
                            if confidence > GUN_THRESHOLD:
                                weapon_count += 1
                                # ✅ BBOX ADDED
                                weapon_list.append({
                                    "name": weapon_name,
                                    "confidence": confidence,
                                    "bbox": [wx1, wy1, wx2, wy2],  # ✅ ADDED
                                    "matched_person": matched_person_id
                                })
                                
                                if matched_person_id:
                                    for person in persons:
                                        if person["id"] == matched_person_id:
                                            person["has_weapon"] = True
                                            person["threat_level"] = "high"
                                            threat_detected = True
                                
                                print(f"🔫 GUN DETECTED: {weapon_name} ({confidence:.2f})")
                                log_event("WEAPON_DETECTED", f"{weapon_name} detected!")
                            else:
                                print(f"⚠️ Gun filtered: {confidence:.2f}")
                    
                    if threat_detected:
                        armed_persons = [p for p in persons if p.get("has_weapon", False)]
                        if armed_persons:
                            log_event("THREAT_ALERT", f"{len(armed_persons)} armed person(s) detected!")
                    
                    prolonged_detected = any(p.get("prolonged", False) for p in persons)
                    if prolonged_detected:
                        log_event("PROLONGED_ALERT", "Person in restricted zone!")
                    
                    # ✅ SEND RESPONSE
                    response = {
                        "type": "detection",
                        "person_count": person_count,
                        "restricted_zone": zone_active,
                        "prolonged_alert": prolonged_detected,
                        "persons": persons,
                        "weapon_count": weapon_count,
                        "weapons": weapon_list,
                        "threat_detected": threat_detected,
                        "system_status": "armed" if threat_detected else "monitoring"
                    }
                    
                    try:
                        await websocket.send_json(response)
                        print(f"📤 Sent: {person_count} persons, {weapon_count} weapons")
                    except Exception as e:
                        print(f"❌ Send failed: {e}")
                    
                except WebSocketDisconnect:
                    print("🔌 WebSocket disconnected during processing")
                    break
                except Exception as e:
                    print(f"❌ Processing error: {e}")
                    continue
                    
    except WebSocketDisconnect:
        print("🔌 WebSocket disconnected gracefully")
    except Exception as e:
        print(f"❌ WebSocket error: {e}")