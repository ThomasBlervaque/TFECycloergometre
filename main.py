from machine import Pin, I2C, ADC, PWM
from lcd_api import LcdApi
from pico_i2c_lcd import I2cLcd
import utime
import time
import math

# Récupération de l'adresse I2C pour l'ecran LCD
I2C_ADDR = 0x27
I2C_NUM_ROWS = 2
I2C_NUM_COLS = 16
i2c = I2C(0, sda=machine.Pin(0), scl=machine.Pin(1), freq=400000)
lcd = I2cLcd(i2c, I2C_ADDR, I2C_NUM_ROWS, I2C_NUM_COLS)

#Association de la pin 15 au capteur de tour
capteur = machine.Pin(15, machine.Pin.IN, machine.Pin.PULL_UP)

# Association de la pin 14 à l'avancé ou recul du moteur
dir_pin = machine.Pin(14, machine.Pin.OUT)

# Association de la pin 13 à pwm qui permet de gérer la vitesse du moteur
pwm = PWM(machine.Pin(13), freq=100)

# Association de la pin 2 au button d'avancé du moteur
button_pin = machine.Pin(2, machine.Pin.IN, machine.Pin.PULL_DOWN)

# Association de la pin 2 au button de recul du moteur
button_av = machine.Pin(3, machine.Pin.IN, machine.Pin.PULL_DOWN)

machine.Pin(23, machine.Pin.OUT).value(0)


# Temps minimum entre deux détections de tour (en millisecondes)
temps_min_entre_tours = 100 # 100 millisecondes

# Dernier temps de détection de tour
dernier_temps_tour = 0

# Initialiser le temps écoulé à 0
temps_ecoule = 0

# Initialiser le compteur de tours à 0
compteur_tours = 0

# Temps de la derniere impulsion
derniereImpulsion = 0

# Temps entre deux impulsions
tempPulse = 0

# Vitesse calculer à partir de tempPulse
vitesse = 0

# Position du moteur ( 1 à 6)
pos_moteur = 0

# Vitesse pwm pour le moteur
duty = 8000

# Vitesse arrondie pour l'affichage
vitesse_arrondie = 0

# Valeur pour eviter le rebond des boutons
last_press_time = 0

last_press_time2 = 0

# Delay pour eviter rebond des boutons
debounce_delay = 600


# Fonction d'affichage du temps et la vitesse sur l'écran LCD
def afficher_temps_lcd(temps, vit):
    heures = temps // 3600
    minutes = (temps % 3600) // 60
    secondes = temps % 60
    lcd.move_to(0, 1)  # Déplacer le curseur à la première colonne de la deuxième ligne
    lcd.putstr("{:02}:{:02}:{:02}      {:02}".format(heures, minutes, secondes, pos_moteur))
    lcd.move_to(0, 0)
    lcd.putstr("Vitesse :   {:04}".format(vit))
        

# Fonction de détection de rotation
def detecter_rotation(pin):
    global compteur_tours, dernier_temps_tour, derniereImpulsion, tempPulse, vitesse, vitesse_arrondie
    print('detect')
    temps_actuel = utime.ticks_ms()
    if utime.ticks_diff(temps_actuel, dernier_temps_tour) > temps_min_entre_tours:
        tempPulse = temps_actuel - dernier_temps_tour
        dernier_temps_tour = temps_actuel
        derniereImpulsion = temps_ecoule
        compteur_tours += 1
        print(tempPulse)
        vitesse = (1/(tempPulse/1000))*60
        print("Moyenne nombre tour minute : ", vitesse)
        vitesse_arrondie = round(vitesse, 0)

# Fonction lié au bouton pour faire avancer le moteur
def bouton_presse(pin):
    global last_press_time, pos_moteur
    current_time = utime.ticks_ms()
    if pin.value() == 0:
        if utime.ticks_diff(current_time, last_press_time) > debounce_delay:
            print("T: ", utime.ticks_diff(current_time, last_press_time))
            new_recul_mot()
            current_time = utime.ticks_ms()
            last_press_time = current_time

# Fonction lié au bouton pour faire reculer le moteur           
def bouton_presse2(pin):
    global last_press_time2, pos_moteur
    current_time = utime.ticks_ms()
    if pin.value() == 0:
        if utime.ticks_diff(current_time, last_press_time2) > debounce_delay:
            print("T: ", utime.ticks_diff(current_time, last_press_time2))
            new_avancer_mot()
            current_time = utime.ticks_ms()
            last_press_time2 = current_time
            
            
# Fonction pour démarrer le chronomètre et le comptage de tours
def demarrer_chronometre_et_compteur():
    global temps_ecoule, compteur_tours, derniereImpulsion, vitesse_arrondie
    print("Démarrage du chrono")
    time.sleep(0.5)
    while True:
        if temps_ecoule > derniereImpulsion + 3:
            t = temps_ecoule - (derniereImpulsion + 4)
            time.sleep(1)
            temps_ecoule += 1
            t += 1
            if temps_ecoule - derniereImpulsion +3 > 12:
                zero = round(0, 4)
                
                afficher_temps_lcd(math.floor(temps_ecoule), zero)
            else:
                vitesse = ((vitesse_arrondie/60)/t)*60
                vitesse_arrondie = round(vitesse, 0)
                afficher_temps_lcd(math.floor(temps_ecoule), vitesse_arrondie)
        else:
            time.sleep(1)
            temps_ecoule += 1
            afficher_temps_lcd(math.floor(temps_ecoule), vitesse_arrondie)
            
# Fonction qui permet de fixer un palier au moteur en fonction de la valeur récupéré par le potentiometre
def recup_pos_moteur():
    global pos_moteur
    adc = ADC(machine.Pin(27))
    if 0 <= (recup_res_moteur()) < 340:
        return(1)
    if 341< (recup_res_moteur()) < 681:
        return(2)
    if 682 < (recup_res_moteur()) < 1022:
        return(3)
    if 1023 < (recup_res_moteur()) < 1363:
        return(4)
    if 1364 < (recup_res_moteur()) < 1704:
        return(5)
    if 1705 < (recup_res_moteur()) < 2047:
        return(6)
    print("recup fait")

def recup_res_moteur():
    adc = ADC(machine.Pin(27))
    return (adc.read_u16()>>4)

# Fonction lié au bouton qui permet le recul du moteur jusqu'à un certain palier
def new_recul_mot():
    global temps_ecoule, pos_moteur
    pwm.duty_u16(0)
    print("Appel recul")
    if pos_moteur == 6:
        print("Recul accepté")
        target_res_max = 1559
        target_res_min = 1509
        while not target_res_min < recup_res_moteur() < target_res_max:
            print(recup_res_moteur())
            time.sleep(0.25)
            dir_pin.value(0)
            pwm.duty_u16(duty)
            temps_ecoule += 0.25
            afficher_temps_lcd(math.floor(temps_ecoule), vitesse_arrondie)
        pwm.duty_u16(0)
        print(pos_moteur)
    elif pos_moteur == 5:
        print("Recul accepté")
        target_res_max = 1218
        target_res_min = 1168
        while not target_res_min < recup_res_moteur() < target_res_max:
            print(recup_res_moteur())
            time.sleep(0.25)
            dir_pin.value(0)
            pwm.duty_u16(duty)
            temps_ecoule += 0.25
            afficher_temps_lcd(math.floor(temps_ecoule), vitesse_arrondie)
        pwm.duty_u16(0)
        #pos_moteur = pos_moteur - 1
        print(pos_moteur)
    elif pos_moteur == 4:
        print("Recul accepté")
        target_res_max = 877
        target_res_min = 827
        while not target_res_min < recup_res_moteur() < target_res_max:
            print(recup_res_moteur())
            time.sleep(0.25)
            dir_pin.value(0)
            pwm.duty_u16(duty)
            temps_ecoule += 0.25
            afficher_temps_lcd(math.floor(temps_ecoule), vitesse_arrondie)
        pwm.duty_u16(0)
        #pos_moteur = pos_moteur - 1
        print(pos_moteur)
    elif pos_moteur == 3:
        print("Recul accepté")
        target_res_max = 536
        target_res_min = 486
        while not target_res_min < recup_res_moteur() < target_res_max:
            print(recup_res_moteur())
            time.sleep(0.25)
            dir_pin.value(0)
            pwm.duty_u16(duty)
            temps_ecoule += 0.25
            afficher_temps_lcd(math.floor(temps_ecoule), vitesse_arrondie)
        pwm.duty_u16(0)
        #pos_moteur = pos_moteur - 1
        print(pos_moteur)
    elif pos_moteur == 2:
        print("Recul accepté")
        target_res_max = 195
        target_res_min = 145
        while not target_res_min < recup_res_moteur() < target_res_max:
            print(recup_res_moteur())
            time.sleep(0.25)
            dir_pin.value(0)
            pwm.duty_u16(duty)
            temps_ecoule += 0.2
            afficher_temps_lcd(math.floor(temps_ecoule), vitesse_arrondie)
        pwm.duty_u16(0)
        #pos_moteur = pos_moteur - 1
        print(pos_moteur)
    elif pos_moteur == 1:
        print("Recul Max")
    time.sleep(0.2)
    # Vérifier la valeur finale
    res = recup_res_moteur()
    print("Valeur finale:", res)
    print(pos_moteur)
    time.sleep(0.5)
    pos_moteur = recup_pos_moteur()

    
# Fonction lié au bouton qui permet l'avancer du moteur jusqu'à un certain palier    
def new_avancer_mot():
    global temps_ecoule, pos_moteur
    pwm.duty_u16(0)
    print("Appel avancer")
    if pos_moteur == 1:
        print("Recul accepté")
        target_res_max = 536
        target_res_min = 486
        while not target_res_min < recup_res_moteur() < target_res_max:
            print(recup_res_moteur())
            time.sleep(0.25)
            dir_pin.value(1)
            pwm.duty_u16(duty)
            temps_ecoule += 0.25
            afficher_temps_lcd(math.floor(temps_ecoule), vitesse_arrondie)
        pwm.duty_u16(0)
        
    elif pos_moteur == 2:
        print("Recul accepté")
        target_res_max = 877
        target_res_min = 827
        while not target_res_min < recup_res_moteur() < target_res_max:
            print(recup_res_moteur())
            time.sleep(0.25)
            dir_pin.value(1)
            pwm.duty_u16(duty)
            temps_ecoule += 0.25
            afficher_temps_lcd(math.floor(temps_ecoule), vitesse_arrondie)
        pwm.duty_u16(0)
        
    elif pos_moteur == 3:
        print("Recul accepté")
        target_res_max = 1218
        target_res_min = 1168
        while not target_res_min < recup_res_moteur() < target_res_max:
            print(recup_res_moteur())
            time.sleep(0.25)
            dir_pin.value(1)
            pwm.duty_u16(duty)
            temps_ecoule += 0.25
            afficher_temps_lcd(math.floor(temps_ecoule), vitesse_arrondie)
        pwm.duty_u16(0)
        
    elif pos_moteur == 4:
        print("Recul accepté")
        target_res_max = 1559
        target_res_min = 1509
        while not target_res_min < recup_res_moteur() < target_res_max:
            print(recup_res_moteur())
            time.sleep(0.25)
            dir_pin.value(1)
            pwm.duty_u16(duty)
            temps_ecoule += 0.25
            afficher_temps_lcd(math.floor(temps_ecoule), vitesse_arrondie)
        pwm.duty_u16(0)
        
    elif pos_moteur == 5:
        print("Recul accepté")
        target_res_max = 1900
        target_res_min = 1850
        while not target_res_min < recup_res_moteur() < target_res_max:
            print(recup_res_moteur())
            time.sleep(0.25)
            dir_pin.value(1)
            pwm.duty_u16(duty)
            temps_ecoule += 0.25
            afficher_temps_lcd(math.floor(temps_ecoule), vitesse_arrondie)
        pwm.duty_u16(0)
        
    elif pos_moteur == 6:
        print("Avancé Max")

    res = recup_res_moteur()
    print("Valeur finale:", res)
    
    time.sleep(0.5)
    pos_moteur = recup_pos_moteur()
    print(pos_moteur)
    
    
# Fonction qui permet de faire reculer manuellement le moteur          
def reculer_moteur():
    print("recul du moteur")
    pwm.duty_u16(0)
    dir_pin.value(0)
    pwm.duty_u16(30000)
    utime.sleep(1.1)
    pwm.duty_u16(0)
    print("recul terminé.")

# Fonction qui permet de faire avancer manuellement le moteur   
def avancer_moteur():
    print("avancé du moteur")
    pwm.duty_u16(0)
    dir_pin.value(1)
    pwm.duty_u16(20000)
    utime.sleep(1.1)
    pwm.duty_u16(0)
    print("avancé terminé.")

# Fonction pour les tests de valeurs sur potentiometre
def test_valeur_pot():
    valeur = []
    for i in range(50):
        valeur.append(recup_res_moteur())
        time.sleep(0.01)
    moyenne = sum(valeur)/len(valeur)
    
    somme_carres_ecarts = sum((x - moyenne) ** 2 for x in valeur)

    
    ecart_type = math.sqrt(somme_carres_ecarts / len(valeur))

    print("Moyenne :", moyenne)
    print("Écart type :", ecart_type)
    
    


# Attacher la fonction de détection à l'interruption du capteur
capteur.irq(trigger=Pin.IRQ_FALLING, handler=detecter_rotation)

# Définir l'interruption sur le front descendant (bouton appuyé)
button_pin.irq(trigger=machine.Pin.IRQ_FALLING, handler=bouton_presse)

button_av.irq(trigger=machine.Pin.IRQ_FALLING, handler=bouton_presse2)

#Récuperer la position du moteur au démarrage
pos_moteur = recup_pos_moteur()

# Démarrer le chronomètre et le comptage de tours dans un thread séparé
demarrer_chronometre_et_compteur()
