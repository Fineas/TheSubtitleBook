import RPi.GPIO as GPIO
import time
GPIO.setmode(GPIO.BOARD)  # Use physical pin numbering

class Servo():

    def __init__(self):
        # Define pins for each servo
        self.page_arm = 3
        self.page_finger = 5
        self.down_left = 18
        self.down_right = 12

        # Set up GPIO pins
        GPIO.setup(self.down_left, GPIO.OUT)  
        GPIO.setup(self.down_right, GPIO.OUT)  
        GPIO.setup(self.page_arm, GPIO.OUT)  
        GPIO.setup(self.page_finger, GPIO.OUT)  

        # Initialize PWM for each servo
        self.pwm_dl = GPIO.PWM(self.down_left, 50)  
        self.pwm_dr = GPIO.PWM(self.down_right, 50)  
        self.pwm_pa = GPIO.PWM(self.page_arm, 50)  
        self.pwm_pf = GPIO.PWM(self.page_finger, 50) 
        self.pwm_dl.start(0)
        self.pwm_dr.start(0)
        self.pwm_pa.start(0)
        self.pwm_pf.start(0)

    # Set a specific angle on the servo
    def set_servo_angle(self, pwm, angle):
        """
        Set the servo to a specific angle (0-180).
        
        Parameters:
        pwm (PWM): The PWM instance for the specific servo.
        angle (int): The angle to set the servo to.
        """
        duty_cycle = 2 + (angle / 18)  # Maps 0-180 to 2-12 duty cycle range
        pwm.ChangeDutyCycle(duty_cycle)
        time.sleep(0.02)  # Small delay to let servo reach position

    # Down movement with simultaneous, mirrored movement for pwm_dl and pwm_dr
    def get_down(self):
        """
        Move pwm_dr from 180 to 90 and pwm_dl from 0 to 90 simultaneously.
        """
        for step in range(0, 61, 2):  # Use step=2 for smoother, gradual movement
            # Calculate angles for each servo
            angle_dr = 170 - step  # pwm_dr goes from 180 to 90
            angle_dl = step   # pwm_dl goes from 0 to 90

            # Set each servo to its calculated angle
            self.set_servo_angle(self.pwm_dr, angle_dr)
            self.set_servo_angle(self.pwm_dl, angle_dl)
            
            time.sleep(0.05)  # Short delay for smooth transition

    # Up movement with simultaneous, mirrored movement for pwm_dl and pwm_dr
    def get_up(self):
        """
        Move pwm_dr from 90 to 180 and pwm_dl from 90 to 0 simultaneously.
        """
        for step in range(0, 61, 2):  # Use step=2 for smoother, gradual movement
            # Calculate angles for each servo
            angle_dr = 110 + step  # pwm_dr goes from 90 to 180
            angle_dl = 60 - step  # pwm_dl goes from 90 to 0

            # Set each servo to its calculated angle
            self.set_servo_angle(self.pwm_dr, angle_dr)
            self.set_servo_angle(self.pwm_dl, angle_dl)
            
            time.sleep(0.05)  # Short delay for smooth transition

    def smooth_move_servo(self, pwm, start_angle, end_angle, step=2, delay=0.05):
        if start_angle < end_angle:
            angle_range = range(start_angle, end_angle + 1, step)
        else:
            angle_range = range(start_angle, end_angle - 1, -step)
        
        for angle in angle_range:
            self.set_servo_angle(pwm, angle)
            time.sleep(delay)
    def turn_page(self):
        try:
            self.set_servo_angle(self.pwm_pa, 90)
            self.set_servo_angle(self.pwm_pf, 180)
            # time.sleep(100)
            # Step 1: Move page_arm from 90 to 20 degrees
            self.smooth_move_servo(self.pwm_pa, start_angle=90, end_angle=160, step=2, delay=0.05)
            
            # Step 2: Move page_finger from 90 to 170 degrees
            self.smooth_move_servo(self.pwm_pf, start_angle=180, end_angle=20, step=2, delay=0.05)

            # Step 3: Move page_arm back to 90 degrees
            self.smooth_move_servo(self.pwm_pa, start_angle=150, end_angle=90, step=2, delay=0.05)
            
            # Step 4: Move page_arm from 90 to 160 and page_finger from 90 to 180 simultaneously
            for step in range(0, 71, 2):  # Steps of 2 for smoother movement
                angle_pa = 90 - step  # page_arm moves from 90 to 160
                angle_pf = 90 + int((step / 70) * 90)  # page_finger moves from 90 to 180
                self.set_servo_angle(self.pwm_pa, angle_pa)
                self.set_servo_angle(self.pwm_pf, angle_pf)
                time.sleep(0.05)  # Short delay for smooth transition

        finally:
            # Stop PWM signals to prevent jitter and cleanup
            self.pwm_pa.ChangeDutyCycle(0)
            self.pwm_pf.ChangeDutyCycle(0)

# Main execution
# if __name__ == "__main__":
    # try:
    #     get_down()
    #     # time.sleep(1)  # Pause between movements
    #     # get_up()
    #     time.sleep(1)
    #     # turn_page()
    # finally:
    #     pwm_dl.stop()
    #     pwm_dr.stop()
    #     pwm_pa.stop()
    #     pwm_pf.stop()
    #     GPIO.cleanup()
