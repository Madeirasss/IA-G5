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

#Slots dos inimigos no tabuleiro
NUMERO_DE_SLOTS = 8  # <--- MUDAS AQUI PARA O NÚMERO QUE QUISERES
slots_inimigos = {
    i: {'tipo': None, 'vida_inicial': 0, 'vida_atual': 0, 'turno_ataque': 0} 
    for i in range(1, NUMERO_DE_SLOTS + 1)
}
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
        movimento.on_for_seconds(SpeedPercent(30), SpeedPercent(-30), 3)
        movimento.on(SpeedPercent(-20), SpeedPercent(-20))
        while sensor_cor.color_name != "Blue":
            # Pequena pausa para não sobrecarregar o CPU
            sleep(0.01)
            
            # (Opcional de Segurança) Se ele recuar demais e vir Verde ou Vermelho, para também!
            cor = sensor_cor.color_name
            if cor == "Red":
                print("Recuei demais! (Vi " + cor + ")")
                break
        #dá print na energia restante
        movimento.on_for_seconds(SpeedPercent(-30), SpeedPercent(-30),0.3)

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
    
    print("A tentar 'Ataque com Toque' (Custo:", custo, ")")
    
    if defender_energia_atual >= custo:

        print("Energia OK. A avancar para o impacto...")
        
        # Liga os motores para a frente
        movimento.on(SpeedPercent(40), SpeedPercent(40)) 

        # --- FASE 1: AVANÇAR ATÉ TOCAR ---
        while not sensor_toque.is_pressed:
            dist = sensor_ultrassonico.distance_centimeters
            sleep(0.01) 
            
            # Segurança (se o alvo fugir)
            if dist > 30: 
                print("Alvo perdido!")
                movimento.stop()
                # Se falhou, recua o que andou (aqui usamos graus porque não sabemos onde estamos)
                graus_para_recuar = movimento.left_motor.position
                movimento.on_for_degrees(SpeedPercent(30), SpeedPercent(30), -graus_para_recuar)
                return 0 

        # --- FASE 2: O IMPACTO ---
        movimento.stop()
        print("ALVO ATINGIDO!")
        
        # Simula o choque
        sleep(0.5)
        
        # --- FASE 3: RECUAR ATÉ VER AZUL ---
        print("A recuar ate encontrar a zona AZUL...")
        
        # 1. Liga os motores para trás (e deixa ligados)
        movimento.on(SpeedPercent(-20), SpeedPercent(-20)) # Velocidade mais baixa para não falhar a cor
        
        # 2. O LOOP MÁGICO
        # Enquanto a cor NÃO for Blue, o programa fica preso aqui à espera
        while sensor_cor.color_name != "Blue":
            # Pequena pausa para não sobrecarregar o CPU
            sleep(0.01)
            
            # (Opcional de Segurança) Se ele recuar demais e vir Verde ou Vermelho, para também!
            cor = sensor_cor.color_name
            if cor == "Red":
                print("Recuei demais! (Vi " + cor + ")")
                break
        
        # 3. Saiu do loop (viu Azul ou outra cor de paragem), então PARA.
        movimento.stop()
        print("Zona Azul encontrada. Posicao restaurada.")
        
        defender_energia_atual -= custo
        print("Energia restante: ", defender_energia_atual)
        return dano
        
    else:
        print("FALHOU! Energia insuficiente.")
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


def executar_ataque_manual_fisico(slot_alvo, tipo_arma):
    """
    Navega ate ao slot e executa o ataque escolhido.
    tipo_arma: 1=Grua, 2=Toque, 3=Som
    """
    print("\n--- A INICIAR ATAQUE MANUAL AO SLOT " + str(slot_alvo) + " ---")
    
    # 1. Navegar ate a posicao (Usando as funcoes que ja tens)
    linha_alvo, direcao = obter_coordenadas_slot(slot_alvo)
    ir_ate_linha(linha_alvo)
    
    # 2. Virar para o inimigo
    print("A virar para o alvo...")
    sensor_giro.reset()
    sleep(0.1)
    
    ang_alvo = 88 if direcao == 1 else -88
    
    if direcao == 1: # Direita
        movimento.on(SpeedPercent(15), SpeedPercent(-15))
        while sensor_giro.angle < ang_alvo: pass
    else: # Esquerda
        movimento.on(SpeedPercent(-15), SpeedPercent(15))
        while sensor_giro.angle > ang_alvo: pass
    movimento.stop()
    
    # 3. Executar o Ataque
    dano_realizado = 0
    if tipo_arma == 1:
        dano_realizado = atacar_com_grua()
    elif tipo_arma == 2:
        dano_realizado = atacar_com_toque()
    elif tipo_arma == 3:
        dano_realizado = atacar_com_som()
        
    # 4. Atualizar Vida
    if dano_realizado > 0:
        slots_inimigos[slot_alvo]['vida_atual'] -= dano_realizado
        if slots_inimigos[slot_alvo]['vida_atual'] <= 0:
            slots_inimigos[slot_alvo]['vida_atual'] = 0
            print("INIMIGO DESTRUIDO!")
            som.speak("Alvo eliminado", espeak_opts='-v pt')
        else:
            print("Vida restante: " + str(slots_inimigos[slot_alvo]['vida_atual']))
            
    # 5. Voltar a Base
    # Primeiro vira para o centro
    print("A voltar a posicao...")
    sensor_giro.reset()
    sleep(0.1)
    if direcao == 1: # Estava Dir -> Vira Esq
        movimento.on(SpeedPercent(-15), SpeedPercent(15))
        while sensor_giro.angle > -88: pass
    else: # Estava Esq -> Vira Dir
        movimento.on(SpeedPercent(15), SpeedPercent(-15))
        while sensor_giro.angle < 88: pass
    movimento.stop()
    
    voltar_a_base()

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
                        print(" 1. Grua (100 Dano / 300 En)")
                        print(" 2. Toque (200 Dano / 150 En)")
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

    print("Scan concluído.")

# ==============================================================================
# 4. VOLTAR A BASE
# ==============================================================================

def voltar_a_base():
    print("\n--- A REGRESSAR A BASE ---")
    
    # 1. Recuar
    movimento.on_for_seconds(SpeedPercent(-20), SpeedPercent(-20), 1.0)
    
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
    movimento.on_for_seconds(SpeedPercent(-20), SpeedPercent(-20), 1.0) # Recuo de seguranca
    
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
                        print("Scan Necessário: Esq=" + str(fazer_esq) + " Dir=" + str(fazer_dir))
                        
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
    sortear_inimigos_com_dados()
    turnos_do_jogo()
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

