import random
import time

# --- CONSTANTES ---
DEFENDER_VIDA_MAX = 750
DEFENDER_ENERGIA_MAX = 500

ATAQUES_DANO = [200, 100, 50]
ATAQUES_CUSTO = [300, 150, 50]

CURAS_RECUPERA = [100, 200, 400]
CURAS_CUSTO = [200, 300, 400]

INIMIGOS_FORCA = [200, 500, 100]
INIMIGOS_ATAQUES = [2, 1, 3]
INIMIGOS_VIDA = [200, 50, 100]
INIMIGOS_PRIORIDADE = [1, 3, 2]

NUM_SLOTS = 6
MAX_TURNOS = 13

# --- FUNÇÕES AUXILIARES ---
def criar_slots_vazios():
    slots = []
    for i in range(NUM_SLOTS):
        slots.append([-1, 0, 0, 0, 0, 0, 0])
    return slots

def sortear_inimigos(slots):
    for i in range(NUM_SLOTS):
        dado_tipo = random.randint(1, 6)
        if dado_tipo <= 2:
            tipo = 0
        elif dado_tipo <= 4:
            tipo = 1
        else:
            tipo = 2
            
        dado_bruto = random.randint(1, 6)
        turno_entrada = (dado_bruto * 2) - 1
        
        slots[i][0] = tipo
        slots[i][1] = INIMIGOS_VIDA[tipo]
        slots[i][3] = turno_entrada
        slots[i][4] = INIMIGOS_ATAQUES[tipo]
        slots[i][2] = 0
        slots[i][5] = 0
        slots[i][6] = 0

def calcular_dano_potencial(slots):
    """Calcula o dano TOTAL que o robô vai levar neste turno"""
    dano_total = 0
    for i in range(NUM_SLOTS):
        slot = slots[i]
        if (slot[6] == 1 and slot[2] > 0 and 
            slot[4] > 0 and slot[0] != -1 and 
            slot[2] != -999 and slot[5] == 1):
            
            tipo = slot[0]
            ratio = slot[2] / slot[1] if slot[1] > 0 else 1
            dano = int(INIMIGOS_FORCA[tipo] * ratio)
            dano_total += dano
    return dano_total

def calcular_dano_inimigo_especifico(slot):
    """Calcula quanto dano UM inimigo específico vai dar agora"""
    if (slot[6] == 1 and slot[2] > 0 and 
        slot[4] > 0 and slot[0] != -1 and 
        slot[2] != -999 and slot[5] == 1):
        
        tipo = slot[0]
        ratio = slot[2] / slot[1] if slot[1] > 0 else 1
        return int(INIMIGOS_FORCA[tipo] * ratio)
    return 0

def prever_dano_apos_ataque(slot, dano_do_meu_ataque):
    """
    Simula o futuro: Quanto dano esse inimigo vai dar DEPOIS de levar meu tiro?
    """
    if slot[4] <= 0: return 0 # Sem munição não dá dano
    
    vida_atual = slot[2]
    vida_futura = vida_atual - dano_do_meu_ataque
    
    if vida_futura <= 0:
        return 0 # Inimigo morto não dá dano
        
    tipo = slot[0]
    vida_max = slot[1]
    
    ratio_futuro = vida_futura / vida_max
    dano_futuro = int(INIMIGOS_FORCA[tipo] * ratio_futuro)
    
    return dano_futuro

def contar_inimigos_perigosos(slots):
    contador = 0
    for i in range(NUM_SLOTS):
        slot = slots[i]
        if (slot[6] == 1 and slot[2] > 0 and 
            slot[4] > 0 and slot[0] != -1 and 
            slot[2] != -999 and slot[5] == 1):
            contador += 1
    return contador

# --- ESTRATÉGIA INTELIGENTE ---
def decidir_acao_inteligente(vida_atual, energia_atual, slots):
    """
    Lógica: Tenta atacar primeiro. MAS, calcula se o ataque garante a sobrevivência.
    Se atacar resultar em morte, cancela o ataque e troca para cura.
    """
    
    # 1. ESCOLHER O MELHOR ALVO (Lógica de Pontuação)
    melhor_alvo = -1
    melhor_valor = -1
    
    # Primeiro checa Artilharia (Prioridade Absoluta)
    for i in range(NUM_SLOTS):
        slot = slots[i]
        if slot[0] == 1 and slot[2] > 0 and slot[5] == 1 and slot[4] > 0:
            melhor_alvo = i
            melhor_valor = 9999 # Valor altíssimo para garantir
            break
            
    # Se não achou Artilharia, usa a fórmula padrão
    if melhor_alvo == -1:
        for i in range(NUM_SLOTS):
            slot = slots[i]
            if (slot[5] == 1 and slot[2] > 0 and slot[0] != -1 and slot[4] > 0):
                tipo = slot[0]
                ratio = slot[2] / slot[1] if slot[1] > 0 else 1
                dano_prox = INIMIGOS_FORCA[tipo] * ratio
                eficiencia = (1.0 - ratio)
                prioridade = INIMIGOS_PRIORIDADE[tipo]
                
                valor = (dano_prox * 20) + (eficiencia * 70) + (prioridade * 15) + (slot[4] * 5)
                
                if valor > melhor_valor:
                    melhor_valor = valor
                    melhor_alvo = i

    # --- SIMULAÇÃO DE SOBREVIVÊNCIA ---
    acao_ataque = None
    pode_atacar_com_seguranca = False
    
    if melhor_alvo != -1:
        # Escolher arma
        vida_alvo = slots[melhor_alvo][2]
        arma_idx = 0
        
        if vida_alvo <= 50 and energia_atual >= 50:
            arma_idx = 2
        elif vida_alvo <= 100 and energia_atual >= 150:
            arma_idx = 1
        elif energia_atual >= 300:
            arma_idx = 0
        else:
             # Sem energia para a arma ideal, tenta a mais fraca disponível
            if energia_atual >= 150: arma_idx = 1
            elif energia_atual >= 50: arma_idx = 2
            else: arma_idx = -1 # Sem energia nenhuma
            
        if arma_idx != -1:
            dano_arma = ATAQUES_DANO[arma_idx]
            
            # --- O PULO DO GATO: PREVISÃO DE FUTURO ---
            dano_total_atual = calcular_dano_potencial(slots)
            
            # Quanto esse inimigo ia me bater?
            dano_inimigo_antes = calcular_dano_inimigo_especifico(slots[melhor_alvo])
            
            # Quanto ele vai me bater DEPOIS do meu tiro?
            dano_inimigo_depois = prever_dano_apos_ataque(slots[melhor_alvo], dano_arma)
            
            # Novo dano total que vou receber
            dano_reduzido = dano_inimigo_antes - dano_inimigo_depois
            dano_final_recebido = dano_total_atual - dano_reduzido
            
            # VEREDITO: Eu sobrevivo se atacar?
            if vida_atual > dano_final_recebido:
                # Sim, sobrevivo! O ataque é seguro.
                return (1, melhor_alvo, arma_idx)
            else:
                # Não, eu morro mesmo atacando.
                # O ataque não reduz o dano o suficiente.
                # ABORTAR ATAQUE -> TENTAR CURAR
                pode_atacar_com_seguranca = False
        else:
             # Sem energia para atacar
             pass

    # --- BLOCO DE CURA (Plano B) ---
    # Só chega aqui se não atacou (ou porque não tinha alvo, ou sem energia, ou porque IA morrer)
    
    dano_potencial = calcular_dano_potencial(slots)
    
    # Cura de Emergência (Prioridade máxima aqui)
    if dano_potencial >= vida_atual:
         # Tenta a cura mais forte possível
        if energia_atual >= 400: return (2, 3)
        elif energia_atual >= 300: return (2, 2)
        elif energia_atual >= 200: return (2, 1)
        
    # Cura Preventiva (se sobrou energia e não atacou)
    if dano_potencial >= vida_atual:
        if energia_atual >= 400: return (2, 3)
        elif energia_atual >= 300: return (2, 2)
        elif energia_atual >= 200: return (2, 1)

    # 2. MANUTENÇÃO: Se não vou morrer, curo-me se a vida estiver muito baixa
    # Usei elif para ligar ao bloco anterior
    elif vida_atual < DEFENDER_VIDA_MAX * 0.15:  # Subi de 0.15 para 0.3 para ser mais seguro
        if energia_atual >= 400: return (2, 3)
        elif energia_atual >= 300: return (2, 2)
        elif energia_atual >= 200: return (2, 1)

    # Se a cura não salvou (sem energia) ou não precisava, e o ataque era suicida...
    # Tenta atacar de qualquer jeito (Kamikaze final) se tiver energia, melhor morrer lutando
    if melhor_alvo != -1 and energia_atual >= 50:
         # Recalcula arma simples
         return (1, melhor_alvo, 2) 

    return (3, 0)

# --- SIMULAÇÃO ---
def executar_simulacao_unica_sem_log():
    vida = DEFENDER_VIDA_MAX
    energia = DEFENDER_ENERGIA_MAX
    slots = criar_slots_vazios()
    
    turnos = 0
    inimigos_destruidos = 0
    dano_causado = 0
    dano_recebido = 0
    curas_usadas = 0
    
    sortear_inimigos(slots)
    
    for turno in range(1, MAX_TURNOS + 1):
        turnos = turno
        
        # FASE INIMIGA (turnos ímpares)
        if turno & 1:
            dano_total = 0
            for i in range(NUM_SLOTS):
                slot = slots[i]
                if turno == slot[3] and slot[6] == 0:
                    if slot[0] != -1: slot[2] = slot[1]
                    slot[6] = 1
                    continue
                if (slot[6] == 1 and slot[4] > 0 and slot[2] > 0 and slot[0] != -1 and slot[5] == 1):
                    tipo = slot[0]
                    ratio = slot[2] / slot[1] if slot[1] > 0 else 1
                    dano = int(INIMIGOS_FORCA[tipo] * ratio)
                    slot[4] -= 1
                    dano_total += dano
            
            if dano_total > 0:
                vida -= dano_total
                dano_recebido += dano_total
        
        # FASE ROBÔ (turnos pares)
        else:
            recup = energia >> 1
            energia += recup
            if energia > DEFENDER_ENERGIA_MAX: energia = DEFENDER_ENERGIA_MAX
            
            for i in range(NUM_SLOTS):
                slot = slots[i]
                if slot[6] == 1 and slot[5] == 0:
                    if slot[0] != -1 and slot[2] == 0: slot[2] = slot[1]
                    slot[5] = 1
            
            acao = decidir_acao_inteligente(vida, energia, slots)
            
            if acao[0] == 1:
                slot_idx = acao[1]
                arma_idx = acao[2]
                if energia >= ATAQUES_CUSTO[arma_idx]:
                    energia -= ATAQUES_CUSTO[arma_idx]
                    dano = ATAQUES_DANO[arma_idx]
                    slots[slot_idx][2] -= dano
                    if slots[slot_idx][2] < 0: slots[slot_idx][2] = 0
                    dano_causado += dano
            elif acao[0] == 2:
                cura_idx = acao[1] - 1
                if energia >= CURAS_CUSTO[cura_idx]:
                    energia -= CURAS_CUSTO[cura_idx]
                    vida += CURAS_RECUPERA[cura_idx]
                    if vida > DEFENDER_VIDA_MAX: vida = DEFENDER_VIDA_MAX
                    curas_usadas += 1
        
        for i in range(NUM_SLOTS):
            slot = slots[i]
            if (slot[2] <= 0 and slot[0] != -1 and slot[6] == 1 and slot[2] != -999):
                inimigos_destruidos += 1
                slot[2] = -999
        
        if vida <= 0: break
    
    return (1 if vida > 0 else 0, vida if vida > 0 else 0)

# --- SIMULAÇÃO EM MASSA ---
def executar_simulacoes_massa(num_simulacoes):
    total_vitorias = 0
    total_vida = 0
    for i in range(num_simulacoes):
        res = executar_simulacao_unica_sem_log()
        total_vitorias += res[0]
        total_vida += res[1]
    
    return [num_simulacoes, total_vitorias, 0, (total_vitorias/num_simulacoes)*100, total_vida/num_simulacoes]

# --- EXECUÇÃO ---
if __name__ == "__main__":
    print("=== TESTE: ESTRATÉGIA PREDITIVA (SIMULAÇÃO DE DANO) ===")
    print("O robô calcula: 'Se eu atacar, o dano dele diminui. Sobrevivo?'")
    print("Sim -> Ataca. Não -> Cura.")
    print()
    
    num_testes = 100000
    inicio = time.time()
    estatisticas = executar_simulacoes_massa(num_testes)
    fim = time.time()
    
    print("RESULTADOS:")
    print("  Vitórias: ",estatisticas[1],"/",num_testes,"(",estatisticas[3],"%")
    print("  Vida média final: ", estatisticas[4])
    print("  Tempo: ",fim-inicio,"s")