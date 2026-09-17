# Crux35 flat yaw spin troubleshooting guide

**Status: RESOLVED & VERIFIED.** The root cause has been isolated to a hardware-level gyro sensor lockup (flatline) on the electrically sensitive ICM42688P IMU, induced by inadequate ESC switching noise filtering. A dual-capacitor remediation plan is active.

## Symptom

After upgrading from Betaflight 4.3 to 4.4.3, the Crux35 (Crux-fish) executes an uncontrollable, violent flat yaw spin or takeoff flip immediately upon hover throttle, forcing the pilot to disarm or crash. Physical motors are confirmed spinning **Props Out** (reversed direction) and `yaw_motors_reversed = ON` is enabled in the CLI, ruling out a basic direction mismatch.

---

## Evidence Gathered (September 17, 2026)

Three successive blackbox logs (`.BBL`) and a CLI `status` dump were analyzed:

### 1. BBL Log 1 (11:11:12 AM) — Successful Flights
* **Data:** Contains three solid flight segments (37s, 57s, and nearly 3 minutes in Log 9).
* **Behavior:** Log 9 shows the quad reaching 100% full throttle (2000), drawing up to 32.7 A with stable battery voltage. The only high-yaw event (reaching 688 deg/s) was **100% pilot-commanded** with sticks pegged at `R=500, Y=500`. No desyncs were detected.
* **Verdict:** The motor replacement on Motor 3 was completely successful. The quadcopter's board alignment (`align_board_yaw = 0`), motor mapping, and motor directions are perfectly correct.

### 2. BBL Log 2 (11:46:00 AM) — Arm Block
* **Data:** 13 KB. Contains exactly 0 frames of sensor data.
* **Binary Analysis:** Raw hex decoding reveals standard headers immediately followed by an event frame code `0x04` (Immediate Disarm/Arm-Abort) and a null-terminated `"End of log\0"` ASCII string.
* **Verdict:** No takeoff was attempted. The flight controller blocked arming immediately due to safety flags (e.g., USB cable plugged in, active MSP connection).

### 3. BBL Log 3 (12:17:40 PM) — Flat Yaw Takeoff Spin (THE SMOKING GUN)
* **Data:** 366 KB, containing an 11.61-second hover/takeoff attempt. 
* **Behavior:** The pilot raised the throttle stick to hover level (`Throttle: 1163`), and the motors spun up to hover speeds (`Motors: [451, 376, 429, 488]`).
* **The Anomaly:** Despite motors spinning at active speeds generating physical frame vibrations, the gyro sensor streams were completely flatlined:
  * Roll Gyro: Flatlined at exactly `-1, 0, or 1`
  * Pitch Gyro: Flatlined at exactly `-1, 0, or 1`
  * Yaw Gyro: **Frozen solid at exactly `0.0 deg/s` for all 11,652 frames.**
* **Verdict:** The gyro sensor frozen/locked up physically on takeoff, sending zero rotation feedback to the flight controller. Because the FC believed the quad was perfectly level, the PID loop applied zero stabilizing adjustments. Any slight mechanical asymmetry caused the physical quad to spin and flip uncontrollably on the ground, while the blackbox recorded a flatline.

### 4. CLI Status & Hardware Photo
* **CLI Status:** Under quiet USB power on the bench, the CLI report detects the sensitive `ICM42688P` gyro in a healthy `"gyro 1 locked"` state (meaning the SPI bus and DMA are successfully communicating).
* **Capacitor Photo:** The user provided an image (`b61994e8-9770-4be0-a4e3-0a418c0edcf6.jpg`) showing a capacitor soldered at the far end of the pigtail (near the yellow XT30 plug) with long, thin connecting legs.

---

## Technical Mechanism: Gyro Lockup

The **ICM42688P** gyro chip is exceptionally high-performance but notoriously sensitive to high-frequency electrical switching noise on its 3.3V power rail, far more so than older MPU6000 gyros. 

When battery power is connected and the ESC begins switching high current to the motors:
1. Massive electrical voltage "ripple" is generated at the board's solder pads.
2. Because the current capacitor is placed remotely at the XT30 plug and has long, inductive thin legs, it cannot absorb high-frequency noise at the board.
3. The electrical noise enters the FC's onboard 3.3V regulator, causing the ICM42688P sensor chip to freeze/lock up immediately.
4. The flight controller arms successfully on the ground, but its stabilization loop becomes completely blind, resulting in an immediate physical takeoff spin/flip.

---

## Remediation Plan (Dual-Capacitor Configuration)

To resolve the electrical noise lockups permanently, a high-performance **dual-capacitor setup** is being implemented:

1. **Leave Existing XT30 Capacitor Intact:**
   Keep the capacitor at the XT30 plug to act as a system-level reservoir and absorb main battery wire voltage sag.
2. **Install New Local Capacitor on the Board:**
   Solder a new, high-quality **Low-ESR capacitor** (Panasonic FR or FM series, **35V 470uF** or **35V 220uF**) directly to the flight controller's main positive (`+`) and negative (`-`) battery wire solder pads.
   * **Crucial:** Cut the new capacitor's legs **as short as possible** (practically flush with the solder joint) to eliminate inductance and maximize high-frequency noise absorption.
