#imports
from ev3dev2.motor import MoveTank, OUTPUT_D, OUTPUT_B, SpeedPercent, OUTPUT_C, MediumMotor
from time import sleep
from ev3dev2.sensor import INPUT_4, INPUT_3, INPUT_1, INPUT_2
from ev3dev2.sensor.lego import UltrasonicSensor, ColorSensor, TouchSensor, GyroSensor
from ev3dev2.console import Console
from ev3dev2.sound import Sound
import sys
import random
import time

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


#Slots dos inimigos no tabuleiro
NUMERO_DE_SLOTS = 6  # <--- MUDAS AQUI PARA O NÚMERO QUE QUISERES
slots_inimigos = {
    i: {'tipo': None, 'vida_inicial': 0, 'vida_atual': 0, 'turno_ataque': 0} 
    for i in range(1, NUMERO_DE_SLOTS + 1)
}

tabuleiro_real = {
    i: {'tipo': "Vazio", 'vida_atual': 0, 'turno_ataque': 0} 
    for i in range(1, NUMERO_DE_SLOTS + 1)
}


#Dicionarios com dados dos ataques, curas e inimigos
ATAQUES = {
    'grua': {'dano': 200, 'custo_en': 300},
    'toque': {'dano': 100, 'custo_en': 150},
    'som':   {'dano': 50,  'custo_en': 50}
}

CURAS = {
    'cura1': {'recupera': 100, 'custo_en': 200},
    'cura2': {'recupera': 200, 'custo_en': 300},
    'cura3': {'recupera': 400, 'custo_en': 400}
}

INIMIGOS = {
    'Tanque':     {'cor':"Blue",'forca': 200, 'ataques': 2, 'vida': 200},
    'Artilharia': {'cor':"Green",'forca': 500, 'ataques': 1, 'vida': 50},
    'Infantaria': {'cor':"Brown",'forca': 100, 'ataques': 3, 'vida': 100}
}

PRIORIDADES = {
    'Artilharia': 3,
    'Infantaria': 2,
    'Tanque': 1,
    'Vazio': 0
}


#Função para confirmar a inicialização do robo
def confirmar_inicialização():
    print("--- ROBO INICIALIZADO ---")
    print("Vida atual: ", defender_vida_atual, "Vida Máxima", defender_vida_max, "Energia atual: ", defender_energia_atual, "Energia Máxima", defender_energia_max)


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
    sleep(0.5)


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
    Sound().play_file('Madeira-Mix-_h_LHYlsr4vI_.wav') #play ao som do madeira mix


#Função para virar o robo com o giroscopio
def virar_com_gyro(graus):
    sensor_giro.reset()
    sleep(0.1)
    
    # Define velocidade e direção baseada no sinal (+ ou -)
    if graus > 0: # Direita
        movimento.on(SpeedPercent(15), SpeedPercent(-15))
        # Loop até chegar ao angulo (margem de erro pequena de 2 graus)
        while sensor_giro.angle < (graus - 2): 
            pass
    else: # Esquerda
        movimento.on(SpeedPercent(-15), SpeedPercent(15))
        while sensor_giro.angle > (graus + 2): 
            pass
            
    movimento.stop()
    sleep(0.5) # Estabilizar


#Função para atacr com a grua
def atacar_com_grua(slot_alvo):
    global defender_energia_atual
    
    custo = ATAQUES['grua']['custo_en']
    dano = ATAQUES['grua']['dano']
    
    print("\n--- ATAQUE GRUA (Slot " + str(slot_alvo) + ") ---")
    
    # 1. Verificar Energia
    if defender_energia_atual < custo:
        print("Energia insuficiente.")
        som.beep()
        return 0

    print("A centrar no quadrado...")
    
    # 4. Decidir lado e Virar 90º (Ficar de frente para o inimigo)
    print("A virar para o alvo...")
    if slot_alvo % 2 != 0:
        # Impar = Esquerda (-90)
        virar_com_gyro(-90)
        direcao_inicial = -1
    else:
        # Par = Direita (90)
        virar_com_gyro(90)
        direcao_inicial = 1

    # 5. Aproximar do Inimigo (Até Ultrassónico ver < 10cm)
    print("A aproximar do inimigo...")
    movimento.on(SpeedPercent(20), SpeedPercent(20))
    
    while sensor_ultrassonico.distance_centimeters > 15:
        # Segurança: Se não encontrar nada e andar demasiado, para.
        pass
    movimento.stop()
    print("Alvo encontrado.")
    sleep(0.5)

    # 6. Ficar de costas para o inimigo
    print("A rodar 180 para posicao de Grua...")
    virar_com_gyro(180)

    # 7. EXECUÇÃO DO ATAQUE
    print(">>> ATAQUE GRUA <<<")
    motor_medio.on_for_seconds(SpeedPercent(100), 1.5) 
    sleep(0.5)
    motor_medio.on_for_seconds(SpeedPercent(-100), 1.5)
    
    defender_energia_atual -= custo
    print("Sucesso! Energia: " + str(defender_energia_atual))

    print("A sair do slot...")
    movimento.on(SpeedPercent(20), SpeedPercent(20))
    
    # Sai do slot até ver preto
    time.sleep(0.5) 
    
    while True:
        cor = sensor_cor.color_name
        # Se vir a linha preta do corredor ou a parede vermelha
        if cor == "Black":
            print("Corredor detetado.")
            break
        if cor == "Red": 
            print("Parede detetada (Seguranca).")
            break
            

    movimento.stop()

    # 9. Virar para a Base
    print("A virar para a Base...")
    
    if direcao_inicial == 1: # Tinhamos virado à Direita
        virar_com_gyro(90) # Vira Esquerda para a base
    else: # Tinhamos virado à Esquerda
        virar_com_gyro(-90) # Vira Direita para a base

    voltar_a_base()
    
    return dano


#Função para atacar com toque
def atacar_com_toque():    
    global defender_energia_atual 
    
    custo = ATAQUES['toque']['custo_en']
    dano = ATAQUES['toque']['dano']
    movimento.stop()
    print(">>> ATAQUE TOQUE (Custo:", custo, ")")
    
    if defender_energia_atual >= custo:
        print("A avancar para impacto...")
        # Avança com força (40%)
        movimento.on(SpeedPercent(40), SpeedPercent(40)) 

        # AVANÇAR ATÉ TOCAR
        # Loop de segurança: Para se tocar no botão OU se andar demasiado 
        tempo_limite = time.time() + 4 # 4 segundos de limite
        
        while not sensor_toque.is_pressed:
            # Se o tempo passar ou o sensor US disser que já não há nada à frente
            if time.time() > tempo_limite:
                print("Tempo esgotado/Alvo falhado!")
                movimento.stop()
                # Recua um pouco por segurança (1 seg)
                movimento.on_for_seconds(SpeedPercent(-30), SpeedPercent(-30), 1)
                return 0 
            sleep(0.01)

        # IMPACTO CONFIRMADO
        movimento.stop()
        print("IMPACTO CONFIRMADO!")
        som.beep()
        sleep(0.5)
        
        # RECUAR ATÉ LINHA PRETA
        print("A recuar para o centro...")
        movimento.on(SpeedPercent(-20), SpeedPercent(-20))
        
        # Sai da colisão (pequeno delay para não ler a cor do inimigo se ele estiver em cima da linha)
        sleep(0.5) 
        
        # Recua até o sensor de cor ver a LINHA PRETA do corredor
        while True:
            cor = sensor_cor.color_name
            if cor == "Black":
                print("Centro (Linha Preta) encontrado.")
                break
            # Segurança: Parede vermelha
            if cor == "Red":
                break
            sleep(0.01)
            
        movimento.stop()
        
        # Pequeno ajuste para o eixo das rodas ficar no meio da linha
        # (O sensor de cor está à frente das rodas, por isso recuamos mais um pouquinho)
        movimento.on_for_seconds(SpeedPercent(-15), SpeedPercent(-15), 0.2)
        
        defender_energia_atual -= custo
        print("Energia restante: ", defender_energia_atual)
        return dano
        
    else:
        print("FALHOU! Energia insuficiente.")
        som.beep() 
        return 0


#Função para atacar com som
def atacar_com_som():
    global defender_energia_atual
    
    custo = ATAQUES['som']['custo_en']
    dano = ATAQUES['som']['dano']
    
    print(">>> ATAQUE SONICO (Custo:", custo, ")")
    
    if defender_energia_atual >= custo:
        # O robô já está virado para o inimigo 
        # Vamos só avançar um pouquinho para "entrar" na sala, gritar e voltar
        
        movimento.on_for_seconds(SpeedPercent(20), SpeedPercent(20), 0.5)
        
        # O Ataque
        som.beep()
        sleep(0.5)
        som.speak("Sonic Boom")
        sleep(0.5)
        
        # Voltar para trás o mesmo tempo que avançou
        movimento.on_for_seconds(SpeedPercent(-20), SpeedPercent(-20), 0.5)
        
        defender_energia_atual -= custo
        print("Ataque concluido. Energia: ", defender_energia_atual)
        return dano
    else:
        print("Energia insuficiente.")
        som.beep() 
        return 0


#Função para usar as curas
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
    
    print("A tentar 'Cura " ,numero_da_cura, "Custo: ",custo, " EN, Recupera: ",recupera)
    #verifica se tem energia suficiente para curar-se
    if defender_energia_atual >= custo:
        defender_energia_atual -= custo
        
        defender_vida_atual += recupera
        
        if defender_vida_atual > defender_vida_max: #verifica se ele curou-se mais que a vida máxima e não deixa ultrapassar esse máximo
            defender_vida_atual = defender_vida_max
            print("Vida recuperada ate ao maximo!")
        
        #dá prints depois de se curar
        print("CURA BEM SUCEDIDA!")
        print("Vida atual: ", defender_vida_atual,"Energia atual: ", defender_energia_atual)
        return True
    else:
        print("FALHOU A CURA! Energia insuficiente.") #energia insuficiente 
        som.beep()
        return False


#Função para obter as coordenadas do slot
def obter_coordenadas_slot(slot_id):
    # 1. Definir a Linha 
    linha_alvo = 1 # Valor base
    
    if slot_id == 1 or slot_id == 2:
        linha_alvo = 1
    elif slot_id == 3 or slot_id == 4:
        linha_alvo = 3 
    elif slot_id == 5 or slot_id == 6:
        linha_alvo = 5  
        
    # 2. Definir a Direção
    # Se o numero for PAR (2, 4, 6), é Direita (1). 
    # Se for IMPAR (1, 3, 5), é Esquerda (-1)
    if slot_id % 2 == 0:
        direcao = 1 # Direita
    else:
        direcao = -1 # Esquerda
        
    return linha_alvo, direcao


#Função para ir até a linha desejada
def ir_ate_linha(numero_linha_desejada):
    print(">> A viajar para a Linha " + str(numero_linha_desejada) + "...")
    movimento.on(SpeedPercent(30), SpeedPercent(30))
    
    linhas_contadas = 0
    estou_na_linha = False
    
    while True:
        cor = sensor_cor.color_name
        if cor == "Black":
            if not estou_na_linha:
                estou_na_linha = True
                linhas_contadas += 1
                print("Passou linha: " + str(linhas_contadas))
                som.beep()
                
                # Se chegámos à linha que queríamos
                if linhas_contadas == numero_linha_desejada:
                    movimento.stop()
                    print("Chegamos ao destino.")
                    break
                    
        elif cor != "Black":
            estou_na_linha = False
            
        if cor == "Red" or sensor_toque.is_pressed:
            movimento.stop()
            print("Erro: Fim da pista encontrado antes do destino.")
            break
            
        sleep(0.01)


#Função que chama as funções de ataque, chama as de coordenadas e faz o movimento completo do ataque
def executar_ataque_manual_fisico(slot_alvo, tipo_arma):
    print("\n" + "="*40)
    print(" INICIAR MOVIMENTO DE ATAQUE (Slot {}) ".format(slot_alvo).center(40, "="))
    print("="*40)
    
    linha_alvo, direcao = obter_coordenadas_slot(slot_alvo)
    ir_ate_linha(linha_alvo)
    
    print("A centrar no quadrado...")
    movimento.on_for_seconds(SpeedPercent(30), SpeedPercent(30), 1.5)
    
    dano_realizado = 0
    direcao_inicial = 0 

    if tipo_arma == 1: 
        dano_realizado = atacar_com_grua(slot_alvo)
        # O atacar_com_grua já chama voltar_a_base() lá dentro
    else: 
        print("A virar para o alvo...")
        if slot_alvo % 2 != 0: 
             virar_com_gyro(-90)
             direcao_inicial = -1
        else: 
             virar_com_gyro(90)
             direcao_inicial = 1
        
        if tipo_arma == 2:
            dano_realizado = atacar_com_toque()
        elif tipo_arma == 3:
            dano_realizado = atacar_com_som()
            
        print("A realinhar com o corredor...")
        if direcao_inicial == 1:
            virar_com_gyro(-90)
        else:
            virar_com_gyro(90)
        
        voltar_a_base()

    # ATUALIZAÇÃO ÚNICA E CORRETA
    if dano_realizado > 0:
        aplicar_dano_ao_inimigo(slot_alvo, dano_realizado)
        print(">>> SUCESSO! HP Inimigo: {}".format(tabuleiro_real[slot_alvo]['vida_atual']))
    else:
        print(">>> FALHA NO ATAQUE.")

    return dano_realizado 


# Função para o menu de ação manual
# Menu que permite ao utilizador escolher ações, apenas para debugging ou controlo total de novas funcionalidades
def menu_acao_manual():
    while True:
        print("\n" + "="*30)
        print("   MENU DE COMANDO MANUAL")
        print("="*30)
        print("Vida Robo: " + str(defender_vida_atual) + " | Energia: " + str(defender_energia_atual))
        print("1. ATACAR INIMIGO")
        print("2. USAR CURA")
        print("3. VERIFICAR MAPA (Relatorio)")
        print("4. TERMINAR TURNO (Passar)")
        
        opcao = input("Escolha (1-4): ")
        
        if opcao == '1':
            slot_str = input("Qual Slot atacar (1-6)? ")
            if slot_str.isdigit():
                slot = int(slot_str)
                if 1 <= slot <= 6:
                    # Verifica se o slot tem inimigo vivo
                    if slots_inimigos[slot]['vida_atual'] > 0:
                        print("Escolha a arma:")
                        print(" 1. Grua (200 Dano / 300 En)")
                        print(" 2. Toque (100 Dano / 150 En)")
                        print(" 3. Som (50 Dano / 50 En)")
                        arma_str = input("Opcao: ")
                        
                        if arma_str.isdigit():
                            arma = int(arma_str)
                            if 1 <= arma <= 3:
                                # EXECUTA O ATAQUE FISICO
                                executar_ataque_manual_fisico(slot, arma)
                                break # Sai do menu apos atacar (gasta o turno)
                            else:
                                print("Arma invalida.")
                        else:
                            print("Numero invalido.")
                    else:
                        print("Esse slot esta vazio ou o inimigo ja morreu.")
                else:
                    print("Slot invalido (1-6).")
            else:
                print("Entrada invalida.")
                
        elif opcao == '2':
            print("Tipos de Cura:")
            print(" 1. Pequena (Recupera 100 / Cust 200 Energia)")
            print(" 2. Media   (Recupera 200 / Cust 300 Energia)")
            print(" 3. Grande  (Recupera 400 / Cust 400 Energia)")
            cura_str = input("Qual cura? ")
            if cura_str.isdigit():
                c = int(cura_str)
                if 1 <= c <= 3:
                    sucesso = usar_cura(c)
                    if sucesso:
                        break # Gasta o turno
                else:
                    print("Opcao invalida.")
                    
        elif opcao == '3':
            imprimir_relatorio_final()
            
        elif opcao == '4':
            print("A passar turno...")
            break
            
        else:
            print("Opcao invalida.")


#Função para ler a cor e guardar o tipo de inimigo no slot correspondente
def ler_cor_e_guardar(slot_id):
    print("A aproximar para identificar...")
    

    sleep(1)
    
    # Le a cor do chão
    cor_lida = sensor_cor.color_name
    print("Cor detetada: " + cor_lida)
    
    nome_inimigo = "Vazio"
    vida_inimigo = 0
    found = False
    
    # Percorre cada item do dicionario: nome="Tanque", dados={'cor': 'Blue', ...}
    for nome, dados in INIMIGOS.items():
        # Compara a cor que está na memoria com a cor que o sensor leu
        if dados['cor'] == cor_lida:
            nome_inimigo = nome       # Guardamos "Tanque"
            vida_inimigo = dados['vida'] # Guardamos 200
            found = True
            print(cor_lida + " corresponde a inimigo: " + nome_inimigo)
            break # Encontramos, podemos parar de procurar
    
    sleep(0.5)
    # Feedback e Registo
    if found:
        print("Identificado: " + nome_inimigo + " (" + str(vida_inimigo) + " HP)")
    else:
        print("Cor nao corresponde a inimigos (Vazio).")
        som.beep()
        
    # Guarda no slot especifico do tabuleiro
    slots_inimigos[slot_id]['tipo'] = nome_inimigo
    slots_inimigos[slot_id]['vida_atual'] = vida_inimigo
    
    # Recua para o centro
    print("A voltar ao centro...")


# Função para scanear lateralmente numa paragem (direita e/ou esquerda)
def scan_lateral(numero_da_paragem, fazer_esq, fazer_dir):
    print("\n--- SCAN PARAGEM " + str(numero_da_paragem) + " ---")
    movimento.stop()
    sleep(0.5)
    
    slot_esq = (numero_da_paragem * 2) - 1
    slot_dir = (numero_da_paragem * 2)
    
    # VERIFICAR ESQUERDA (Se solicitado)
    if fazer_esq:
        print(">> A verificar ESQUERDA (Slot " + str(slot_esq) + ")...")
        sensor_giro.reset()
        sleep(0.1)
        
        # Virar -90
        movimento.on(SpeedPercent(-15), SpeedPercent(15))
        while sensor_giro.angle > -90: 
            pass 
        movimento.stop()
        sleep(0.5)

        # Avançar um pouco para ler melhor a cor (Scan)
        movimento.on_for_seconds(SpeedPercent(20), SpeedPercent(20), 1.3)
        movimento.stop()
        sleep(0.5)

        dist = sensor_ultrassonico.distance_centimeters
        cor = sensor_cor.color_name
        # Lógica de Deteção
        if dist < 40 or cor in ["Blue", "Green", "Brown"]:
            print("Objeto detetado.")
            ler_cor_e_guardar(slot_esq)
        else:
            print("Vazio.")
            slots_inimigos[slot_esq]['tipo'] = "Vazio"
            slots_inimigos[slot_esq]['vida_atual'] = 0
            
        # Recuar para o centro do corredor
        movimento.on_for_seconds(SpeedPercent(-20), SpeedPercent(-20), 1.3)
        
        # Recentrar (Voltar a 0 graus)
        print(">> A voltar ao centro...")
        movimento.on(SpeedPercent(15), SpeedPercent(-15))
        while sensor_giro.angle < -2:  
            pass
        movimento.stop()
        sleep(0.5)

    # VERIFICAR DIREITA (Se solicitado)
    if fazer_dir:
        print(">> A verificar DIREITA (Slot " + str(slot_dir) + ")...")
        sensor_giro.reset() 
        sleep(0.5)
        
        movimento.on(SpeedPercent(15), SpeedPercent(-15))
        while sensor_giro.angle < 90: 
            pass 
        movimento.stop()
        sleep(0.5)
        # Avançar um pouco para ler melhor a cor (Scan)
        movimento.on_for_seconds(SpeedPercent(20), SpeedPercent(20), 1.3)
        movimento.stop()
        sleep(0.5)
        dist = sensor_ultrassonico.distance_centimeters
        cor = sensor_cor.color_name
        
        if dist < 40 or cor in ["Blue", "Green", "Brown"]:
            print("Objeto detetado.")
            ler_cor_e_guardar(slot_dir)
        else:
            print("Vazio.")
            slots_inimigos[slot_dir]['tipo'] = "Vazio"
            slots_inimigos[slot_dir]['vida_atual'] = 0
            
        movimento.on_for_seconds(SpeedPercent(-20), SpeedPercent(-20), 1.3)
        
        # Recentrar (Voltar a 0 graus)
        print(">> A voltar ao centro...")
        movimento.on(SpeedPercent(-15), SpeedPercent(15))
        while sensor_giro.angle > 0: 
            pass
        movimento.stop()
        sleep(0.5)

    print("Scan concluido.")


# Função para voltar à base
def voltar_a_base():
    print("\n--- A REGRESSAR A BASE ---")
    
    #Virar 180 (Topo)
    print("Topo: A dar meia volta (180)...")
    sensor_giro.reset()
    sleep(0.1)
    movimento.on(SpeedPercent(15), SpeedPercent(-15))
    while sensor_giro.angle < 178: pass
    movimento.stop()
    sleep(0.5)
    
    # Viajar ate À Base
    print("A navegar para a base...")
    movimento.on(SpeedPercent(30), SpeedPercent(30))
    
    while True:
        cor = sensor_cor.color_name
        # Se vir a base (Vermelho) OU bater no fundo
        if cor == "Red" or sensor_toque.is_pressed:
            movimento.stop()
            print("Base encontrada!")
            som.beep()
            break
        sleep(0.01)
            
    # Virar 180 (Base)
    print("Base: A dar meia volta final (180)...")
    
    sensor_giro.reset()
    sleep(0.1)
    movimento.on(SpeedPercent(15), SpeedPercent(-15))
    while sensor_giro.angle < 178: pass
    movimento.stop()
    
    print("Posicao inicial restaurada.")


# Função para percorrer o percurso e mapear os inimigos
def percorrer_e_mapear(turno_atual):
    print("\n--- INICIO DA PATRULHA (Turno " + str(turno_atual) + ") ---")
    movimento.on(SpeedPercent(30), SpeedPercent(30))
    
    linhas_contadas = 0
    estou_na_linha = False
    
    while True:
        cor = sensor_cor.color_name
        
        # LINHA PRETA DE CORREDOR
        if cor == "Black":
            if not estou_na_linha:
                estou_na_linha = True
                linhas_contadas += 1
                print("Linha Preta: " + str(linhas_contadas))
                som.beep()
                
                # Variáveis de decisão
                fazer_esq = False
                fazer_dir = False
                slot_id_esq = 0
                slot_id_dir = 0
                numero_paragem = 0
                
                # Mapear Linhas -> Slots
                if linhas_contadas == 1:
                    numero_paragem = 1
                    slot_id_esq = 1; slot_id_dir = 2
                elif linhas_contadas == 3:
                    numero_paragem = 2
                    slot_id_esq = 3; slot_id_dir = 4
                elif linhas_contadas == 5:
                    numero_paragem = 3
                    slot_id_esq = 5; slot_id_dir = 6

                if numero_paragem > 0: # Se for uma linha válida (1, 3 ou 5)
                    
                    # TURNO 2: Verifica TUDO
                    if turno_atual == 2:
                        fazer_esq = True
                        fazer_dir = True
                        
                    # OUTROS TURNOS: Só verifica VAZIOS
                    elif turno_atual > 2:
                        # Se o slot da esquerda estiver Vazio, ativa flag esquerda
                        if slots_inimigos[slot_id_esq]['tipo'] == "Vazio":
                            fazer_esq = True
                        
                        # Se o slot da direita estiver Vazio, ativa flag direita
                        if slots_inimigos[slot_id_dir]['tipo'] == "Vazio":
                            fazer_dir = True

                    # EXECUÇÃO
                    if fazer_esq or fazer_dir:
                        print("Scan Necessario: Esq=" + str(fazer_esq) + " Dir=" + str(fazer_dir))
                        
                        # ALINHAMENTO SEGURO (Com deteção de Vermelho)
                        tempo_inicial = time.time()
                        viu_vermelho = False
                        
                        # Avança para alinhar as rodas com a linha
                        movimento.on(SpeedPercent(30), SpeedPercent(30))
                        while time.time() - tempo_inicial < 1.3:
                            if sensor_cor.color_name == "Red":
                                viu_vermelho = True
                                break
                        movimento.stop()
                        
                        if viu_vermelho:
                            print("Fim da pista detetado no alinhamento!")
                            voltar_a_base()
                            break

                        # Executa o Scan Seletivo
                        scan_lateral(numero_paragem, fazer_esq, fazer_dir)
                        
                        print("A continuar patrulha...")
                        movimento.on(SpeedPercent(30), SpeedPercent(30))
                    else:
                        print("Slots ocupados. A ignorar.")

        elif cor != "Black":
            estou_na_linha = False
            
        # FIM DE PISTA
        if cor == "Red" or sensor_toque.is_pressed:
            movimento.stop()
            voltar_a_base()
            break
            
        time.sleep(0.01)
        
    movimento.stop()


#Função para gerir os turnos do jogo
def turnos_do_jogo():
    global defender_vida_atual
    global defender_energia_atual
    
    print("\n" + "="*40)
    print("      SISTEMA DE COMBATE HIBRIDO")
    print("="*40)

    for turno in range(1, 14):
        # 1. MOSTRAR CONFIGURAÇÃO DO TABULEIRO (Antes do Enter)
        # Chamamos o relatório para saberes o que o robô mapeou até agora
        print("\n" + "-"*30)
        print(" ESTADO DO TABULEIRO (Turno {})".format(turno))
        imprimir_relatorio_final()
        print("-"*30)

        print("\n" + "!"*40)
        print(" TURNO {:02d} / 13 ".format(turno).center(40, " "))
        print("!"*40)
        
        # Pausa para controlo total do utilizador
        input("\n>>> Pressiona ENTER para iniciar o turno...")

        # TURNOS ÍMPARES (INIMIGO)
        if turno % 2 != 0:
            print("[FASE INIMIGA]")
            
            # Passamos o turno atual para o cálculo correto de dano (regra de 1 turno de espera)
            dano_recebido = calcular_ameaca_total_no_tabuleiro(turno)
            
            if dano_recebido > 0:
                defender_vida_atual -= dano_recebido
                print(">> Recebeste {} de dano.".format(dano_recebido))
                som.beep() # Alerta de dano
            else:
                print(">> Nenhum inimigo em posicao de ataque (aguardando turno ou vazio).")

        # TURNOS PARES (ROBÔ)
        else:
            print("\n[FASE ROBO]")
            
            # Recuperação de Energia
            recup = int(defender_energia_atual * 0.5)
            defender_energia_atual += recup
            if defender_energia_atual > defender_energia_max:
                defender_energia_atual = defender_energia_max
            
            print(">> Energia: {} (+{}) | Vida: {}".format(defender_energia_atual, recup, defender_vida_atual))
            
            # Patrulha Automática (Turnos de Scan)
            if turno in [2, 4, 6, 8, 10, 12]:
                percorrer_e_mapear(turno)
            
            # DECISÃO DE COMANDO
            print("\n--- DECISAO DE COMANDO ---")
            escolha = input("Escolha: (A) para IA Preditiva ou (M) para Menu Manual: ").upper()
            
            if escolha == 'M':
                menu_acao_manual()
            else:
                print(">> A consultar IA Preditiva...")
                decisao, alvo, detalhe = decidir_jogada_IA(turno)
                
                if decisao == "ATACAR":
                    print(">> IA decidiu ATACAR Slot {} com arma {}".format(alvo, detalhe))
                    executar_ataque_manual_fisico(alvo, detalhe)
                
                elif decisao == "CURAR":

                    print(">> IA decidiu CURAR-SE (Nivel {})".format(alvo))
                    usar_cura(alvo) 
                
                else:
                    print(">> IA decidiu PASSAR TURNO para acumular energia.")
            
        # --- FIM DO TURNO: MOSTRAR VIDA SE SOBREVIVER ---
        if defender_vida_atual > 0:
            print("\n" + "."*30)
            print(" RESUMO FINAL DO TURNO {}".format(turno))
            print(" VIDA RESTANTE DO ROBO: {}".format(defender_vida_atual))
            print(" ENERGIA ATUAL: {}".format(defender_energia_atual))
            print("."*30)
        else:
            print("\n" + "X"*40)
            print("      GAME OVER - O ROBO FOI DESTRUIDO")
            print("X"*40)
            break
            
        print("\n--- Turno {} concluido. Aguardando proximo... ---".format(turno))

    if defender_vida_atual > 0:
        print("\n" + "#"*40)
        print("      VITORIA - MISSAO CUMPRIDA!")
        print("#"*40)
        imprimir_relatorio_final()


# Função para imprimir o relatório final dos inimigos mapeados
def imprimir_relatorio_final():
    print("\n" + "="*30)
    print("   RELATORIO DE INIMIGOS (Memoria)")
    print("="*30)
    for i in range(1, 7):
        info = slots_inimigos[i]
        
        tipo_txt = info['tipo'] if info['tipo'] is not None else "Desconhecido"
        vida_txt = str(info['vida_atual'])
        
        print("Slot " + str(i) + ": " + tipo_txt + " (Vida: " + vida_txt + ")")
    print("-" * 30)


# Função para calcular o dano real que um inimigo causará no turno atual
def calcular_dano_real_inimigos(turno_atual, slot_id):
    total_dano = 0
    inimigo = tabuleiro_real[slot_id]
    
    # REGRA: Só ataca se a vida for > 0 E se o turno em que ele entrou 
    # for MENOR que o turno atual (ou seja, já passou pelo menos 1 turno).
    if inimigo['vida_atual'] > 0 and inimigo['turno_ataque'] < turno_atual:
        stats = INIMIGOS[inimigo['tipo']]
        ratio = inimigo['vida_atual'] / stats['vida']
        total_dano = int(stats['forca'] * ratio)
        
    return total_dano


# Função para calcular o dano total que o robô receberá no turno atual
def calcular_ameaca_total_no_tabuleiro(turno_atual):
    total = 0
    for i in range(1, NUMERO_DE_SLOTS + 1):
        total += calcular_dano_real_inimigos(turno_atual, i) 
    return total


# Função para prever o dano que o inimigo causará após ser atacado
def prever_dano_apos_ataque(slot_id, dano_da_arma):
    info = slots_inimigos[slot_id]
    tipo = info['tipo']
    stats = INIMIGOS[tipo]
    
    vida_futura = info['vida_atual'] - dano_da_arma
    if vida_futura <= 0:
        return 0 # Inimigo morto não causa dano
        
    ratio_futuro = vida_futura / stats['vida']
    return int(stats['forca'] * ratio_futuro)


# Função para aplicar o dano ao inimigo no tabuleiro real e na memória
def aplicar_dano_ao_inimigo(slot_id, dano):
    # Se o robô atacou algo que não tinha mapeado (tipo é None ou Vazio)
    if slots_inimigos[slot_id]['tipo'] is None or slots_inimigos[slot_id]['tipo'] == "Vazio":
        slots_inimigos[slot_id]['tipo'] = tabuleiro_real[slot_id]['tipo']

    # Subtrair vida em ambos
    tabuleiro_real[slot_id]['vida_atual'] -= dano
    slots_inimigos[slot_id]['vida_atual'] = tabuleiro_real[slot_id]['vida_atual']
    
    # Garantir que não há vida negativa
    if tabuleiro_real[slot_id]['vida_atual'] < 0:
        tabuleiro_real[slot_id]['vida_atual'] = 0
        slots_inimigos[slot_id]['vida_atual'] = 0


# Função principal da IA para decidir a jogada do robô
def decidir_jogada_IA(turno_atual):
    # 1. Encontrar o melhor alvo
    alvo = selecionar_melhor_alvo()
    
    if alvo != -1:
        # 2. Escolher a arma para esse alvo
        arma = escolher_arma_ideal(alvo)
        
        if arma != -1:
            # 3. Validar se o ataque é seguro 
            if verificar_seguranca_ataque(alvo, arma, turno_atual):
                return ("ATACAR", alvo, arma)
    
    # 4. Se não há alvo, não há energia ou o ataque é perigoso: Tentar Curar
    nivel_cura = avaliar_necessidade_cura(turno_atual)
    if nivel_cura != -1:
        return ("CURAR", nivel_cura, None)
        
    # 5. Último recurso: Ataque Kamikaze (Melhor morrer a lutar do que parado)
    if alvo != -1 and defender_energia_atual >= 50:
        return ("ATACAR", alvo, 3)
    return ("PASSAR", None, None)


#Heurística para selecionar o melhor alvo, esta decide qual o inimigo mais perigoso no tabuleiro e retorna o slot desse inimigo
def selecionar_melhor_alvo():
    melhor_alvo = -1
    melhor_valor = -1
    
    for i in range(1, NUMERO_DE_SLOTS + 1):
        info = slots_inimigos[i]
        
        # SÓ ATACA SE O INIMIGO ESTIVER PRONTO
        if info['tipo'] is None or info['tipo'] == "Vazio" or info['vida_atual'] <= 0:
            continue
            
        tipo = info['tipo']
        stats = INIMIGOS[tipo]
        
        multiplicador_urgencia = 1.5 
        
        ratio = info['vida_atual'] / stats['vida']
        dano_potencial = stats['forca'] * ratio
        prioridade = PRIORIDADES[tipo]
        
        valor = (dano_potencial * 20) + (prioridade * 15)
        valor *= multiplicador_urgencia # Dá peso ao facto de ele já estar pronto para atacar
        
        if valor > melhor_valor:
            melhor_valor = valor
            melhor_alvo = i
            
    return melhor_alvo


# Heurística para escolher a arma ideal para um alvo específico, esta foca-se na eficiência energética
def escolher_arma_ideal(slot_id):
    vida_alvo = slots_inimigos[slot_id]['vida_atual']
    
    # Tenta matar com o mínimo de energia, ou usa o mais forte que puder pagar
    if vida_alvo <= 50 and defender_energia_atual >= 50: 
        return 3 # Som
    if vida_alvo <= 100 and defender_energia_atual >= 150: 
        return 2 # Toque
    if defender_energia_atual >= 300: 
        return 1 # Grua
    if defender_energia_atual >= 150: 
        return 2 # Toque 
    if defender_energia_atual >= 50: 
        return 3 # Som 
    
    return -1 # Sem energia para atacar


# Heurística para verificar se o ataque é seguro para o robô
# 1. calcula o dano total que o robô está a receber agora
# 2. calcula o dano que o robô receberia depois do ataque
# 3. decide o que fazer, se o dano depois do ataque for menor que a vida atual, é seguro atacar
def verificar_seguranca_ataque(slot_id, arma_id, turno_atual):
    # Mapeia o dano da arma
    key_arma = 'grua' if arma_id == 1 else 'toque' if arma_id == 2 else 'som'
    dano_previsto = ATAQUES[key_arma]['dano']
    
    dano_total_agora = calcular_ameaca_total_no_tabuleiro(turno_atual)
    dano_inimigo_antes = calcular_dano_real_inimigos(turno_atual, slot_id)
    dano_inimigo_depois = prever_dano_apos_ataque(slot_id, dano_previsto)
    
    # Simulação: Dano total diminuído pela redução de vida deste alvo específico
    dano_final_previsto = dano_total_agora - (dano_inimigo_antes - dano_inimigo_depois)
    
    return defender_vida_atual > dano_final_previsto


# Heurística para avaliar se o robô precisa de se curar
def avaliar_necessidade_cura(turno_atual):
    ameaca_total = calcular_ameaca_total_no_tabuleiro(turno_atual)
    
    # Se o perigo for alto ou a vida estiver crítica
    if ameaca_total >= defender_vida_atual or defender_vida_atual < (defender_vida_max * 0.15):
        # Tenta a maior cura possível de acordo com a energia disponível
        if defender_energia_atual >= 400: 
            return 3 # Grande
        if defender_energia_atual >= 300: 
            return 2 # Média
        if defender_energia_atual >= 200: 
            return 1 # Pequena
        
    return -1 # Não precisa ou não pode curar


# Função para sortear inimigos com dados
def sortear_inimigos_com_dados():
    global tabuleiro_real
    print("\n--- CONFIGURACAO DO TABULEIRO (Sorteio Manual) ---")
    
    for slot_atual in range(1, 7):        
        dado_tipo = random.randint(1, 6)
        tipo = "Tanque" if dado_tipo <= 2 else "Artilharia" if dado_tipo <= 4 else "Infantaria"
        
        # Turnos ímpares conforme a tua regra: 1, 3, 5...
        dado_turno = (random.randint(1, 6) * 2) - 1
        
        tabuleiro_real[slot_atual]['tipo'] = tipo
        tabuleiro_real[slot_atual]['vida_atual'] = INIMIGOS[tipo]['vida']
        tabuleiro_real[slot_atual]['turno_ataque'] = dado_turno

        # O robô imprime para ti, mas a IA dele não lê esta variável
        print("Slot", slot_atual, ":", tipo, "(Entra no Turno", dado_turno, ")")


# MAIN
def main():
    sortear_inimigos_com_dados()
    turnos_do_jogo()
    #turnos_do_jogo()
    # Pergunta qual slot atacar
    
    # Simulação: Vamos atacar o Slot 3
    # No futuro podes usar o input() para escolher
    
    #usar_som()
    
    #verificar_flancos_com_gyro()
    #som.play_file("cbaec71a.wav") #play ao som do max verstappen
    #som.play_file("Madeira-Mix-_h_LHYlsr4vI_.wav") #play ao som do madeira mix
    
    #confirmar_inicialização() #confirma a inicialização do robo
    #turnos_do_jogo() #inicia os turnos do jogo, podem tirar isto para ser mais fácil testar o tabuleiro
    #atacar_com_toque() #ataque de toque
    #atacar_com_grua() #ataque com grua
    #usem este while para testar os sensores, se quiserem resultados mais rápidos metam um numero
    #mais pequeno no sleep, para terminar usem ctrl+c
    #recomendo começarem por testar quais cores o gajo tá a ler com o sensor de cor no tabuleiro 
    #e façam ele dar uma volta dentro do quadrado para ver se ele esta dentro para depois ele começar o jogo
    #vejam tbm as cores das cartolinas como estão
    #while True:
        #detetar_cor() 
        #distancia()
        #sensor_toque_estado()
        #print("---------------------------") 
        #sleep(0.5)
    #sortear_inimigos_com_dados()

main()

