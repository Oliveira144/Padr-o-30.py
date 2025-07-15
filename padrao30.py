# predict_pro_v3_complete_revisado.py

import streamlit as st
from collections import deque, Counter
import time

# ====== CONFIGURAÇÃO STREAMLIT ======
st.set_page_config(page_title="🎯 PREDICT PRO v3 – Anti-Cassino", layout="centered")
st.title("🎯 PREDICT PRO v3 – Anti-Cassino")
st.markdown("Sistema profissional de previsão inteligente para Football Studio Live 🎲")

# ====== INICIALIZAÇÃO DO ESTADO ======
if "historico" not in st.session_state:
    st.session_state.historico = deque(maxlen=27)
if "acertos" not in st.session_state:
    st.session_state.acertos = 0
if "erros" not in st.session_state:
    st.session_state.erros = 0
if "ultima_sugestao" not in st.session_state:
    st.session_state.ultima_sugestao = None
if "padrao_sugerido" not in st.session_state:
    st.session_state.padrao_sugerido = None
if "memoria_padroes" not in st.session_state:
    # Formato: {"nome_do_padrao": {"acertos": 0, "erros": 0}}
    st.session_state.memoria_padroes = {}
if "ultimo_resultado" not in st.session_state:
    st.session_state.ultimo_resultado = None

cores = {"C": "🔴", "V": "🔵", "E": "🟡"}

# ====== FUNÇÕES DE LÓGICA DO SISTEMA ======
def registrar_resultado(resultado):
    """
    Registra o resultado, avalia a sugestão anterior e limpa o estado para a próxima rodada.
    """
    # 1. Avalia o acerto da última sugestão
    if st.session_state.ultima_sugestao is not None and st.session_state.padrao_sugerido is not None:
        sugestao = st.session_state.ultima_sugestao
        padrao = st.session_state.padrao_sugerido

        if sugestao == resultado:
            st.session_state.acertos += 1
            st.session_state.memoria_padroes.setdefault(padrao, {"acertos": 0, "erros": 0})["acertos"] += 1
        else:
            st.session_state.erros += 1
            st.session_state.memoria_padroes.setdefault(padrao, {"acertos": 0, "erros": 0})["erros"] += 1

    # 2. Adiciona o novo resultado ao histórico
    st.session_state.historico.append(resultado)
    st.session_state.ultimo_resultado = resultado

    # 3. Limpa a sugestão para a próxima rodada
    st.session_state.ultima_sugestao = None
    st.session_state.padrao_sugerido = None

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

# ====== DETECÇÃO DE PADRÕES (REVISADA) ======
def detect_all_patterns_revisada(hist):
    """
    Detecta padrões com lógica mais clara e sugestão baseada na tendência.
    Retorna uma lista de tuplas: (nome, sugestão, confiança_fixa, motivo).
    """
    padroes = []
    h = ''.join(hist)
    
    # É crucial usar a lista do histórico para fatiamento
    hist_list = list(hist)

    # 1. Sequência Crescente
    # Padrão: A-A-A, sugere A
    if len(hist_list) >= 3 and hist_list[-3] == hist_list[-2] == hist_list[-1] != "E":
        sugestao = hist_list[-1]
        padroes.append(("Sequência Crescente", sugestao, 0.75, "3 repetições seguidas"))
    
    # 2. Alternância Simples
    # Padrão: A-B-A-B, sugere A
    if len(hist_list) >= 4 and hist_list[-1] == hist_list[-3] and hist_list[-2] == hist_list[-4] and hist_list[-1] != hist_list[-2]:
        sugestao = hist_list[-1]
        padroes.append(("Alternância Simples", sugestao, 0.65, "Padrão A-B-A-B"))

    # 3. Empate após alternância
    # Padrão: A-B-E, sugere A ou V (o que não for Empate)
    if len(hist_list) >= 3 and hist_list[-1] == "E" and hist_list[-2] != hist_list[-3] and hist_list[-3] != "E":
        sugestao = hist_list[-3] # Sugere o lado que "parou"
        padroes.append(("Empate após alternância", sugestao, 0.68, "Empate surge após troca de lados"))

    # 4. 2x2 alternado
    # Padrão: CCVV ou VVCC, sugere o contrário do último grupo
    if h.endswith("CCVV"):
        padroes.append(("2x2 alternado", "C", 0.70, "Sequência CCVV, sugere C"))
    if h.endswith("VVCC"):
        padroes.append(("2x2 alternado", "V", 0.70, "Sequência VVCC, sugere V"))

    # 5. Casa-Empate-Casa
    # Padrão: C-E-C, sugere V
    if h.endswith("CEC"):
        padroes.append(("Casa-Empate-Casa", "V", 0.72, "Empate cercado por Casa, sugere V"))

    # 6. Palíndromo 5 posições
    # Padrão: A-B-C-B-A, sugere C
    if len(hist_list) >= 5 and hist_list[-5] == hist_list[-1] and hist_list[-4] == hist_list[-2] and hist_list[-3] not in ["E", hist_list[-1]]:
        sugestao = hist_list[-3]
        padroes.append(("Palíndromo 5 posições", sugestao, 0.66, "Sequência simétrica"))

    # 7. Coluna repetida (usando histórico completo)
    if len(hist_list) >= 9:
        col1 = hist_list[-9:-6]
        col3 = hist_list[-3:]
        if col1 == col3 and col1 != ["E", "E", "E"]:
            sugestao = col3[0] # Sugere a próxima da sequência
            padroes.append(("Coluna repetida", sugestao, 0.80, "Repetição estrutural detectada"))

    # 8. Reescrita Vertical
    if len(hist_list) >= 12:
        col1 = hist_list[-12:-9]
        col4 = hist_list[-3:]
        if col1 == col4 and col1 != ["E", "E", "E"]:
            sugestao = col4[0] # Sugere a próxima da sequência
            padroes.append(("Reescrita Vertical", sugestao, 0.85, "Coluna 4 igual à Coluna 1"))
    
    # 9. Troca de paleta
    if len(hist_list) >= 6:
        bloco1 = sorted(hist_list[-6:-3])
        bloco2 = sorted(hist_list[-3:])
        if bloco1 == bloco2 and hist_list[-6:-3] != hist_list[-3:]:
            sugestao = hist_list[-1] # Sugere a continuidade do último bloco
            padroes.append(("Troca de paleta", sugestao, 0.78, "Mesma estrutura com cores trocadas"))

    # 10. Espelhamento de Linhas (usando histórico completo)
    if len(hist_list) == 27:
        linha1 = hist_list[-9:]
        linha3 = hist_list[:9]
        if linha1 == linha3 and linha1 != ["E", "E", "E"]:
            sugestao = linha1[0] # Sugere o início da linha
            padroes.append(("Espelhamento de Linhas", sugestao, 0.82, "Linha 1 igual à Linha 3"))
    
    # 11. Coluna 1 = Coluna 5
    if len(hist_list) >= 15:
        col1 = hist_list[-15:-12]
        col5 = hist_list[-3:]
        if col1 == col5 and col1 != ["E", "E", "E"]:
            sugestao = col5[0]
            padroes.append(("Coluna 1 = Coluna 5", sugestao, 0.83, "Padrão estrutural oculto detectado"))
    
    # 12. Loop CCE
    if h.endswith("CCE"):
        padroes.append(("Loop CCE", "C", 0.77, "Sequência C-C-E, sugere C"))

    # 13. Disfarce de Dominância
    if h.endswith("CVCV"):
        padroes.append(("Disfarce de Dominância", "C", 0.70, "Padrão de alternância CVCV, sugere C"))
    if h.endswith("VCEC"):
        padroes.append(("Disfarce de Dominância", "V", 0.70, "Padrão de alternância VCEC, sugere V"))

    # 14. Reinício Dominante
    if len(hist_list) >= 6:
        ultimos = hist_list[-6:]
        mais_comum = Counter(ultimos).most_common(1)[0][0]
        if ultimos[-1] != mais_comum and mais_comum != "E":
            padroes.append(("Reinício Dominante", mais_comum, 0.76, f"Tendência voltando para cor dominante ({mais_comum})"))
    
    # 15. Empate Estruturado
    # (Este padrão precisa ser repensado pois a posição 5, 14, 23 não é fixa no deque)
    # Ignorado na revisão para evitar lógica complexa
    
    # 16. Loop EVC
    if h.endswith("EVC"):
        padroes.append(("Loop EVC", "E", 0.73, "Sequência E-V-C, sugere E"))

    # 17. Reescrita Deslocada
    if len(hist_list) >= 6:
        a = hist_list[-6:-3]
        b = hist_list[-3:]
        if a[0] == b[1] and a[1] == b[2]:
            sugestao = b[0]
            padroes.append(("Reescrita Deslocada", sugestao, 0.75, "Colunas com padrão deslocado"))

    # 18. Colunas Intercaladas Iguais
    if len(hist_list) >= 15:
        col1 = hist_list[-15:-12]
        col3 = hist_list[-9:-6]
        col5 = hist_list[-3:]
        if col1 == col3 == col5 and col1 != ["E", "E", "E"]:
            sugestao = col5[0]
            padroes.append(("Colunas Intercaladas Iguais", sugestao, 0.86, "3 colunas não contíguas repetidas"))

    # 19. Linha 3 espelha Linha 1 invertida
    if len(hist_list) == 27:
        l1 = hist_list[-9:]
        l3 = hist_list[0:9]
        if l3 == l1[::-1] and l1 != ["E","E","E","E","E","E","E","E","E"]:
            sugestao = l3[0] # Sugere o início da linha
            padroes.append(("Linha 3 espelha Linha 1 invertida", sugestao, 0.81, "Reversão detectada entre linhas"))

    # 20. 4x Repetição com Desvio
    if len(hist_list) >= 5:
        seq = hist_list[-5:]
        count_e = seq.count("E")
        if count_e < 4 and len(set(seq)) <= 2:
            mais_comum = Counter(seq).most_common(1)[0][0]
            if mais_comum != "E":
                padroes.append(("4x Repetição com Desvio", mais_comum, 0.74, "Apenas 1 valor diferente em 5"))
    
    # 21. Empate Disfarçado
    if len(hist_list) >= 5 and hist_list[-1] == "E":
        if hist_list[-2] != hist_list[-3] != hist_list[-4] != hist_list[-5]:
            padroes.append(("Empate Disfarçado", "E", 0.72, "Empate após alternância longa"))

    # 22. Quebra de Dominância
    if len(hist_list) >= 5 and hist_list[-5] == hist_list[-4] == hist_list[-3] == hist_list[-2] and hist_list[-1] != hist_list[-2]:
        sugestao = hist_list[-2] # Sugere o retorno à cor dominante
        padroes.append(("Quebra de Dominância", sugestao, 0.74, "4x mesma cor quebrada, sugere retorno"))

    # 23. Empate pós-dominância
    if len(hist_list) >= 5 and hist_list[-5] == hist_list[-4] == hist_list[-3] == hist_list[-2] != "E" and hist_list[-1] == "E":
        sugestao = hist_list[-2] # Sugere a cor dominante que foi quebrada pelo empate
        padroes.append(("Empate pós-dominância", sugestao, 0.73, "Empate surge após 4x da mesma, sugere a cor dominante"))

    # 24. Padrão 2-1-2
    if len(hist_list) >= 5 and hist_list[-5] == hist_list[-3] == hist_list[-2] and hist_list[-4] == hist_list[-1] and hist_list[-1] != hist_list[-2]:
        sugestao = hist_list[-1] # Sugere a repetição do último par
        padroes.append(("Padrão 2-1-2", sugestao, 0.76, "Repetição com quebra central"))

    # 25. Coluna Escada
    if len(hist_list) >= 3 and hist_list[-3] == hist_list[-1] and hist_list[-2] != hist_list[-1]:
        sugestao = hist_list[-1] # Sugere a repetição do topo e base
        padroes.append(("Coluna Escada", sugestao, 0.72, "Topo e base iguais com meio diferente"))

    # 26. Inversão frequente
    if len(hist_list) >= 6:
        pares = [hist_list[-6], hist_list[-5]], [hist_list[-4], hist_list[-3]], [hist_list[-2], hist_list[-1]]
        if all(a != b for a, b in pares):
            sugestao = hist_list[-1]
            padroes.append(("Inversão frequente", sugestao, 0.71, "3 inversões sucessivas"))

    # 27. Simetria Irregular
    if len(hist_list) >= 7:
        seq = hist_list[-7:]
        # Ex: C V E E E V C
        if seq[0] == seq[6] and seq[1] == seq[5] and seq[2] == seq[4]:
            sugestao = seq[3]
            padroes.append(("Simetria Irregular", sugestao, 0.77, "Padrão espelhado alternado"))
    
    # Adicionando um novo padrão para demonstrar
    # 28. Quebra de Sequência com Empate
    if len(hist_list) >= 4 and hist_list[-4] == hist_list[-3] == hist_list[-2] and hist_list[-1] == "E":
        sugestao = hist_list[-2] # Sugere a cor da sequência que foi quebrada
        padroes.append(("Quebra de Sequência com Empate", sugestao, 0.78, "Empate quebra uma sequência de 3"))
        
    # Adicionar mais padrões aqui...
    
    return padroes

# ====== SUGESTÃO INTELIGENTE E APRENDIZADO ======
def gerar_sugestao_inteligente():
    hist = st.session_state.historico
    if len(hist) < 5:
        return None, None, 0.0, "Histórico insuficiente para análise"

    padroes_encontrados = detect_all_patterns_revisada(hist)
    
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

# ====== PAINEL DE CONTROLE ======
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

# Estatísticas simples
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

# Botão para limpar dados
if st.button("Limpar Histórico e Estatísticas"):
    st.session_state.historico = deque(maxlen=27)
    st.session_state.acertos = 0
    st.session_state.erros = 0
    st.session_state.ultima_sugestao = None
    st.session_state.padrao_sugerido = None
    st.session_state.memoria_padroes = {}
    st.session_state.ultimo_resultado = None
    st.rerun()

# ====== FIM DO APP ======
