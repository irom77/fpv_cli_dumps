# Crux35 flat yaw spin troubleshooting guide

**Status: Investigation prepared, awaiting physical bench tests.** The quad executes a violent, flat yaw spin immediately on takeoff or when throttle is raised. 

## Symptom

After upgrading from Betaflight 4.3 to 4.4.3, the Crux35 (Crux-fish) executes an uncontrollable flat yaw spin on takeoff. The owner has verified that physical motors are spinning **Props Out** (reversed direction) and `yaw_motors_reversed = ON` is correctly enabled in the CLI, ruling out a basic motor direction mismatch.

## The Control-Loop Mechanism

A flat yaw spin is caused by a **positive feedback loop** in the flight controller's PID yaw axis. If the gyro senses a minute clockwise (CW) disturbance:
1. The flight controller attempts to correct it by commanding leftward (CCW) yaw torque.
2. It increases throttle to the CW-stabilizing motors (which are expected to spin CCW).
3. If there is an orientation, mapping, or pin mismatch, this corrective output actually generates **more CW torque** instead of CCW torque.
4. The quad rotates faster CW. The flight controller detects the growing error and applies even more corrective power, spinning the quad flat on the spot.

---

## Ranked Hypotheses

### 1. Incorrect Board/Gyro Alignment (`align_board_yaw`) (HIGH PROBABILITY)
The Crux35 All-in-One (AIO) flight controller is physically mounted in a **45-degree diamond pattern** relative to the frame arms. Because the generic `BETAFLIGHTF4` target defaults to a standard 0-degree square orientation, if the custom board alignment was not restored after the 4.4.3 upgrade, pitch/roll/yaw corrections will be "cross-talked" onto the wrong axes, triggering an instant spin/flip.

*   **Prediction:** Moving the physical quadcopter on its pitch/roll/yaw axes will not be mirrored correctly by the 3D model in the **Setup** tab of Betaflight Configurator.
*   **Test Command (CLI):**
    ```cli
    get align_board_yaw
    ```
*   **Correction Commands (CLI):**
    ```cli
    set align_board_yaw = 45
    save
    ```
    *(If 45 is incorrect, try `315` or `-45` depending on the physical board's orientation).*

### 2. Incorrect Motor Mapping / Swapped Pins (MEDIUM PROBABILITY)
In Betaflight 4.4+, unified target resource mappings can sometimes mismatch with the ESC's physical connections. If physical Motor 3 and Motor 4 pins are swapped, corrective yaw commands will go to the wrong corner of the quad.

*   **Prediction:** In the **Motors** tab (props off, battery in), spinning Slider 3 or 4 will spin the incorrect physical motor.
*   **Current Mapping (CLI):**
    ```cli
    resource MOTOR 1 B00
    resource MOTOR 2 B01
    resource MOTOR 3 C09
    resource MOTOR 4 C08
    ```
*   **Test:** Spin up Sliders 1 through 4 one-by-one. Verify:
    *   Slider 1 -> Rear-Right motor spins.
    *   Slider 2 -> Front-Right motor spins.
    *   Slider 3 -> Rear-Left motor spins.
    *   Slider 4 -> Front-Left motor spins.
*   **Correction:** Use the built-in **Reorder Motors** wizard in the Betaflight Configurator Motors tab to automatically detect and remap the resources.

### 3. Propeller Orientation / Mounting Mismatch (LOW PROBABILITY)
Although the motor directions are verified as spinning **Props Out** (Motor 1 CCW, Motor 2 CW, Motor 3 CW, Motor 4 CCW), the propellers themselves might be installed on the wrong corners or upside down.

*   **Prediction:** Visual inspection of propeller blades shows thrust is pushed upwards or blade curve is backwards relative to rotation.
*   **Test:** Ensure:
    *   CW-curved propellers are on CW-spinning motors (Motors 2 & 3).
    *   CCW-curved propellers are on CCW-spinning motors (Motors 1 & 4).
    *   Propeller embossing/text faces **UP** toward the sky.

---

## Action Plan (Next Bench Steps)

Since USB port access is currently restricted, apply these steps once bench access is available:

1.  **Verify Gyro Alignment:**
    Place the quad flat on the desk facing forward. Tilt the physical nose down and rotate it clockwise. Ensure the 3D model in the **Setup** tab mirrors this behavior exactly.
2.  **Verify Motor Sliders:**
    Go to the **Motors** tab (props off!), slide up Sliders 1, 2, 3, and 4 individually, and verify the correct physical motor spins.
3.  **Confirm Propellers:**
    Double-check that CW/CCW props match CW/CCW motor bells.
