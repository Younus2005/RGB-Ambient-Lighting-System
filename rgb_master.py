import serial
import time
import threading
import numpy as np
import sounddevice as sd
import mss
import cv2
import math
import random
import tkinter as tk
from tkinter import ttk, colorchooser
from collections import deque

# ================= CONFIG =================
COM_PORT = "COM5"
BAUD = 500000
NUM_LEDS = 64
LEDS_PER_FAN = 16
DEVICE_ID = 1
TARGET_FPS = 90
FRAME_TIME = 1 / TARGET_FPS

MODE = "screen"

arduino = serial.Serial(COM_PORT, BAUD)
time.sleep(2)

# ================= BUFFERS =================
screen_ring = np.zeros((NUM_LEDS,3), dtype=np.float32)
music_ring  = np.zeros((NUM_LEDS,3), dtype=np.float32)
manual_color = np.array([255,0,0], dtype=np.float32)

# =================================================
# ================= SCREEN ENGINE =================
# =================================================

def ultra_hdr(frame):
    frame = frame / 255.0
    mapped = frame / (1.0 + 0.6 * frame)
    return np.clip(mapped * 255.0, 0, 255)

def screen_thread():
    global screen_ring
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        while True:
            img = np.array(sct.grab(monitor))
            frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            h, w, _ = frame.shape
            thickness = 80
            ring = np.zeros((NUM_LEDS,3), dtype=np.float32)

            top = frame[0:thickness,:]
            right = frame[:,w-thickness:w]
            bottom = frame[h-thickness:h,:]
            left = frame[:,0:thickness]

            for i in range(LEDS_PER_FAN):
                x1 = int(i*w/LEDS_PER_FAN)
                x2 = int((i+1)*w/LEDS_PER_FAN)
                y1 = int(i*h/LEDS_PER_FAN)
                y2 = int((i+1)*h/LEDS_PER_FAN)

                ring[16+i] = np.mean(top[:,x1:x2],axis=(0,1))
                ring[32+i] = np.mean(right[y1:y2,:],axis=(0,1))
                ring[48+i] = np.mean(bottom[:,x1:x2],axis=(0,1))
                ring[i]     = np.mean(left[y1:y2,:],axis=(0,1))

            screen_ring[:] = ultra_hdr(np.clip(ring,0,255))
            time.sleep(0.02)

# =================================================
# ================= MUSIC ENGINE ==================
# =================================================

audio_state = {"bass":0,"mids":0,"highs":0,"volume":0,"beat":False}
energy_history = deque(maxlen=40)

def audio_thread():
    device_info = sd.query_devices(DEVICE_ID)
    samplerate = int(device_info['default_samplerate'])
    channels = device_info['max_input_channels']

    smoothing = 0.85
    prev_bass = 0

    def callback(indata, frames, time_info, status):
        nonlocal prev_bass
        audio = indata[:,0]
        fft = np.abs(np.fft.rfft(audio))

        bass_raw = np.mean(fft[0:20])
        mids_raw = np.mean(fft[20:100])
        highs_raw = np.mean(fft[100:300])
        volume = np.mean(fft)

        energy_history.append(volume)
        avg = np.mean(energy_history)
        beat = volume > avg * 1.3

        sensitivity = 3.0
        bass = min(int(bass_raw*sensitivity),255)
        mids = min(int(mids_raw*sensitivity),255)
        highs = min(int(highs_raw*sensitivity),255)

        bass = int(prev_bass*smoothing + bass*(1-smoothing))
        prev_bass = bass

        audio_state.update({
            "bass":bass,
            "mids":mids,
            "highs":highs,
            "volume":volume,
            "beat":beat
        })

    with sd.InputStream(device=DEVICE_ID,
                        channels=channels,
                        samplerate=samplerate,
                        blocksize=2048,
                        callback=callback):
        while True:
            time.sleep(1)

def music_thread():
    global music_ring

    prev_frame = np.zeros((NUM_LEDS,3))
    particles = []
    collapse_active = False
    collapse_radius = 0
    shockwave_active = False
    shockwave_radius = 0
    depth_offset = 0
    depth_direction = 1

    while True:

        full_frame = np.zeros((NUM_LEDS,3))

        bass = audio_state["bass"]
        mids = audio_state["mids"]
        highs = audio_state["highs"]
        base_color = np.array([bass,mids,highs])

        # 3D swirl mapping
        for fan in range(4):
            start = fan * LEDS_PER_FAN
            for i in range(LEDS_PER_FAN):
                idx = start + i
                swirl = math.sin(i*0.5 + time.time()*2 + fan*0.8)
                full_frame[idx] += base_color*(swirl+1)/2

        depth_offset += depth_direction*(bass/255)*0.4
        if audio_state["beat"]:
            depth_direction *= -1

        # Fog
        for i in range(NUM_LEDS):
            fog = math.sin(i*0.15 + time.time()*0.3)
            full_frame[i] += base_color*((fog+1)/2)*0.2

        # Ember particles
        if random.random() < 0.05:
            particles.append({"pos":random.randint(0,NUM_LEDS),"life":1.0})

        for p in particles:
            idx = int(p["pos"])%NUM_LEDS
            intensity = p["life"]*255
            full_frame[idx] += [intensity,intensity*0.4,0]
            p["pos"] += random.uniform(-0.5,0.5)
            p["life"] -= 0.02

        particles = [p for p in particles if p["life"]>0]

        # Lightning
        if audio_state["beat"] and random.random()<0.3:
            start = random.randint(0,NUM_LEDS)
            for i in range(10):
                full_frame[(start+i)%NUM_LEDS] += [255,255,255]

        # Black hole collapse
        if bass>210 and not collapse_active:
            collapse_active=True
            collapse_radius=NUM_LEDS//2

        if collapse_active:
            for i in range(NUM_LEDS):
                if abs(i-NUM_LEDS//2)<collapse_radius:
                    full_frame[i]*=0.1
            collapse_radius-=3
            if collapse_radius<=0:
                collapse_active=False
                shockwave_active=True
                shockwave_radius=0

        # Shockwave
        if shockwave_active:
            for i in range(NUM_LEDS):
                dist=min(abs(i-shockwave_radius),
                         NUM_LEDS-abs(i-shockwave_radius))
                intensity=max(0,255-dist*25)
                full_frame[i]+=[255,255,255]*(intensity/255)
            shockwave_radius+=4
            if shockwave_radius>NUM_LEDS:
                shockwave_active=False

        full_frame=np.clip(full_frame,0,255)
        current=prev_frame+(full_frame-prev_frame)*0.4
        prev_frame=current.copy()

        music_ring[:]=current
        time.sleep(0.01)

# =================================================
# ================= MASTER RENDER =================
# =================================================

def render_thread():
    prev_frame=np.zeros((NUM_LEDS,3))
    while True:
        start=time.time()

        if MODE=="screen":
            full=np.copy(screen_ring)
        elif MODE=="music":
            full=np.copy(music_ring)
        elif MODE=="hybrid":
            full=0.5*np.copy(screen_ring)+0.5*np.copy(music_ring)
        elif MODE=="manual":
            full=np.ones((NUM_LEDS,3))*manual_color
        else:
            full=np.zeros((NUM_LEDS,3))

        current=prev_frame+(full-prev_frame)*0.35
        prev_frame=current.copy()

        try:
            arduino.write(np.clip(current,0,255)
                          .astype(np.uint8)
                          .flatten()
                          .tobytes())
        except:
            pass

        elapsed=time.time()-start
        if FRAME_TIME-elapsed>0:
            time.sleep(FRAME_TIME-elapsed)

# =================================================
# ===================== GUI =======================
# =================================================

def launch_gui():
    global MODE, manual_color
    root=tk.Tk()
    root.title("RGB Control")
    root.geometry("300x260")
    root.configure(bg="#111")

    def set_mode(m):
        global MODE
        MODE=m

    def pick():
        global manual_color
        c=colorchooser.askcolor()[0]
        if c:
            manual_color=np.array(c)

    ttk.Button(root,text="Screen Mode",command=lambda:set_mode("screen")).pack(pady=6)
    ttk.Button(root,text="Music Mode",command=lambda:set_mode("music")).pack(pady=6)
    ttk.Button(root,text="Hybrid Mode",command=lambda:set_mode("hybrid")).pack(pady=6)
    ttk.Button(root,text="Manual Mode",command=lambda:set_mode("manual")).pack(pady=6)
    ttk.Button(root,text="Pick Manual Color",command=pick).pack(pady=6)

    root.mainloop()

# ================= START =================
threading.Thread(target=screen_thread,daemon=True).start()
threading.Thread(target=audio_thread,daemon=True).start()
threading.Thread(target=music_thread,daemon=True).start()
threading.Thread(target=render_thread,daemon=True).start()
threading.Thread(target=launch_gui).start()

while True:
    time.sleep(1)