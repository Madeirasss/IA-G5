import sys
import random
import time

# --- CONSTANTES GLOBAIS ---
defender_vida_max = 750
defender_vida_atual = 750
defender_energia_max = 500
defender_energia_atual = 500

# Dados de Jogo
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
    'Tanque':     {'cor':"Blue", 'forca': 200, 'ataques': 2, 'vida': 200},
    'Artilharia': {'cor':"Green", 'forca': 500, 'ataques': 1, 'vida': 50},
    'Infantaria': {'cor':"Brown", 'forca': 100, 'ataques': 3, 'vida': 100}
}

NUMERO_DE_SLOTS = 6

# Estrutura do Slot
slots_inimigos = {
    i: {
        'tipo': "Vazio", 
        'vida_inicial': 0, 
        'vida_atual': 0, 
        'turno_entrada': 0,     # 1, 3, 5, 7, 9 ou 11
        'ataques_restantes': 0, 
        'detetado': False,      
        'chegou': False         
    } 
    for i in range(1, NUMERO_DE_SLOTS + 1)
}

# --- FUNCOES DE ACAO ---

def simular_movimento_e_ataque(slot_alvo, tipo_arma):
    global defender_energia_atual
    
    if tipo_arma == 1: nome_arma = 'Grua'
    elif tipo_arma == 2: nome_arma = 'Toque'
    else: nome_arma = 'Som'
        
    arma_dados = ATAQUES[nome_arma.lower()]
    custo = arma_dados['custo_en']
    dano = arma_dados['dano']
    
    print("\n[SIMULACAO] A navegar para Slot", slot_alvo, "...")
    time.sleep(0.1)

    if defender_energia_atual < custo:
        print("[FALHA] Energia insuficiente (", custo, "EN necessario).")
        return 0
    
    defender_energia_atual -= custo
    print("[SUCESSO] Ataque", nome_arma, "realizado!")
    
    return dano

def usar_cura(numero_da_cura):
    global defender_energia_atual
    global defender_vida_atual
    
    key = 'cura' + str(numero_da_cura)
    custo = CURAS[key]['custo_en']
    recupera = CURAS[key]['recupera']
    
    if defender_energia_atual >= custo:
        defender_energia_atual -= custo
        defender_vida_atual += recupera
        if defender_vida_atual > defender_vida_max:
            defender_vida_atual = defender_vida_max
        
        print("[SUCESSO] Cura realizada. Vida:", defender_vida_atual, "| Energia:", defender_energia_atual)
        return True
    else:
        print("[FALHA] Energia insuficiente para curar.")
        return False

# --- FUNCOES DE PATRULHA ---

def ler_cor_e_guardar(slot_id):
    global slots_inimigos
    
    tipo_real = slots_inimigos[slot_id]['tipo']
    
    if tipo_real != "Vazio":
        if not slots_inimigos[slot_id]['detetado']:
            if slots_inimigos[slot_id]['vida_atual'] == 0:
                slots_inimigos[slot_id]['vida_atual'] = slots_inimigos[slot_id]['vida_inicial']
            
            slots_inimigos[slot_id]['detetado'] = True
            
        hp = slots_inimigos[slot_id]['vida_atual']
        mun = slots_inimigos[slot_id]['ataques_restantes']
        print("  > Slot", slot_id, ": DETETADO", tipo_real, "(HP:", hp, "| Balas:", mun, ")")
    else:
        slots_inimigos[slot_id]['detetado'] = True
        print("  > Slot", slot_id, ": Vazio.")


def patrulha_simulada(turno_atual):
    print("\n[FASE DE PATRULHA] A verificar novos inimigos (Turno", turno_atual, ")...")
    
    slots_por_verificar = []
    
    for i in range(1, NUMERO_DE_SLOTS + 1):
        info = slots_inimigos[i]
        
        # Deteta se ja chegou (chegou=True) e ainda nao sabemos o que e
        if info['chegou'] and not info['detetado']:
            slots_por_verificar.append(i)
        
    if not slots_por_verificar:
        print("  > Nenhum novo sinal detetado nesta patrulha.")
        return

    print("  > A verificar slots:", slots_por_verificar)
    
    for slot_id in sorted(slots_por_verificar):
        time.sleep(0.1) 
        ler_cor_e_guardar(slot_id)
    
    print("Patrulha terminada.")


# --- CONFIGURACAO E TURNOS ---

def sortear_inimigos_com_dados():
    global slots_inimigos
    print("\n--- INICIO: SORTEIO (DADOS VIRTUAIS) ---")
    
    for slot_atual in range(1, NUMERO_DE_SLOTS + 1):
        # 1. Dado do Tipo de Inimigo (1-6)
        dado_tipo = random.randint(1, 6)
        if dado_tipo <= 2: tipo = "Tanque"
        elif dado_tipo <= 4: tipo = "Artilharia"
        else: tipo = "Infantaria"
            
        # 2. Dado do Turno de Entrada (1-6) convertido para Impares (1,3,5,7,9,11)
        dado_bruto = random.randint(1, 6)
        turno_entrada_impar = (dado_bruto * 2) - 1
        
        stats = INIMIGOS[tipo]
        
        slots_inimigos[slot_atual]['tipo'] = tipo
        slots_inimigos[slot_atual]['vida_inicial'] = stats['vida']
        slots_inimigos[slot_atual]['ataques_restantes'] = stats['ataques'] 
        slots_inimigos[slot_atual]['turno_entrada'] = turno_entrada_impar
        
        slots_inimigos[slot_atual]['vida_atual'] = 0 
        slots_inimigos[slot_atual]['detetado'] = False
        slots_inimigos[slot_atual]['chegou'] = False 
        
        print("Slot", slot_atual, ":", tipo, "| Dado:", dado_bruto, "-> Entra Turno:", turno_entrada_impar)

    print("-" * 30)

def menu_acao_manual():
    while True:
        print("\n" + "="*40)
        print("         MENU DE COMANDO MANUAL")
        print("="*40)
        print("Vida Robo:", defender_vida_atual, "| Energia:", defender_energia_atual)
        imprimir_relatorio_conhecido() 
        print("1. ATACAR (So inimigos detetados)")
        print("2. CURAR")
        print("3. PASSAR TURNO")
        
        opcao = input("Opcao: ")
        
        if opcao == '1':
            slot_str = input("Slot (1-6): ")
            if slot_str.isdigit():
                slot = int(slot_str)
                if 1 <= slot <= 6:
                    info = slots_inimigos[slot]
                    if info['detetado'] and info['vida_atual'] > 0:
                        print("Arma: 1.Grua(300EN) 2.Toque(150EN) 3.Som(50EN)")
                        arma = input("?> ")
                        if arma.isdigit() and 1 <= int(arma) <= 3:
                            dano = simular_movimento_e_ataque(slot, int(arma))
                            if dano > 0:
                                slots_inimigos[slot]['vida_atual'] -= dano
                                if slots_inimigos[slot]['vida_atual'] < 0: slots_inimigos[slot]['vida_atual'] = 0
                                print("Dano aplicado. HP Restante:", slots_inimigos[slot]['vida_atual'])
                                break
                    else:
                        print("Erro: Slot vazio, desconhecido ou destruido.")
                else:
                    print("Slot invalido.")
        elif opcao == '2':
            print("Cura: 1(200EN) 2(300EN) 3(400EN)")
            c = input("?> ")
            if c.isdigit() and 1 <= int(c) <= 3:
                if usar_cura(int(c)): break
        elif opcao == '3':
            break

def imprimir_relatorio_conhecido():
    print("-" * 50)
    print("   RADAR DO ROBO")
    print("-" * 50)
    for i in range(1, NUMERO_DE_SLOTS + 1):
        info = slots_inimigos[i]
        
        if info['detetado']:
            if info['tipo'] == "Vazio":
                estado = "[ VAZIO ]"
            elif info['vida_atual'] <= 0:
                estado = "[ DESTRUIDO ]"
            else:
                estado = str(info['tipo']) + " (HP:" + str(info['vida_atual']) + " | Balas:" + str(info['ataques_restantes']) + ")"
        else:
            estado = "[ ? ]"
            
        print("Slot", i, ":", estado)
    print("-" * 50)

def turnos_do_jogo():
    global defender_vida_atual
    global defender_energia_atual
    
    print("\n" + "="*40)
    print("         BATTLE START")
    print("="*40)
    time.sleep(1)

    for turno in range(1, 14):
        print("\n" + "="*15 + " TURNO", turno, "/ 13 " + "="*15)
        
        # =================================================================
        # FASE INIMIGA (Turnos Impares)
        # =================================================================
        if turno % 2 != 0:
            print("[FASE INIMIGA]")
            dano_total = 0
            
            for i in range(1, NUMERO_DE_SLOTS + 1):
                info = slots_inimigos[i]
                
                # --- EVENTO DE CHEGADA ---
                # Se o turno atual corresponde ao turno calculado (1,3,5...)
                if turno == info['turno_entrada'] and not info['chegou']:
                    if info['tipo'] != "Vazio":
                        print("[NOVA AMEACA] Slot", i, "acabou de chegar e esta a posicionar-se.")
                        
                        # Define a vida inicial (sistema sabe que esta la, mas robo ainda nao)
                        slots_inimigos[i]['vida_atual'] = slots_inimigos[i]['vida_inicial']
                        slots_inimigos[i]['chegou'] = True
                    else:
                        slots_inimigos[i]['chegou'] = True # Chegou um "Vazio"
                    
                    # Quem chega agora, so se posiciona. Nao ataca.
                    continue

                # --- EVENTO DE ATAQUE ---
                # Condicoes: Ja chegou (antes deste turno), tem balas, esta vivo
                
                pode_atacar = info['chegou']
                tem_balas = info['ataques_restantes'] > 0
                esta_vivo = info['vida_atual'] > 0
                nao_vazio = info['tipo'] != "Vazio"
                
                if pode_atacar and tem_balas and esta_vivo and nao_vazio:
                    
                    nome = info['tipo']
                    
                    if info['detetado']:
                        ratio = float(info['vida_atual']) / float(info['vida_inicial'])
                    else:
                        ratio = 1.0 
                        print("  [ALERTA] Disparo de origem desconhecida (Slot", i, ")!")
                        slots_inimigos[i]['detetado'] = True 

                    stats = INIMIGOS[nome]
                    dano_atk = int(stats['forca'] * ratio)
                    
                    slots_inimigos[i]['ataques_restantes'] -= 1
                    balas = slots_inimigos[i]['ataques_restantes']
                    
                    print("  > INIMIGO SLOT", i, "DISPARA! Dano:", dano_atk, "(Balas rest:", balas, ")")
                    dano_total += dano_atk
            
            if dano_total > 0:
                defender_vida_atual -= dano_total
                print("    [IMPACTO] DANO TOTAL:", dano_total, "| HP Robo:", defender_vida_atual)
            else:
                print("    [SILENCIO] Nenhum ataque recebido.")

        # =================================================================
        # FASE ROBO (Turnos Pares)
        # =================================================================
        else:
            recup = int(defender_energia_atual * 0.5)
            defender_energia_atual += recup
            if defender_energia_atual > defender_energia_max: defender_energia_atual = defender_energia_max
            
            print("[FASE ROBO] Energia:", defender_energia_atual, "(Recuperado:", recup, ")")
            
            patrulha_simulada(turno)
            menu_acao_manual()
            
        if defender_vida_atual <= 0:
            print("GAME OVER")
            break
            
        time.sleep(0.5)

    if defender_vida_atual > 0:
        print("VITORIA! HP Final:", defender_vida_atual)

def main():
    sortear_inimigos_com_dados()
    turnos_do_jogo()

main()