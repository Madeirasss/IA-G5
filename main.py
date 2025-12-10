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

energia_a_recuperar_prox_turno = 0 #Para calculo de energia a recuperar no proximo turno
vida_a_recuperar_prox_turno = 0 #Para calculo de vida a recuperar no proximo turno

#Slots dos inimigos no tabuleiro
NUMERO_DE_SLOTS = 8  # <--- MUDAS AQUI PARA O NÚMERO QUE QUISERES
slots_inimigos = {
    i: {'tipo': None, 'vida_inicial': 0, 'vida_atual': 0, 'turno_ataque': 0} 
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

def virar_com_gyro(graus):
    """
    Vira o robô X graus usando o Gyro.
    Positivo = Direita, Negativo = Esquerda.
    """
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

# ==============================================================================
# NOVA FUNÇÃO DE ATAQUE (SEM MEDIR ROTAÇÃO DAS RODAS)
# ==============================================================================
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

    # 2. Navegar até à linha (Já implementado no teu código principal)
    # A função 'executar_ataque_manual_fisico' já chama o 'ir_ate_linha' antes disto.
    # Assumimos que o robô acabou de parar em cima da linha preta.

    # 3. Avançar para o Meio do Quadrado
    # Como não queres medir rotação, usamos um tempo fixo seguro.
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
        # Mas como pediste simples, deixamos só o US.
        pass
    movimento.stop()
    print("Alvo encontrado.")
    sleep(0.5)

    # 6. O GRANDE 180 (Ficar de costas para o inimigo)
    print("A rodar 180 para posicao de Grua...")
    virar_com_gyro(180)

    # 7. EXECUÇÃO DO ATAQUE
    print(">>> ATAQUE GRUA <<<")
    # Baixa a grua
    motor_medio.on_for_seconds(SpeedPercent(100), 1.5) 
    sleep(0.5)
    # Levanta a grua
    motor_medio.on_for_seconds(SpeedPercent(-100), 1.5)
    
    defender_energia_atual -= custo
    print("Sucesso! Energia: " + str(defender_energia_atual))

    # ==================================================================
    # 8. O REGRESSO (SEM ROTAÇÃO)
    # ==================================================================
    # O robô está de costas para o inimigo.
    # Logo, está de FRENTE para o corredor central.
    # Só precisamos de andar em frente até detetar a LINHA PRETA central.
    
    print("A sair do slot...")
    movimento.on(SpeedPercent(20), SpeedPercent(20))
    
    # Sai do slot até ver preto (ou até bater na parede oposta, cuidado)
    # Usamos um timer minimo para ele não ler a linha do próprio quadrado imediatamente
    time.sleep(0.5) 
    
    while True:
        cor = sensor_cor.color_name
        # Se vir a linha preta do corredor ou a parede vermelha
        if cor == "Black":
            print("Corredor detetado.")
            break
        if cor == "Red": 
            print("Parede detetada (Segurança).")
            break
            
    # Avança mais um bocadinho (0.3s) para o eixo das rodas ficar em cima da linha
    # movimento.on_for_seconds(SpeedPercent(20), SpeedPercent(20), 0.3)
    movimento.stop()

    # 9. Virar para a Base
    print("A virar para a Base...")
    
    # Se entramos à Direita, e estamos de frente para o corredor, a Base está à Esquerda.
    # Se entramos à Esquerda, a Base está à Direita.
    if direcao_inicial == 1: # Tinhamos virado à Direita
        virar_com_gyro(90) # Vira Esquerda para a base
    else: # Tinhamos virado à Esquerda
        virar_com_gyro(-90) # Vira Direita para a base

    # 10. Voltar à Base
    voltar_a_base()
    
    return dano


#Função de ataque com toque


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
    
    print("A tentar 'Cura " ,numero_da_cura, "Custo: ",custo, " EN, Recupera: ",recupera)
    #verifica se tem enregia suficiente para curar-se
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



def obter_coordenadas_slot(slot_id):
    """
    Mapeamento manual dos slots para as linhas que pediste:
    - Slot 1 e 2 -> Linha 1
    - Slot 3 e 4 -> Linha 3
    - Slot 5 e 6 -> Linha 5
    """
    
    # 1. Definir a Linha (AGORA COM OS TEUS VALORES FIXOS)
    linha_alvo = 1 # Valor base
    
    if slot_id == 1 or slot_id == 2:
        linha_alvo = 1
    elif slot_id == 3 or slot_id == 4:
        linha_alvo = 3  # <--- Mudado conforme pediste
    elif slot_id == 5 or slot_id == 6:
        linha_alvo = 5  # <--- Mudado conforme pediste
        
    # 2. Definir a Direção (Igual a antes)
    # Se o numero for PAR (2, 4, 6), é Direita (1). 
    # Se for IMPAR (1, 3, 5), é Esquerda (-1)
    if slot_id % 2 == 0:
        direcao = 1 # Direita
    else:
        direcao = -1 # Esquerda
        
    return linha_alvo, direcao


def ir_ate_linha(numero_linha_desejada):
    """
    Sai da base e avança até contar o numero certo de linhas pretas.
    """
    print(">> A viajar para a Linha " + str(numero_linha_desejada) + "...")
    movimento.on(SpeedPercent(30), SpeedPercent(30))
    
    linhas_contadas = 0
    estou_na_linha = False
    
    while True:
        cor = sensor_cor.color_name
        
        # Lógica de contagem igual à da Patrulha
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
            
        # Segurança: Se bater ou vir parede vermelha
        if cor == "Red" or sensor_toque.is_pressed:
            movimento.stop()
            print("Erro: Fim da pista encontrado antes do destino.")
            break
            
        sleep(0.01)
        
    # Pequeno ajuste para parar as rodas exatamente em cima da cor (opcional)
    # movimento.on_for_seconds(SpeedPercent(10), SpeedPercent(10), 0.2)

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

        # --- FASE 1: AVANÇAR ATÉ TOCAR ---
        # Loop de segurança: Para se tocar no botão OU se andar demasiado (US > 30cm)
        tempo_limite = time.time() + 4 # 4 segundos maximo para encontrar algo
        
        while not sensor_toque.is_pressed:
            # Se o tempo passar ou o sensor US disser que já não há nada à frente
            if time.time() > tempo_limite:
                print("Tempo esgotado/Alvo falhado!")
                movimento.stop()
                # Recua um pouco por segurança (1 seg)
                movimento.on_for_seconds(SpeedPercent(-30), SpeedPercent(-30), 1)
                return 0 # Falhou
            sleep(0.01)

        # --- FASE 2: O IMPACTO ---
        movimento.stop()
        print("IMPACTO CONFIRMADO!")
        som.beep()
        sleep(0.5)
        
        # --- FASE 3: RECUAR ATÉ LINHA PRETA (CENTRO) ---
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

# ==============================================================================
# 2. ATAQUE COM SOM (Só gasta energia e faz barulho)
# ==============================================================================
def atacar_com_som():
    global defender_energia_atual
    
    custo = ATAQUES['som']['custo_en']
    dano = ATAQUES['som']['dano']
    
    print(">>> ATAQUE SONICO (Custo:", custo, ")")
    
    if defender_energia_atual >= custo:
        # O robô já está virado para o inimigo (feito pela função principal)
        # Vamos só avançar um pouquinho para "entrar" na sala, gritar e voltar
        
        # Opcional: Entrar um pouco no slot
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

def executar_ataque_manual_fisico(slot_alvo, tipo_arma):
    """
    Controla toda a sequência do ataque manual.
    """
    print("\n--- INICIAR ATAQUE MANUAL (Slot " + str(slot_alvo) + ") ---")
    
    # 1. Navegar até à linha correta (Usando a nova lógica de slots 1, 3, 5)
    linha_alvo, direcao = obter_coordenadas_slot(slot_alvo)
    ir_ate_linha(linha_alvo)
    
    # Centrar no quadrado (Avançar um pouco depois de ver a linha para as rodas ficarem no sitio)
    movimento.on_for_seconds(SpeedPercent(30), SpeedPercent(30), 1.5)
    
    dano_realizado = 0
    
    # --- OPÇÃO A: GRUA (Faz tudo sozinha) ---
    if tipo_arma == 1: 
        dano_realizado = atacar_com_grua(slot_alvo)
        # A função atacar_com_grua já inclui o voltar_a_base, por isso acabamos aqui.
        
    # --- OPÇÃO B: TOQUE OU SOM (Nós controlamos a rotação) ---
    else: 
        # 2. Virar 90º para o inimigo
        print("A virar para o alvo...")
        
        if slot_alvo % 2 != 0: # Impar = Esquerda
             virar_com_gyro(-90)
             direcao_inicial = -1
        else: # Par = Direita
             virar_com_gyro(90)
             direcao_inicial = 1
        
        # 3. Executar o Ataque Específico
        if tipo_arma == 2:
            dano_realizado = atacar_com_toque()
        elif tipo_arma == 3:
            dano_realizado = atacar_com_som()
            
        # 4. Re-alinhar (Virar para a Base)
        print("A realinhar com o corredor...")
        
        # Se virámos à Direita (1), agora para olhar para a Base temos de virar Esquerda (-90)
        # Se virámos à Esquerda (-1), agora para olhar para a Base temos de virar Direita (90)
        
        if direcao_inicial == 1:
            virar_com_gyro(-90)
        else:
            virar_com_gyro(90)
        
        # 5. Voltar à Base
        voltar_a_base()

    # --- ATUALIZAÇÃO DE DADOS ---
    if dano_realizado > 0:
        slots_inimigos[slot_alvo]['vida_atual'] -= dano_realizado
        if slots_inimigos[slot_alvo]['vida_atual'] <= 0:
            slots_inimigos[slot_alvo]['vida_atual'] = 0
            print("INIMIGO DESTRUIDO!")
            som.speak("Target Down")
        else:
            print("Inimigo HP: " + str(slots_inimigos[slot_alvo]['vida_atual']))


def menu_acao_manual():
    """
    Menu interativo para o jogador escolher o que fazer.
    """
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

# ==============================================================================
# LOGICA DOS TURNOS (O CEREBRO DO JOGO)
# ==============================================================================

def turnos_do_jogo():
    global defender_vida_atual
    global defender_energia_atual
    
    print("\n" + "="*30)
    print("   INICIO DA BATALHA")
    print("="*30)
    sleep(1)

    # Loop de 1 a 13
    for turno in range(1, 14):
        print("\n" + "-"*30)
        print("TURNO " + str(turno) + " / 13")
        print("-" * 30)
        
        # --- TURNOS IMPARES (INIMIGO) ---
        if turno % 2 != 0:
            print("[FASE INIMIGA]")
            print("Inimigos a atacar...")
            sleep(1)
            
            dano_recebido = 0
            #for i in range(1, NUMERO_DE_SLOTS + 1):
            #    info = slots_inimigos[i]
            #    if info['tipo'] != "Vazio" and info['vida_atual'] > 0:
            #        nome = info['tipo']
                    
                    # Procura stats do inimigo
            #        forca_base = 0
            #        ataques = 1
                    
                    # Procura no dicionario global INIMIGOS
            #        for k, v in INIMIGOS.items():
            #            if k == nome:
            #                forca_base = v['forca']
            #                ataques = v['ataques']
            #                break
            #        
            #        dano_ataque = forca_base * ataques
            #        print("Slot " + str(i) + " (" + nome + ") ataca: " + str(dano_ataque) + " dano.")
            #        dano_recebido += dano_ataque
            
            if dano_recebido > 0:
                defender_vida_atual -= dano_recebido
                print(">> TOTAL DANO SOFRIDO: " + str(dano_recebido))
            else:
                print("Nenhum dano recebido.")

        # --- TURNOS PARES (ROBO) ---
        else:
            print("[FASE ROBO]")
            
            # 1. Energia
            recup = int(defender_energia_atual * 0.5)
            defender_energia_atual += recup
            if defender_energia_atual > defender_energia_max:
                defender_energia_atual = defender_energia_max
            
            print("Energia: " + str(defender_energia_atual) + " (+" + str(recup) + ")")
            print("Vida: " + str(defender_vida_atual))
            
            # 2. PATRULHA AUTOMATICA
            # (Turnos especificos ou sempre, conforme preferires)
            if turno in [2, 4, 6, 8, 10, 12]:
                print("A iniciar patrulha automatica...")
                
                # Turno 2 = Scan Tudo, Outros = Scan Vazios
                modo_scan = "tudo" if turno == 2 else "seletivo"
                percorrer_e_mapear(turno) # Nota: tens de atualizar a funcao percorrer_e_mapear para aceitar argumento ou criar variavel global
                
                # Se a tua funcao percorrer_e_mapear nao aceita argumentos, usa so:
                # percorrer_e_mapear() 
            
            # 3. MENU MANUAL (A Tua Escolha)
            # Permite atacar ou curar depois da patrulha
            menu_acao_manual()
            
        # Fim de Jogo?
        if defender_vida_atual <= 0:
            print("GAME OVER.")
            break
            
        sleep(1)

    if defender_vida_atual > 0:
        print("VITORIA!")


def sortear_inimigos_com_dados():
    global slots_inimigos
    global INIMIGOS
    print("\n--- A PREENCHER TABULEIRO (DADOS VIRTUAIS) ---")
    
    # Loop direto do 1 ao 6 (Slot 1, Slot 2, ..., Slot 6)
    for slot_atual in range(1, 7):        
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
        
        # 3. Guardar na memória do Robô
        # Vai buscar a vida máxima ao dicionário de stats
        vida_inicial = INIMIGOS[tipo]['vida']

        # Como estamos no loop 'for slot_atual', guardamos diretamente nesse slot
        slots_inimigos[slot_atual]['tipo'] = tipo
        slots_inimigos[slot_atual]['vida_atual'] = vida_inicial
        slots_inimigos[slot_atual]['turno_ataque'] = dado_turno

        # 4. Instruir o jogador (opcional: podes comentar isto se quiseres ser mais rápido)
        print("Slot",slot_atual,"Coloca",tipo,"Turno",dado_turno) 



def ler_cor_e_guardar(slot_id):
    """ 
    Avanca, le a cor, compara com a estrutura INIMIGOS e guarda. 
    """
    print("A aproximar para identificar...")
    
    # 1. Avanca um pouco para o sensor ficar em cima da cor
    sleep(1)
    
    # 2. Le a cor do chão
    cor_lida = sensor_cor.color_name
    print("Cor detetada: " + cor_lida)
    
    nome_inimigo = "Vazio"
    vida_inimigo = 0
    found = False
    
    # 3. PROCURA INTELIGENTE
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
    # 4. Feedback e Registo
    if found:
        print("Identificado: " + nome_inimigo + " (" + str(vida_inimigo) + " HP)")
    else:
        print("Cor nao corresponde a inimigos (Vazio).")
        som.beep()
        
    # Guarda no slot especifico do tabuleiro
    slots_inimigos[slot_id]['tipo'] = nome_inimigo
    slots_inimigos[slot_id]['vida_atual'] = vida_inimigo
    
    # 5. Recua para o centro
    print("A voltar ao centro...")


def scan_lateral(numero_da_paragem, fazer_esq, fazer_dir):
    print("\n--- SCAN PARAGEM " + str(numero_da_paragem) + " ---")
    movimento.stop()
    sleep(0.5)
    
    slot_esq = (numero_da_paragem * 2) - 1
    slot_dir = (numero_da_paragem * 2)
    
    # ==========================================
    # 1. VERIFICAR ESQUERDA (Se solicitado)
    # ==========================================
    if fazer_esq:
        print(">> A verificar ESQUERDA (Slot " + str(slot_esq) + ")...")
        sensor_giro.reset()
        sleep(0.1)
        
        # Virar -90
        movimento.on(SpeedPercent(-15), SpeedPercent(15))
        while sensor_giro.angle > -80: 
            pass 
        movimento.stop()
        sleep(0.5)
        
        # Leitura
        
        
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
        while sensor_giro.angle < -2:  # Margem pequena perto do 0
            pass
        movimento.stop()
        sleep(0.5)

    # ==========================================
    # 2. VERIFICAR DIREITA (Se solicitado)
    # ==========================================
    if fazer_dir:
        print(">> A verificar DIREITA (Slot " + str(slot_dir) + ")...")
        sensor_giro.reset() 
        sleep(0.5)
        
        # Virar +90
        movimento.on(SpeedPercent(15), SpeedPercent(-15))
        while sensor_giro.angle < 80: 
            pass 
        movimento.stop()
        sleep(0.5)
        
        
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
        while sensor_giro.angle > 2: # Margem pequena perto do 0
            pass
        movimento.stop()
        sleep(0.5)

    print("Scan concluido.")

# ==============================================================================
# 4. VOLTAR A BASE
# ==============================================================================

def voltar_a_base():
    print("\n--- A REGRESSAR A BASE ---")
    
    # 1. Recuar
    
    # 2. Virar 180 (Topo)
    print("Topo: A dar meia volta (180)...")
    sensor_giro.reset()
    sleep(0.1)
    movimento.on(SpeedPercent(15), SpeedPercent(-15))
    while sensor_giro.angle < 178: pass
    movimento.stop()
    sleep(0.5)
    
    # 3. Viajar ate Base
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
            
    # 4. Virar 180 (Base)
    print("Base: A dar meia volta final (180)...")
    
    sensor_giro.reset()
    sleep(0.1)
    movimento.on(SpeedPercent(15), SpeedPercent(-15))
    while sensor_giro.angle < 178: pass
    movimento.stop()
    
    print("Posicao inicial restaurada.")

# ==============================================================================
# 5. NAVEGACAO
# ==============================================================================

def percorrer_e_mapear(turno_atual):
    print("\n--- INICIO DA PATRULHA (Turno " + str(turno_atual) + ") ---")
    movimento.on(SpeedPercent(30), SpeedPercent(30))
    
    linhas_contadas = 0
    estou_na_linha = False
    
    while True:
        cor = sensor_cor.color_name
        
        # --- LINHA PRETA ---
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

                # --- LÓGICA DE DECISÃO INTELIGENTE ---
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

                    # --- EXECUÇÃO ---
                    if fazer_esq or fazer_dir:
                        print("Scan Necessario: Esq=" + str(fazer_esq) + " Dir=" + str(fazer_dir))
                        
                        # ALINHAMENTO SEGURO (Com deteção de Vermelho)
                        tempo_inicial = time.time()
                        viu_vermelho = False
                        
                        # Avança para alinhar as rodas com a linha (aprox 1.1s)
                        movimento.on(SpeedPercent(30), SpeedPercent(30))
                        while time.time() - tempo_inicial < 1.1:
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
            
        # --- FIM DE PISTA ---
        if cor == "Red" or sensor_toque.is_pressed:
            movimento.stop()
            voltar_a_base()
            break
            
        time.sleep(0.01)
        
    movimento.stop()

def imprimir_relatorio_final():
    print("\n" + "="*30)
    print("   RELATORIO DE INIMIGOS")
    print("="*30)
    for i in range(1, 7):
        tipo = slots_inimigos[i]['tipo']
        vida = str(slots_inimigos[i]['vida_atual'])
        print("Slot " + str(i) + ": " + tipo + " (Vida: " + vida + ")")
    print("-" * 30)




# ==============================================================================
# MAIN
# ==============================================================================
def main():
    turnos_do_jogo()
    sortear_inimigos_com_dados()
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

