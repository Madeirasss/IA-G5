import random
import time

# --- CONSTANTES IGUAIS AO MAIN.PY ---
DEFENDER_VIDA_MAX = 750     # Ajustado para 550 conforme recomendado
DEFENDER_ENERGIA_MAX = 500

# Dados dos Ataques (Indices: 0=Grua, 1=Toque, 2=Som)
# Nota: No main.py Grua é 1, Toque 2, Som 3. Aqui ajustamos para indices de lista 0,1,2.
ATAQUES_DANO = [200, 100, 50]
ATAQUES_CUSTO = [300, 150, 50]

# Dados das Curas (Indices: 0=Cura1, 1=Cura2, 2=Cura3)
CURAS_RECUPERA = [100, 200, 400]
CURAS_CUSTO = [200, 300, 400]

# Dados dos Inimigos (Indices: 0=Tanque, 1=Artilharia, 2=Infantaria)
INIMIGOS_FORCA = [200, 500, 100]
INIMIGOS_VIDA = [200, 50, 100]
INIMIGOS_ATAQUES = [2, 1, 3] # Municao
INIMIGOS_PRIORIDADE = [1, 3, 2] # Tanque=1, Artilharia=3, Infantaria=2

NUM_SLOTS = 6
MAX_TURNOS = 13

# --- GESTÃO DE SLOTS ---
def criar_slots_vazios():
    # Estrutura do Slot na Simulação:
    # [0:Tipo, 1:VidaMax, 2:VidaAtual, 3:TurnoEntrada, 4:Municao, 5:JaEntrou?, 6:NaoUsado]
    slots = []
    for i in range(NUM_SLOTS):
        slots.append([-1, 0, 0, 0, 0, 0, 0])
    return slots

def sortear_inimigos(slots):
    for i in range(NUM_SLOTS):
        dado_tipo = random.randint(1, 6)
        # Mapeamento do main.py: 1-2 Tanque, 3-4 Artilharia, 5-6 Infantaria
        if dado_tipo <= 2:
            tipo = 0 # Tanque
        elif dado_tipo <= 4:
            tipo = 1 # Artilharia
        else:
            tipo = 2 # Infantaria
            
        dado_bruto = random.randint(1, 6)
        turno_entrada = (dado_bruto * 2) - 1
        
        slots[i][0] = tipo
        slots[i][1] = INIMIGOS_VIDA[tipo]
        slots[i][2] = 0 # Vida começa a 0 (so aparece quando entra)
        slots[i][3] = turno_entrada
        slots[i][4] = INIMIGOS_ATAQUES[tipo] # Carrega Municao
        slots[i][5] = 0 # Flag 'JaEntrou' falsa
        slots[i][6] = 0

# --- LÓGICA DE DANO DO MAIN.PY ---
def calcular_ameaca_total(slots, turno_atual):
    total = 0
    for i in range(NUM_SLOTS):
        slot = slots[i]
        # Regra Main.py: Vivo E Turno de entrada < Atual E Municao > 0
        if slot[5] == 1 and slot[2] > 0 and slot[3] < turno_atual and slot[4] > 0:
            tipo = slot[0]
            ratio = slot[2] / slot[1]
            dano = int(INIMIGOS_FORCA[tipo] * ratio)
            total += dano
    return total

def prever_dano_inimigo_especifico(slot, dano_recebido):
    # Simula quanto dano o inimigo faria se levasse 'dano_recebido'
    vida_futura = slot[2] - dano_recebido
    if vida_futura <= 0:
        return 0
    
    tipo = slot[0]
    ratio = vida_futura / slot[1]
    return int(INIMIGOS_FORCA[tipo] * ratio)

# --- HEURÍSTICAS DO MAIN.PY ---

def selecionar_melhor_alvo(slots):
    melhor_alvo = -1
    melhor_valor = -1
    
    for i in range(NUM_SLOTS):
        slot = slots[i]
        
        # Ignorar se nao esta presente, morto ou SEM MUNICAO
        if slot[5] == 0 or slot[2] <= 0 or slot[4] <= 0:
            continue
            
        tipo = slot[0]
        stats_vida = slot[1]
        stats_forca = INIMIGOS_FORCA[tipo]
        prioridade = INIMIGOS_PRIORIDADE[tipo]
        
        ratio = slot[2] / stats_vida
        dano_potencial = stats_forca * ratio
        
        # Fórmula exata do main.py
        valor = (dano_potencial * 20) + (prioridade * 15)
        valor *= 1.5 # Multiplicador urgencia
        
        if valor > melhor_valor:
            melhor_valor = valor
            melhor_alvo = i
            
    return melhor_alvo

def escolher_arma_ideal(energia_atual, vida_alvo):
    # Logica Finisher do main.py
    if vida_alvo <= 50 and energia_atual >= 50:
        return 2 # Som
    if vida_alvo <= 100 and energia_atual >= 150:
        return 1 # Toque
        
    # Logica Disponibilidade
    if energia_atual >= 300: return 0 # Grua
    if energia_atual >= 150: return 1 # Toque
    if energia_atual >= 50: return 2 # Som
    
    return -1 # Sem energia

def verificar_seguranca_ataque(slots, alvo_idx, arma_idx, vida_atual, turno_atual):
    dano_arma = ATAQUES_DANO[arma_idx]
    
    dano_total_agora = calcular_ameaca_total(slots, turno_atual)
    
    # Dano que este inimigo especifico causa AGORA
    slot = slots[alvo_idx]
    ratio_atual = slot[2] / slot[1]
    dano_inimigo_antes = int(INIMIGOS_FORCA[slot[0]] * ratio_atual)
    
    # Dano que causaria DEPOIS do ataque
    dano_inimigo_depois = prever_dano_inimigo_especifico(slot, dano_arma)
    
    # Simula o turno
    dano_final_previsto = dano_total_agora - (dano_inimigo_antes - dano_inimigo_depois)
    
    return vida_atual > dano_final_previsto

def avaliar_necessidade_cura(vida_atual, energia_atual, ameaca_total):
    # Regra main.py: Ameaca >= Vida OU Vida < 15%
    if ameaca_total >= vida_atual or vida_atual < (DEFENDER_VIDA_MAX * 0.15):
        if energia_atual >= 400: return 2 # Grande
        if energia_atual >= 300: return 1 # Media
        if energia_atual >= 200: return 0 # Pequena
    return -1

# --- CÉREBRO DA IA (REPLICA decidir_jogada_IA) ---
def decidir_jogada_ia_main(vida, energia, slots, turno):
    
    # 1. Encontrar melhor alvo
    alvo = selecionar_melhor_alvo(slots)
    
    if alvo != -1:
        # 2. Escolher arma
        arma = escolher_arma_ideal(energia, slots[alvo][2])
        
        if arma != -1:
            # 3. Validar Seguranca
            if verificar_seguranca_ataque(slots, alvo, arma, vida, turno):
                return (1, alvo, arma) # Acao 1: Atacar
    
    # 4. Tentar Curar
    ameaca = calcular_ameaca_total(slots, turno)
    cura = avaliar_necessidade_cura(vida, energia, ameaca)
    if cura != -1:
        return (2, cura) # Acao 2: Curar
        
    # 5. Kamikaze
    if alvo != -1 and energia >= 50:
        return (1, alvo, 2) # Ataque Som (Kamikaze)
        
    return (3, 0) # Acao 3: Passar

# --- SIMULAÇÃO ÚNICA ---
def executar_simulacao():
    vida = DEFENDER_VIDA_MAX
    energia = DEFENDER_ENERGIA_MAX
    slots = criar_slots_vazios()
    sortear_inimigos(slots)
    
    for turno in range(1, MAX_TURNOS + 1):
        
        # FASE INIMIGA (Turnos Impares)
        if turno % 2 != 0:
            # 1. Verificar quem entra
            for s in slots:
                if s[3] == turno:
                    s[5] = 1 # Entrou
                    s[2] = s[1] # Define vida inicial
            
            # 2. Calcular Dano e Gastar Municao
            dano_turno = 0
            for s in slots:
                # Se esta no campo, vivo e tem municao (e nao acabou de entrar neste turno)
                if s[5] == 1 and s[2] > 0 and s[4] > 0 and s[3] < turno:
                    ratio = s[2] / s[1]
                    dano = int(INIMIGOS_FORCA[s[0]] * ratio)
                    dano_turno += dano
                    s[4] -= 1 # GASTA MUNICAO
            
            vida -= dano_turno
            if vida <= 0: return 0 # Derrota
            
        # FASE ROBO (Turnos Pares)
        else:
            # 1. Regenerar Energia
            recup = int(energia * 0.5)
            energia += recup
            if energia > DEFENDER_ENERGIA_MAX: energia = DEFENDER_ENERGIA_MAX
            
            # 2. Decidir Jogada
            acao = decidir_jogada_ia_main(vida, energia, slots, turno)
            
            if acao[0] == 1: # Atacar
                idx_alvo, idx_arma = acao[1], acao[2]
                custo = ATAQUES_CUSTO[idx_arma]
                dano = ATAQUES_DANO[idx_arma]
                
                energia -= custo
                slots[idx_alvo][2] -= dano # Aplica dano
                if slots[idx_alvo][2] < 0: slots[idx_alvo][2] = 0
                
            elif acao[0] == 2: # Curar
                idx_cura = acao[1]
                custo = CURAS_CUSTO[idx_cura]
                recupera = CURAS_RECUPERA[idx_cura]
                
                energia -= custo
                vida += recupera
                if vida > DEFENDER_VIDA_MAX: vida = DEFENDER_VIDA_MAX
                
    return 1 if vida > 0 else 0 # Vitoria se sobreviveu

# --- SIMULAÇÃO EM MASSA ---
def executar_teste_massa(n=10000):
    vitorias = 0
    inicio = time.time()
    
    for _ in range(n):
        vitorias += executar_simulacao()
        
    fim = time.time()
    print("--- RESULTADO (" + str(n) + " Jogos) ---")
    print("Taxa de Vitoria: " + str((vitorias/n)*100) + "%")
    print("Tempo: " + str(round(fim-inicio, 2)) + "s")

if __name__ == "__main__":
    print("A simular com regras do MAIN.PY (750HP + Municao Limitada)...")
    executar_teste_massa(100000)