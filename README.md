# NEXUS SENTINEL
## Security Monitoring System with Weapon Detection

## Project Overview

NEXUS SENTINEL is a security monitoring system that provides real-time surveillance with weapon detection capabilities. It uses YOLOv11 for person detection and a trained model for weapon detection (knife/gun), making it suitable for office, warehouse, school, and retail security applications.

## Key Features

- Live Webcam Feed: Real-time video capture from browser camera
- Person Detection: YOLOv11 powered person detection with bounding boxes
- Restricted Zone: Customizable restricted area with visual boundary
- Weapon Detection: Detects knives and guns using trained YOLO model
- Prolonged Stay Alert: Alert when person stays in restricted zone for more than 3 seconds
- Movement Detection: Detects significant movement changes
- Audio Alerts: Real-time audio notifications for security events
- Performance Metrics: Live FPS, Latency, and Detection counter
- Event Logging: Complete event history with timestamps
- Responsive UI: Works on desktop, tablet, and mobile devices

## Weapon Detection Details

The system detects the following weapons:

- Knife: Detected when confidence score is 0.20 or higher
- Gun: Detected when confidence score is 0.55 or higher

Why different thresholds?
- Knife detection is prioritized because knives are common threats
- Gun detection requires higher confidence to avoid false positives
- Both detections trigger security alerts with visual and audio feedback

## Technology Stack

- Backend: Python 3.13 + FastAPI + WebSocket
- Object Detection: YOLOv11 (Ultralytics)
- Computer Vision: OpenCV + NumPy
- Frontend: HTML5 + CSS3 + Vanilla JavaScript
- Real-time Communication: WebSocket
- Deployment: Render / Railway

## Project Structure
NEXUS-SENTINEL/
├── backend/
│ └── main.py
├── frontend/
│ └── index.html
├── models/
│ └── weapon_model_final.pt
├── yolo11n.pt
├── security_events.log
├── requirements.txt
└── README.md

text

## Installation & Setup

Prerequisites:
- Python 3.11 or higher
- Webcam (built-in or external)

Step 1: Clone Repository
git clone https://github.com/gmafsd775/NEXUS-SENTINEL.git
cd NEXUS-SENTINEL

text

Step 2: Create Virtual Environment
python -m venv venv
venv\Scripts\activate

text

Step 3: Install Dependencies
pip install -r requirements.txt

text

Step 4: Run Application
python -m uvicorn backend.main:app --reload

text

Step 5: Access Application
Open browser and go to: http://127.0.0.1:8000

## How It Works

1. Browser captures webcam frames
2. Frames are sent to backend via WebSocket (10-16 FPS)
3. Backend decodes JPEG frames using OpenCV
4. YOLO model detects persons in the frame
5. Weapon model detects knives and guns
6. Restricted zone check is performed on each person
7. Movement is tracked using center point changes
8. Security events trigger visual and audio alerts
9. Frontend displays bounding boxes and status updates

## Detection Flow and Alerts

- Person Detected: Green bounding box, No audio
- Person enters Zone: Red bounding box, Single beep, ZONE_ENTRY logged
- Person in Zone > 3 seconds: Blinking red box, Double beep, PROLONGED_STAY logged
- Movement Detected: Orange badge, Single beep, MOVEMENT_ALERT logged
- Knife Detected: Orange bounding box, Single beep, WEAPON_DETECTED logged
- Gun Detected: Orange bounding box, Single beep, WEAPON_DETECTED logged
- Person with Weapon: Red blinking box, Triple beep, THREAT_ALERT logged

## Demo Instructions

1. Start the Application: Run server and open browser, click Start Camera
2. Test Person Detection: Walk in front of camera, green box appears
3. Test Restricted Zone: Enter top-right area, red box appears, beep plays
4. Test Prolonged Stay: Stay in zone >3 seconds, blinking red box, double beep
5. Test Weapon Detection: Show knife, orange box, beep, weapon count increases
6. Test Threat Alert: Show knife and enter zone, red blinking box, triple beep

## Performance Metrics

- Frame Rate: 10-16 FPS
- Latency: Less than 5ms
- Person Detection Accuracy: 95%+
- Weapon Detection Accuracy: 77% mAP50
- Alert Delay: Less than 1 second

## Deployment

Render Deployment:
1. Push code to GitHub
2. Connect repository to Render
3. Build Command: pip install -r requirements.txt
4. Start Command: uvicorn backend.main:app --host 0.0.0.0 --port 10000

Railway Deployment:
1. Push code to GitHub
2. Connect repository to Railway
3. Set environment variable: PORT=8000
4. Start Command: uvicorn backend.main:app --host 0.0.0.0 --port $PORT

## Security Event Log

All security events are logged to security_events.log file with timestamps:
[2026-09-07 11:24:41] ZONE_ENTRY: Person p34_22 entered restricted zone
[2026-09-07 11:24:44] PROLONGED_STAY: Person p34_22 in zone for 3.2s
[2026-09-07 11:24:41] WEAPON_DETECTED: knife detected! | Confidence: 0.31
[2026-09-07 11:24:41] THREAT_ALERT: 1 armed person(s) detected!

text

## Future Enhancements

- Multi-camera support (up to 10 cameras)
- Cloud recording and playback
- Mobile application
- Face recognition
- Automatic alert emails and SMS
- Advanced analytics dashboard
- Real-time notifications

## Important Notes

1. The system does not claim to detect mental state, criminal intent, personality, suspicious thoughts, or identity.
2. Suspicious refers only to observable computer-vision events such as:
   - Person detected
   - Person enters restricted zone
   - Person remains in restricted zone
   - Measurable movement or position change
   - Weapon detected
3. No face recognition or identity recognition is required or implemented.

## License

This project is for educational purposes only. Commercial use requires proper licensing and compliance with local laws regarding surveillance and weapon detection.

## Author

**Ahmed Nawaz**
- GitHub: [gmafsd775](https://github.com/gmafsd775)
- LinkedIn: [Ahmed Nawaz](https://www.linkedin.com/in/ahmed-nawaz-52134733b)

## Acknowledgments

- Ultralytics for YOLOv11
- FastAPI for the backend framework
- Roboflow for dataset management
- OpenCV for computer vision

Made for Class Project