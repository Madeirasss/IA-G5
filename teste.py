import random
import time

# --- CONSTANTES ---
DEFENDER_VIDA_MAX = 750
DEFENDER_ENERGIA_MAX = 500

# Dados de ataque (índice: 0=grua, 1=toque, 2=som)
ATAQUES_DANO = [200, 100, 50]
ATAQUES_CUSTO = [300, 150, 50]

# Dados de cura (índice: 0=cura1, 1=cura2, 2=cura3)
CURAS_RECUPERA = [100, 200, 400]
CURAS_CUSTO = [200, 300, 400]

# Inimigos: índice 0=Tanque, 1=Artilharia, 2=Infantaria
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

def calcular_dano_potencial_proximo_turno(slots):
    """Calcula o dano exato que o robô pode receber no próximo turno"""
    dano_total = 0
    
    for i in range(NUM_SLOTS):
        slot = slots[i]
        
        # Inimigo pode atacar se: chegou, vivo, tem ataques, não destruído
        if (slot[6] == 1 and slot[2] > 0 and 
            slot[4] > 0 and slot[0] != -1 and slot[2] != -999):
            
            tipo = slot[0]
            
            # Dano reduzido se estiver ferido E detectado
            if slot[5] == 1:  # Detectado
                ratio = slot[2] / slot[1] if slot[1] > 0 else 1
                dano = int(INIMIGOS_FORCA[tipo] * ratio)
            else:
                # Não detectado = dano total (será detectado após ataque)
                dano = INIMIGOS_FORCA[tipo]
            
            dano_total += dano
    
    return dano_total

def decidir_acao_balanceada(vida_atual, energia_atual, slots, dano_potencial):
    """Estratégia balanceada com cálculo preciso de dano"""
    
    # 1. EMERGÊNCIA: Dano potencial > Vida atual
    if dano_potencial >= vida_atual:
        # Tentar eliminar a maior ameaça
        maior_ameaca = -1
        maior_dano_individual = 0
        
        for i in range(NUM_SLOTS):
            slot = slots[i]
            if (slot[6] == 1 and slot[2] > 0 and 
                slot[4] > 0 and slot[0] != -1):
                
                tipo = slot[0]
                if slot[5] == 1:
                    ratio = slot[2] / slot[1] if slot[1] > 0 else 1
                    dano = INIMIGOS_FORCA[tipo] * ratio
                else:
                    dano = INIMIGOS_FORCA[tipo]
                
                if dano > maior_dano_individual:
                    maior_dano_individual = dano
                    maior_ameaca = i
        
        if maior_ameaca != -1:
            vida_alvo = slots[maior_ameaca][2]
            if vida_alvo <= 50 and energia_atual >= 50:
                return (1, maior_ameaca, 2)
            elif vida_alvo <= 100 and energia_atual >= 150:
                return (1, maior_ameaca, 1)
            elif energia_atual >= 300:
                return (1, maior_ameaca, 0)
        
        # Se não pode eliminar, curar
        cura_necessaria = dano_potencial - vida_atual + 1
        if cura_necessaria > 0:
            if cura_necessaria <= 400 and energia_atual >= 400:
                return (2, 3)
            elif cura_necessaria <= 200 and energia_atual >= 300:
                return (2, 2)
            elif cura_necessaria <= 100 and energia_atual >= 200:
                return (2, 1)
    
    # 2. PERIGO ALTO: Dano potencial > 60% da vida
    if dano_potencial > vida_atual * 0.6:
        # Prioridade: eliminar ameaças ou curar
        for i in range(NUM_SLOTS):
            slot = slots[i]
            if slot[0] == 1 and slot[2] > 0:  # Artilharia
                vida_alvo = slot[2]
                if vida_alvo <= 50 and energia_atual >= 50:
                    return (1, i, 2)
                elif vida_alvo <= 100 and energia_atual >= 150:
                    return (1, i, 1)
                elif energia_atual >= 300:
                    return (1, i, 0)
        
        # Curar se não pode eliminar artilharia
        if energia_atual >= 300:
            return (2, 2)  # Cura2
    
    # 3. CURA PREVENTIVA
    if vida_atual < DEFENDER_VIDA_MAX * 0.4:
        if energia_atual >= 400:
            return (2, 3)
        elif energia_atual >= 300:
            return (2, 2)
        elif energia_atual >= 200:
            return (2, 1)
    
    # 4. SELEÇÃO DE ALVO INTELIGENTE
    melhor_alvo = -1
    melhor_valor = -1
    
    for i in range(NUM_SLOTS):
        slot = slots[i]
        if slot[5] == 1 and slot[2] > 0 and slot[0] != -1:
            tipo = slot[0]
            prioridade = INIMIGOS_PRIORIDADE[tipo]
            
            # Calcular "perigo" do inimigo
            if slot[4] > 0:  # Pode atacar
                if slot[5] == 1:
                    ratio = slot[2] / slot[1] if slot[1] > 0 else 1
                    dano_prox = INIMIGOS_FORCA[tipo] * ratio
                else:
                    dano_prox = INIMIGOS_FORCA[tipo]
            else:
                dano_prox = 0
            
            # Calcular "eficiencia" de matar
            eficiencia = (1.0 - (slot[2] / slot[1])) if slot[1] > 0 else 1.0
            
            # FÓRMULA BALANCEADA:
            valor = (dano_prox * 20) + (eficiencia * 80) + (prioridade * 10)
            
            if valor > melhor_valor:
                melhor_valor = valor
                melhor_alvo = i
    
    if melhor_alvo == -1:
        return (3, 0)
    
    # 5. ESCOLHA DA ARMA OTIMIZADA
    vida_alvo = slots[melhor_alvo][2]
    
    # SEMPRE usar a arma mais eficiente (menor custo que mate)
    if vida_alvo <= 50 and energia_atual >= 50:
        return (1, melhor_alvo, 2)
    elif vida_alvo <= 100 and energia_atual >= 150:
        return (1, melhor_alvo, 1)
    elif vida_alvo <= 200 and energia_atual >= 300:
        return (1, melhor_alvo, 0)
    
    return (3, 0)

def decidir_acao_agressiva(vida_atual, energia_atual, slots, dano_potencial):
    """Estratégia AGRESSIVA CORRIGIDA - FUNCIONA BEM"""
    
    # 1. EMERGÊNCIA COMUM (igual a todas)
    if dano_potencial >= vida_atual:
        maior_ameaca = -1
        maior_dano = 0
        
        for i in range(NUM_SLOTS):
            slot = slots[i]
            if (slot[6] == 1 and slot[2] > 0 and 
                slot[4] > 0 and slot[0] != -1):
                
                tipo = slot[0]
                if slot[5] == 1:
                    ratio = slot[2] / slot[1] if slot[1] > 0 else 1
                    dano = INIMIGOS_FORCA[tipo] * ratio
                else:
                    dano = INIMIGOS_FORCA[tipo]
                
                if dano > maior_dano:
                    maior_dano = dano
                    maior_ameaca = i
        
        if maior_ameaca != -1:
            vida_alvo = slots[maior_ameaca][2]
            if vida_alvo <= 50 and energia_atual >= 50:
                return (1, maior_ameaca, 2)
            elif vida_alvo <= 100 and energia_atual >= 150:
                return (1, maior_ameaca, 1)
            elif energia_atual >= 300:
                return (1, maior_ameaca, 0)
    
    # 2. CURA AGRESSIVA (apenas em 30%)
    if vida_atual < DEFENDER_VIDA_MAX * 0.3:
        if energia_atual >= CURAS_CUSTO[2]:
            return (2, 3)
        elif energia_atual >= CURAS_CUSTO[1]:
            return (2, 2)
        elif energia_atual >= CURAS_CUSTO[0]:
            return (2, 1)
    
    # 3. SELEÇÃO DE ALVO AGRESSIVA (ORIGINAL QUE FUNCIONA)
    melhor_alvo = -1
    melhor_valor = -1
    
    for i in range(NUM_SLOTS):
        slot = slots[i]
        if slot[5] == 1 and slot[2] > 0 and slot[0] != -1:
            tipo = slot[0]
            prioridade = INIMIGOS_PRIORIDADE[tipo]
            
            # FÓRMULA AGRESSIVA ORIGINAL (funciona bem!)
            valor = prioridade * 1000 - slot[2]
            
            if valor > melhor_valor:
                melhor_valor = valor
                melhor_alvo = i
    
    if melhor_alvo == -1:
        return (3, 0)
    
    # 4. ESCOLHA DE ARMA AGRESSIVA: SEMPRE A MAIS FORTE
    if energia_atual >= ATAQUES_CUSTO[0]:
        return (1, melhor_alvo, 0)  # Grua
    elif energia_atual >= ATAQUES_CUSTO[1]:
        return (1, melhor_alvo, 1)  # Toque
    elif energia_atual >= ATAQUES_CUSTO[2]:
        return (1, melhor_alvo, 2)  # Som
    
    return (3, 0)

def decidir_acao_defensiva(vida_atual, energia_atual, slots, dano_potencial):
    """Estratégia DEFENSIVA CORRIGIDA - FUNCIONA BEM"""
    
    # 1. EMERGÊNCIA COMUM
    if dano_potencial >= vida_atual:
        maior_ameaca = -1
        maior_dano = 0
        
        for i in range(NUM_SLOTS):
            slot = slots[i]
            if (slot[6] == 1 and slot[2] > 0 and 
                slot[4] > 0 and slot[0] != -1):
                
                tipo = slot[0]
                if slot[5] == 1:
                    ratio = slot[2] / slot[1] if slot[1] > 0 else 1
                    dano = INIMIGOS_FORCA[tipo] * ratio
                else:
                    dano = INIMIGOS_FORCA[tipo]
                
                if dano > maior_dano:
                    maior_dano = dano
                    maior_ameaca = i
        
        if maior_ameaca != -1:
            vida_alvo = slots[maior_ameaca][2]
            if vida_alvo <= 50 and energia_atual >= 50:
                return (1, maior_ameaca, 2)
            elif vida_alvo <= 100 and energia_atual >= 150:
                return (1, maior_ameaca, 1)
            elif energia_atual >= 300:
                return (1, maior_ameaca, 0)
    
    # 2. CURA DEFENSIVA (50% da vida)
    if vida_atual < DEFENDER_VIDA_MAX * 0.5 or dano_potencial > vida_atual * 0.7:
        if energia_atual >= CURAS_CUSTO[2]:
            return (2, 3)
        elif energia_atual >= CURAS_CUSTO[1]:
            return (2, 2)
        elif energia_atual >= CURAS_CUSTO[0]:
            return (2, 1)
    
    # 3. SELEÇÃO DE ALVO DEFENSIVA (ORIGINAL QUE FUNCIONA)
    melhor_alvo = -1
    melhor_valor = -1
    
    for i in range(NUM_SLOTS):
        slot = slots[i]
        if slot[5] == 1 and slot[2] > 0 and slot[0] != -1:
            tipo = slot[0]
            prioridade = INIMIGOS_PRIORIDADE[tipo]
            
            # FÓRMULA DEFENSIVA ORIGINAL (funciona bem!)
            valor = slot[4] * 100 + prioridade
            
            if valor > melhor_valor:
                melhor_valor = valor
                melhor_alvo = i
    
    if melhor_alvo == -1:
        return (3, 0)
    
    # 4. ESCOLHA DE ARMA DEFENSIVA: ECONÔMICA
    vida_alvo = slots[melhor_alvo][2]
    
    if vida_alvo <= 50 and energia_atual >= 50:
        return (1, melhor_alvo, 2)
    elif vida_alvo <= 100 and energia_atual >= 150:
        return (1, melhor_alvo, 1)
    elif vida_alvo <= 200 and energia_atual >= 300:
        return (1, melhor_alvo, 0)
    
    return (3, 0)

def decidir_acao_ia(vida_atual, energia_atual, slots, estrategia):
    """Função principal de decisão da IA"""
    
    # Calcular dano potencial do próximo turno
    dano_potencial = calcular_dano_potencial_proximo_turno(slots)
    
    # Chamar estratégia específica
    if estrategia == 0:  # Balanceada
        return decidir_acao_balanceada(vida_atual, energia_atual, slots, dano_potencial)
    elif estrategia == 1:  # Agressiva
        return decidir_acao_agressiva(vida_atual, energia_atual, slots, dano_potencial)
    elif estrategia == 2:  # Defensiva
        return decidir_acao_defensiva(vida_atual, energia_atual, slots, dano_potencial)
    
    return (3, 0)

# --- SIMULAÇÃO ÚNICA COM LOG DETALHADO ---
def executar_simulacao_unica_com_log(estrategia):
    vida = DEFENDER_VIDA_MAX
    energia = DEFENDER_ENERGIA_MAX
    slots = criar_slots_vazios()
    
    log_detalhado = []
    log_detalhado.append("=== INICIO DA SIMULACAO ===")
    
    turnos = 0
    inimigos_destruidos = 0
    dano_causado = 0
    dano_recebido = 0
    curas_usadas = 0
    
    sortear_inimigos(slots)
    
    for i in range(NUM_SLOTS):
        slot = slots[i]
        if slot[0] != -1:
            tipo_nome = ["Tanque", "Artilharia", "Infantaria"][slot[0]]
            log_detalhado.append("Slot " + str(i) + ": " + tipo_nome + 
                               " (vida " + str(slot[1]) + 
                               ", turno chegada " + str(slot[3]) + 
                               ", ataques " + str(slot[4]) + ")")
    
    for turno in range(1, MAX_TURNOS + 1):
        turnos = turno
        log_detalhado.append("\n=== TURNO " + str(turno) + " ===")
        
        if turno & 1:
            log_detalhado.append("[FASE INIMIGA]")
            dano_total = 0
            
            for i in range(NUM_SLOTS):
                slot = slots[i]
                
                if turno == slot[3] and slot[6] == 0:
                    if slot[0] != -1:
                        slot[2] = slot[1]
                    slot[6] = 1
                    tipo_nome = ["Tanque", "Artilharia", "Infantaria"][slot[0]]
                    log_detalhado.append("- " + tipo_nome + " chegou no slot " + str(i) + 
                                       " (vida: " + str(slot[2]) + ")")
                    continue
                
                if (slot[6] == 1 and slot[4] > 0 and 
                    slot[2] > 0 and slot[0] != -1):
                    
                    tipo = slot[0]
                    tipo_nome = ["Tanque", "Artilharia", "Infantaria"][tipo]
                    
                    if slot[5] == 1:
                        ratio = slot[2] / slot[1] if slot[1] > 0 else 1
                    else:
                        ratio = 1.0
                        slot[5] = 1
                        log_detalhado.append("- " + tipo_nome + " no slot " + str(i) + " foi detectado")
                    
                    dano = int(INIMIGOS_FORCA[tipo] * ratio)
                    slot[4] -= 1
                    dano_total += dano
                    
                    log_detalhado.append("- " + tipo_nome + " atacou (dano: " + str(dano) + 
                                       ", ataques restantes: " + str(slot[4]) + ")")
            
            if dano_total > 0:
                vida -= dano_total
                dano_recebido += dano_total
                log_detalhado.append("DANO TOTAL RECEBIDO: " + str(dano_total))
                log_detalhado.append("VIDA DO ROBO: " + str(vida))
        
        else:
            log_detalhado.append("[FASE ROBO]")
            log_detalhado.append("Vida atual: " + str(vida) + ", Energia: " + str(energia))
            
            # Calcular dano potencial para mostrar no log
            dano_potencial = calcular_dano_potencial_proximo_turno(slots)
            log_detalhado.append("Dano potencial proximo turno: " + str(dano_potencial))
            
            recup = energia >> 1
            energia_antes = energia
            energia += recup
            if energia > DEFENDER_ENERGIA_MAX:
                energia = DEFENDER_ENERGIA_MAX
            log_detalhado.append("Energia recuperada: " + str(recup) + " (de " + 
                               str(energia_antes) + " para " + str(energia) + ")")
            
            for i in range(NUM_SLOTS):
                slot = slots[i]
                if slot[6] == 1 and slot[5] == 0:
                    if slot[0] != -1 and slot[2] == 0:
                        slot[2] = slot[1]
                    slot[5] = 1
                    tipo_nome = ["Tanque", "Artilharia", "Infantaria"][slot[0]]
                    log_detalhado.append("- " + tipo_nome + " no slot " + str(i) + 
                                       " detectado automaticamente")
            
            acao = decidir_acao_ia(vida, energia, slots, estrategia)
            
            if acao[0] == 1:
                slot_idx = acao[1]
                arma_idx = acao[2]
                arma_nome = ["Grua", "Toque", "Som"][arma_idx]
                
                if energia >= ATAQUES_CUSTO[arma_idx]:
                    energia -= ATAQUES_CUSTO[arma_idx]
                    dano = ATAQUES_DANO[arma_idx]
                    vida_antes = slots[slot_idx][2]
                    slots[slot_idx][2] -= dano
                    if slots[slot_idx][2] < 0:
                        slots[slot_idx][2] = 0
                    dano_causado += dano
                    
                    tipo_nome = ["Tanque", "Artilharia", "Infantaria"][slots[slot_idx][0]]
                    log_detalhado.append("- ATAQUE: " + arma_nome + " no slot " + str(slot_idx) + 
                                       " (" + tipo_nome + ")")
                    log_detalhado.append("  Dano: " + str(dano) + ", Vida alvo: " + 
                                       str(vida_antes) + " -> " + str(slots[slot_idx][2]))
                    log_detalhado.append("  Custo energia: " + str(ATAQUES_CUSTO[arma_idx]) + 
                                       ", Energia restante: " + str(energia))
                    
            elif acao[0] == 2:
                cura_idx = acao[1] - 1
                cura_nome = ["Cura1", "Cura2", "Cura3"][cura_idx]
                
                if energia >= CURAS_CUSTO[cura_idx]:
                    energia -= CURAS_CUSTO[cura_idx]
                    vida_antes = vida
                    vida += CURAS_RECUPERA[cura_idx]
                    if vida > DEFENDER_VIDA_MAX:
                        vida = DEFENDER_VIDA_MAX
                    curas_usadas += 1
                    
                    log_detalhado.append("- CURA: " + cura_nome)
                    log_detalhado.append("  Vida recuperada: " + str(CURAS_RECUPERA[cura_idx]))
                    log_detalhado.append("  Vida: " + str(vida_antes) + " -> " + str(vida))
                    log_detalhado.append("  Custo energia: " + str(CURAS_CUSTO[cura_idx]) + 
                                       ", Energia restante: " + str(energia))
            
            elif acao[0] == 3:
                log_detalhado.append("- PASSOU o turno")
        
        for i in range(NUM_SLOTS):
            slot = slots[i]
            if (slot[2] <= 0 and slot[0] != -1 and 
                slot[6] == 1 and slot[2] != -999):
                inimigos_destruidos += 1
                tipo_nome = ["Tanque", "Artilharia", "Infantaria"][slot[0]]
                log_detalhado.append("- " + tipo_nome + " no slot " + str(i) + " DESTRUIDO")
                slot[2] = -999
        
        if vida <= 0:
            log_detalhado.append("\n!!! ROBO DESTRUIDO !!!")
            break
    
    vida_final = vida if vida > 0 else 0
    vitoria = 1 if vida > 0 else 0
    
    return (vitoria, vida_final, turnos, inimigos_destruidos, 
            dano_causado, dano_recebido, curas_usadas, log_detalhado)

# --- SIMULAÇÃO ÚNICA SEM LOG (PARA SIMULAÇÕES EM MASSA) ---
def executar_simulacao_unica_sem_log(estrategia):
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
        
        if turno & 1:
            dano_total = 0
            
            for i in range(NUM_SLOTS):
                slot = slots[i]
                
                if turno == slot[3] and slot[6] == 0:
                    if slot[0] != -1:
                        slot[2] = slot[1]
                    slot[6] = 1
                    continue
                
                if (slot[6] == 1 and slot[4] > 0 and 
                    slot[2] > 0 and slot[0] != -1):
                    
                    tipo = slot[0]
                    
                    if slot[5] == 1:
                        ratio = slot[2] / slot[1] if slot[1] > 0 else 1
                    else:
                        ratio = 1.0
                        slot[5] = 1
                    
                    dano = int(INIMIGOS_FORCA[tipo] * ratio)
                    slot[4] -= 1
                    dano_total += dano
            
            if dano_total > 0:
                vida -= dano_total
                dano_recebido += dano_total
        
        else:
            recup = energia >> 1
            energia += recup
            if energia > DEFENDER_ENERGIA_MAX:
                energia = DEFENDER_ENERGIA_MAX
            
            for i in range(NUM_SLOTS):
                slot = slots[i]
                if slot[6] == 1 and slot[5] == 0:
                    if slot[0] != -1 and slot[2] == 0:
                        slot[2] = slot[1]
                    slot[5] = 1
            
            acao = decidir_acao_ia(vida, energia, slots, estrategia)
            
            if acao[0] == 1:
                slot_idx = acao[1]
                arma_idx = acao[2]
                
                if energia >= ATAQUES_CUSTO[arma_idx]:
                    energia -= ATAQUES_CUSTO[arma_idx]
                    dano = ATAQUES_DANO[arma_idx]
                    slots[slot_idx][2] -= dano
                    if slots[slot_idx][2] < 0:
                        slots[slot_idx][2] = 0
                    dano_causado += dano
                    
            elif acao[0] == 2:
                cura_idx = acao[1] - 1
                
                if energia >= CURAS_CUSTO[cura_idx]:
                    energia -= CURAS_CUSTO[cura_idx]
                    vida += CURAS_RECUPERA[cura_idx]
                    if vida > DEFENDER_VIDA_MAX:
                        vida = DEFENDER_VIDA_MAX
                    curas_usadas += 1
        
        for i in range(NUM_SLOTS):
            slot = slots[i]
            if (slot[2] <= 0 and slot[0] != -1 and 
                slot[6] == 1 and slot[2] != -999):
                inimigos_destruidos += 1
                slot[2] = -999
        
        if vida <= 0:
            break
    
    vida_final = vida if vida > 0 else 0
    vitoria = 1 if vida > 0 else 0
    
    return (vitoria, vida_final, turnos, inimigos_destruidos, 
            dano_causado, dano_recebido, curas_usadas)

# --- SIMULAÇÃO EM MASSA ---
def executar_simulacoes_massa(num_simulacoes, estrategia):
    total_vitorias = 0
    total_vida = 0
    total_turnos = 0
    total_inimigos = 0
    total_dano_causado = 0
    total_dano_recebido = 0
    total_curas = 0
    total_vida_vitorias = 0
    total_turnos_vitorias = 0
    
    for i in range(num_simulacoes):
        resultado = executar_simulacao_unica_sem_log(estrategia)
        
        vitoria = resultado[0]
        vida_final = resultado[1]
        turnos = resultado[2]
        inimigos = resultado[3]
        dano_causado = resultado[4]
        dano_recebido = resultado[5]
        curas = resultado[6]
        
        total_vitorias += vitoria
        total_vida += vida_final
        total_turnos += turnos
        total_inimigos += inimigos
        total_dano_causado += dano_causado
        total_dano_recebido += dano_recebido
        total_curas += curas
        
        if vitoria:
            total_vida_vitorias += vida_final
            total_turnos_vitorias += turnos
    
    taxa_vitoria = (total_vitorias / num_simulacoes) * 100 if num_simulacoes > 0 else 0
    vida_media = total_vida / num_simulacoes if num_simulacoes > 0 else 0
    turnos_media = total_turnos / num_simulacoes if num_simulacoes > 0 else 0
    inimigos_media = total_inimigos / num_simulacoes if num_simulacoes > 0 else 0
    dano_causado_media = total_dano_causado / num_simulacoes if num_simulacoes > 0 else 0
    dano_recebido_media = total_dano_recebido / num_simulacoes if num_simulacoes > 0 else 0
    curas_media = total_curas / num_simulacoes if num_simulacoes > 0 else 0
    
    vida_media_vitorias = total_vida_vitorias / total_vitorias if total_vitorias > 0 else 0
    turnos_media_vitorias = total_turnos_vitorias / total_vitorias if total_vitorias > 0 else 0
    
    estatisticas = [
        num_simulacoes,
        total_vitorias,
        num_simulacoes - total_vitorias,
        taxa_vitoria,
        vida_media,
        turnos_media,
        inimigos_media,
        dano_causado_media,
        dano_recebido_media,
        curas_media,
        vida_media_vitorias,
        turnos_media_vitorias
    ]
    
    return estatisticas

# --- ENCONTRAR AS 10 MELHORES SIMULAÇÕES ---
def encontrar_melhores_simulacoes(num_simulacoes, estrategia, top_n=10):
    melhores = []
    
    for i in range(num_simulacoes):
        resultado = executar_simulacao_unica_com_log(estrategia)
        vida_final = resultado[1]
        
        if len(melhores) < top_n:
            melhores.append(resultado)
            melhores.sort(key=lambda x: x[1], reverse=True)
        else:
            if vida_final > melhores[-1][1]:
                melhores[-1] = resultado
                melhores.sort(key=lambda x: x[1], reverse=True)
    
    return melhores

# --- SALVAR ESTATÍSTICAS MÉDIAS ---
def salvar_estatisticas_medias(estatisticas, estrategia, tempo_total):
    try:
        timestamp = int(time.time())
        nome_arquivo = "estatisticas_" + str(estrategia) + "_" + str(timestamp) + ".txt"
        
        f = open(nome_arquivo, "w")
        
        nomes_estrategia = ["BALANCEADA", "AGRESSIVA", "DEFENSIVA"]
        nome_estrategia = nomes_estrategia[estrategia] if estrategia < 3 else "DESCONHECIDA"
        
        f.write("ESTATISTICAS MEDIAS DE SIMULACAO\n")
        f.write("=" * 60 + "\n")
        f.write("Estrategia: " + nome_estrategia + "\n")
        f.write("Tempo total: " + str(round(tempo_total, 2)) + " segundos\n")
        f.write("Numero de simulacoes: " + str(estatisticas[0]) + "\n")
        f.write("=" * 60 + "\n\n")
        
        f.write("RESULTADOS GERAIS:\n")
        f.write("-" * 40 + "\n")
        f.write("Vitorias: " + str(estatisticas[1]) + "\n")
        f.write("Derrotas: " + str(estatisticas[2]) + "\n")
        f.write("Taxa de vitoria: " + str(round(estatisticas[3], 2)) + "%\n")
        f.write("\n")
        
        f.write("ESTATISTICAS MEDIAS:\n")
        f.write("-" * 40 + "\n")
        f.write("Vida final media: " + str(round(estatisticas[4], 2)) + "\n")
        f.write("Turnos medios jogados: " + str(round(estatisticas[5], 2)) + "\n")
        f.write("Inimigos destruidos (media): " + str(round(estatisticas[6], 2)) + "\n")
        f.write("Dano causado (media): " + str(round(estatisticas[7], 2)) + "\n")
        f.write("Dano recebido (media): " + str(round(estatisticas[8], 2)) + "\n")
        f.write("Curas usadas (media): " + str(round(estatisticas[9], 2)) + "\n")
        f.write("\n")
        
        f.write("ESTATISTICAS APENAS NAS VITORIAS:\n")
        f.write("-" * 40 + "\n")
        f.write("Vida final media nas vitorias: " + str(round(estatisticas[10], 2)) + "\n")
        f.write("Turnos medios nas vitorias: " + str(round(estatisticas[11], 2)) + "\n")
        
        f.close()
        return nome_arquivo
    except Exception as e:
        print("Erro ao salvar estatisticas: " + str(e))
        return None

# --- SALVAR AS MELHORES SIMULAÇÕES ---
def salvar_melhores_simulacoes(melhores, estrategia, tempo_total):
    try:
        timestamp = int(time.time())
        nome_arquivo = "melhores_" + str(estrategia) + "_" + str(timestamp) + ".txt"
        
        f = open(nome_arquivo, "w")
        
        f.write("TOP 10 MELHORES SIMULACOES\n")
        f.write("=" * 60 + "\n")
        f.write("Estrategia: " + str(estrategia) + "\n")
        f.write("Tempo total de simulacao: " + str(round(tempo_total, 2)) + " segundos\n")
        f.write("Numero de simulacoes analisadas: " + str(len(melhores) * 100) + "\n")
        f.write("=" * 60 + "\n\n")
        
        for idx, resultado in enumerate(melhores, 1):
            vitoria, vida_final, turnos, inimigos, dano_c, dano_r, curas, log = resultado
            
            f.write("SIMULACAO " + str(idx) + "\n")
            f.write("-" * 40 + "\n")
            f.write("Resultado: " + ("VITORIA" if vitoria else "DERROTA") + "\n")
            f.write("Vida final: " + str(vida_final) + "\n")
            f.write("Turnos jogados: " + str(turnos) + "\n")
            f.write("Inimigos destruidos: " + str(inimigos) + "\n")
            f.write("Dano causado: " + str(dano_c) + "\n")
            f.write("Dano recebido: " + str(dano_r) + "\n")
            f.write("Curas usadas: " + str(curas) + "\n")
            f.write("\nDETALHES DA SIMULACAO:\n")
            
            for linha in log:
                f.write(linha + "\n")
            
            f.write("\n" + "=" * 60 + "\n\n")
        
        f.close()
        return nome_arquivo
    except Exception as e:
        print("Erro ao salvar arquivo: " + str(e))
        return None

# --- FUNÇÃO PRINCIPAL ---
def main():
    print("=== SIMULADOR DE BATALHA COM IA AVANCADA ===")
    print("Analisando as 3 estrategias melhoradas...")
    print()
    
    num_simulacoes_massa = 1000000
    num_simulacoes_melhores = 100
    
    for estrategia in range(3):
        nomes_estrategia = ["BALANCEADA", "AGRESSIVA", "DEFENSIVA"]
        print("=== ESTRATEGIA: " + nomes_estrategia[estrategia] + " ===")
        
        # 1. Simulações em massa (para estatísticas)
        print("1. Executando simulacoes em massa (" + str(num_simulacoes_massa) + ")...")
        inicio_massa = time.time()
        estatisticas = executar_simulacoes_massa(num_simulacoes_massa, estrategia)
        fim_massa = time.time()
        tempo_massa = fim_massa - inicio_massa
        
        # 2. Encontrar melhores simulações
        print("2. Encontrando as 10 melhores simulacoes...")
        inicio_melhores = time.time()
        melhores = encontrar_melhores_simulacoes(num_simulacoes_melhores, estrategia)
        fim_melhores = time.time()
        tempo_melhores = fim_melhores - inicio_melhores
        
        # 3. Salvar resultados
        print("3. Salvando resultados...")
        nome_estatisticas = salvar_estatisticas_medias(estatisticas, estrategia, tempo_massa)
        nome_melhores = salvar_melhores_simulacoes(melhores, estrategia, tempo_melhores)
        
        # 4. Mostrar resumo
        print("RESUMO:")
        print("  - Tempo simulacoes em massa: " + str(round(tempo_massa, 2)) + "s")
        print("  - Tempo encontrar melhores: " + str(round(tempo_melhores, 2)) + "s")
        print("  - Taxa de vitoria: " + str(round(estatisticas[3], 2)) + "%")
        print("  - Vida final media: " + str(round(estatisticas[4], 2)))
        print("  - Inimigos destruidos (media): " + str(round(estatisticas[6], 2)))
        if nome_estatisticas:
            print("  - Estatisticas salvas em: " + nome_estatisticas)
        if nome_melhores:
            print("  - Melhores simulacoes salvas em: " + nome_melhores)
        print()
    
    print("=== FIM DA SIMULACAO ===")

# --- TESTE RÁPIDO DAS ESTRATÉGIAS CORRIGIDAS ---
if __name__ == "__main__":
    # Teste rápido com 100 simulações de cada estratégia
    print("TESTE RÁPIDO DAS ESTRATÉGIAS CORRIGIDAS")
    print("100 simulações por estratégia")
    print("-" * 50)
    
    resultados_estrategias = []
    
    for estrategia in range(3):
        nomes = ["BALANCEADA", "AGRESSIVA", "DEFENSIVA"]
        print("\n",{nomes[estrategia]},":") 
            
        inicio = time.time()
        estatisticas = executar_simulacoes_massa(100, estrategia)
        fim = time.time()
        
        resultados_estrategias.append(estatisticas)
        
        print("  Vitorias: ",estatisticas[1]/estatisticas[0], estatisticas[3],"%)")
        print("  Vida media: ",estatisticas[4])
        print("  Dano C/R: ",estatisticas[7]/estatisticas[8])
        print("  Curas: ",estatisticas[9])
        print("  Tempo: ",fim-inicio,"s")
    
    # Comparação final
    print("\n" + "=" * 50)
    print("COMPARAÇÃO FINAL:")
    print("Estratégia        Vitórias  Vida Média  Inimigos  Dano C/R    Curas")
    print("-" * 65)
    
    for i in range(3):
        nomes = ["BALANCEADA", "AGRESSIVA", "DEFENSIVA"]
        print(nomes[i], resultados_estrategias[i][3],"% ",resultados_estrategias[i][4]
              ,resultados_estrategias[i][6],resultados_estrategias[i][7]/resultados_estrategias[i][8]
              ,resultados_estrategias[i][9])
    
    # Perguntar se quer executar a simulação completa
    print("\n" + "=" * 50)
    resposta = input("Executar simulacao completa (1000 simulações por estrategia)? (s/n): ")
    
    if resposta.lower() == 's':
        main()
    else:
        print("Programa terminado.")