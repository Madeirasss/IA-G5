from ev3dev2.motor import MoveTank, OUTPUT_D, OUTPUT_B, SpeedPercent, OUTPUT_C, MediumMotor
from time import sleep
from ev3dev2.sensor import INPUT_4, INPUT_3, INPUT_1, INPUT_2
from ev3dev2.sensor.lego import UltrasonicSensor, ColorSensor, TouchSensor, GyroSensor
from ev3dev2.console import Console
from ev3dev2.sound import Sound
import sys

sensor_ultrassonico = UltrasonicSensor(INPUT_3)
sensor_toque = TouchSensor(INPUT_2)
sensor_cor = ColorSensor(INPUT_1)
motor_medio = MediumMotor(OUTPUT_C)
movimento = MoveTank(OUTPUT_D, OUTPUT_B)
sensor_giro = GyroSensor(INPUT_4)
som = Sound()


def calcular_angulo_giro():
    sensor_giro.reset()
    angulo = sensor_giro.angle
    print("Angulo de giro: ")
    print(angulo)
    print(" graus")

def detetar_cor():
    color_id = sensor_cor.color
    color_name = ""
    
    if color_id == 0:
        color_name = "Unknown"
    elif color_id == 1:
        color_name = "Black"
    elif color_id == 2:
        color_name = "Blue"
    elif color_id == 3:
        color_name = "Green"
    elif color_id == 4:
        color_name = "Yellow"
    elif color_id == 5:
        color_name = "Red"
    elif color_id == 6:
        color_name = "White"
    elif color_id == 7:
        color_name = "Brown"
    else:
        color_name = "ID Desconhecido"
    
    print("Cor:")
    print(color_name)

def distancia():
    distancia_cm = sensor_ultrassonico.distance_centimeters
    print("Distancia: ")
    print(distancia_cm)
    print(" cm")

def sensor_toque_estado():
    if sensor_toque.is_pressed:
        print("Estado: PRESSIONADO!")
        som.speak("Amassa-me a manteiga", espeak_opts='-v pt')
    else:
        print("Estado: Nao pressionado.")

def main():
    som.speak("Se ela quiser somos 2 a querer", espeak_opts='-v pt',volume=100)
    movimento.on_for_seconds(SpeedPercent(30), SpeedPercent(30), 3)
    calcular_angulo_giro()
    movimento.on_for_seconds(SpeedPercent(-30), SpeedPercent(30), 3)
    calcular_angulo_giro()
    movimento.on_for_seconds(SpeedPercent(30), SpeedPercent(30), 3)
    calcular_angulo_giro()
    movimento.on_for_seconds(SpeedPercent(-30), SpeedPercent(30), 3)
    calcular_angulo_giro()
    som.speak("Morre SACANA", espeak_opts='-v pt',volume=100)
    motor_medio.on_for_seconds(SpeedPercent(75), 3)
    while True:
        detetar_cor()
        distancia()
        sensor_toque_estado()
        print("---------------------------") 
        sleep(1)
    

main()

