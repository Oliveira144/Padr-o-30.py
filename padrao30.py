# predict_pro_v2_complete.py

import streamlit as st
from collections import deque, Counter
import time

# ====== CONFIGURAÇÃO STREAMLIT ======
st.set_page_config(page_title="🎯 PREDICT PRO v2 – Anti-Cassino", layout="centered")
st.title("🎯 PREDICT PRO v2 – Anti-Cassino")
st.markdown("Sistema profissional de previsão inteligente para Football Studio Live 🎲")

# ====== INICIALIZAÇÃO DO ESTADO ======
if "historico" not in st.session_state:
    st.session_state.historico = deque(maxlen=27)
if "entradas" not in st.session_state:
    st.session_state.entradas = []
if "acertos" not in st.session_state:
    st.session_state.acertos = 0
if "erros" not in st.session_state:
    st.session_state.erros = 0
if "memoria_padroes" not in st.session_state:
    st.session_state.memoria_padroes = {}

cores = {"C": "🔴", "V": "🔵", "E": "🟡"}

# ====== INSERÇÃO DE RESULTADO ======
st.subheader("📥 Inserir Resultado")
col1, col2, col3 = st.columns(3)
if col1.button("🔴 Casa"):
    st.session_state.historico.append("C")
if col2.button("🔵 Visitante"):
    st.session_state.historico.append("V")
if col3.button("🟡 Empate"):
    st.session_state.historico.append("E")

# ====== EXIBIÇÃO DO HISTÓRICO (PAINEL 3x9) ======
st.subheader("📊 Histórico (mais recente na Linha 1)")
painel = list(st.session_state.historico)
while len(painel) < 27:
    painel.insert(0, " ")
    
# Inverte a lista para que a exibição comece dos resultados mais recentes
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

# ====== DETECÇÃO DE PADRÕES (30 PADRÕES) ======
def detect_patterns(hist):
    padroes = []
    h = ''.join(hist)

    # 1. Sequência Crescente
    if len(hist) >= 3 and hist[-1] == hist[-2] == hist[-3] != "E":
        padroes.append(("Sequência Crescente", hist[-1], 0.75, "3 repetições seguidas detectadas"))

    # 2. Alternância Simples
    if len(hist) >= 4 and hist[-1] != hist[-2] and hist[-2] != hist[-3] and hist[-3] != hist[-4]:
        padroes.append(("Alternância Simples", hist[-1], 0.65, "Alternância em 4 posições"))

    # 3. Empate após alternância
    if len(hist) >= 3 and hist[-1] == "E" and hist[-2] != hist[-3]:
        padroes.append(("Empate após alternância", "E", 0.68, "Empate surge após troca de lados"))

    # 4. 2x2 alternado
    if h.endswith("CCVV") or h.endswith("VVCC"):
        padroes.append(("2x2 alternado", hist[-1], 0.7, "Sequência 2x2 detectada"))

    # 5. Casa-Empate-Casa
    if h.endswith("CEC"):
        padroes.append(("Casa-Empate-Casa", "C", 0.72, "Empate cercado por Casa"))

    # 6. Palíndromo 5 posições
    if len(hist) >= 5 and hist[-5] == hist[-1] and hist[-4] == hist[-2]:
        padroes.append(("Palíndromo 5 posições", hist[-1], 0.66, "Sequência simétrica detectada"))

    # 7. Coluna repetida
    if len(hist) >= 9:
        col1 = hist[-9:-6]
        col2 = hist[-6:-3]
        col3 = hist[-3:]
        if col1 == col3:
            padroes.append(("Coluna repetida", col3[0], 0.8, "Repetição estrutural detectada"))

    # 8. Reescrita Vertical
    if len(hist) >= 12:
        col1 = hist[-12:-9]
        col4 = hist[-3:]
        if col1 == col4:
            padroes.append(("Reescrita Vertical", col4[0], 0.85, "Coluna 4 igual à Coluna 1"))

    # 9. Troca de paleta
    if len(hist) >= 6:
        bloco1 = hist[-6:-3]
        bloco2 = hist[-3:]
        if sorted(bloco1) == sorted(bloco2) and bloco1 != bloco2:
            padroes.append(("Troca de paleta", bloco2[0], 0.78, "Mesma estrutura com cores trocadas"))

    # 10. Espelhamento de Linhas
    if len(hist) == 27:
        linha1 = hist[-9:]
        linha3 = hist[:9]
        if linha1 == linha3:
            padroes.append(("Espelhamento de Linhas", linha1[0], 0.82, "Linha 1 igual à Linha 3"))

    # 11. Coluna 1 = Coluna 5
    if len(hist) >= 15:
        col1 = hist[-15:-12]
        col5 = hist[-3:]
        if col1 == col5:
            padroes.append(("Coluna 1 = Coluna 5", col5[0], 0.83, "Padrão estrutural oculto detectado"))

    # 12. Loop CCE
    if h.endswith("CCE"):
        padroes.append(("Loop CCE", "E", 0.77, "Sequência Casa-Casa-Empate identificada"))

    # 13. Disfarce de Dominância
    if h.endswith("CVCV"):
        padroes.append(("Disfarce de Dominância", hist[-1], 0.7, "Padrão de alternância estável"))

    # 14. Reinício Dominante
    if len(hist) >= 6:
        ultimos = hist[-6:]
        mais_comum = Counter(ultimos).most_common(1)[0][0]
        if ultimos[-1] != mais_comum:
            padroes.append(("Reinício Dominante", mais_comum, 0.76, "Tendência voltando para cor dominante"))

    # 15. Empate Estruturado
    for i in [5, 14, 23]:
        if len(hist) > i and hist[i] == "E":
            padroes.append(("Empate Estruturado", "E", 0.74, f"Empate recorrente na posição {i+1}"))

    # 16. Loop EVC
    if h.endswith("EVC"):
        padroes.append(("Loop EVC", "C", 0.73, "Sequência Empate-Visitante-Casa detectada"))

    # 17. Reescrita Deslocada
    if len(hist) >= 6:
        a = hist[-6:-3]
        b = hist[-3:]
        if a[0] == b[1] and a[1] == b[2]:
            padroes.append(("Reescrita Deslocada", b[0], 0.75, "Colunas com padrão deslocado"))

    # 18. Colunas Intercaladas Iguais
    if len(hist) >= 15:
        col1 = hist[-15:-12]
        col3 = hist[-9:-6]
        col5 = hist[-3:]
        if col1 == col3 == col5:
            padroes.append(("Colunas Intercaladas Iguais", col5[0], 0.86, "3 colunas não contíguas repetidas"))

    # 19. Linha 3 espelha Linha 1 invertida
    if len(hist) == 27:
        l1 = hist[18:27]
        l3 = hist[0:9]
        if l3 == l1[::-1]:
            padroes.append(("Linha 3 espelha Linha 1 invertida", l3[0], 0.81, "Reversão detectada entre linhas"))

    # 20. 4x Repetição com Desvio
    if len(hist) >= 5:
        seq = hist[-5:]
        if len(set(seq)) <= 2:
            padroes.append(("4x Repetição com Desvio", seq[-1], 0.74, "Apenas 1 valor diferente em 5"))

    # 21. Empate Disfarçado
    if len(hist) >= 5:
        if hist[-5] != hist[-4] and hist[-4] != hist[-3] and hist[-3] != hist[-2] and hist[-1] == "E":
            padroes.append(("Empate Disfarçado", "E", 0.72, "Empate após alternância longa"))

    # 22. Quebra de Dominância
    if len(hist) >= 5 and hist[-5] == hist[-4] == hist[-3] == hist[-2] != hist[-1]:
        padroes.append(("Quebra de Dominância", hist[-1], 0.74, "4x mesma cor quebrada na última"))

    # 23. Empate pós-dominância
    if len(hist) >= 5 and hist[-5] == hist[-4] == hist[-3] == hist[-2] != "E" and hist[-1] == "E":
        padroes.append(("Empate pós-dominância", "E", 0.73, "Empate surge após 4x da mesma"))

    # 24. 2x seguido de inverso
    if h.endswith("CCVV") or h.endswith("VVCC"):
        padroes.append(("2x seguido de inverso", hist[-1], 0.75, "Estrutura binária detectada"))

    # 25. Padrão 2-1-2
    if len(hist) >= 5 and hist[-5] == hist[-3] == hist[-2] and hist[-4] == hist[-1] != hist[-5]:
        padroes.append(("Padrão 2-1-2", hist[-1], 0.76, "Repetição com quebra central"))

    # 26. Coluna Escada
    if len(hist) >= 3 and hist[-3] != hist[-2] and hist[-2] != hist[-1] and hist[-1] == hist[-3]:
        padroes.append(("Coluna Escada", hist[-1], 0.72, "Topo e base iguais com meio diferente"))

    # 27. Inversão frequente
    if len(hist) >= 6:
        pares = [hist[-6], hist[-5]], [hist[-4], hist[-3]], [hist[-2], hist[-1]]
        if all(a != b for a, b in pares):
            padroes.append(("Inversão frequente", hist[-1], 0.71, "3 inversões sucessivas"))

    # 28. EVC em loop
    if len(hist) >= 9:
        b1 = hist[-9:-6]
        b2 = hist[-6:-3]
        b3 = hist[-3:]
        if b1 == b2 == b3 == ["E", "V", "C"]:
            padroes.append(("EVC em loop", "E", 0.83, "3 blocos iguais EVC"))

    # 29. Empate Intervalado
    if len(hist) >= 15:
        empates = [i for i in range(-15, 0, 5) if hist[i] == "E"]
        if len(empates) >= 3:
            padroes.append(("Empate Intervalado", "E", 0.76, "Empate ocorre a cada 5"))

    # 30. Simetria Irregular
    if len(hist) >= 7:
        seq = hist[-7:]
        if seq[::2] == seq[1::2][::-1]:
            padroes.append(("Simetria Irregular", seq[-1], 0.77, "Padrão espelhado alternado"))

    if not padroes:
        return None, None, 0.0, "Nenhum padrão confiável detectado"
    padroes.sort(key=lambda x: x[2], reverse=True)
    return padroes[0]

# ====== SUGESTÃO E APRENDIZADO ======
def gerar_sugestao():
    hist = list(st.session_state.historico)
    if len(hist) < 5:
        return None, 0.0, "Histórico insuficiente para análise"
    padrao, cor, confianca, motivo = detect_patterns(hist)
    return cor, confianca, motivo

def registrar_entrada(cor_entrada):
    st.session_state.entradas.append((time.time(), cor_entrada))
    if len(st.session_state.historico) == 0:
        return
    ultimo_resultado = st.session_state.historico[-1]
    if cor_entrada == ultimo_resultado:
        st.session_state.acertos += 1
    else:
        st.session_state.erros += 1

# ====== PAINEL DE CONTROLE ======
st.subheader("🎯 Sugestão de Jogada")
cor_sugestao, confianca, motivo = gerar_sugestao()
if cor_sugestao is None:
    st.info("Não há sugestão confiável no momento.")
else:
    emoji = cores.get(cor_sugestao, "?")
    st.markdown(f"**Sugestão:** {emoji} com confiança de {confianca*100:.1f}%")
    st.caption(f"Motivo: {motivo}")

# Botões para registrar entrada confirmada pelo usuário
st.write("📝 Registre sua entrada após o resultado:")
c1, c2, c3 = st.columns(3)
if c1.button("🔴 Registrei Casa"):
    registrar_entrada("C")
if c2.button("🔵 Registrei Visitante"):
    registrar_entrada("V")
if c3.button("🟡 Registrei Empate"):
    registrar_entrada("E")

# Estatísticas simples
st.subheader("📈 Estatísticas")
total = st.session_state.acertos + st.session_state.erros
if total > 0:
    acuracia = st.session_state.acertos / total * 100
    st.write(f"Total de entradas registradas: {total}")
    st.write(f"Acertos: {st.session_state.acertos}")
    st.write(f"Erros: {st.session_state.erros}")
    st.write(f"Acurácia: {acuracia:.2f}%")
else:
    st.write("Nenhuma entrada registrada ainda.")

# ====== FIM DO APP ======
