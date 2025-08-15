import subprocess
import time
import ctypes
from ctypes import wintypes
from config import GestureConfig

# Constantes de Windows para teclas multimedia
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1  
VK_MEDIA_STOP = 0xB2
VK_MEDIA_PLAY_PAUSE = 0xB3

# Constantes para keybd_event
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002

class MediaControl:
    def __init__(self):
        self.last_action_time = 0
        self.action_cooldown = GestureConfig.MEDIA_COOLDOWN
        
        # Cargar user32.dll para acceso directo a teclas multimedia
        self.user32 = ctypes.windll.user32
        
    def _send_media_key(self, vk_code):
        """Enviar tecla multimedia usando la API de Windows directamente"""
        try:
            # Presionar tecla
            self.user32.keybd_event(vk_code, 0, KEYEVENTF_EXTENDEDKEY, 0)
            # Soltar tecla
            self.user32.keybd_event(vk_code, 0, KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, 0)
            return True
        except Exception as e:
            print(f"❌ Error enviando tecla multimedia: {e}")
            return False
        
    def next_track(self):
        """Pasar a la siguiente canción"""
        current_time = time.time()
        if current_time - self.last_action_time > self.action_cooldown:
            self.last_action_time = current_time
            print("🎵 Siguiente canción (tecla multimedia)")
            return self._send_media_key(VK_MEDIA_NEXT_TRACK)
        return False

    def previous_track(self):
        """Volver a la canción anterior"""
        current_time = time.time()
        if current_time - self.last_action_time > self.action_cooldown:
            self.last_action_time = current_time
            print("⏮️ Canción anterior (tecla multimedia)")
            return self._send_media_key(VK_MEDIA_PREV_TRACK)
        return False

    def play_pause(self):
        """Play/Pause"""
        current_time = time.time()
        if current_time - self.last_action_time > self.action_cooldown:
            self.last_action_time = current_time
            print("⏯️ Play/Pause (tecla multimedia)")
            return self._send_media_key(VK_MEDIA_PLAY_PAUSE)
        return False
    
    def stop(self):
        """Stop (función adicional)"""
        current_time = time.time()
        if current_time - self.last_action_time > self.action_cooldown:
            self.last_action_time = current_time
            print("⏹️ Stop (tecla multimedia)")
            return self._send_media_key(VK_MEDIA_STOP)
        return False
