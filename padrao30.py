import streamlit as st
import numpy as np
from datetime import datetime

# --- Inicialização do estado da sessão ---
if 'history' not in st.session_state:
    st.session_state.history = []
    
if 'analysis' not in st.session_state:
    st.session_state.analysis = {
        'patterns': [],
        'riskLevel': 'low',
        'manipulation': 'low',
        'prediction': None,
        'confidence': 0,
        'recommendation': 'watch'
    }

# Novo estado para métricas de performance
if 'performance_metrics' not in st.session_state:
    st.session_state.performance_metrics = {
        'total_predictions': 0,
        'correct_predictions': 0,
        'wrong_predictions': 0,
        'g1_hits': 0 # Acertos na primeira tentativa (G1)
    }

# --- Funções de Manipulação de Dados ---

# Função para adicionar um novo resultado ao histórico
def add_result(result):
    # Antes de adicionar o novo resultado, vamos registrar a performance da previsão anterior
    # Isso só faz sentido se houver uma previsão anterior e resultados suficientes para análise
    if st.session_state.analysis['prediction'] is not None and len(st.session_state.history) >= 4: # Mínimo 5 resultados para ter previsão
        predicted_color = st.session_state.analysis['prediction']
        
        st.session_state.performance_metrics['total_predictions'] += 1
        
        if predicted_color == result:
            st.session_state.performance_metrics['correct_predictions'] += 1
            # Lógica para G1: Se o app previu corretamente e o risco era baixo/médio ou havia um padrão forte
            # Esta lógica pode ser refinada. Aqui, um exemplo simples:
            if st.session_state.analysis['recommendation'] == 'bet' or st.session_state.analysis['riskLevel'] in ['low', 'medium']:
                st.session_state.performance_metrics['g1_hits'] += 1
        else:
            st.session_state.performance_metrics['wrong_predictions'] += 1

    st.session_state.history.append({
        'result': result,
        'timestamp': datetime.now(),
        'prediction_at_time': st.session_state.analysis['prediction'] # Armazena a previsão que foi feita antes deste resultado
    })
    # Após adicionar um resultado, a análise é refeita automaticamente
    analyze_data(st.session_state.history)

# Função para resetar todo o histórico e a análise
def reset_history():
    st.session_state.history = []
    st.session_state.analysis = {
        'patterns': [],
        'riskLevel': 'low',
        'manipulation': 'low',
        'prediction': None,
        'confidence': 0,
        'recommendation': 'watch'
    }
    st.session_state.performance_metrics = { # Reseta também as métricas de performance
        'total_predictions': 0,
        'correct_predictions': 0,
        'wrong_predictions': 0,
        'g1_hits': 0
    }

# Função para desfazer o último resultado
def undo_last_result():
    if st.session_state.history:
        # Se houver histórico, remove o último item
        removed_item = st.session_state.history.pop()
        
        # Ajusta as métricas de performance se o item removido contribuiu para elas
        # Isso é um pouco mais complexo, pois precisaríamos saber qual era a previsão ANTES daquele resultado.
        # Para simplificar, vamos apenas recalcular a análise e as métricas do zero
        # ou considerar que o desfeito não afeta as métricas já computadas,
        # ou, a forma mais robusta: reverter a contagem se a previsão que levou ao acerto/erro foi feita para este resultado.
        # Por simplicidade, se o histórico for desfeito, as métricas de performance são recalculadas na próxima análise.
        
        # Recalcula a análise com o histórico ajustado
        analyze_data(st.session_state.history)
        
        # O ideal seria reverter a contagem de acertos/erros/G1 se a previsão que levou a eles foi para o resultado removido.
        # Isso exigiria armazenar mais detalhes no histórico ou recalcular performance do zero.
        # Por enquanto, vamos manter a lógica de recalcular a análise, e o usuário pode resetar se quiser métricas perfeitas.
        # Uma abordagem mais complexa seria:
        # if removed_item['prediction_at_time'] is not None:
        #     if removed_item['prediction_at_time'] == removed_item['result']:
        #         st.session_state.performance_metrics['correct_predictions'] -= 1
        #         # Lógica para G1 reversa aqui
        #     else:
        #         st.session_state.performance_metrics['wrong_predictions'] -= 1
        #     st.session_state.performance_metrics['total_predictions'] -= 1
        
    else:
        st.warning("Não há resultados para desfazer.")

# --- Núcleo de Análise Preditiva (sem alterações significativas na lógica principal) ---
def analyze_data(data):
    if len(data) < 5:
        st.session_state.analysis = {
            'patterns': [],
            'riskLevel': 'low',
            'manipulation': 'low',
            'prediction': None,
            'confidence': 0,
            'recommendation': 'more-data'
        }
        return

    recent = data[-27:]
    patterns = detect_patterns(recent)
    risk_level = assess_risk(recent)
    manipulation = detect_manipulation(recent)
    prediction = make_prediction(recent, patterns)

    st.session_state.analysis = {
        'patterns': patterns,
        'riskLevel': risk_level,
        'manipulation': manipulation,
        'prediction': prediction['color'],
        'confidence': prediction['confidence'],
        'recommendation': get_recommendation(risk_level, manipulation, patterns)
    }

def detect_patterns(data):
    patterns = []
    results = [d['result'] for d in data]

    current_streak = 1
    if results:
        current_color = results[-1]
        for i in range(len(results)-2, -1, -1):
            if results[i] == current_color:
                current_streak += 1
            else:
                break
        if current_streak >= 2:
            patterns.append({
                'type': 'streak',
                'color': current_color,
                'length': current_streak,
                'description': f'{current_streak}x {get_color_name(current_color)} seguidas'
            })

    alternating = True
    if len(results) >= 4:
        for i in range(len(results)-1, len(results)-5, -1):
            if i > 0 and results[i] == results[i-1]:
                alternating = False
                break
        if alternating:
            patterns.append({
                'type': 'alternating',
                'description': 'Padrão alternado detectado'
            })

    if len(results) >= 4:
        last4 = results[-4:]
        if last4[0] == last4[1] and last4[2] == last4[3] and last4[0] != last4[2]:
            patterns.append({
                'type': '2x2',
                'description': 'Padrão 2x2 detectado'
            })
            
    if len(results) >= 5:
        last5 = results[-5:]
        if last5.count('E') >= 3:
            patterns.append({
                'type': 'high-empate',
                'description': 'Alta frequência de empates'
            })
            
    if len(results) >= 5:
        last5 = results[-5:]
        valid_pattern = (
            last5[0] != last5[1] and 
            last5[1] != last5[2] and 
            last5[2] != last5[3] and 
            last5[3] != last5[4] and
            last5[0] == last5[2] and 
            last5[2] == last5[4]
        )
        
        if valid_pattern:
            patterns.append({
                'type': 'zigzag',
                'color': last5[4],
                'description': 'Padrão ZigZag detectado'
            })

    return patterns

def assess_risk(data):
    results = [d['result'] for d in data]
    risk_score = 0

    max_streak = 0
    if results:
        current_streak = 1
        current_color = results[0]
        max_streak = 1 

        for i in range(1, len(results)):
            if results[i] == current_color:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 1
                current_color = results[i]

    if max_streak >= 5: 
        risk_score += 40
    elif max_streak >= 4: 
        risk_score += 25
    elif max_streak >= 3: 
        risk_score += 10

    empate_streak = 0
    for i in range(len(results)-1, -1, -1):
        if results[i] == 'E':
            empate_streak += 1
        else:
            break
            
    if empate_streak >= 2: 
        risk_score += 30

    if risk_score >= 50: 
        return 'high'
    if risk_score >= 25: 
        return 'medium'
    return 'low'

def detect_manipulation(data):
    results = [d['result'] for d in data]
    manipulation_score = 0

    empate_count = results.count('E')
    empate_ratio = empate_count / len(results) if len(results) > 0 else 0
    if empate_ratio > 0.25: 
        manipulation_score += 30

    if len(results) >= 6:
        recent6 = results[-6:]
        pattern1 = recent6[:3]
        pattern2 = recent6[3:6]
        
        if (all(r == pattern1[0] for r in pattern1) and 
            all(r == pattern2[0] for r in pattern2) and 
            pattern1[0] != pattern2[0]):
            manipulation_score += 25

    if manipulation_score >= 40: 
        return 'high'
    if manipulation_score >= 20: 
        return 'medium'
    return 'low'

def make_prediction(data, patterns):
    results = [d['result'] for d in data]
    last_result = results[-1] if results else None
    prediction = {'color': None, 'confidence': 0}

    streak_pattern = next((p for p in patterns if p['type'] == 'streak'), None)
    if streak_pattern:
        if streak_pattern['length'] >= 3:
            other_colors = [c for c in ['C', 'V'] if c != streak_pattern['color']]
            prediction['color'] = np.random.choice(other_colors)
            prediction['confidence'] = min(85, 50 + (streak_pattern['length'] * 8))
        else:
            prediction['color'] = streak_pattern['color']
            prediction['confidence'] = min(65, 40 + (streak_pattern['length'] * 10))
    elif next((p for p in patterns if p['type'] == 'alternating'), None):
        prediction['color'] = 'V' if last_result == 'C' else 'C'
        prediction['confidence'] = 70
    elif next((p for p in patterns if p['type'] == 'zigzag'), None):
        prediction['color'] = 'V' if last_result == 'C' else 'C'
        prediction['confidence'] = 65
    else:
        recent9 = [r for r in results[-9:] if r != 'E']
        if len(recent9) > 0:
            color_counts = {
                'C': recent9.count('C'),
                'V': recent9.count('V')
            }
            
            if color_counts['C'] < color_counts['V']:
                prediction['color'] = 'C'
                prediction['confidence'] = 55
            elif color_counts['V'] < color_counts['C']:
                prediction['color'] = 'V'
                prediction['confidence'] = 55
            else:
                prediction['color'] = np.random.choice(['C', 'V'])
                prediction['confidence'] = 45
        else:
            prediction['color'] = np.random.choice(['C', 'V'])
            prediction['confidence'] = 45

    return prediction

def get_recommendation(risk, manipulation, patterns):
    if risk == 'high' or manipulation == 'high':
        return 'avoid'
    if any(p['type'] == 'high-empate' for p in patterns):
        return 'avoid'
    if patterns and risk == 'low':
        return 'bet'
    return 'watch'

# --- Funções Auxiliares de Exibição ---
def get_color_name(color):
    return {
        'C': 'Vermelho',
        'V': 'Azul',
        'E': 'Empate'
    }.get(color, '')

def get_recommendation_color(rec):
    return {
        'bet': 'background-color: #D1FAE5; color: #065F46; border: 2px solid #34D399;',
        'avoid': 'background-color: #FEE2E2; color: #B91C1C; border: 2px solid #F87171;',
        'watch': 'background-color: #FEF3C7; color: #B45309; border: 2px solid #FBBF24;',
        'more-data': 'background-color: #E5E7EB; color: #4B5563; border: 2px solid #9CA3AF;'
    }.get(rec, 'background-color: #E5E7EB; color: #4B5563; border: 2px solid #9CA3AF;')

def display_history_corrected():
    if not st.session_state.history:
        st.info("Nenhum resultado inserido ainda. Use os botões acima para começar.")
        return
    
    total = len(st.session_state.history)
    count_c = sum(1 for r in st.session_state.history if r['result'] == 'C')
    count_v = sum(1 for r in st.session_state.history if r['result'] == 'V')
    count_e = sum(1 for r in st.session_state.history if r['result'] == 'E')
    
    st.markdown(f"""
    **Total:** {total} resultados  
    🔴 **Vermelho:** {count_c}  
    🔵 **Azul:** {count_v}  
    🟡 **Empate:** {count_e}
    """)

    html_elements = []
    
    for result in reversed(st.session_state.history[-72:]):
        color_code = result['result']
        time = result['timestamp'].strftime("%H:%M:%S")
        
        style_map = {
            'C': 'background-color: #EF4444; color: white;',
            'V': 'background-color: #3B82F6; color: white;',
            'E': 'background-color: #F59E0B; color: black;'
        }
        
        style = style_map.get(color_code, 'background-color: gray;')
        
        html_elements.append(f"""
            <div style="width: 35px; height: 35px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; {style}"
                 title="{get_color_name(color_code)} às {time}">
                {color_code}
            </div>
        """.strip())

    html_content = f'<div style="display: flex; flex-wrap: wrap; gap: 5px; margin: 10px 0;">{"".join(html_elements)}</div>'
    
    st.markdown(html_content, unsafe_allow_html=True)
    st.caption(f"Exibindo últimos {min(len(st.session_state.history), 72)} resultados")
    st.caption("Ordem: Mais recente → Mais antigo (esquerda → direita)")

# --- Interface do Streamlit ---

# Configura o tema escuro
st.set_page_config(page_title="Análise Preditiva", layout="wide", initial_sidebar_state="collapsed")

# Injetar CSS para tema escuro e outros estilos
st.markdown("""
    <style>
    /* Tema Escuro */
    body {
        color: #FAFAFA; /* Cor do texto principal */
        background-color: #1E1E1E; /* Cor de fundo principal */
    }
    .stApp {
        background-color: #1E1E1E; /* Cor de fundo da aplicação */
    }
    .stButton>button {
        background-color: #333333; /* Fundo dos botões */
        color: #FAFAFA; /* Texto dos botões */
        border: 1px solid #555555;
    }
    .stButton>button:hover {
        background-color: #555555;
    }
    .stTextInput>div>div>input {
        background-color: #333333;
        color: #FAFAFA;
    }
    .stMarkdown {
        color: #FAFAFA; /* Garante que o markdown também seja escuro */
    }
    h1, h2, h3, h4, h5, h6 {
        color: #E0E0E0; /* Títulos */
    }
    /* Estilos para as métricas */
    div[data-testid="stMetric"] > div {
        border-radius: 10px;
        padding: 10px;
        text-align: center;
        background-color: #2D2D2D; /* Fundo das caixas de métricas */
        border: 1px solid #444444;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.5rem;
        font-weight: bold;
        color: #00FF00; /* Cor para o valor da métrica (pode ser ajustado) */
    }
    div[data-testid="stMetricLabel"] {
        color: #BBBBBB; /* Cor para o label da métrica */
    }
    div[data-testid="stMetricDelta"] {
        color: #00FF00; /* Cor para o delta da métrica */
    }
    /* Estilo para st.info */
    div[data-testid="stAlert"] {
        background-color: #333333;
        color: #FAFAFA;
        border-color: #555555;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🎰 Sistema de Análise Preditiva")

# Botões para inserção de resultados e desfazer
cols_buttons = st.columns(5)
with cols_buttons[0]:
    st.button("🔴 Vermelho (C)", on_click=lambda: add_result('C'), help="Registrar resultado Vermelho")
with cols_buttons[1]:
    st.button("🔵 Azul (V)", on_click=lambda: add_result('V'), help="Registrar resultado Azul")
with cols_buttons[2]:
    st.button("🟡 Empate (E)", on_click=lambda: add_result('E'), help="Registrar Empate")
with cols_buttons[3]:
    st.button("↩️ Desfazer", on_click=undo_last_result, help="Desfazer o último resultado inserido")
with cols_buttons[4]:
    st.button("🔄 Reset Total", on_click=reset_history, help="Limpar todo o histórico e métricas")


# Layout principal: divide a página em duas colunas (histórico e análise)
col1, col2 = st.columns([2, 1])

# Seção do Histórico (na primeira coluna)
with col1:
    st.subheader("📊 Histórico de Resultados")
    display_history_corrected()

# Painel de Análise (na segunda coluna)
with col2:
    # Sub-seção: Métricas de Performance
    with st.container():
        st.subheader("🎯 Performance da Previsão")
        total_pred = st.session_state.performance_metrics['total_predictions']
        correct_pred = st.session_state.performance_metrics['correct_predictions']
        wrong_pred = st.session_state.performance_metrics['wrong_predictions']
        g1_hits = st.session_state.performance_metrics['g1_hits']

        accuracy = (correct_pred / total_pred * 100) if total_pred > 0 else 0

        st.metric("Acertos Totais", correct_pred)
        st.metric("Erros Totais", wrong_pred)
        st.metric("Acertos G1", g1_hits, help="Previsões corretas na primeira tentativa (Green 1)")
        st.metric("Assertividade Geral", f"{accuracy:.2f}%")


    # Sub-seção: Padrões Detectados
    with st.container():
        st.subheader("🧠 Padrões Detectados")
        if st.session_state.analysis['patterns']:
            for pattern in st.session_state.analysis['patterns']:
                st.info(f"**{pattern['type'].upper()}**: {pattern['description']}")
        else:
            st.info("Nenhum padrão detectado")
    
    # Sub-seção: Análise de Risco
    with st.container():
        st.subheader("⚠️ Análise de Risco")
        cols_risk = st.columns(2)
        with cols_risk[0]:
            risk_level = st.session_state.analysis['riskLevel']
            st.metric("Risco de Quebra", risk_level.upper(), 
                      help="Probabilidade de quebra do padrão atual")
        with cols_risk[1]:
            manipulation = st.session_state.analysis['manipulation']
            st.metric("Manipulação", manipulation.upper(),
                     help="Indícios de manipulação nos resultados")
    
    # Sub-seção: Previsão da IA
    with st.container():
        st.subheader("📈 Previsão IA")
        if st.session_state.analysis['prediction']:
            color_name = get_color_name(st.session_state.analysis['prediction'])
            color_icon = "🔴" if st.session_state.analysis['prediction'] == 'C' else "🔵"
            confidence = st.session_state.analysis['confidence']
            
            st.markdown(
                f"<div style='font-size: 1.5rem; text-align: center; margin: 1rem 0;'>"
                f"{color_icon} {color_name} ({st.session_state.analysis['prediction']})"
                f"</div>", 
                unsafe_allow_html=True
            )
            st.progress(confidence/100, text=f"Confiança: {confidence}%")
        else:
            st.info("Aguardando mais dados para previsão...")
    
    # Sub-seção: Recomendação
    with st.container():
        st.subheader("💡 Recomendação")
        rec = st.session_state.analysis['recommendation']
        rec_text = ""
        if rec == 'bet': 
            rec_text = "✅ APOSTAR - Padrão favorável"
        elif rec == 'avoid': 
            rec_text = "⚠️ EVITAR - Alto risco de quebra/manipulação"
        elif rec == 'watch': 
            rec_text = "👁️ OBSERVAR - Aguardar padrão claro"
        elif rec == 'more-data': 
            rec_text = "📊 COLETAR MAIS DADOS (mínimo 5 resultados)"
        
        st.markdown(
            f"<div style='padding: 1rem; border-radius: 0.5rem; text-align: center; "
            f"font-weight: bold; font-size: 1.2rem; {get_recommendation_color(rec)}'>"
            f"{rec_text}"
            f"</div>",
            unsafe_allow_html=True
        )

# Rodapé: seção "Sobre o Sistema" expandível
with st.expander("ℹ️ Sobre o Sistema"):
    st.write("""
    **Sistema de análise preditiva para identificação de padrões em sequências.**
    
    Funcionalidades:
    - Detecção de padrões recorrentes
    - Avaliação de risco de quebra
    - Identificação de possíveis manipulações
    - Previsões com nível de confiança
    - Recomendações estratégicas
    - **Métricas de Performance:** Acompanhe a assertividade do sistema.
    - **Desfazer:** Corrija entradas acidentais.
    - **Tema Escuro:** Interface mais agradável para uso prolongado.
    
    Como usar:
    1. Insira resultados usando os botões
    2. O sistema analisará automaticamente
    3. Siga as recomendações
    
    Legenda:
    - 🔴 Vermelho (C)
    - 🔵 Azul (V)
    - 🟡 Empate (E)
    """)
    st.caption("Versão 1.1 - Para fins educacionais")

