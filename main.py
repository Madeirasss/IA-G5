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



defender_vida_max = 750
defender_vida_atual = 750
defender_energia_max = 500
defender_energia_atual = 500

energia_a_recuperar_prox_turno = 0 # (Para a regra da cura)
vida_a_recuperar_prox_turno = 0

ATAQUES = {
    'grua': {'dano': 100, 'custo_en': 300},
    'toque': {'dano': 200, 'custo_en': 150},
    'som':   {'dano': 50,  'custo_en': 50}
}

CURAS = {
    'cura1': {'recupera': 100, 'custo_en': 200},
    'cura2': {'recupera': 200, 'custo_en': 300},
    'cura3': {'recupera': 400, 'custo_en': 400}
}

INIMIGOS = {
    'Tanque':     {'forca': 200, 'ataques': 2, 'vida': 200},
    'Artilharia': {'forca': 500, 'ataques': 1, 'vida': 50},
    'Infantaria': {'forca': 100, 'ataques': 3, 'vida': 100}
}

def confirmar_inicialização():
    print("--- ROBO INICIALIZADO ---")
    print("VIDA: ")
    print(defender_vida_atual)  
    print(defender_vida_max)
    print("ENERGIA: ")
    print(defender_energia_atual)
    print(defender_energia_max)

#Função para calcular o angulo de giro com o sensor giroscopico
def calcular_angulo_giro():
    sensor_giro.reset()
    angulo = sensor_giro.angle
    print("Angulo de giro: ")
    print(angulo)
    print(" graus")

#Função para detetar a cor com o sensor de cor
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

#Função para medir a distancia com o sensor ultrassonico
def distancia():
    distancia_cm = sensor_ultrassonico.distance_centimeters
    print("Distancia: ")
    print(distancia_cm)
    print(" cm")

#Função para verificar o estado do sensor de toque
def sensor_toque_estado():
    if sensor_toque.is_pressed:
        print("Estado: PRESSIONADO!")
        return 1
    else:
        print("Estado: Nao pressionado.")
        return 0

#Função para emitir som
def usar_som():
    Sound().play_file('cbaec71a.wav',50)
    Sound().speak("Ola, eu sou o fogueirinha", espeak_opts='-v pt')


def atacar_com_grua():
    global defender_energia_atual
    custo = ATAQUES['grua']['custo_en']#vai buscar o custo do ataque com grua
    dano = ATAQUES['grua']['dano']#vai buscar o dano do ataque com grua
    
    print("A tentar 'Ataque com Grua' Custo:")
    print(custo)

    if defender_energia_atual >= custo:
        print("Energia OK. A procurar alvo (a andar para a frente)...")
        movimento.on(SpeedPercent(30), SpeedPercent(30))
        # Continua a andar até o sensor ultrassonico detetar um objeto a menos de 10 cm
        while sensor_ultrassonico.distance_centimeters > 10:
            dist = sensor_ultrassonico.distance_centimeters
            print("Distancia: ")
            print(dist)
            sleep(0.05) 

        print("\nAlvo encontrado! A parar.")
        movimento.stop()
        
        print("A ATACAR!")
        movimento.on_for_seconds(SpeedPercent(-30), SpeedPercent(30), 3) # Vira
        sleep(0.5) 
        motor_medio.on_for_seconds(SpeedPercent(100), 1.5) # Ataca com a grua
        
        print("Ataque concluido.")
        # Reduz a energia do defensor
        defender_energia_atual -= custo
        print("Ataque bem sucedido! Energia restante: ")
        print(defender_energia_atual)
        
        return dano
        
    else:
        print("FALHOU! Energia insuficiente.")
        som.beep() 
        return 0 

def atacar_com_toque():    
    global defender_energia_atual 
    
    custo = ATAQUES['toque']['custo_en']
    dano = ATAQUES['toque']['dano']
    
    print("A tentar 'Ataque com Toque' (Custo: ")
    print(custo)
    
    if defender_energia_atual >= custo:

        print("Energia OK. A procurar alvo (< 15cm)...")
        movimento.on(SpeedPercent(40), SpeedPercent(40)) 

        while sensor_ultrassonico.distance_centimeters > 15:
            dist = sensor_ultrassonico.distance_centimeters
            print("A aproximar... Dist: ")
            print(dist)
            sleep(0.05) 
            
            if sensor_toque.is_pressed:
                print("Obstaculo atingido inesperadamente!")
                break 

        print("\nAlvo proximo! A avancar para o impacto...")
        

        while not sensor_toque.is_pressed:
            dist = sensor_ultrassonico.distance_centimeters
            print("A avancar para o toque... Dist: ")
            print(dist)
            sleep(0.05)
            
            if dist > 30: 
                print("Alvo fugiu durante a aproximacao final!")
                movimento.stop()
                return 0 

        movimento.stop()
        print("\nALVO ATINGIDO! (Toque)")
        
        som.play_tone(150, 0.2)
        
        movimento.on_for_seconds(SpeedPercent(-30), SpeedPercent(-30), 0.5)
        
        print("Ataque de toque concluido.")
        
        defender_energia_atual -= custo
        print("Ataque bem sucedido! Energia restante: ")
        print(defender_energia_atual)
        
        return dano
        
    else:
        print("FALHOU! Energia insuficiente.")
        som.beep() 
        return 0

def atacar_com_som():
    global defender_energia_atual
    
    custo = ATAQUES['som']['custo_en']
    dano = ATAQUES['som']['dano']
    
    print("A tentar 'Ataque com Som' (Custo: ")
    print(custo)

    if defender_energia_atual >= custo:
        defender_energia_atual -= custo
        
        som.beep()
        print("Ataque bem sucedido! Energia restante: ")
        print(defender_energia_atual)
        
        return dano
    else:
        print("FALHOU! Energia insuficiente.")
        som.beep() 
        return 0

def usar_cura(numero_da_cura):
    global defender_energia_atual
    global defender_vida_atual
    global defender_vida_max 
    
    if numero_da_cura == 1:
        key = 'cura1'
    elif numero_da_cura == 2:
        key = 'cura2'
    elif numero_da_cura == 3:
        key = 'cura3'
    else:
        print("ERRO: Cura invalida ")
        print(numero_da_cura)
        print("Use 1, 2, ou 3.")
        return False 

    custo = CURAS[key]['custo_en']
    recupera = CURAS[key]['recupera']
    
    print("A tentar 'Cura " )
    print(numero_da_cura)
    print("Custo: ")
    print(custo)
    print("EN, Recupera: ")
    print(recupera)
    if defender_energia_atual >= custo:
        defender_energia_atual -= custo
        
        defender_vida_atual += recupera
        
        if defender_vida_atual > defender_vida_max:
            defender_vida_atual = defender_vida_max
            print("Vida recuperada ate ao maximo!")
        

        print("CURA BEM SUCEDIDA!")
        print("Vida atual: ")
        print(defender_vida_atual)
        print("Vida max: ")
        print(defender_vida_max)
        print("Energia atual: ")
        print(defender_energia_atual) 
        print("Energia max: ")
        print(defender_energia_max)
        return True
    else:
        print("FALHOU A CURA! Energia insuficiente.")
        som.beep()
        return False

def turnos_do_jogo():
    global defender_vida_atual
    global defender_energia_atual
    print("\n--- O JOGO VAI COMECAR! ---")
    
    for turno_atual in range(1, 14):
        
        print("\n-------------------------------------")
        print("--- INICIANDO TURNO ---")
        print(turno_atual)
        
        print("Queres executar este turno?")
        resposta = input("Escreve 's' para sim ou 'n' para nao: ")
        
        if resposta.lower() != 's':
            print("Execucao do turno cancelada. A sair do jogo...")
            break 
        
        if turno_atual % 2 != 0:
            print("TURNO DO INIMIGO")
            
            inimigo_atacou = False
            dano_total_neste_turno = 0 

            
            if inimigo_atacou:
                print("\nDANO TOTAL RECEBIDO NESTE TURNO:")
                print(dano_total_neste_turno)
                defender_vida_atual -= dano_total_neste_turno
            else:
                print("Nenhum inimigo (vivo) atacou neste turno.")
        else:
            print("TURNO DO ROBO!")
            
            energia_a_recuperar = int(defender_energia_atual * 0.5)
            defender_energia_atual += energia_a_recuperar
            if defender_energia_atual > defender_energia_max:
                defender_energia_atual = defender_energia_max
            
            print("Energia atual: ")
            print(defender_energia_atual)
            
            print("\nO que queres fazer?")
            print(" 1 - Atacar com Grua")
            print(" 2 - Atacar com Toque")
            print(" 3 - Atacar com Som")
            print(" 4 - Usar Cura 1 (100 UV)")
            print(" 5 - Usar Cura 2 (200 UV)")
            print(" 6 - Usar Cura 3 (400 UV)")
            print(" (Qualquer outra tecla para PASSAR O TURNO)")
            
            acao_jogador = input("Escolhe a tua acao: ")
            
            if acao_jogador == '1':
                atacar_com_grua()
            elif acao_jogador == '2':
                atacar_com_toque()
            elif acao_jogador == '3':
                atacar_com_som()
            elif acao_jogador == '4':
                usar_cura(1)
            elif acao_jogador == '5':
                usar_cura(2)
            elif acao_jogador == '6':
                usar_cura(3)
            else:
                print("Decidiste PASSAR o turno.")
        
        print("\n--- FIM DO TURNO ---")
        
        if defender_vida_atual <= 0:
            print("\nGAME OVER! Foste destruido!")
            break 
            
        sleep(2) 

    if defender_vida_atual > 0:
        print("\n--- VITORIA! ---")
        print("Sobreviveste aos 13 turnos!")

def main():
    som.play_file("cbaec71a.wav")
    #som.play_file("Madeira-Mix-_h_LHYlsr4vI_.wav")
    
    confirmar_inicialização()
    turnos_do_jogo()
    #atacar_com_toque()
    #atacar_com_grua()
    #while True:
    #    detetar_cor()
    #    distancia()
    #    sensor_toque_estado()
    #    print("---------------------------") 
    #    sleep(1)


main()

