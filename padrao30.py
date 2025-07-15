# predict_pro_v3_decifrador.py

import streamlit as st
from collections import deque, Counter
import time
import math

# ====== CONFIGURAÇÃO STREAMLIT ======
st.set_page_config(page_title="🎯 PREDICT PRO v3 – Decifrador de Algoritmo", layout="centered")
st.title("🎯 PREDICT PRO v3 – Decifrador de Algoritmo")
st.markdown("Análise reversa dos padrões de geração de jogos no Football Studio Live 🎲")

# (O restante do código de inicialização de estado e registro de resultados permanece o mesmo)
# ... [Inclua o código de inicialização de estado e a função registrar_resultado] ...
# ... [Inclua o código de exibição do histórico] ...

# As funções de inicialização de estado, registro e visualização do histórico do código anterior são mantidas aqui.
# ... [Código anterior de st.session_state e botões] ...

# Código de registro_resultado e exibição do histórico
def registrar_resultado(resultado):
    if st.session_state.ultima_sugestao is not None and st.session_state.padrao_sugerido is not None:
        sugestao = st.session_state.ultima_sugestao
        padrao = st.session_state.padrao_sugerido

        if sugestao == resultado:
            st.session_state.acertos += 1
            st.session_state.memoria_padroes.setdefault(padrao, {"acertos": 0, "erros": 0})["acertos"] += 1
        else:
            st.session_state.erros += 1
            st.session_state.memoria_padroes.setdefault(padrao, {"acertos": 0, "erros": 0})["erros"] += 1

    st.session_state.historico.append(resultado)
    st.session_state.ultimo_resultado = resultado
    st.session_state.ultima_sugestao = None
    st.session_state.padrao_sugerido = None

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

st.subheader("📊 Histórico (mais recente na Linha 1)")
painel = list(st.session_state.historico)
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


# ====== DETECÇÃO DE PADRÕES (REVISADA E ESTENDIDA) ======
def detect_all_patterns_avancados(hist):
    padroes = []
    h = ''.join(hist)
    hist_list = list(hist)
    
    # Adicionando os padrões da sua lista extendida
    
    # 15. Indução de Ganância (3-1 armadilha)
    if len(hist_list) >= 4:
        if hist_list[-4] == hist_list[-3] == hist_list[-2] and hist_list[-1] != hist_list[-2] and hist_list[-2] != 'E':
            sugestao = hist_list[-2]
            padroes.append(("Indução de Ganância (3-1)", sugestao, 0.90, "Armadilha de 3-1, sugere a cor dominante para retorno"))
            
    # 16. Padrão de Gancho (Hook Pattern)
    if h.endswith("CVCV") or h.endswith("VCVC"):
        if h.endswith("CVC"): # Se a sequência for CVC, sugere C (a quebra)
            padroes.append(("Padrão de Gancho (Hook)", 'C', 0.85, "Gancho em C-V-C, sugere C"))
        elif h.endswith("VCV"): # Se a sequência for VCV, sugere V
            padroes.append(("Padrão de Gancho (Hook)", 'V', 0.85, "Gancho em V-C-V, sugere V"))
            
    # 17. Padrão Armadilha de Empate
    if len(hist_list) >= 3 and hist_list[-1] == 'E' and hist_list[-2] != 'E':
        sugestao = hist_list[-2]
        padroes.append(("Armadilha de Empate", sugestao, 0.75, "Empate quebrou o padrão, sugere a cor anterior"))

    # 18. Ciclo 9 Invertido
    if len(hist_list) >= 18:
        bloco1 = hist_list[-18:-9]
        bloco2 = hist_list[-9:]
        if bloco1 == bloco2[::-1] and 'E' not in bloco1:
            sugestao = bloco2[0] # Sugere o primeiro do bloco invertido
            padroes.append(("Ciclo 9 Invertido", sugestao, 0.88, "O ciclo de 9 resultados se inverteu"))

    # 19. Reescrita de Bloco 18
    if len(hist_list) >= 36:
        bloco_anterior = set(hist_list[-36:-18])
        bloco_atual = set(hist_list[-18:])
        if bloco_anterior == bloco_atual:
            sugestao = hist_list[-1]
            padroes.append(("Reescrita de Bloco 18", sugestao, 0.92, "Bloco de 18 resultados reescrito"))
            
    # 20. Inversão Diagonal
    if len(hist_list) >= 9:
        diag1 = [hist_list[-9], hist_list[-5], hist_list[-1]]
        diag2 = [hist_list[-7], hist_list[-5], hist_list[-3]]
        if diag1[0] == diag1[2] and diag1[1] != diag1[0]:
            sugestao = diag1[0]
            padroes.append(("Inversão Diagonal", sugestao, 0.80, "Diagonal principal está se formando"))
        if diag2[0] == diag2[2] and diag2[1] != diag2[0]:
            sugestao = diag2[0]
            padroes.append(("Inversão Diagonal", sugestao, 0.80, "Diagonal secundária está se formando"))
            
    # 21. Padrão de Dominância 5x1
    if len(hist_list) >= 6:
        seq = hist_list[-6:]
        count = Counter(seq)
        if (count.get('C', 0) == 5 and count.get('V', 0) == 1) or \
           (count.get('V', 0) == 5 and count.get('C', 0) == 1):
            sugestao = count.most_common(1)[0][0]
            padroes.append(("Dominância 5x1", sugestao, 0.85, "Padrão de dominância 5x1"))
            
    # 22. Padrão de Frequência Oculta
    if len(hist_list) >= 18:
        freq = Counter(hist_list[-18:])
        if freq.get('C', 0) < 6 and freq.get('V', 0) < 6:
            sugestao = freq.most_common()[-1][0]
            if sugestao != 'E':
                padroes.append(("Frequência Oculta", sugestao, 0.78, "Cor menos frequente tende a voltar"))
                
    # 23. Padrão “Zona Morta”
    for cor in ['C', 'V']:
        if len(hist_list) > 12:
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
    # Várias sequências curtas repetidas
    if len(hist_list) >= 9:
        if hist_list[-3:] == hist_list[-6:-3]:
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


# ... [O restante do código para gerar sugestão, painel de controle e botão de limpeza permanece o mesmo,
# mas a chamada para a função de detecção de padrões deve ser alterada] ...

def gerar_sugestao_inteligente():
    hist = st.session_state.historico
    if len(hist) < 5:
        return None, None, 0.0, "Histórico insuficiente para análise"

    # AQUI ESTÁ A MUDANÇA
    padroes_encontrados = detect_all_patterns_avancados(hist)
    
    if not padroes_encontrados:
        return None, None, 0.0, "Nenhum padrão confiável detectado"

    padroes_pontuados = []
    for nome, cor, confianca_fixa, motivo in padroes_encontrados:
        memoria = st.session_state.memoria_padroes.get(nome, {"acertos": 0, "erros": 0})
        total_entradas = memoria["acertos"] + memoria["erros"]

        pontuacao = confianca_fixa
        if total_entradas >= 5: # Só pondera se houver dados suficientes
            acuracia_memoria = memoria["acertos"] / total_entradas
            pontuacao = (confianca_fixa * 0.7) + (acuracia_memoria * 0.3)

        padroes_pontuados.append((nome, cor, pontuacao, motivo))
    
    padroes_pontuados.sort(key=lambda x: x[2], reverse=True)

    padrao_escolhido = padroes_pontuados[0]
    
    st.session_state.ultima_sugestao = padrao_escolhido[1]
    st.session_state.padrao_sugerido = padrao_escolhido[0]
    
    return padrao_escolhido[0], padrao_escolhido[1], padrao_escolhido[2], padrao_escolhido[3]

# Painel de controle e estatísticas
st.subheader("🎯 Sugestão de Jogada")

if st.session_state.ultimo_resultado:
    nome_sugestao, cor_sugestao, confianca, motivo = gerar_sugestao_inteligente()
    if cor_sugestao is None:
        st.info("Não há sugestão confiável no momento.")
    else:
        emoji = cores.get(cor_sugestao, "?")
        st.markdown(f"**Sugestão:** {emoji} com confiança de {confianca*100:.1f}%")
        st.caption(f"Padrão: {nome_sugestao} | Motivo: {motivo}")
else:
    st.info("Aguardando o primeiro resultado para começar a análise...")

st.subheader("📈 Estatísticas")
total = st.session_state.acertos + st.session_state.erros
if total > 0:
    acuracia = st.session_state.acertos / total * 100
    st.write(f"Total de entradas avaliadas: {total}")
    st.write(f"Acertos: {st.session_state.acertos}")
    st.write(f"Erros: {st.session_state.erros}")
    st.write(f"Acurácia: {acuracia:.2f}%")
else:
    st.write("Nenhuma entrada avaliada ainda.")
st.caption("Acurácia baseada nas sugestões do sistema.")
st.caption("O sistema só avalia acertos/erros após a primeira sugestão.")

if st.button("Limpar Histórico e Estatísticas"):
    st.session_state.historico = deque(maxlen=27)
    st.session_state.acertos = 0
    st.session_state.erros = 0
    st.session_state.ultima_sugestao = None
    st.session_state.padrao_sugerido = None
    st.session_state.memoria_padroes = {}
    st.session_state.ultimo_resultado = None
    st.rerun()
