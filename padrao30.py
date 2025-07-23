import streamlit as st
import numpy as np
from datetime import datetime
from collections import defaultdict, Counter
import math # Importar para logaritmo ou outras operações matemáticas

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
        'recommendation': 'watch',
        'prediction_reason': '' # Nova informação: motivo da previsão
    }

# Estado para métricas de performance (mantido do anterior)
if 'performance_metrics' not in st.session_state:
    st.session_state.performance_metrics = {
        'total_predictions': 0,
        'correct_predictions': 0,
        'wrong_predictions': 0,
        'g1_hits': 0,
        'accuracy_history': [], # Para registrar a acurácia ao longo do tempo
        'g1_accuracy_history': [] # Acurácia dos G1 hits
    }

# --- Funções Auxiliares ---
def get_color_name(color_code):
    """Retorna o nome completo da cor para exibição."""
    if color_code == 'C':
        return 'Azul'
    elif color_code == 'V':
        return 'Vermelho'
    elif color_code == 'E':
        return 'Empate'
    return 'Desconhecido'

def calculate_accuracy():
    """Calcula a acurácia geral das previsões."""
    if st.session_state.performance_metrics['total_predictions'] == 0:
        return 0
    return (st.session_state.performance_metrics['correct_predictions'] / 
            st.session_state.performance_metrics['total_predictions']) * 100

def calculate_g1_accuracy():
    """Calcula a acurácia das previsões quando a recomendação era 'bet'."""
    # G1 hits são considerados apenas quando a recomendação era 'bet'
    relevant_predictions = [
        item for item in st.session_state.history 
        if item['prediction_at_time'] is not None and item['recommendation_at_time'] == 'bet'
    ]
    
    total_g1_opportunities = len(relevant_predictions)
    
    if total_g1_opportunities == 0:
        return 0
    
    correct_g1_predictions = sum(1 for item in relevant_predictions if item['prediction_at_time'] == item['result'])
    
    return (correct_g1_predictions / total_g1_opportunities) * 100


# --- Funções de Manipulação de Dados ---

def add_result(result):
    """Adiciona um novo resultado ao histórico e dispara a análise."""
    # Validação de entrada para 'result'
    if result not in ['C', 'V', 'E']:
        st.error("Resultado inválido. Por favor, use 'C' (Azul), 'V' (Vermelho) ou 'E' (Empate).")
        return

    # Apenas computa métricas se havia uma previsão ativa e dados suficientes
    if st.session_state.analysis['prediction'] is not None and len(st.session_state.history) >= 4:
        predicted_color = st.session_state.analysis['prediction']
        recommendation = st.session_state.analysis['recommendation']
        
        st.session_state.performance_metrics['total_predictions'] += 1
        
        if predicted_color == result:
            st.session_state.performance_metrics['correct_predictions'] += 1
            if recommendation == 'bet': # G1 mais restrito à recomendação 'bet'
                st.session_state.performance_metrics['g1_hits'] += 1
        else:
            st.session_state.performance_metrics['wrong_predictions'] += 1
            
        # Registrar acurácia após cada nova previsão
        st.session_state.performance_metrics['accuracy_history'].append(calculate_accuracy())
        if recommendation == 'bet':
            st.session_state.performance_metrics['g1_accuracy_history'].append(calculate_g1_accuracy())


    st.session_state.history.append({
        'result': result,
        'timestamp': datetime.now(),
        'prediction_at_time': st.session_state.analysis['prediction'],
        'recommendation_at_time': st.session_state.analysis['recommendation'] # Armazenar recomendação também
    })
    analyze_data(st.session_state.history)

def reset_history():
    """Reseta todo o histórico e o estado da análise."""
    st.session_state.history = []
    st.session_state.analysis = {
        'patterns': [],
        'riskLevel': 'low',
        'manipulation': 'low',
        'prediction': None,
        'confidence': 0,
        'recommendation': 'watch',
        'prediction_reason': ''
    }
    st.session_state.performance_metrics = {
        'total_predictions': 0,
        'correct_predictions': 0,
        'wrong_predictions': 0,
        'g1_hits': 0,
        'accuracy_history': [],
        'g1_accuracy_history': []
    }
    st.success("Histórico e análises resetados!")

def undo_last_result():
    """Desfaz o último resultado adicionado e reverte as métricas."""
    if st.session_state.history:
        # Removendo o último item
        removed_item = st.session_state.history.pop()
        
        # Lógica para reverter as métricas de performance (melhorada e mais precisa)
        # Só reverte se a entrada anterior gerou uma previsão válida e havia dados suficientes
        if removed_item['prediction_at_time'] is not None and len(st.session_state.history) >= 4: 
            if st.session_state.performance_metrics['total_predictions'] > 0:
                st.session_state.performance_metrics['total_predictions'] -= 1
            
            if removed_item['prediction_at_time'] == removed_item['result']:
                if st.session_state.performance_metrics['correct_predictions'] > 0:
                    st.session_state.performance_metrics['correct_predictions'] -= 1
                if removed_item['recommendation_at_time'] == 'bet' and st.session_state.performance_metrics['g1_hits'] > 0:
                    st.session_state.performance_metrics['g1_hits'] -= 1
            else:
                if st.session_state.performance_metrics['wrong_predictions'] > 0:
                    st.session_state.performance_metrics['wrong_predictions'] -= 1
            
            # Remover a última entrada de acurácia dos históricos
            if st.session_state.performance_metrics['accuracy_history']:
                st.session_state.performance_metrics['accuracy_history'].pop()
            if st.session_state.performance_metrics['g1_accuracy_history'] and removed_item['recommendation_at_time'] == 'bet':
                st.session_state.performance_metrics['g1_accuracy_history'].pop()


        analyze_data(st.session_state.history)
        st.info("Último resultado desfeito.")
    else:
        st.warning("Não há resultados para desfazer.")

# --- NÚCLEO DE ANÁLISE PREDITIVA INTELIGENTE ---

# Função auxiliar para pegar os últimos N resultados
def get_last_n_results(data, n):
    """Retorna os resultados dos últimos N itens do histórico."""
    return [d['result'] for d in data[-n:]]

# Função para detectar padrões
def detect_patterns(data):
    """Detecta padrões específicos nos resultados."""
    patterns = []
    results = [d['result'] for d in data] # Usar todos os dados para padrões de longo prazo, ou ajustar o escopo aqui

    if len(results) < 2:
        return patterns

    # Padrão de Sequência (Streak)
    if len(results) >= 2:
        last_color = results[-1]
        streak_length = 0
        for i in range(len(results) - 1, -1, -1):
            if results[i] == last_color:
                streak_length += 1
            else:
                break
        if streak_length >= 2:
            patterns.append({
                'type': 'streak',
                'color': last_color,
                'length': streak_length,
                'description': f"Sequência de {streak_length}x {get_color_name(last_color)}"
            })

    # Padrão de Alternância (Ex: C V C V C V) - Últimos 6 para ser mais robusto
    if len(results) >= 6:
        is_alternating = True
        # Verifica os últimos 6, pulando Empates
        temp_results = [r for r in results[-6:] if r != 'E']
        if len(temp_results) >= 4: # Pelo menos 4 não-empates para alternância
            for i in range(len(temp_results) - 1):
                if temp_results[i] == temp_results[i+1]:
                    is_alternating = False
                    break
            if is_alternating:
                patterns.append({
                    'type': 'alternating',
                    'description': "Padrão alternado (ex: C V C V C V)"
                })
    
    # Padrão 2x2 (Ex: C C V V C C) - Últimos 4
    if len(results) >= 4:
        last_4 = results[-4:]
        if (last_4[0] == last_4[1] and last_4[2] == last_4[3] and 
            last_4[0] != last_4[2] and 'E' not in last_4):
            patterns.append({
                'type': '2x2',
                'description': "Padrão 2x2 (ex: C C V V)"
            })

    # Padrão ZigZag (Ex: C V V C C V) - Últimos 6
    if len(results) >= 6:
        last_6 = results[-6:]
        # Verifica se há um padrão C V V C C V ou V C C V V C
        if (last_6[0] == last_6[3] and last_6[1] == last_6[4] and last_6[2] == last_6[5] and
            last_6[0] != last_6[1] and last_6[1] == last_6[2] and 'E' not in last_6):
             patterns.append({
                'type': 'zigzag',
                'description': "Padrão ZigZag (ex: C V V C C V)"
            })
        elif (last_6[0] == last_6[2] and last_6[1] == last_6[4] and last_6[0] == last_6[5] and # C V C C V C
              last_6[0] != last_6[1] and 'E' not in last_6):
            patterns.append({
                'type': 'zigzag_complex',
                'description': "Padrão ZigZag Complexo (ex: C V C C V C)"
            })

    # Alta frequência de Empates (em uma janela maior para ser mais robusto)
    empate_count_recent = results[-15:].count('E') # Últimos 15 resultados
    if len(results[-15:]) >= 7 and (empate_count_recent / len(results[-15:])) > 0.35: # Mais de 35% de empates recentes
        patterns.append({
            'type': 'high-empate',
            'description': f"Alta frequência de empates ({empate_count_recent} nos últimos {len(results[-15:])})"
        })
        
    return patterns

# Orquestrador da análise
def analyze_data(data):
    """Orquestra a análise de dados, detecção de padrões, risco e manipulação."""
    if len(data) < 5:
        st.session_state.analysis = {
            'patterns': [],
            'riskLevel': 'low',
            'manipulation': 'low',
            'prediction': None,
            'confidence': 0,
            'recommendation': 'more-data',
            'prediction_reason': 'Poucos dados para análise inicial.'
        }
        return

    # Usar janelas de tempo diferentes para diferentes análises
    recent_short_term = data[-10:] # Para risco/manipulação mais imediata
    recent_medium_term = data[-30:] # Para padrões mais gerais e probabilidades condicionais
    all_results = [d['result'] for d in data]

    # 1. Detecção de Padrões
    patterns = detect_patterns(all_results) # Usar todos os dados para detectar padrões
    pattern_strengths = calculate_pattern_strength(patterns, all_results)

    # 2. Análise de Probabilidades Condicionais (Inteligência Central)
    conditional_probs = get_conditional_probabilities(all_results, lookback=3) # Lookback de 3 para um bom equilíbrio

    # 3. Avaliação de Risco e Manipulação (usando dados mais recentes)
    risk_level = assess_risk(recent_short_term)
    manipulation = detect_manipulation(recent_short_term)

    # 4. Previsão Inteligente
    prediction_info = make_smarter_prediction(all_results, pattern_strengths, conditional_probs, risk_level, manipulation)

    # 5. Recomendação Final
    recommendation = get_recommendation(risk_level, manipulation, patterns, prediction_info['confidence'])

    st.session_state.analysis = {
        'patterns': patterns,
        'riskLevel': risk_level,
        'manipulation': manipulation,
        'prediction': prediction_info['color'],
        'confidence': prediction_info['confidence'],
        'recommendation': recommendation,
        'prediction_reason': prediction_info['reason']
    }

# --- Novas Funções e Funções Aprimoradas ---

# Função para dar um "peso" aos padrões
def calculate_pattern_strength(patterns, all_results):
    """Calcula a força (relevância) de cada padrão detectado."""
    strengths = {}
    
    # Pesos base para diferentes tipos de padrões (ajustados)
    base_weights = {
        'streak': 0.7,
        'alternating': 0.8, # Alternância forte
        '2x2': 0.6,
        'high-empate': 0.9, # Empate é um forte sinal, especialmente em jogos que buscam "resetar"
        'zigzag': 0.5,
        'zigzag_complex': 0.5
    }

    for p in patterns:
        strength = base_weights.get(p['type'], 0.1) # Padrão desconhecido tem peso baixo

        if p['type'] == 'streak':
            # Sequências mais longas podem indicar quebra iminente, ou uma tendência muito forte
            if p['length'] >= 6: # Muito longa, aumenta a força para PREVER A QUEBRA
                strength = 1.0 # Força máxima para quebra iminente
            elif p['length'] >= 4: # Média, alta chance de continuação ou quebra
                strength *= 0.8
            else: # Curta, maior chance de continuação
                strength *= 0.6
        
        # Outros ajustes de força para outros padrões podem ser adicionados aqui
        
        strengths[p['type']] = strength
    return strengths

# Função para obter probabilidades condicionais (Cadeia de Markov simplificada)
# Calcula a probabilidade do próximo resultado dado os N resultados anteriores
def get_conditional_probabilities(history_list, lookback=3):
    """Calcula probabilidades condicionais do próximo resultado baseadas em estados anteriores."""
    transitions = defaultdict(lambda: defaultdict(int))
    outcomes = defaultdict(int)

    # Constrói as transições
    if len(history_list) < lookback + 1: # Precisa de pelo menos lookback + 1 resultados para uma transição
        return defaultdict(lambda: Counter())

    for i in range(len(history_list) - lookback):
        state = tuple(history_list[i : i + lookback])
        next_result = history_list[i + lookback]
        transitions[state][next_result] += 1
        outcomes[state] += 1
    
    # Calcula as probabilidades
    probabilities = defaultdict(lambda: Counter()) # Guarda contagens, para calcular probabilidade depois
    for state, counts in transitions.items():
        total = sum(counts.values())
        if total > 0:
            for next_res, count in counts.items():
                probabilities[state][next_res] = count / total
    
    return probabilities

# Previsão Inteligente que combina lógica e probabilidades
def make_smarter_prediction(all_results, pattern_strengths, conditional_probs, risk_level, manipulation_level):
    """Realiza a previsão inteligente combinando probabilidades, padrões e níveis de risco/manipulação."""
    prediction = {'color': None, 'confidence': 0, 'reason': 'Analisando dados...'}
    
    if len(all_results) < 3: # Precisa de pelo menos 3 para um estado de lookback=3
        prediction['reason'] = 'Poucos resultados para análise preditiva avançada.'
        return prediction

    current_state = tuple(all_results[-3:]) # Pega os 3 últimos resultados para o estado
    last_result = all_results[-1]

    # Prioridade 1: Manipulação (se for alta, parar de prever)
    if manipulation_level == 'high':
        prediction['color'] = None
        prediction['confidence'] = 0
        prediction['reason'] = 'ALTO NÍVEL DE MANIPULAÇÃO DETECTADO. NÃO RECOMENDADO APOSTAR.'
        return prediction

    # Prioridade 2: Previsão baseada em Probabilidades Condicionais (mais inteligente)
    if current_state in conditional_probs:
        state_probs = conditional_probs[current_state]
        
        # Filtra para C e V, mas mantendo Empate para avaliação posterior
        most_likely_color = None
        max_prob = 0.0
        
        # Prioriza C/V se houver boa probabilidade
        filtered_cv_probs = {k: v for k, v in state_probs.items() if k in ['C', 'V']}
        if filtered_cv_probs:
            most_likely_color = max(filtered_cv_probs, key=filtered_cv_probs.get)
            max_prob = filtered_cv_probs[most_likely_color]
            
            prediction['color'] = most_likely_color
            prediction['confidence'] = int(max_prob * 100)
            prediction['reason'] = f'Alta probabilidade condicional para {get_color_name(most_likely_color)} após {current_state}.'
        
        # Avalia Empate: Se a probabilidade de Empate for significativamente alta, pode sobrescrever
        empate_prob = state_probs.get('E', 0.0)
        if empate_prob > 0.35 and empate_prob > max_prob + 0.1: # Empate tem que ser bem mais provável
            prediction['color'] = 'E'
            prediction['confidence'] = min(95, int(empate_prob * 100))
            prediction['reason'] = f'Probabilidade muito alta de Empate ({int(empate_prob*100)}%) após {current_state}.'
        
        # Reduz confiança se o risco for médio/alto, mesmo com boa prob.
        if risk_level == 'medium':
            prediction['confidence'] = int(prediction['confidence'] * 0.8)
            prediction['reason'] += ' (Risco médio)'
        elif risk_level == 'high':
            prediction['confidence'] = int(prediction['confidence'] * 0.5)
            prediction['reason'] += ' (ALTO RISCO)'

    # Prioridade 3: Refinamento/Fallback para Padrões Detectados (se previsão condicional não for forte ou clara)
    # Aplica-se se a confiança da previsão condicional for baixa ou se não houver estado registrado
    if prediction['confidence'] < 60: 
        
        streak_pattern_info = next((p for p in st.session_state.analysis['patterns'] if p['type'] == 'streak'), None)
        if streak_pattern_info:
            current_color = streak_pattern_info['color']
            streak_length = streak_pattern_info['length']
            strength = pattern_strengths.get('streak', 0.0)

            if streak_length >= 6: # Sequências muito longas (6+), forte indício de quebra
                other_colors = [c for c in ['C', 'V'] if c != current_color]
                if other_colors:
                    prediction['color'] = np.random.choice(other_colors) # Escolhe aleatoriamente a cor oposta
                    prediction['confidence'] = min(90, 75 + (streak_length - 5) * 5) # Alta confiança para quebra
                    prediction['reason'] = f'Forte indício de quebra de sequência ({streak_length}x {get_color_name(current_color)}).'
                else: # Em caso de sequência de Empate, prevê C ou V
                    prediction['color'] = np.random.choice(['C', 'V'])
                    prediction['confidence'] = min(80, 60 + (streak_length - 5) * 5)
                    prediction['reason'] = f'Sequência de Empate longa, prevendo C ou V.'

            elif streak_length >= 3: # Sequências médias (3-5), maior chance de continuação, mas olho na quebra
                prediction['color'] = current_color
                prediction['confidence'] = min(70, 50 + (streak_length * 5))
                prediction['reason'] = f'Continuação provável de sequência ({streak_length}x {get_color_name(current_color)}).'
            
            # Ajusta a confiança final pela força do padrão
            prediction['confidence'] = int(prediction['confidence'] * strength)


        # Outros padrões (Alternância, 2x2, ZigZag) - se não houver previsão de streak forte
        if prediction['confidence'] < 60: # Se a previsão da streak não for superconfiante ou não existir
            if next((p for p in st.session_state.analysis['patterns'] if p['type'] == 'alternating'), None):
                prediction['color'] = 'V' if last_result == 'C' else 'C'
                prediction['confidence'] = int(75 * pattern_strengths.get('alternating', 0.0))
                prediction['reason'] = 'Continuação de padrão alternado (C V C V).'
            elif next((p for p in st.session_state.analysis['patterns'] if p['type'] == 'zigzag_complex'), None):
                prediction['color'] = 'V' if last_result == 'C' else 'C' # Pode ser ajustado conforme a complexidade do zigzag
                prediction['confidence'] = int(70 * pattern_strengths.get('zigzag_complex', 0.0))
                prediction['reason'] = 'Continuação de padrão ZigZag Complexo.'
            elif next((p for p in st.session_state.analysis['patterns'] if p['type'] == 'zigzag'), None):
                prediction['color'] = 'V' if last_result == 'C' else 'C' # Pode ser ajustado conforme o zigzag
                prediction['confidence'] = int(65 * pattern_strengths.get('zigzag', 0.0))
                prediction['reason'] = 'Continuação de padrão ZigZag.'
            elif next((p for p in st.session_state.analysis['patterns'] if p['type'] == '2x2'), None):
                # Se os dois últimos resultados são iguais (ex: C C V V), prevê a mudança para o bloco oposto.
                if len(all_results) >= 2 and all_results[-1] == all_results[-2]:
                    prediction['color'] = 'V' if last_result == 'C' else 'C' # Se C C, prevê V; se V V, prevê C
                    prediction['reason'] = 'Padrão 2x2: Prevendo mudança de bloco.'
                else: # Se os dois últimos são diferentes (ex: C V ou V C), implica que um bloco já terminou.
                      # Prevê a continuação do bloco que acabou de começar, ou a próxima cor no ciclo.
                    prediction['color'] = 'V' if last_result == 'V' else 'C' # Se V C, prevê C; se C V, prevê V
                    prediction['reason'] = 'Padrão 2x2: Prevendo continuação do bloco atual.'

                prediction['confidence'] = int(60 * pattern_strengths.get('2x2', 0.0))

    # Prioridade 4: Empate com Alta Frequência (pode sobrescrever outras previsões se for muito forte)
    if 'high-empate' in pattern_strengths and pattern_strengths['high-empate'] > 0.6: # Limiar alto
        empate_strength = pattern_strengths['high-empate']
        # Se a confiança da previsão atual não for super alta, e empate for forte
        if prediction['confidence'] < 85: 
            prediction['color'] = 'E'
            prediction['confidence'] = min(95, int(empate_strength * 100))
            prediction['reason'] = 'ALERTA: Alta frequência de empates, forte indicativo de empate.'
    
    # Prioridade 5: Fallback: Análise estatística simples (se nada acima gerar alta confiança)
    if prediction['color'] is None or prediction['confidence'] < 50:
        recent_non_empate = [r for r in all_results[-15:] if r != 'E'] # Mais dados para estatística simples
        if len(recent_non_empate) > 0:
            color_counts = Counter(recent_non_empate)
            
            if color_counts['C'] < color_counts['V']:
                prediction['color'] = 'C'
                prediction['confidence'] = 50
                prediction['reason'] = 'Tendência de equalização: Azul em menor frequência.'
            elif color_counts['V'] < color_counts['C']:
                prediction['color'] = 'V'
                prediction['confidence'] = 50
                prediction['reason'] = 'Tendência de equalização: Vermelho em menor frequência.'
            else:
                prediction['color'] = np.random.choice(['C', 'V'])
                prediction['confidence'] = 40
                prediction['reason'] = 'Frequência de cores equilibrada, previsão aleatória (C/V).'
        else: # Se só tem empate ou poucos dados de C/V
            prediction['color'] = np.random.choice(['C', 'V', 'E'])
            prediction['confidence'] = 25
            prediction['reason'] = 'Dados insuficientes ou apenas empates, previsão aleatória.'

    return prediction

# Ajuste no assess_risk para ser mais sensível
def assess_risk(data):
    """Avalia o nível de risco do ambiente de jogo com base nos resultados recentes."""
    results = [d['result'] for d in data]
    risk_score = 0

    # Risco por Sequência Extrema
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

    if max_streak >= 7: # Sequência extremamente perigosa
        risk_score += 100
    elif max_streak >= 6: 
        risk_score += 80
    elif max_streak >= 5: 
        risk_score += 50
    elif max_streak >= 4: 
        risk_score += 25

    # Risco por Sequência de Empate
    empate_streak = 0
    for i in range(len(results)-1, -1, -1):
        if results[i] == 'E':
            empate_streak += 1
        else:
            break
            
    if empate_streak >= 3: 
        risk_score += 60 # Muito alto para 3+ empates seguidos
    elif empate_streak >= 2:
        risk_score += 30 

    # Risco por Volatilidade (alternância rápida)
    alternating_count = 0
    for i in range(len(results) - 1):
        if results[i] != results[i+1] and results[i] != 'E' and results[i+1] != 'E':
            alternating_count += 1
    if len(results) > 5 and (alternating_count / (len(results) - 1)) > 0.75: # Mais de 75% de alternância em um curto período
        risk_score += 30 # Indica um ambiente mais imprevisível
        
    # Risco por falta de equilíbrio recente (se uma cor sumiu ou dominou muito)
    if len(results) > 10:
        recent_counts = Counter([r for r in results[-10:] if r != 'E'])
        if len(recent_counts) == 1 and ('C' in recent_counts or 'V' in recent_counts): # Apenas uma cor (C ou V)
            risk_score += 40 # Indica um desequilíbrio forte
        
    if risk_score >= 80:
        return 'high'
    if risk_score >= 50:
        return 'medium'
    return 'low'

# Ajuste no detect_manipulation (mais sensível a padrões suspeitos)
def detect_manipulation(data):
    """Detecta possíveis sinais de manipulação com base em anomalias nos resultados."""
    results = [d['result'] for d in data]
    manipulation_score = 0

    if len(results) < 10: # Precisa de mais dados para detectar manipulação
        return 'low'

    # 1. Anomalia na frequência de cores vs. Empate
    # Se Empate ocorre em uma frequência muito alta ou baixa de repente
    empate_count = results.count('E')
    total_non_empate = len(results) - empate_count
    
    if len(results) > 10:
        empate_ratio = empate_count / len(results)
        # Limiares arbitrários, precisam de calibração
        if empate_ratio > 0.45: # Mais de 45% de empates recentes
            manipulation_score += 60
        elif empate_ratio < 0.05 and total_non_empate > 5: # Quase nenhum empate onde antes havia
             manipulation_score += 30

    # 2. Sequências extremamente longas e incomuns
    # Se uma cor aparece um número "não natural" de vezes seguidas (ex: 8+ vezes)
    max_streak = 0
    if results:
        current_streak = 1
        for i in range(1, len(results)):
            if results[i] == results[i-1]:
                current_streak += 1
            else:
                max_streak = max(max_streak, current_streak)
                current_streak = 1
        max_streak = max(max_streak, current_streak) # Para pegar a última sequência
    
    if max_streak >= 8:
        manipulation_score += 70 # Forte indício
    elif max_streak >= 7:
        manipulation_score += 50

    # 3. Desequilíbrio extremo nas últimas N rodadas (ex: 15 últimas sem C ou V)
    recent_non_empate = [r for r in results[-15:] if r != 'E']
    if len(recent_non_empate) >= 10:
        counts = Counter(recent_non_empate)
        if len(counts) == 1: # Apenas uma cor (C ou V) em 10+ resultados recentes
            manipulation_score += 50
        elif counts['C'] == 0 and counts['V'] > 0: # Só tem V, por exemplo
             manipulation_score += 40
        elif counts['V'] == 0 and counts['C'] > 0: # Só tem C
             manipulation_score += 40

    if manipulation_score >= 90: # Limiar para HIGH
        return 'high'
    if manipulation_score >= 60: # Limiar para MEDIUM
        return 'medium'
    return 'low'

# Função para a recomendação final
def get_recommendation(risk_level, manipulation_level, patterns, confidence):
    """Gera uma recomendação de aposta baseada nos níveis de risco, manipulação, padrões e confiança."""
    if manipulation_level == 'high':
        return 'STOP - Manipulação Detectada!'
    if risk_level == 'high':
        return 'AVISO - Risco Alto, não apostar.'
    if confidence < 50:
        return 'watch' # Baixa confiança, observar mais
    if confidence >= 50 and confidence < 70:
        return 'consider' # Considerar, com cautela
    if confidence >= 70:
        return 'bet' # Boa confiança, recomendar aposta

    return 'watch' # Padrão padrão

# --- Interface do Streamlit ---
st.set_page_config(layout="wide", page_title="Analisador de Padrões de Cores")

st.title("🔮 Analisador Inteligente de Padrões de Cores")
st.markdown("---")

col1, col2, col3 = st.columns(3)

with col1:
    st.header("Entrada de Resultados")
    st.write("Adicione os resultados um por um:")
    
    btn_c = st.button("🔵 Azul (C)", use_container_width=True)
    btn_v = st.button("🔴 Vermelho (V)", use_container_width=True)
    btn_e = st.button("🟡 Empate (E)", use_container_width=True)

    if btn_c:
        add_result('C')
    if btn_v:
        add_result('V')
    if btn_e:
        add_result('E')

    st.markdown("---")
    st.header("Controle")
    st.button("↩️ Desfazer Último", on_click=undo_last_result, use_container_width=True)
    st.button("🗑️ Resetar Histórico", on_click=reset_history, use_container_width=True)

with col2:
    st.header("Previsão e Recomendação")

    analysis = st.session_state.analysis
    
    if analysis['prediction']:
        predicted_color_name = get_color_name(analysis['prediction'])
        st.metric(label="Próxima Previsão", value=f"{predicted_color_name} ({analysis['prediction']})")
        st.metric(label="Confiança", value=f"{analysis['confidence']:.0f}%")
        st.info(f"**Motivo:** {analysis['prediction_reason']}")
    else:
        st.info("Aguardando mais dados para previsão...")
    
    st.markdown("---")
    st.subheader("Recomendação Atual")
    rec_text = analysis['recommendation']
    if rec_text == 'bet':
        st.success(f"**🟢 RECOMENDADO: {rec_text.upper()}** - Oportunidade identificada.")
    elif rec_text == 'consider':
        st.warning(f"**🟠 ATENÇÃO: {rec_text.upper()}** - Considere com cautela.")
    elif rec_text == 'watch' or rec_text == 'more-data':
        st.info(f"**⚪️ OBSERVAR: {rec_text.upper()}** - Analisando ou aguardando mais dados.")
    elif 'RISK' in rec_text.upper() or 'STOP' in rec_text.upper():
        st.error(f"**🔴 PERIGO: {rec_text.upper()}** - Evite apostar agora.")
    else:
        st.write(f"Recomendação: {rec_text}")

    st.markdown("---")
    st.subheader("Níveis de Alerta")
    st.write(f"**Nível de Risco:** :red[{analysis['riskLevel'].upper()}]")
    st.write(f"**Potencial Manipulação:** :orange[{analysis['manipulation'].upper()}]")

with col3:
    st.header("Métricas de Performance")
    perf = st.session_state.performance_metrics

    accuracy = calculate_accuracy()
    g1_accuracy = calculate_g1_accuracy()

    st.metric(label="Acurácia Geral", value=f"{accuracy:.2f}%")
    st.metric(label="Acurácia G1 (Recomendação 'Bet')", value=f"{g1_accuracy:.2f}%")
    st.write(f"Previsões Totais: **{perf['total_predictions']}**")
    st.write(f"Acertos: **{perf['correct_predictions']}**")
    st.write(f"Erros: **{perf['wrong_predictions']}**")
    st.write(f"G1 Hits (Acertos em 'Bet'): **{perf['g1_hits']}**")

    st.markdown("---")
    st.header("Padrões Detectados")
    if analysis['patterns']:
        for p in analysis['patterns']:
            st.code(p['description'], language='text')
    else:
        st.info("Nenhum padrão claro detectado ainda.")

st.markdown("---")
st.header("Histórico de Resultados")

# Exibição do histórico de forma mais organizada e limitada
display_history = st.session_state.history[-20:] # Exibe os últimos 20 resultados
if display_history:
    # Cria uma string com os resultados formatados para melhor visualização
    history_str = " | ".join([
        f"{get_color_name(item['result'])} ({item['result']})"
        for item in display_history
    ])
    st.text_area("Últimos Resultados (20)", history_str, height=100, disabled=True)

    # Exibe em tabela para mais detalhes
    st.subheader("Detalhes do Histórico Completo")
    st.dataframe(
        [
            {
                "Resultado": get_color_name(item['result']),
                "Hora": item['timestamp'].strftime("%H:%M:%S"),
                "Previsão na Hora": get_color_name(item['prediction_at_time']) if item['prediction_at_time'] else "N/A",
                "Recomendação na Hora": item['recommendation_at_time']
            }
            for item in st.session_state.history[::-1] # Inverte para mostrar o mais recente primeiro
        ],
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("Nenhum resultado adicionado ainda.")
