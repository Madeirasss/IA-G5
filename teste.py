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

def calcular_dano_potencial_proximo_turno(slots):
    """Versão CORRETA: só inimigos DETECTADOS atacam"""
    dano_total = 0
    
    for i in range(NUM_SLOTS):
        slot = slots[i]
        
        # Só pode atacar se: chegou, vivo, tem ataques, DETECTADO, não destruído
        if (slot[6] == 1 and slot[2] > 0 and 
            slot[4] > 0 and slot[0] != -1 and 
            slot[2] != -999 and slot[5] == 1):  # slot[5] == 1 = DETECTADO
            
            tipo = slot[0]
            
            # Inimigo detectado: dano proporcional à vida
            ratio = slot[2] / slot[1] if slot[1] > 0 else 1
            dano = int(INIMIGOS_FORCA[tipo] * ratio)
            
            dano_total += dano
    
    return dano_total

def decidir_acao_balanceada_melhorada(vida_atual, energia_atual, slots):
    """Balanceada OTIMIZADA baseada nos dados reais"""
    
    # 1. DETECTAR ARTILHARIA (PRIORIDADE MÁXIMA)
    tem_artilharia = False
    artilharia_slots = []
    
    for i in range(NUM_SLOTS):
        slot = slots[i]
        if slot[0] == 1 and slot[2] > 0:  # Artilharia viva
            tem_artilharia = True
            artilharia_slots.append(i)
    
    # 2. SE HÁ ARTILHARIA, ELIMINAR PRIMEIRO
    if tem_artilharia:
        # Encontrar artilharia com menos vida
        melhor_alvo = -1
        menor_vida = 1000
        
        for slot_idx in artilharia_slots:
            vida_alvo = slots[slot_idx][2]
            if vida_alvo < menor_vida:
                menor_vida = vida_alvo
                melhor_alvo = slot_idx
        
        if melhor_alvo != -1:
            vida_alvo = slots[melhor_alvo][2]
            
            # Arma mais barata que mate a artilharia
            if vida_alvo <= 50 and energia_atual >= 50:
                return (1, melhor_alvo, 2)  # Som
            elif vida_alvo <= 100 and energia_atual >= 150:
                return (1, melhor_alvo, 1)  # Toque
            elif energia_atual >= 300:
                return (1, melhor_alvo, 0)  # Grua
    
    # 3. CURA INTELIGENTE (APRENDIZADO DOS DADOS)
    # Se tem artilharia e vida < 500, CURA EMERGÊNCIA
    if tem_artilharia and vida_atual < 500:
        if vida_atual + 400 > 500 and energia_atual >= 400:
            return (2, 3)  # Cura3
        elif vida_atual + 200 > 500 and energia_atual >= 300:
            return (2, 2)  # Cura2
        elif vida_atual + 100 > 500 and energia_atual >= 200:
            return (2, 1)  # Cura1
    
    # Cura padrão (40% da vida)
    if vida_atual < DEFENDER_VIDA_MAX * 0.4:
        if energia_atual >= 400:
            return (2, 3)
        elif energia_atual >= 300:
            return (2, 2)
        elif energia_atual >= 200:
            return (2, 1)
    
    # 4. SELEÇÃO DE ALVO GERAL
    melhor_alvo = -1
    melhor_valor = -1
    
    for i in range(NUM_SLOTS):
        slot = slots[i]
        if slot[5] == 1 and slot[2] > 0 and slot[0] != -1:
            tipo = slot[0]
            prioridade = INIMIGOS_PRIORIDADE[tipo]
            
            # Valor baseado em prioridade e eficiência
            eficiencia = (1.0 - (slot[2] / slot[1])) if slot[1] > 0 else 1.0
            valor = prioridade * 100 + eficiencia * 50
            
            if valor > melhor_valor:
                melhor_valor = valor
                melhor_alvo = i
    
    if melhor_alvo == -1:
        return (3, 0)
    
    # 5. ESCOLHA DE ARMA EFICIENTE
    vida_alvo = slots[melhor_alvo][2]
    
    # Arma mais barata que mate
    if vida_alvo <= 50 and energia_atual >= 50:
        return (1, melhor_alvo, 2)
    elif vida_alvo <= 100 and energia_atual >= 150:
        return (1, melhor_alvo, 1)
    elif vida_alvo <= 200 and energia_atual >= 300:
        return (1, melhor_alvo, 0)
    
    return (3, 0)

def decidir_acao_agressiva_melhorada(vida_atual, energia_atual, slots):
    """Agressiva OTIMIZADA - foco absoluto em artilharia"""
    
    # 1. BUSCAR ARTILHARIA PRIMEIRO (SEMPRE)
    for i in range(NUM_SLOTS):
        slot = slots[i]
        if slot[0] == 1 and slot[2] > 0:  # Artilharia viva
            # ELIMINAR IMEDIATAMENTE
            if energia_atual >= 300:
                return (1, i, 0)  # Grua
            elif energia_atual >= 150:
                return (1, i, 1)  # Toque
            elif energia_atual >= 50:
                return (1, i, 2)  # Som
    
    # 2. CURA APENAS SE VIDA BAIXA E SEM ARTILHARIA
    if vida_atual < DEFENDER_VIDA_MAX * 0.3:
        if energia_atual >= 400:
            return (2, 3)
        elif energia_atual >= 300:
            return (2, 2)
        elif energia_atual >= 200:
            return (2, 1)
    
    # 3. ATACAR OUTROS INIMIGOS
    melhor_alvo = -1
    maior_prioridade = -1
    
    for i in range(NUM_SLOTS):
        slot = slots[i]
        if slot[5] == 1 and slot[2] > 0 and slot[0] != -1:
            tipo = slot[0]
            prioridade = INIMIGOS_PRIORIDADE[tipo]
            
            if prioridade > maior_prioridade:
                maior_prioridade = prioridade
                melhor_alvo = i
    
    if melhor_alvo == -1:
        return (3, 0)
    
    # 4. ARMA MAIS FORTE DISPONÍVEL
    if energia_atual >= 300:
        return (1, melhor_alvo, 0)
    elif energia_atual >= 150:
        return (1, melhor_alvo, 1)
    elif energia_atual >= 50:
        return (1, melhor_alvo, 2)
    
    return (3, 0)

def decidir_acao_defensiva_melhorada(vida_atual, energia_atual, slots):
    """Defensiva OTIMIZADA - cura mais inteligente"""
    
    # 1. CURA EMERGÊNCIA CONTRA ARTILHARIA
    tem_artilharia = False
    for i in range(NUM_SLOTS):
        slot = slots[i]
        if slot[0] == 1 and slot[2] > 0:
            tem_artilharia = True
            break
    
    if tem_artilharia and vida_atual < 550:  # Cura mais cedo com artilharia
        if energia_atual >= 400:
            return (2, 3)
        elif energia_atual >= 300:
            return (2, 2)
        elif energia_atual >= 200:
            return (2, 1)
    
    # 2. CURA PADRÃO (50% da vida)
    if vida_atual < DEFENDER_VIDA_MAX * 0.5:
        if energia_atual >= 400:
            return (2, 3)
        elif energia_atual >= 300:
            return (2, 2)
        elif energia_atual >= 200:
            return (2, 1)
    
    # 3. ELIMINAR ARTILHARIA PRIMEIRO (MESMO DEFENSIVA)
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
    
    # 4. SELEÇÃO DE ALVO DEFENSIVA
    melhor_alvo = -1
    melhor_valor = -1
    
    for i in range(NUM_SLOTS):
        slot = slots[i]
        if slot[5] == 1 and slot[2] > 0 and slot[0] != -1:
            tipo = slot[0]
            
            # Foco em inimigos que ainda podem atacar muito
            valor = slot[4] * 50 + INIMIGOS_PRIORIDADE[tipo] * 10
            
            if valor > melhor_valor:
                melhor_valor = valor
                melhor_alvo = i
    
    if melhor_alvo == -1:
        return (3, 0)
    
    # 5. ARMA MAIS BARATA
    vida_alvo = slots[melhor_alvo][2]
    
    if vida_alvo <= 50 and energia_atual >= 50:
        return (1, melhor_alvo, 2)
    elif vida_alvo <= 100 and energia_atual >= 150:
        return (1, melhor_alvo, 1)
    elif vida_alvo <= 200 and energia_atual >= 300:
        return (1, melhor_alvo, 0)
    
    return (3, 0)

def decidir_acao_ia(vida_atual, energia_atual, slots, estrategia):
    """Função principal OTIMIZADA"""
    
    if estrategia == 0:  # Balanceada melhorada
        return decidir_acao_balanceada_melhorada(vida_atual, energia_atual, slots)
    elif estrategia == 1:  # Agressiva melhorada
        return decidir_acao_agressiva_melhorada(vida_atual, energia_atual, slots)
    elif estrategia == 2:  # Defensiva melhorada
        return decidir_acao_defensiva_melhorada(vida_atual, energia_atual, slots)
    
    return (3, 0)

# Resto do código permanece similar (funções de simulação)...

# --- TESTE DAS ESTRATÉGIAS OTIMIZADAS ---
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
        
        if turno & 1:  # Turno ímpar: inimigos
            dano_total = 0
            
            for i in range(NUM_SLOTS):
                slot = slots[i]
                
                if turno == slot[3] and slot[6] == 0:
                    if slot[0] != -1:
                        slot[2] = slot[1]
                    slot[6] = 1
                    continue
                
                if (slot[6] == 1 and slot[4] > 0 and 
                    slot[2] > 0 and slot[0] != -1 and slot[5] == 1):  # Só ataca se detectado!
                    
                    tipo = slot[0]
                    
                    # Dano proporcional à vida
                    ratio = slot[2] / slot[1] if slot[1] > 0 else 1
                    dano = int(INIMIGOS_FORCA[tipo] * ratio)
                    slot[4] -= 1
                    dano_total += dano
            
            if dano_total > 0:
                vida -= dano_total
                dano_recebido += dano_total
        
        else:  # Turno par: robô
            recup = energia >> 1
            energia += recup
            if energia > DEFENDER_ENERGIA_MAX:
                energia = DEFENDER_ENERGIA_MAX
            
            # Detecção automática
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
        
        # Contar inimigos destruídos
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

def executar_simulacoes_massa(num_simulacoes, estrategia):
    total_vitorias = 0
    total_vida = 0
    total_turnos = 0
    total_inimigos = 0
    total_dano_causado = 0
    total_dano_recebido = 0
    total_curas = 0
    
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
    
    taxa_vitoria = (total_vitorias / num_simulacoes) * 100 if num_simulacoes > 0 else 0
    vida_media = total_vida / num_simulacoes if num_simulacoes > 0 else 0
    
    estatisticas = [
        num_simulacoes,
        total_vitorias,
        num_simulacoes - total_vitorias,
        taxa_vitoria,
        vida_media
    ]
    
    return estatisticas

# --- TESTE DAS ESTRATÉGIAS OTIMIZADAS ---
if __name__ == "__main__":
    print("=== TESTE DAS ESTRATEGIAS OTIMIZADAS ===")
    print("Baseado na analise de 1M simulacoes anteriores")
    print("Balanceada: 51%, Defensiva: 31%, Agressiva: 12%")
    print()
    
    num_testes = 100000  # 10K simulações por estratégia
    
    resultados = []
    
    for estrategia in range(3):
        nomes = ["BALANCEADA OTIMIZADA", "AGRESSIVA OTIMIZADA", "DEFENSIVA OTIMIZADA"]
        print("Testando: " + nomes[estrategia] + "...")
        
        inicio = time.time()
        estatisticas = executar_simulacoes_massa(num_testes, estrategia)
        fim = time.time()
        
        resultados.append(estatisticas)
        
        print("  Vitorias: " + str(estatisticas[1]) + ", " + str(num_testes) + " (" + str(estatisticas[3]) + "%)")
        print("  Vida media final: " + str(estatisticas[4]))
        print("  Tempo: " + str(fim-inicio) + "s")
        print()
    
    print("=== RESULTADOS OTIMIZADOS ===")
    print("Estrategia, Vitorias, Vida Media")
    print("-" * 40)
    
    nomes = ["Balanceada", "Agressiva", "Defensiva"]
    for i in range(3):
        print(nomes[i] + "  " + str(resultados[i][3]) + "%  " + str(resultados[i][4]))
    
    # Identificar a melhor
    melhor_idx = 0
    melhor_taxa = resultados[0][3]
    for i in range(1, 3):
        if resultados[i][3] > melhor_taxa:
            melhor_taxa = resultados[i][3]
            melhor_idx = i
    
    print()
    print("MELHOR ESTRATEGIA: " + nomes[melhor_idx] + " (" + str(melhor_taxa) + "%)")