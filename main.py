from machine import Pin, I2C
from lcd_api import LcdApi
from pico_i2c_lcd import I2cLcd
import utime
import time

I2C_ADDR = 0x27
I2C_NUM_ROWS = 2
I2C_NUM_COLS = 16
i2c = I2C(0, sda=machine.Pin(0), scl=machine.Pin(1), freq=400000)
lcd = I2cLcd(i2c, I2C_ADDR, I2C_NUM_ROWS, I2C_NUM_COLS)

capteur = machine.Pin(15, machine.Pin.IN, machine.Pin.PULL_UP)


# Temps minimum entre deux détections de tour (en millisecondes)
temps_min_entre_tours = 100  # 100 millisecondes

# Dernier temps de détection de tour
dernier_temps_tour = 0



def afficher_temps_lcd(temps):
    global temps_ecoule, compteur_tours, pause
    heures = temps // 3600
    minutes = (temps % 3600) // 60
    secondes = temps % 60
    lcd.move_to(0, 0)  # Déplacer le curseur à la première colonne de la première ligne
    lcd.putstr("Tours : " + str(compteur_tours))
    lcd.move_to(0, 1)  # Déplacer le curseur à la première colonne de la deuxième ligne
    lcd.putstr("{:02}:{:02}:{:02}".format(heures, minutes, secondes))
    if temps_ecoule - derniereImpulsion >= 8 :
        lcd.move_to(10, 0)
        lcd.putstr("Pause")
        pause = False
    if temps_ecoule - derniereImpulsion < 8 :
        lcd.move_to(10, 0)
        lcd.putstr("Route")
        

# Fonction de détection de rotation
def detecter_rotation(pin):
    global compteur_tours, dernier_temps_tour, derniereImpulsion, pause
    temps_actuel = utime.ticks_ms()
    if utime.ticks_diff(temps_actuel, dernier_temps_tour) > temps_min_entre_tours:
        print("Temps tour dernier tour:", dernier_temps_tour)
        dernier_temps_tour = temps_actuel
        derniereImpulsion = temps_ecoule
        compteur_tours += 1
        if pause == False:
            pause = True
            demarrer_chronometre_et_compteur()



# Fonction pour démarrer le chronomètre et le comptage de tours
def demarrer_chronometre_et_compteur():
    global temps_ecoule, compteur_tours
    print("Démarrage du chrono")
    #temps_ecoule = 0
    #compteur_tours = 0
    while pause:
        time.sleep(1)
        temps_ecoule += 1
        afficher_temps_lcd(temps_ecoule)

# Initialiser le temps écoulé à 0
temps_ecoule = 0

# Initialiser le compteur de tours à 0
compteur_tours = 0

# Variable pour mettre en pause le chrono
pause = True

derniereImpulsion = 0


# Attacher la fonction de détection à l'interruption du capteur
capteur.irq(trigger=Pin.IRQ_FALLING, handler=detecter_rotation)

# Démarrer le chronomètre et le comptage de tours dans un thread séparé
demarrer_chronometre_et_compteur()