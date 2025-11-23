#imports
from ev3dev2.motor import MoveTank, OUTPUT_D, OUTPUT_B, SpeedPercent, OUTPUT_C, MediumMotor
from time import sleep
from ev3dev2.sensor import INPUT_4, INPUT_3, INPUT_1, INPUT_2
from ev3dev2.sensor.lego import UltrasonicSensor, ColorSensor, TouchSensor, GyroSensor
from ev3dev2.console import Console
from ev3dev2.sound import Sound
import sys
import random

#definir inputs e outputs
sensor_ultrassonico = UltrasonicSensor(INPUT_3)
sensor_toque = TouchSensor(INPUT_2)
sensor_cor = ColorSensor(INPUT_1)
motor_medio = MediumMotor(OUTPUT_C)
movimento = MoveTank(OUTPUT_D, OUTPUT_B)
sensor_giro = GyroSensor(INPUT_4)
som = Sound()


#Definir variaveis do jogo
defender_vida_max = 750
defender_vida_atual = 750
defender_energia_max = 500
defender_energia_atual = 500

energia_a_recuperar_prox_turno = 0 #Para calculo de energia a recuperar no proximo turno
vida_a_recuperar_prox_turno = 0 #Para calculo de vida a recuperar no proximo turno

#Dicionarios com dados dos ataques, curas e inimigos
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

#Função para confirmar a inicialização do robo
def confirmar_inicialização():
    print("--- ROBO INICIALIZADO ---")
    print("VIDA: ")
    print(defender_vida_atual)  
    print(defender_vida_max)
    print("ENERGIA: ")
    print(defender_energia_atual)
    print(defender_energia_max)

#Função para calcular o angulo de giro com o sensor giroscopico
#Ela apenas está definida para caso de debugging, se necessário, não está a ser chamada em nenhum lugar
def calcular_angulo_giro():
    sensor_giro.reset()
    angulo = sensor_giro.angle
    print("Angulo de giro: ")
    print(angulo)
    print(" graus")

#Função para detetar a cor com o sensor de cor
#Função apenas está definida para caso de debugging, se necessário, não está a ser chamada em nenhum lugar
#Podem usar para ver as cores detetadas pelo sensor no tabuleiro, precisamos ver se o sensor está numa altura fixe
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
#Função apenas está definida para caso de debugging, se necessário, não está a ser chamada em nenhum lugar
def distancia():
    distancia_cm = sensor_ultrassonico.distance_centimeters
    print("Distancia: ")
    print(distancia_cm)
    print(" cm")


#Função para verificar o estado do sensor de toque
#Função apenas está definida para caso de debugging, se necessário, não está a ser chamada em nenhum lugar
def sensor_toque_estado():
    if sensor_toque.is_pressed:
        print("Estado: PRESSIONADO!")
        return 1
    else:
        print("Estado: Nao pressionado.")
        return 0

#Função para emitir som (max verstappen) e para ele falar
#Função apenas está definida para caso de debugging, se necessário, não está a ser chamada em nenhum lugar
def usar_som():
    Sound().play_file('cbaec71a.wav',50)
    Sound().speak("Ola, eu sou o fogueirinha", espeak_opts='-v pt')

#Função de ataque com a grua, confirma se tem energia suficiente para atacar
def atacar_com_grua():
    global defender_energia_atual
    custo = ATAQUES['grua']['custo_en']#vai buscar o custo do ataque com grua
    dano = ATAQUES['grua']['dano']#vai buscar o dano do ataque com grua
    
    print("A tentar 'Ataque com Grua' Custo:")
    print(custo)

    if defender_energia_atual >= custo: #confirma se tem energia suficiente
        print("Energia OK. A procurar alvo (a andar para a frente)...")
        movimento.on(SpeedPercent(30), SpeedPercent(30))#anda para a frente
        # Continua a andar até o sensor ultrassonico detetar um objeto a menos de 10 cm
        while sensor_ultrassonico.distance_centimeters > 10: #fica sempre a dar print da distancia que ta de um objeto
            dist = sensor_ultrassonico.distance_centimeters
            print("Distancia: ")
            print(dist)
            sleep(0.05) 

        print("\nAlvo encontrado! A parar.")
        movimento.stop()#o robo pára para atacar o alvo
        
        print("A ATACAR!")
        movimento.on_for_seconds(SpeedPercent(-30), SpeedPercent(30), 3) #faz um 180º
        sleep(0.5) #pára durante 0.5 seg para não bugar de os comandos sempre rápidos
        motor_medio.on_for_seconds(SpeedPercent(100), 1.5) # Ataca com a grua
        
        print("Ataque concluido.")
        # Reduz a energia do robô
        defender_energia_atual -= custo
        print("Ataque bem sucedido! Energia restante: ")
        print(defender_energia_atual)
        #dá print na energia restante
        return dano
        
    else:
        print("FALHOU! Energia insuficiente.")#caso não tenha energia suficiente
        som.beep() 
        return 0 

#Função de ataque com toque
def atacar_com_toque():    
    global defender_energia_atual 
    
    custo = ATAQUES['toque']['custo_en']
    dano = ATAQUES['toque']['dano']
    
    print("A tentar 'Ataque com Toque' (Custo: ")
    print(custo)
    
    if defender_energia_atual >= custo: #verifica se tem energia suficiente

        print("Energia OK. A procurar alvo (< 15cm)...")
        movimento.on(SpeedPercent(40), SpeedPercent(40)) 

        while sensor_ultrassonico.distance_centimeters > 15:#procura o alvo a menos de 15 cm
            dist = sensor_ultrassonico.distance_centimeters
            #dá print da distancia ao alvo
            print("A aproximar... Dist: ")
            print(dist)
            sleep(0.05) 
            
            if sensor_toque.is_pressed: # se o sensor de toque for pressionado inesperadamente, ele pára
                print("Obstaculo atingido inesperadamente!")
                break 

        print("\nAlvo proximo! A avancar para o impacto...")
        

        while not sensor_toque.is_pressed:
            dist = sensor_ultrassonico.distance_centimeters
            #dá print da distancia ao alvo
            print("A avancar para o toque... Dist: ")
            print(dist)
            sleep(0.05)
            
            if dist > 30: # se o algo estiver a mais de 30 cm, ele consigera como se tivesse fugido
                print("Alvo fugiu durante a aproximacao final!")
                movimento.stop()
                return 0 

        movimento.stop()
        print("\nALVO ATINGIDO! (Toque)")
        
        som.play_tone(150, 0.2)# dá um som se for atingido
        
        #anda para tras depois do toque (pode não tar a funcionar por ser 0.5 seg)
        movimento.on_for_seconds(SpeedPercent(-30), SpeedPercent(-30), 0.5)
        
        print("Ataque de toque concluido.")
        
        defender_energia_atual -= custo #reduz a energia do robo
        print("Ataque bem sucedido! Energia restante: ")
        print(defender_energia_atual)
        
        return dano
        
    else:
        print("FALHOU! Energia insuficiente.")#caso não tenha energia suficiente
        som.beep() 
        return 0

#Função que faz o ataque com som
def atacar_com_som():
    global defender_energia_atual
    
    custo = ATAQUES['som']['custo_en']
    dano = ATAQUES['som']['dano']
    
    print("A tentar 'Ataque com Som' (Custo: ")
    print(custo)
    
    if defender_energia_atual >= custo: #verifica se tem energia suficiente
        defender_energia_atual -= custo #reduz a energia do robo
        
        som.beep()# realiza o ataque com som
        print("Ataque bem sucedido! Energia restante: ")
        print(defender_energia_atual)
        
        return dano
    else:
        print("FALHOU! Energia insuficiente.") #caso não tenha energia suficiente
        som.beep() 
        return 0

#Função para usar as curas no menu
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
    #verifica se tem enregia suficiente para curar-se
    if defender_energia_atual >= custo:
        defender_energia_atual -= custo
        
        defender_vida_atual += recupera
        
        if defender_vida_atual > defender_vida_max: #verifica se ele curou-se mais que a vida máxima e não deixa ultrapassar esse máximo
            defender_vida_atual = defender_vida_max
            print("Vida recuperada ate ao maximo!")
        
        #dá prints depois de se curar
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
        print("FALHOU A CURA! Energia insuficiente.") #energia insuficiente 
        som.beep()
        return False

#Função que faz os turnos do jogo
def turnos_do_jogo():
    global defender_vida_atual
    global defender_energia_atual
    print("\n--- O JOGO VAI COMECAR! ---")
    
    for turno_atual in range(1, 14): #percorre os 13 turnos do jogo
        
        print("\n-------------------------------------")
        print("--- INICIANDO TURNO ---")
        print(turno_atual)
        
        print("Queres executar este turno?")
        resposta = input("Escreve 's' para sim ou 'n' para nao: ")
        
        if resposta.lower() != 's':
            print("Execucao do turno cancelada. A sair do jogo...")
            break 
        
        if turno_atual % 2 != 0: # turno do inimigo
            print("TURNO DO INIMIGO")
            #Lógica do turno do inimigo (ainda por implementar)
            inimigo_atacou = False
            dano_total_neste_turno = 0 

            #calculo do dano do inimigo (ainda não testado)
            if inimigo_atacou:
                print("\nDANO TOTAL RECEBIDO NESTE TURNO:")
                print(dano_total_neste_turno)
                defender_vida_atual -= dano_total_neste_turno
            else:
                print("Nenhum inimigo (vivo) atacou neste turno.")
        else: #tuno do robô
            print("TURNO DO ROBO!")
            #faz o calculo de recuperar a energia do robô segundo as regras
            energia_a_recuperar = int(defender_energia_atual * 0.5)
            defender_energia_atual += energia_a_recuperar
            if defender_energia_atual > defender_energia_max:# não deixa ultrapassar o máximo de energia
                defender_energia_atual = defender_energia_max
            
            print("Energia atual: ")
            print(defender_energia_atual)
            #menu de escolha entre atacar ou usar cura
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
        
        if defender_vida_atual <= 0: #verifica se o robô foi destruido
            print("\nGAME OVER! Foste destruido!")
            break 
            
        sleep(2) 
    #se no ultimo turno o robô ainda tiver vida, ele vence
    if defender_vida_atual > 0:
        print("\n--- VITORIA! ---")
        print("Sobreviveste aos 13 turnos!")

#Função de ataque inimigo (não foi testada ainda, pode conter erros)
def ataque inimigo():
    inimigo_atacou = False
    dano_total_neste_turno = 0 # Acumulador de dano

    for slot_id, info in slots_inimigos.items():
        
        # 1. Verifica se é o turno deste slot E se o inimigo está VIVO
        if info['turno_ataque'] == turno_atual and info['vida_atual'] > 0:
            
            inimigo_atacou = True
            tipo_inimigo = info['tipo']
            
            # 2. Vai buscar os dados do inimigo
            dados_inimigo = INIMIGOS[tipo_inimigo]
            dano_por_ataque = dados_inimigo['forca']
            num_ataques = dados_inimigo['ataques'] # A REGRA QUE FALTAVA
            
            print("ATAQUE! O ")
            print(tipo_inimigo)
            print(" no slot ")
            print(slot_id)
            print(" ataca ") 
            print(num_ataques) 
            print("vez(es)!")
            
            # 3. Executa os ataques (um por um)
            for i in range(num_ataques):
                # i vai de 0 até (num_ataques - 1)
                print(f"  -> Ataque {i+1}/{num_ataques}: Dano de {dano_por_ataque}!")
                dano_total_neste_turno += dano_por_ataque
                # (Podes adicionar um som.beep() aqui para cada hit)
            
            som.speak("Dano recebido", espeak_opts='-v pt')
    
    # 4. Aplica o dano total ao Defender-bot
    if inimigo_atacou:
        print("DANO TOTAL RECEBIDO NESTE TURNO: ")
        orint(dano_total_neste_turno)
        # Aplica o dano total ao Defender-bot
        defender_vida_atual -= dano_total_neste_turno
    else:
        print("Nenhum inimigo (vivo) atacou neste turno.")

#Função para sortear os inimigos e quais rounds colocar os mesmos no tabuleiro(ainda não testada)
def sortear_inimigos_com_dados():

    #Simula o lançamento de dados para configurar o tabuleiro.
    #Define Tipo, Slot e Turno aleatoriamente.
    #O robô diz ao utilizador onde colocar as peças.
    global slots_inimigos
    global INIMIGOS
    
    print("\n--- A SORTEAR INIMIGOS (DADOS VIRTUAIS) ---")
    
    # Lista de slots disponíveis. À medida que escolhemos, removemos da lista.
    slots_disponiveis = [1, 2, 3, 4, 5, 6]
    
    # Vamos criar 6 inimigos (a força atacante tem 6 unidades)
    for i in range(6):
        
        print("\n--- Sorteio da Unidade ---")
        print(i+1)
        # 1. Rolar Dado para o TIPO (1 a 6)
        dado_tipo = random.randint(1, 6)
        
        if dado_tipo <= 2:    # 1 ou 2
            tipo = "Tanque"
        elif dado_tipo <= 4:  # 3 ou 4
            tipo = "Artilharia"
        else:                 # 5 ou 6
            tipo = "Infantaria"
            
        # 2. Rolar Dado para o TURNO (1 a 6)
        dado_turno = random.randint(1, 6)
        
        # 3. Escolher um SLOT LIVRE (sem repetição)
        # O random.choice escolhe um da lista
        slot_escolhido = random.choice(slots_disponiveis)
        # Removemos da lista para não voltar a sair
        slots_disponiveis.remove(slot_escolhido)
        
        # 4. Guardar na memória do Robô
        vida_inicial = INIMIGOS[tipo]['vida']
        
        slots_inimigos[slot_escolhido]['tipo'] = tipo
        slots_inimigos[slot_escolhido]['vida_atual'] = vida_inicial
        slots_inimigos[slot_escolhido]['turno_ataque'] = dado_turno
        
        # 5. INSTRUIR O JOGADOR
        print("Coloca ") 
        print(tipo)
        print(" no Slot ") 
        print(slot_escolhido)
        print("Turno ") 
        print(dado_turno)






def main():
    #som.play_file("cbaec71a.wav") #play ao som do max verstappen
    #som.play_file("Madeira-Mix-_h_LHYlsr4vI_.wav") #play ao som do madeira mix
    
    confirmar_inicialização() #confirma a inicialização do robo
    turnos_do_jogo() #inicia os turnos do jogo, podem tirar isto para ser mais fácil testar o tabuleiro
    #atacar_com_toque() #ataque de toque
    #atacar_com_grua() #ataque com grua
    #usem este while para testar os sensores, se quiserem resultados mais rápidos metam um numero
    #mais pequeno no sleep, para terminar usem ctrl+c
    #recomendo começarem por testar quais cores o gajo tá a ler com o sensor de cor no tabuleiro 
    #e façam ele dar uma volta dentro do quadrado para ver se ele esta dentro para depois ele começar o jogo
    #vejam tbm as cores das cartolinas como estão
    #while True:
    #    detetar_cor() 
    #    distancia()
    #    sensor_toque_estado()
    #    print("---------------------------") 
    #    sleep(1)


main()

