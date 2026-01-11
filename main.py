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
som.volume = 100

#Definir variaveis do jogo
defender_vida_max = 750
defender_vida_atual = 750
defender_energia_max = 500
defender_energia_atual = 500


#Slots dos inimigos no tabuleiro
NUMERO_DE_SLOTS = 6 
slots_inimigos = {
    i: {'tipo': None, 'vida_inicial': 0, 'vida_atual': 0, 'turno_ataque': 0, 'munição': 0} 
    for i in range(1, NUMERO_DE_SLOTS + 1)
}

#Tabuleiro real com dados verdadeiros dos inimigos
tabuleiro_real = {
    i: {'tipo': "Vazio", 'vida_atual': 0, 'turno_ataque': 0, 'munição': 0} 
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
    print("Vida atual: ", defender_vida_atual, "Vida Maxima", defender_vida_max, "Energia atual: ", defender_energia_atual, "Energia Maxima", defender_energia_max)


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


# Função para virar o robô com precisão usando o Giroscópio
# Lógica: Reinicia o ângulo (0), define a direção das rodas e espera até o sensor ler o valor desejado.
def virar_com_gyro(graus):
    sensor_giro.reset() # Zera o ângulo atual
    sleep(0.1) # Pequena pausa para o sensor estabilizar
    
    # Define velocidade e direção baseada no sinal (+ ou -)
    if graus > 0: # Valores positivos = Virar à Direita
        movimento.on(SpeedPercent(15), SpeedPercent(-15))
        # Loop de espera ativa: continua a girar até chegar ao ângulo
        # A margem de erro (-2) serve para compensar a inércia do motor ao travar
        while sensor_giro.angle < (graus - 2): 
            pass
    else: # Valores negativos = Virar à Esquerda
        movimento.on(SpeedPercent(-15), SpeedPercent(15))
        while sensor_giro.angle > (graus + 2): 
            pass
            
    movimento.stop() # Trava os motores
    sleep(0.5) # Tempo para o robô parar de abanar antes da próxima leitura


#Função para atacar com a grua
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
    
    # 2. Decidir lado e Virar 90º (Ficar de frente para o inimigo)
    print("A virar para o alvo...")
    if slot_alvo % 2 != 0:
        # Impar = Esquerda (-90)
        virar_com_gyro(-90)
        direcao_inicial = -1
    else:
        # Par = Direita (90)
        virar_com_gyro(90)
        direcao_inicial = 1

    # 3. Aproximar do Inimigo (Até Ultrassónico ver < 10cm)
    print("A aproximar do inimigo...")
    movimento.on(SpeedPercent(20), SpeedPercent(20))
    
    while sensor_ultrassonico.distance_centimeters > 20:
        # Segurança: Se não encontrar nada e andar demasiado, para.
        pass
    movimento.stop()
    print("Alvo encontrado.")
    sleep(0.5)

    # 4. Ficar de costas para o inimigo
    print("A rodar 180 para posicao de Grua...")
    virar_com_gyro(180)

    # 5. EXECUÇÃO DO ATAQUE
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

    # 6. Virar para a Base
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

        sleep(0.5)
        som.play_file('ataque de som.wav')
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
        som.play_file('cura.wav')
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


# Função para navegar no corredor central contando linhas pretas
# O robô avança até contar o número de linhas pedido (1, 3 ou 5).
def ir_ate_linha(numero_linha_desejada):
    print(">> A viajar para a Linha " + str(numero_linha_desejada) + "...")
    movimento.on(SpeedPercent(30), SpeedPercent(30))
    
    linhas_contadas = 0
    estou_na_linha = False # Flag para evitar contar a mesma linha várias vezes enquanto passa por cima dela
    
    while True:
        cor = sensor_cor.color_name
        
        # Detetou linha preta
        if cor == "Black":
            if not estou_na_linha: # É uma nova linha?
                estou_na_linha = True
                linhas_contadas += 1
                print("Passou linha: " + str(linhas_contadas))
                som.beep()
                
                # Se chegámos ao destino, para imediatamente
                if linhas_contadas == numero_linha_desejada:
                    movimento.stop()
                    print("Chegamos ao destino.")
                    break
                    
        elif cor != "Black":
            estou_na_linha = False # Saiu de cima da linha, pronto para contar a próxima
            
        # Segurança: Se vir Vermelho (Parede) ou bater (Toque), para tudo.
        if cor == "Red" or sensor_toque.is_pressed:
            movimento.stop()
            print("Erro: Fim da pista encontrado antes do destino.")
            break
            
        sleep(0.01) # Poupa processador


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


# Função de Reconhecimento de Inimigo
# Entra no slot, lê a cor, consulta a base de dados (Dicionário INIMIGOS) e guarda na memória.
def ler_cor_e_guardar(slot_id):
    print("A aproximar para identificar...")
    sleep(1)
    
    cor_lida = sensor_cor.color_name
    print("Cor detetada: " + cor_lida)
    
    # Valores padrão (caso não encontre nada ou cor desconhecida)
    nome_inimigo = "Vazio"
    vida_inimigo = 0
    municao_inicial = 0
    found = False
    
    # Procura a cor lida no dicionário de configurações
    for nome, dados in INIMIGOS.items():
        if dados['cor'] == cor_lida:
            nome_inimigo = nome
            vida_inimigo = dados['vida']
            municao_inicial = dados['ataques']
            found = True
            break
    
    # Atualiza a "Memória da IA" (O que o robô sabe)
    slots_inimigos[slot_id]['tipo'] = nome_inimigo
    slots_inimigos[slot_id]['vida_atual'] = vida_inimigo
    slots_inimigos[slot_id]['municao'] = municao_inicial
    
    # Atualiza o "Tabuleiro Real" (A verdade absoluta do jogo)
    # Nota: Em um cenário real 100% autónomo, não terias acesso a esta variável 'tabuleiro_real'
    tabuleiro_real[slot_id]['tipo'] = nome_inimigo
    tabuleiro_real[slot_id]['vida_atual'] = vida_inimigo
    tabuleiro_real[slot_id]['municao'] = municao_inicial
    tabuleiro_real[slot_id]['turno_ataque'] = 0 
    
    if found:
        print("Inimigo registado: " + nome_inimigo)
    else:
        print("Espaco vazio.")


# Função complexa de Scan Lateral
# O robô para numa interseção e decide se olha para a esquerda, direita ou ambos.
# Usa o sensor Ultrassónico para ver se vale a pena entrar no slot.
def scan_lateral(numero_da_paragem, fazer_esq, fazer_dir):
    print("\n--- SCAN SELETIVO PARAGEM " + str(numero_da_paragem) + " ---")
    movimento.stop()
    sleep(0.5)
    
    # Matemática para converter o número da paragem (1, 2, 3) em IDs de Slots (1 a 6)
    slot_esq = (numero_da_paragem * 2) - 1
    slot_dir = (numero_da_paragem * 2)
    
    # --- VERIFICAR ESQUERDA ---
    if fazer_esq:
        print(">> A apontar para ESQUERDA (Slot " + str(slot_esq) + ")...")
        virar_com_gyro(-90) # Vira 90 à esquerda
        sleep(0.3) 

        # Otimização: Só entra se o ultrassónico vir algo perto (< 40cm)
        dist = sensor_ultrassonico.distance_centimeters
        print("Distancia lida: " + str(dist) + " cm")

        if dist < 40: 
            print("Inimigo detetado! A entrar no quadrado...")
            movimento.on_for_seconds(SpeedPercent(20), SpeedPercent(20), 1.3) # Entra
            ler_cor_e_guardar(slot_esq) # Identifica
            movimento.on_for_seconds(SpeedPercent(-20), SpeedPercent(-20), 1.3) # Sai
        else:
            print("Slot vazio. A ignorar entrada.") # Poupa tempo e bateria
            slots_inimigos[slot_esq]['tipo'] = "Vazio"
            slots_inimigos[slot_esq]['vida_atual'] = 0
            
        # Volta a alinhar com o corredor principal
        print(">> A voltar ao eixo do corredor...")
        virar_com_gyro(90)
        sleep(0.2)

    # --- VERIFICAR DIREITA ---
    # (Mesma lógica da esquerda, mas com giros invertidos)
    if fazer_dir:
        print(">> A apontar para DIREITA (Slot " + str(slot_dir) + ")...")
        virar_com_gyro(90)
        sleep(0.3)

        dist = sensor_ultrassonico.distance_centimeters
        print("Distancia lida: " + str(dist) + " cm")

        if dist < 40:
            print("Inimigo detetado! A entrar...")
            movimento.on_for_seconds(SpeedPercent(20), SpeedPercent(20), 1.3)
            ler_cor_e_guardar(slot_dir)
            movimento.on_for_seconds(SpeedPercent(-20), SpeedPercent(-20), 1.3)
        else:
            print("Slot vazio. A ignorar entrada.")
            slots_inimigos[slot_dir]['tipo'] = "Vazio"
            slots_inimigos[slot_dir]['vida_atual'] = 0
            
        print(">> A voltar ao eixo do corredor...")
        virar_com_gyro(-90)
        sleep(0.2)

    print("Scan da paragem concluido.")

# Função de retorno à segurança (Home)
# Usada após ataques ou no fim do jogo.
def voltar_a_base():
    print("\n--- A REGRESSAR A BASE ---")
    
    # 1. Virar 180 graus para ficar de costas para o fundo do corredor
    print("Topo: A dar meia volta (180)...")
    sensor_giro.reset()
    sleep(0.1)
    movimento.on(SpeedPercent(15), SpeedPercent(-15))
    while sensor_giro.angle < 178: pass
    movimento.stop()
    sleep(0.5)
    
    # 2. Recuar até à base
    print("A navegar para a base...")
    movimento.on(SpeedPercent(30), SpeedPercent(30))
    
    while True:
        cor = sensor_cor.color_name
        # Condição de paragem: Ver cor Vermelha (Chão da base) ou Sensor de Toque (Parede)
        if cor == "Red" or sensor_toque.is_pressed:
            movimento.stop()
            print("Base encontrada!")
            som.beep()
            break
        sleep(0.01)
            
    # 3. Virar 180 graus novamente para ficar pronto para a próxima saída
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


# Loop Principal do Jogo (Turnos 1 a 13)
# Gere a alternância entre Inimigos (Ímpares) e Robô (Pares).
def turnos_do_jogo():
    global defender_vida_atual
    global defender_energia_atual
    
    print("SISTEMA AUTOMATIZADO COM IA")

    for turno in range(1, 14):
        # Relatório Inicial do Turno
        print("\n" + "-"*30)
        print(" STATUS DO CAMPO (Turno {})".format(turno))
        imprimir_relatorio_final()
        print(" Vida: {} | Energia: {}".format(defender_vida_atual, defender_energia_atual))
        print("-"*30)

        # --- FASE INIMIGA (TURNOS ÍMPARES) ---
        if turno % 2 != 0:
            print("\n!!! [FASE INIMIGA] !!!")
            input(">>> Pressiona ENTER para processar dano dos inimigos...")
            
            dano_total_turno = 0
            
            # Percorre todos os slots para ver quem ataca
            for i in range(1, NUMERO_DE_SLOTS + 1):
                dano_deste_inimigo = calcular_dano_real_inimigos(turno, i)
                
                if dano_deste_inimigo > 0:
                    print("Slot", i, "atacou! Dano: {}".format(dano_deste_inimigo))
                    dano_total_turno += dano_deste_inimigo
                    
                    # Consumo de munição do inimigo
                    tabuleiro_real[i]['municao'] -= 1
                    # Atualiza também a memória do robô
                    if slots_inimigos[i]['tipo'] is not None:
                        slots_inimigos[i]['municao'] = tabuleiro_real[i]['municao']
            
            # Aplica o dano total à vida do Defender
            if dano_total_turno > 0:
                defender_vida_atual -= dano_total_turno
                som.play_file('som de dano.wav')

        # --- FASE ROBO (TURNOS PARES) ---
        else:
            print("\n>>> [FASE ROBO - IA EM EXECUCAO] <<<")
            
            # 1. Regeneração de Energia (Regra do jogo: +50% da atual)
            recup = int(defender_energia_atual * 0.5)
            defender_energia_atual += recup
            if defender_energia_atual > defender_energia_max:
                defender_energia_atual = defender_energia_max
            
            # 2. Scout/Patrulha (Apenas se houver slots desconhecidos)
            if turno in [2, 4, 6, 8, 10, 12]:
                if not todos_os_inimigos_identificados():
                    print(">> Ainda ha slots desconhecidos. A iniciar scout...")
                    percorrer_e_mapear(turno)
                else:
                    print(">> Scout desnecessario (Tudo identificado).")
            
            # 3. Decisão da IA (Chama o "Cérebro" comentado anteriormente)
            decisao, alvo, detalhe = decidir_jogada_IA(turno)
            
            # Executa a decisão da IA
            if decisao == "ATACAR":
                print(">> IA DECIDIU: Atacar Slot {} com arma {}".format(alvo, detalhe))
                executar_ataque_manual_fisico(alvo, detalhe)
            
            elif decisao == "CURAR":
                print(">> IA DECIDIU: Curar-se (Nivel {})".format(alvo))
                usar_cura(alvo)
            
            else:
                print(">> IA DECIDIU: Passar turno.")

        # --- GAME OVER CHECK ---
        if defender_vida_atual <= 0:
            print("GAME OVER")
            som.play_file('robo morte.wav')
            break
            
        print("\n--- Turno {} concluido. ---".format(turno))

    # Vitória (Se sobreviveu aos 13 turnos com vida > 0)
    if defender_vida_atual > 0:
        print("VITORIA - MISSAO CUMPRIDA!")
        som.play_file('Vitoria.wav')


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
    
    # Ataca se estiver vivo, identificado e com munição
    if inimigo['vida_atual'] > 0 and inimigo['tipo'] != "Vazio" and inimigo['municao'] > 0:
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
# Lógica: Prioriza eliminar ameaças letais. Se não for possível, tenta curar.
# Se a morte for certa, ataca para causar o máximo de dano antes de morrer.
def decidir_jogada_IA(turno_atual):
    alvo = selecionar_melhor_alvo()
    ameaca_total = calcular_ameaca_total_no_tabuleiro(turno_atual)
    
    # 1. TÁTICA OFENSIVA DE SOBREVIVÊNCIA
    # Verifica se atacar um inimigo específico reduz o dano recebido o suficiente para sobreviver ao turno.
    if alvo != -1:
        arma = escolher_arma_ideal(alvo)
        if arma != -1:
            # Simula o turno: "Se eu matar este inimigo, eu sobrevivo?"
            if verificar_seguranca_ataque(alvo, arma, turno_atual):
                print(">> IA: Ataque Tatico detetado. Destruir alvo garante sobrevivencia!")
                return ("ATACAR", alvo, arma)

    # 2. TÁTICA DEFENSIVA (CURA)
    # Se o ataque não garante a sobrevivência, verifica se a cura consegue com que o robo sobreviva ao dano.
    nivel_cura = avaliar_necessidade_cura(turno_atual)
    if nivel_cura != -1:
        # Verifica se a cura selecionada cobre a ameaça total dos inimigos
        recuperacao = 400 if nivel_cura == 3 else 200 if nivel_cura == 2 else 100
        if (defender_vida_atual + recuperacao) >= ameaca_total:
            print(">> IA: Cura necessaria e suficiente para sobreviver ao turno.")
            return ("CURAR", nivel_cura, None)

    # 3. MODO KAMIKAZE (Último Recurso)
    # Se nem atacar nem curar salvam o robô, ataca o melhor alvo para levar alguém com ele.
    if alvo != -1:
        arma = escolher_arma_ideal(alvo)
        if arma != -1:
            print(">> IA: MORTE INEVITAVEL detetada. Iniciando modo KAMIKAZE!")
            return ("ATACAR", alvo, arma)
            
    # 4. POUPANÇA DE ENERGIA
    # Se não há ameaças imediatas ou recursos para agir, passa o turno.
    return ("PASSAR", None, None)


# Heurística para selecionar o melhor alvo
# Calcula um 'Score' para cada inimigo baseada no Dano Potencial e na Prioridade do tipo.
# Retorna o ID do slot do inimigo mais perigoso.
def selecionar_melhor_alvo():
    melhor_alvo = -1
    melhor_valor = -1
    
    for i in range(1, NUMERO_DE_SLOTS + 1):
        info = slots_inimigos[i]
        
        # Ignora slots vazios, desconhecidos ou inimigos já mortos
        if info['tipo'] is None or info['tipo'] == "Vazio" or info['vida_atual'] <= 0:
            continue
            
        # Ignora inimigos que já não têm munição (não representam ameaça)
        if info['municao'] <= 0:
            continue
            
        tipo = info['tipo']
        stats = INIMIGOS[tipo]
        
        multiplicador_urgencia = 1.5 
        
        # Cálculo do Perigo:
        # 1. Quanto dano ele causa agora? (Força * % de Vida)
        ratio = info['vida_atual'] / stats['vida']
        dano_potencial = stats['forca'] * ratio
        # 2. Qual a prioridade fixa deste tipo de inimigo? (Artilharia > Infantaria > Tanque)
        prioridade = PRIORIDADES[tipo]
        # Fórmula de Pontuação (Dano pesa mais que a prioridade fixa)
        valor = (dano_potencial * 20) + (prioridade * 15)
        valor *= multiplicador_urgencia 
        
        if valor > melhor_valor:
            melhor_valor = valor
            melhor_alvo = i
            print("IA: Selecionado Slot {} como melhor alvo".format(melhor_alvo))
            
    return melhor_alvo



# Heurística para escolher a arma ideal (Eficiência Energética)
# Objetivo: Matar o inimigo gastando o minimo de energia possível.
# Evita usar arma forte em inimigo fraco.
def escolher_arma_ideal(slot_id):
    vida_alvo = slots_inimigos[slot_id]['vida_atual']
    
    # 1. Tenta matar com SOM (Custo 50) se o inimigo tiver pouca vida
    if vida_alvo <= 50 and defender_energia_atual >= 50: 
        return 3 # Som
        
    # 2. Tenta matar com TOQUE (Custo 150) se vida média
    if vida_alvo <= 100 and defender_energia_atual >= 150: 
        return 2 # Toque
        
    # 3. Se tem muita vida, usa GRUA (Custo 300) se houver energia
    if defender_energia_atual >= 300: 
        return 1 # Grua
        
    # 4. Se não tem energia para a arma ideal, usa a mais forte disponível
    if defender_energia_atual >= 150: 
        return 2 # Toque 
    if defender_energia_atual >= 50: 
        return 3 # Som 
    
    return -1 # Sem energia para qualquer ataque


# Heurística de Simulação de Risco
# Verifica se vale a pena atacar:
# 1. Calcula quanto dano vou receber se não fizer nada.
# 2. Calcula quanto dano vou receber se atacar este inimigo (ele fica mais fraco ou morre).
# 3. Retorna True apenas se o robô sobreviver após realizar este ataque.
def verificar_seguranca_ataque(slot_id, arma_id, turno_atual):
    # Identifica o dano base da arma escolhida
    key_arma = 'grua' if arma_id == 1 else 'toque' if arma_id == 2 else 'som'
    dano_previsto = ATAQUES[key_arma]['dano']
    
    # Cenário A: Não faço nada (Ameaça total atual)
    dano_total_agora = calcular_ameaca_total_no_tabuleiro(turno_atual)
    
    # Cenário B: Eu ataco
    dano_inimigo_antes = calcular_dano_real_inimigos(turno_atual, slot_id)
    dano_inimigo_depois = prever_dano_apos_ataque(slot_id, dano_previsto)
    
    # O dano final será a ameaça total MENOS a diferença que o meu ataque causou
    # Ex: Se o inimigo ia dar 500 dano e agora dá 0 (morreu), poupei 500 de vida.
    dano_final_previsto = dano_total_agora - (dano_inimigo_antes - dano_inimigo_depois)
    
    # Retorna Verdadeiro se a vida restante for maior que o dano previsto
    return defender_vida_atual > dano_final_previsto


# Heurística para avaliar necessidade de cura
# Decide curar se:
# a) A ameaça dos inimigos for maior que a minha vida atual (Risco de Morte).
# b) A vida atual for muito baixa (< 15%), independentemente dos inimigos (Precaução).
def avaliar_necessidade_cura(turno_atual):
    ameaca_total = calcular_ameaca_total_no_tabuleiro(turno_atual)
    
    # Verifica condição de perigo ou vida crítica
    if ameaca_total >= defender_vida_atual or defender_vida_atual < (defender_vida_max * 0.15):
        # Seleciona a cura mais potente que a energia atual permite
        if defender_energia_atual >= 400: 
            return 3 # Grande (400 HP)
        if defender_energia_atual >= 300: 
            return 2 # Média (200 HP)
        if defender_energia_atual >= 200: 
            return 1 # Pequena (100 HP)
        
    return -1 # Não precisa de cura ou não tem energia suficiente


# MAIN
def main():
    confirmar_inicialização()
    turnos_do_jogo()

    #Funções para debugs
    #usar_som()
    
    #verificar_flancos_com_gyro()

    
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

