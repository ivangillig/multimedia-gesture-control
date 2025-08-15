try:
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    from comtypes import CLSCTX_ALL
    from ctypes import cast, POINTER
    PYCAW_AVAILABLE = True
except ImportError:
    PYCAW_AVAILABLE = False

import subprocess
import time

class VolumeControl:
    def __init__(self):
        self.current_volume = 50
        self.is_muted = False
        self.last_mute_toggle = 0
        self.mute_cooldown = 1.0  # 1 segundo entre toggles
        
        if PYCAW_AVAILABLE:
            try:
                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                self.volume = cast(interface, POINTER(IAudioEndpointVolume))
                self.vol_range = self.volume.GetVolumeRange()
                self.min_vol = self.vol_range[0]
                self.max_vol = self.vol_range[1]
                self.pycaw_enabled = True
            except:
                self.pycaw_enabled = False
        else:
            self.pycaw_enabled = False

    def map_distance_to_volume(self, distance, min_dist=0.05, max_dist=0.8):
        """Mapear distancia entre manos a porcentaje de volumen"""
        if distance < min_dist:
            distance = min_dist
        if distance > max_dist:
            distance = max_dist
        
        volume_percent = ((distance - min_dist) / (max_dist - min_dist)) * 100
        return int(volume_percent)

    def set_volume(self, vol_percent):
        """Establecer volumen del sistema"""
        self.current_volume = max(0, min(100, vol_percent))
        print(f"🔊 Volumen: {self.current_volume}%")  # Debug
        
        if self.pycaw_enabled:
            try:
                vol_db = self.min_vol + (self.current_volume / 100) * (self.max_vol - self.min_vol)
                self.volume.SetMasterVolumeLevel(vol_db, None)
                return True
            except Exception as e:
                print(f"❌ Error pycaw: {e}")
                return self._fallback_volume_control(self.current_volume)
        else:
            return self._fallback_volume_control(self.current_volume)

    def toggle_mute(self):
        """Alternar mute/unmute con cooldown"""
        current_time = time.time()
        if current_time - self.last_mute_toggle > self.mute_cooldown:
            self.is_muted = not self.is_muted
            self.last_mute_toggle = current_time
            
            if self.pycaw_enabled:
                try:
                    self.volume.SetMute(self.is_muted, None)
                except:
                    self._fallback_mute()
            else:
                self._fallback_mute()
            
            return True
        return False

    def _fallback_volume_control(self, volume):
        """Control de volumen alternativo usando PowerShell"""
        try:
            print(f"🔊 Fallback volumen: {volume}%")
            # Usar PowerShell para controlar volumen
            cmd = f'''
            Add-Type -TypeDefinition @"
            using System.Runtime.InteropServices;
            [Guid("5CDF2C82-841E-4546-9722-0CF74078229A"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
            interface IAudioEndpointVolume {{
                int NotImpl1(); int NotImpl2(); int NotImpl3(); int NotImpl4();
                int SetMasterVolumeLevelScalar(float fLevel, System.Guid pguidEventContext);
            }}
            "@
            $speakers = (New-Object -ComObject MMDeviceEnumerator).GetDefaultAudioEndpoint(0, 1)
            $volume = $speakers.Activate([System.Type]::GetTypeFromCLSID("5CDF2C82-841E-4546-9722-0CF74078229A"), $null, $null)
            $volume.SetMasterVolumeLevelScalar({volume / 100}, [System.Guid]::Empty)
            '''
            subprocess.run(['powershell', '-Command', cmd], 
                         check=False, capture_output=True, timeout=3)
            return True
        except Exception as e:
            print(f"❌ Error fallback volumen: {e}")
            return False

    def _fallback_mute(self):
        """Mute alternativo usando nircmd"""
        try:
            subprocess.run(['nircmd.exe', 'mutesysvolume', '2'], 
                         check=False, capture_output=True)
        except:
            pass

    def get_current_volume(self):
        """Obtener volumen actual"""
        if self.pycaw_enabled:
            try:
                current_vol_db = self.volume.GetMasterVolumeLevel()
                volume_percent = ((current_vol_db - self.min_vol) / (self.max_vol - self.min_vol)) * 100
                self.current_volume = max(0, min(100, int(volume_percent)))
            except:
                pass
        
        return self.current_volume
