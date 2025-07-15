# predict_pro_v3_g1.py

import streamlit as st
from collections import deque, Counter
import time
import math

# ====== CONFIGURAÇÃO STREAMLIT ======
st.set_page_config(page_title="🎯 PREDICT PRO v3 – G1 Único", layout="centered")
st.title("🎯 PREDICT PRO v3 – G1 Único")
st.markdown("Sistema de Decifração de Algoritmo com Foco Total no G1 🎲")

# ====== INICIALIZAÇÃO DO ESTADO ======
if "historico" not in st.session_state:
    st.session_state.historico = []
if "suggestion_for_next_round" not in st.session_state:
    st.session_state.suggestion_for_next_round = None # A sugestão que será avaliada na *próxima* rodada
if "pattern_for_next_round" not in st.session_state:
    st.session_state.pattern_for_next_round = None # O padrão para a sugestão da *próxima* rodada
if "confidence_for_next_round" not in st.session_state:
    st.session_state.confidence_for_next_round = 0.0 # Confiança para a sugestão da *próxima* rodada
if "memoria_padroes" not in st.session_state:
    st.session_state.memoria_padroes = {}
if "ultimo_resultado" not in st.session_state:
    st.session_state.ultimo_resultado = None

# Contadores para estatísticas gerais (sem G2/G3)
if "estatisticas" not in st.session_state:
    st.session_state.estatisticas = {
        "acertos": 0,
        "erros": 0,
        "tentativas": 0 # Total de vezes que uma sugestão foi avaliada
    }

cores = {"C": "🔴", "V": "🔵", "E": "🟡"}

# Helper para calcular a melhor sugestão baseada em padrões (função pura, não mexe no estado)
def _calculate_best_pattern_suggestion_pure(hist_data):
    if len(hist_data) < 5:
        return None, None, 0.0, "Histórico insuficiente para análise"

    padroes_encontrados = detect_all_patterns_avancados(hist_data) # Usa a função dos 30 padrões

    if not padroes_encontrados:
        return None, None, 0.0, "Nenhum padrão confiável detectado"

    padroes_pontuados = []
    for nome, cor, confianca_fixa, motivo in padroes_encontrados:
        memoria = st.session_state.memoria_padroes.get(nome, {"acertos": 0, "erros": 0})
        total_entradas = memoria["acertos"] + memoria["erros"]

        pontuacao = confianca_fixa
        if total_entradas >= 5: # Pondera a confiança fixa com a acurácia da memória
            acuracia_memoria = memoria["acertos"] / total_entradas
            pontuacao = (confianca_fixa * 0.7) + (acuracia_memoria * 0.3)

        padroes_pontuados.append((nome, cor, pontuacao, motivo))

    padroes_pontuados.sort(key=lambda x: x[2], reverse=True)
    padrao_escolhido = padroes_pontuados[0]

    return padrao_escolhido[0], padrao_escolhido[1], padrao_escolhido[2], padrao_escolhido[3]


# ====== FUNÇÕES DE LÓGICA DO SISTEMA ======
def registrar_resultado(resultado):
    """
    Registra o resultado, avalia a sugestão ativa e gera uma nova sugestão G1.
    """
    # Só processa se havia uma sugestão ativa para esta rodada
    if st.session_state.suggestion_for_next_round is not None:
        sugestao_ativa = st.session_state.suggestion_for_next_round
        padrao_ativo = st.session_state.pattern_for_next_round

        # Incrementa o total de tentativas (rodadas avaliadas)
        st.session_state.estatisticas["tentativas"] += 1

        # Lógica de avaliação:
        # 1. Acerto (GREEN)
        if sugestao_ativa == resultado:
            st.session_state.estatisticas["acertos"] += 1
            st.session_state.memoria_padroes.setdefault(padrao_ativo, {"acertos": 0, "erros": 0})["acertos"] += 1
        # 2. Empate (Neutro - não é RED nem GREEN para apostas C/V)
        elif sugestao_ativa != 'E' and resultado == 'E':
            # Não é contado como erro nem acerto, apenas como uma tentativa.
            # A memória de padrões NÃO é atualizada para este "pass"
            pass
        # 3. Erro (RED)
        else:
            st.session_state.estatisticas["erros"] += 1
            st.session_state.memoria_padroes.setdefault(padrao_ativo, {"acertos": 0, "erros": 0})["erros"] += 1

    # Adiciona o novo resultado ao histórico
    st.session_state.historico.append(resultado)
    st.session_state.ultimo_resultado = resultado

    # Sempre gera uma nova sugestão G1 para a próxima rodada
    nome, cor, conf, motivo = _calculate_best_pattern_suggestion_pure(st.session_state.historico)
    st.session_state.suggestion_for_next_round = cor
    st.session_state.pattern_for_next_round = nome
    st.session_state.confidence_for_next_round = conf

# ====== INSERÇÃO DE RESULTADO ======
st.subheader("📥 Inserir Resultado")
col1, col2, col3 = st.columns(3)
if col1.button("🔴 Casa"):
    registrar_resultado("C")
    st.rerun()
if col2.button("🔵 Visitante"):
    registrar_resultado("V")
    st.rerun()
if col3.button("🟡 Empate"):
    registrar_resultado("E")
    st.rerun()

# ====== EXIBIÇÃO DO HISTÓRICO (PAINEL 3x9) ======
st.subheader("📊 Histórico (mais recente na Linha 1)")
# Exibe apenas os últimos 27 resultados para manter o painel visual limpo
painel = list(st.session_state.historico[-27:]) 
while len(painel) < 27:
    painel.insert(0, " ")
painel.reverse()

for linha in range(3):
    cols = st.columns(9)
    for i in range(9):
        pos = linha * 9 + i
        if pos < len(painel):
            valor = painel[pos]
            emoji = cores.get(valor, "⬛")
            cols[i].markdown(f"<div style='text-align:center; font-size:28px'>{emoji}</div>", unsafe_allow_html=True)
        else:
            cols[i].markdown(f"<div style='text-align:center; font-size:28px'>⬛</div>", unsafe_allow_html=True)

# ====== DETECÇÃO DE PADRÕES AVANÇADOS (30 PADRÕES) ======
# Esta função contém os 30 padrões que você forneceu.
# Ela é chamada pela função _calculate_best_pattern_suggestion_pure.
def detect_all_patterns_avancados(hist):
    """
    Detecta os 30 padrões com lógica aprimorada e sugestão baseada na tendência.
    Retorna uma lista de tuplas: (nome, sugestão, confiança_fixa, motivo).
    """
    padroes = []
    h = ''.join(hist)
    hist_list = list(hist)
    
    # 1. Sequência Crescente
    if len(hist_list) >= 3 and hist_list[-3] == hist_list[-2] == hist_list[-1] and hist_list[-1] != "E":
        sugestao = hist_list[-1]
        padroes.append(("Sequência Crescente", sugestao, 0.75, "3 repetições seguidas"))
    
    # 2. Alternância Simples
    if len(hist_list) >= 4 and hist_list[-1] == hist_list[-3] and hist_list[-2] == hist_list[-4] and hist_list[-1] != hist_list[-2]:
        sugestao = hist_list[-1]
        padroes.append(("Alternância Simples", sugestao, 0.65, "Padrão A-B-A-B"))

    # 3. Empate após alternância
    if len(hist_list) >= 3 and hist_list[-1] == "E" and hist_list[-2] != hist_list[-3]:
        sugestao = hist_list[-3]
        padroes.append(("Empate após alternância", sugestao, 0.68, "Empate surge após troca de lados"))

    # 4. 2x2 alternado
    if h.endswith("CCVV"):
        padroes.append(("2x2 alternado", "C", 0.70, "Sequência CCVV, sugere C"))
    if h.endswith("VVCC"):
        padroes.append(("2x2 alternado", "V", 0.70, "Sequência VVCC, sugere V"))

    # 5. Casa-Empate-Casa
    if h.endswith("CEC"):
        padroes.append(("Casa-Empate-Casa", "V", 0.72, "Empate cercado por Casa, sugere V"))

    # 6. Palíndromo 5 posições
    if len(hist_list) >= 5 and hist_list[-5] == hist_list[-1] and hist_list[-4] == hist_list[-2] and hist_list[-3] not in ["E", hist_list[-1]]:
        sugestao = hist_list[-3]
        padroes.append(("Palíndromo 5 posições", sugestao, 0.66, "Sequência simétrica"))

    # 7. Coluna repetida
    if len(hist_list) >= 9:
        col1 = hist_list[-9:-6]
        col3 = hist_list[-3:]
        if col1 == col3:
            sugestao = col3[0]
            padroes.append(("Coluna repetida", sugestao, 0.80, "Repetição estrutural detectada"))

    # 8. Reescrita Vertical
    if len(hist_list) >= 12:
        col1 = hist_list[-12:-9]
        col4 = hist_list[-3:]
        if col1 == col4:
            sugestao = col4[0]
            padroes.append(("Reescrita Vertical", sugestao, 0.85, "Coluna 4 igual à Coluna 1"))
    
    # 9. Troca de paleta
    if len(hist_list) >= 6:
        bloco1 = sorted(hist_list[-6:-3])
        bloco2 = sorted(hist_list[-3:])
        if bloco1 == bloco2 and hist_list[-6:-3] != hist_list[-3:]:
            sugestao = hist_list[-1]
            padroes.append(("Troca de paleta", sugestao, 0.78, "Mesma estrutura com cores trocadas"))

    # 10. Espelhamento de Linhas (usando histórico completo)
    if len(hist_list) >= 27:
        linha1 = hist_list[-9:]
        linha3 = hist_list[-27:-18]
        if linha1 == linha3:
            sugestao = linha1[0]
            padroes.append(("Espelhamento de Linhas", sugestao, 0.82, "Linha 1 igual à Linha 3"))
    
    # 11. Coluna 1 = Coluna 5
    if len(hist_list) >= 15:
        col1 = hist_list[-15:-12]
        col5 = hist_list[-3:]
        if col1 == col5:
            sugestao = col5[0]
            padroes.append(("Coluna 1 = Coluna 5", sugestao, 0.83, "Padrão estrutural oculto detectado"))
    
    # 12. Loop CCE
    if h.endswith("CCE"):
        padroes.append(("Loop CCE", "C", 0.77, "Sequência C-C-E, sugere C"))

    # 13. Disfarce de Dominância
    if h.endswith("CVCV"):
        padroes.append(("Disfarce de Dominância", "C", 0.70, "Padrão de alternância CVCV, sugere C"))
    if h.endswith("VCVC"):
        padroes.append(("Disfarce de Dominância", "V", 0.70, "Padrão de alternância VCVC, sugere V"))

    # 14. Reinício Dominante
    if len(hist_list) >= 6:
        ultimos = hist_list[-6:]
        mais_comum = Counter(ultimos).most_common(1)[0][0]
        if ultimos[-1] != mais_comum and mais_comum != "E":
            padroes.append(("Reinício Dominante", mais_comum, 0.76, f"Tendência voltando para cor dominante ({mais_comum})"))
    
    # Padrões da Lista Estendida
    
    # 15. Indução de Ganância (3-1 armadilha)
    if len(hist_list) >= 4:
        if hist_list[-4] == hist_list[-3] == hist_list[-2] and hist_list[-1] != hist_list[-2] and hist_list[-2] != 'E':
            sugestao = hist_list[-2]
            padroes.append(("Indução de Ganância (3-1)", sugestao, 0.90, "Armadilha de 3-1, sugere a cor dominante para retorno"))
            
    # 16. Padrão de Gancho (Hook Pattern)
    if len(hist_list) >= 6:
        if hist_list[-6:] == ['C', 'V', 'V', 'C', 'C', 'V']:
            padroes.append(("Padrão de Gancho (Hook)", 'V', 0.85, "Gancho em C-V-V-C-C-V, sugere V"))
        elif hist_list[-6:] == ['V', 'C', 'C', 'V', 'V', 'C']:
            padroes.append(("Padrão de Gancho (Hook)", 'C', 0.85, "Gancho em V-C-C-V-V-C, sugere C"))
            
    # 17. Padrão Armadilha de Empate
    if len(hist_list) >= 3 and hist_list[-1] == 'E' and hist_list[-2] != hist_list[-3]:
        sugestao = hist_list[-2]
        padroes.append(("Armadilha de Empate", sugestao, 0.75, "Empate quebrou o padrão, sugere a cor anterior"))

    # 18. Ciclo 9 Invertido
    if len(hist_list) >= 18:
        bloco1 = hist_list[-18:-9]
        bloco2 = hist_list[-9:]
        if bloco1 == bloco2[::-1] and 'E' not in bloco1:
            sugestao = bloco2[0]
            padroes.append(("Ciclo 9 Invertido", sugestao, 0.88, "O ciclo de 9 resultados se inverteu"))

    # 19. Reescrita de Bloco 18
    if len(hist_list) >= 36:
        bloco_anterior_set = set(hist_list[-36:-18])
        bloco_atual_set = set(hist_list[-18:])
        if bloco_anterior_set == bloco_atual_set and 'E' not in bloco_atual_set:
            sugestao = hist_list[-1]
            padroes.append(("Reescrita de Bloco 18", sugestao, 0.92, "Bloco de 18 resultados reescrito"))
            
    # 20. Inversão Diagonal
    if len(hist_list) >= 9:
        if hist_list[-9] == hist_list[-1]:
            sugestao = hist_list[-1]
            padroes.append(("Inversão Diagonal", sugestao, 0.80, "Diagonal principal está se formando"))
        if hist_list[-7] == hist_list[-3]:
            sugestao = hist_list[-3]
            padroes.append(("Inversão Diagonal", sugestao, 0.80, "Diagonal secundária está se formando"))
            
    # 21. Padrão de Dominância 5x1
    if len(hist_list) >= 6:
        seq = hist_list[-6:]
        count = Counter(seq)
        if (count.get('C', 0) == 5 and count.get('V', 0) == 1) or (count.get('V', 0) == 5 and count.get('C', 0) == 1):
            sugestao = count.most_common(1)[0][0]
            if sugestao != 'E':
                padroes.append(("Dominância 5x1", sugestao, 0.85, "Padrão de dominância 5x1"))
            
    # 22. Padrão de Frequência Oculta
    if len(hist_list) >= 18:
        freq = Counter(hist_list[-18:])
        if freq.get('C', 0) > 0 and freq.get('V', 0) > 0 and freq.get('E', 0) < 6:
            sugestao = freq.most_common()[-1][0]
            if sugestao != 'E':
                padroes.append(("Frequência Oculta", sugestao, 0.78, "Cor menos frequente tende a voltar"))
                
    # 23. Padrão “Zona Morta”
    for cor in ['C', 'V']:
        if len(hist_list) >= 12:
            historico_sem_cor = [r for r in hist_list[-12:] if r != cor]
            if len(historico_sem_cor) == 12:
                padroes.append(("Zona Morta", cor, 0.95, f"Cor {cor} está sumida por 12+ rodadas, tendência de retorno"))
                
    # 24. Inversão com Delay
    if len(hist_list) >= 6 and hist_list[-6:-3] == hist_list[-3:]:
        sugestao = hist_list[-1]
        padroes.append(("Inversão com Delay", sugestao, 0.82, "Padrão repetido, inversão pode vir"))
        
    # 25. Reflexo com Troca Lenta
    if len(hist_list) >= 8:
        bloco1 = hist_list[-8:-4]
        bloco2 = hist_list[-4:]
        invertido = ['V' if c == 'C' else 'C' for c in bloco1]
        if bloco2 == invertido:
            sugestao = bloco2[0]
            padroes.append(("Reflexo com Troca Lenta", sugestao, 0.88, "Padrão reflete com cores invertidas"))
            
    # 26. Padrão Cascata Fragmentada
    if len(hist_list) >= 9 and hist_list[-3:] == hist_list[-6:-3]:
        sugestao = hist_list[-1]
        padroes.append(("Cascata Fragmentada", sugestao, 0.77, "Repetição de blocos curtos"))
            
    # 27. Empate Enganoso
    if len(hist_list) >= 4 and hist_list[-3] == 'E' and hist_list[-1] != 'E':
        sugestao = hist_list[-1]
        padroes.append(("Empate Enganoso", sugestao, 0.70, "Empate usado como ponto de corte, sugere continuidade"))
        
    # 28. Reação à Perda do Jogador (padrão reverso)
    if len(hist_list) >= 4 and hist_list[-4] == hist_list[-2] and hist_list[-3] == hist_list[-1]:
        sugestao = hist_list[-1]
        padroes.append(("Reação à Perda (padrão reverso)", sugestao, 0.85, "Padrão reverso detectado após sequência"))

    # 29. Zebra Lenta
    if len(hist_list) >= 8:
        if hist_list[-8] != hist_list[-7] and hist_list[-6] != 'E' and hist_list[-5] == 'E' and hist_list[-4] != 'E':
            sugestao = hist_list[-1]
            padroes.append(("Zebra Lenta", sugestao, 0.72, "Padrão de zebra difícil de ler, detectado"))
            
    # 30. Padrão de Isca (padrão real + quebra suja)
    if len(hist_list) >= 12 and hist_list[-12:-6] == hist_list[-6:]:
        sugestao = hist_list[-1]
        padroes.append(("Padrão de Isca", sugestao, 0.95, "Padrão repetido, a quebra pode vir em breve"))
        
    return padroes


# ====== PAINEL DE CONTROLE ======
st.subheader("🎯 Sugestão de Jogada (G1)")

# Lógica para determinar a sugestão a ser exibida
sugestao_display = None
padrao_display = None
confianca_display = 0.0
motivo_display = ""

# Se não há sugestão para a próxima rodada (primeira execução ou após limpar)
if st.session_state.suggestion_for_next_round is None:
    # Tenta gerar a primeira sugestão G1
    nome, cor, conf, motivo = _calculate_best_pattern_suggestion_pure(st.session_state.historico)
    if cor is not None:
        st.session_state.suggestion_for_next_round = cor
        st.session_state.pattern_for_next_round = nome
        st.session_state.confidence_for_next_round = conf
        sugestao_display = cor
        padrao_display = nome
        confianca_display = conf
        motivo_display = motivo
else:
    # Se já existe uma sugestão para a próxima rodada, use-a
    sugestao_display = st.session_state.suggestion_for_next_round
    padrao_display = st.session_state.pattern_for_next_round
    confianca_display = st.session_state.confidence_for_next_round
    # Recalcula o motivo para exibir o mais recente, se houver histórico suficiente
    if len(st.session_state.historico) >= 5:
        _, _, _, motivo_display = _calculate_best_pattern_suggestion_pure(st.session_state.historico)


if sugestao_display is None:
    st.info("Aguardando histórico para gerar a primeira sugestão...")
else:
    emoji = cores.get(sugestao_display, "?")
    st.markdown(f"**Sugestão:** {emoji} com confiança de {confianca_display*100:.1f}%")
    st.caption(f"Padrão: {padrao_display} | Motivo: {motivo_display}")


st.subheader("📈 Estatísticas (G1)")

total_tentativas = st.session_state.estatisticas["tentativas"]
if total_tentativas > 0:
    acuracia_total = st.session_state.estatisticas["acertos"] / total_tentativas * 100
    st.write(f"Total de Tentativas: {total_tentativas}")
    st.write(f"Acertos (GREEN): {st.session_state.estatisticas['acertos']}")
    st.write(f"Erros (RED): {st.session_state.estatisticas['erros']}")
    st.write(f"Acurácia: {acuracia_total:.2f}%")
else:
    st.write("Nenhuma tentativa avaliada ainda.")

st.caption("Acurácia focada no G1. Empates não contam como erros diretos.")

if st.button("Limpar Histórico e Estatísticas"):
    st.session_state.historico = []
    st.session_state.suggestion_for_next_round = None
    st.session_state.pattern_for_next_round = None
    st.session_state.confidence_for_next_round = 0.0
    st.session_state.memoria_padroes = {}
    st.session_state.ultimo_resultado = None
    st.session_state.estatisticas = {
        "acertos": 0,
        "erros": 0,
        "tentativas": 0
    }
    st.rerun()

# ====== FIM DO APP ======

