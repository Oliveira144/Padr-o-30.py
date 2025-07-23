import streamlit as st
import numpy as np
from datetime import datetime
from collections import defaultdict, Counter

# --- Inicialização do estado da sessão ---
if 'history' not in st.session_state: # CORRIGIDO: de 'not not' para 'not in'
    st.session_state.history = []
    
if 'analysis' not in st.session_state: # CORRIGIDO: de 'not not' para 'not in'
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
if 'performance_metrics' not in st.session_state: # CORRIGIDO: de 'not not' para 'not in'
    st.session_state.performance_metrics = {
        'total_predictions': 0,
        'correct_predictions': 0,
        'wrong_predictions': 0,
        'g1_hits': 0 
    }

# --- Funções de Manipulação de Dados ---

def add_result(result):
    if st.session_state.analysis['prediction'] is not None and len(st.session_state.history) >= 4:
        predicted_color = st.session_state.analysis['prediction']
        
        st.session_state.performance_metrics['total_predictions'] += 1
        
        if predicted_color == result:
            st.session_state.performance_metrics['correct_predictions'] += 1
            if st.session_state.analysis['recommendation'] == 'bet': # G1 mais restrito à recomendação 'bet'
                st.session_state.performance_metrics['g1_hits'] += 1
        else:
            st.session_state.performance_metrics['wrong_predictions'] += 1

    st.session_state.history.append({
        'result': result,
        'timestamp': datetime.now(),
        'prediction_at_time': st.session_state.analysis['prediction'],
        'recommendation_at_time': st.session_state.analysis['recommendation'] # Armazenar recomendação também
    })
    analyze_data(st.session_state.history)

def reset_history():
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
        'g1_hits': 0
    }

def undo_last_result():
    if st.session_state.history:
        # Removendo o último item
        removed_item = st.session_state.history.pop()
        
        # Lógica para reverter as métricas de performance (melhorada)
        if removed_item['prediction_at_time'] is not None and removed_item['recommendation_at_time'] == 'bet':
            # Só reverte se a entrada anterior gerou uma previsão válida e uma recomendação 'bet'
            if st.session_state.performance_metrics['total_predictions'] > 0:
                st.session_state.performance_metrics['total_predictions'] -= 1
            if removed_item['prediction_at_time'] == removed_item['result']:
                if st.session_state.performance_metrics['correct_predictions'] > 0:
                    st.session_state.performance_metrics['correct_predictions'] -= 1
                if st.session_state.performance_metrics['g1_hits'] > 0: # Assumindo G1 é para 'bet'
                    st.session_state.performance_metrics['g1_hits'] -= 1
            else:
                if st.session_state.performance_metrics['wrong_predictions'] > 0:
                    st.session_state.performance_metrics['wrong_predictions'] -= 1
        
        analyze_data(st.session_state.history)
    else:
        st.warning("Não há resultados para desfazer.")

# --- NÚCLEO DE ANÁLISE PREDITIVA INTELIGENTE ---

# Orquestrador da análise
def analyze_data(data):
    if len(data) < 5:
        st.session_state.analysis = {
            'patterns': [],
            'riskLevel': 'low',
            'manipulation': 'low',
            'prediction': None,
            'confidence': 0,
            'recommendation': 'more-data',
            'prediction_reason': 'Poucos dados para análise.'
        }
        return

    recent = data[-30:] # Usar mais dados recentes para análise de padrões e tendências
    all_results = [d['result'] for d in data]

    # 1. Detecção de Padrões Aprimorada
    patterns = detect_patterns(recent)
    pattern_strengths = calculate_pattern_strength(patterns, all_results) # Nova função

    # 2. Análise de Probabilidades Condicionais (Inteligência Central)
    # Tenta prever o próximo resultado baseado nos N resultados anteriores
    conditional_probs = get_conditional_probabilities(all_results, lookback=3) # Lookback ajustável

    # 3. Avaliação de Risco e Manipulação (com ajustes)
    risk_level = assess_risk(recent)
    manipulation = detect_manipulation(recent)

    # 4. Previsão Inteligente
    prediction_info = make_smarter_prediction(all_results, pattern_strengths, conditional_probs, risk_level, manipulation) # Nova função

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
    strengths = {}
    total_results = len(all_results)
    
    # Pesos base para diferentes tipos de padrões
    base_weights = {
        'streak': 0.7,
        'alternating': 0.6,
        '2x2': 0.5,
        'high-empate': 0.8, # Empate é um forte sinal
        'zigzag': 0.4
    }

    for p in patterns:
        strength = base_weights.get(p['type'], 0.1) # Padrão desconhecido tem peso baixo

        if p['type'] == 'streak':
            # Sequências mais longas têm mais força (mas também mais risco de quebra)
            strength *= (p['length'] / 5) if p['length'] <= 5 else 1.0 # Normaliza até 5, acima disso, força total
            
            # Se a sequência for MUITO longa (ex: > 6), ela pode indicar quebra iminente
            if p['length'] >= 6:
                strength *= 1.2 # Maior força para a previsão de QUEBRA
        
        # Outros ajustes de força para outros padrões podem ser adicionados aqui

        strengths[p['type']] = strength
    return strengths

# Função para obter probabilidades condicionais (Cadeia de Markov simplificada)
# Calcula a probabilidade do próximo resultado dado os N resultados anteriores
def get_conditional_probabilities(history_list, lookback=3):
    transitions = defaultdict(lambda: defaultdict(int))
    outcomes = defaultdict(int)

    # Constrói as transições
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
    prediction = {'color': None, 'confidence': 0, 'reason': 'Aguardando mais dados ou sem padrão claro.'}
    
    current_state = tuple(all_results[-3:]) # Pega os 3 últimos resultados para o estado
    
    # 1. Prioridade: Previsão baseada em Probabilidades Condicionais (mais inteligente)
    if current_state in conditional_probs and sum(conditional_probs[current_state].values()) > 0: # Verifica se há histórico para este estado
        # Obter a cor com a maior probabilidade para o estado atual
        most_likely_color = None
        max_prob = 0.0
        
        # Filtrar apenas C e V para decisão primária, E se tiver alta prob.
        filtered_probs = {k: v for k, v in conditional_probs[current_state].items() if k in ['C', 'V']}
        
        if filtered_probs:
            most_likely_color = max(filtered_probs, key=filtered_probs.get)
            max_prob = filtered_probs[most_likely_color]

            # Ajusta a confiança com base na probabilidade e no histórico
            prediction['color'] = most_likely_color
            prediction['confidence'] = int(max_prob * 100) # Probabilidade direta como confiança
            prediction['reason'] = f'Baseado na alta probabilidade condicional após {current_state}.'

            # Se a probabilidade de Empate for alta para este estado, considerar
            if 'E' in conditional_probs[current_state] and conditional_probs[current_state]['E'] > 0.3: # Ex: mais de 30% de chance de Empate
                if conditional_probs[current_state]['E'] > max_prob: # Se empate for mais provável que C/V
                    prediction['color'] = 'E'
                    prediction['confidence'] = int(conditional_probs[current_state]['E'] * 100)
                    prediction['reason'] = f'Alta probabilidade de Empate após {current_state}.'
        
        # Considerar desvio se a confiança for muito baixa para a cor principal (ex: menos de 40%)
        if prediction['confidence'] < 40 and len(all_results) >= 5:
            # Fallback para padrões gerais ou estatística se a previsão condicional for fraca
            pass # Deixa que a próxima etapa (padrões) tente melhorar

    # 2. Refinamento/Fallback para Padrões Detectados (se previsão condicional não for forte ou clara)
    if prediction['confidence'] < 60: # Se a previsão condicional não for muito confiável
        last_result = all_results[-1] if all_results else None

        # Lógica para Padrão de Sequência (Streak)
        streak_pattern_info = next((p for p in st.session_state.analysis['patterns'] if p['type'] == 'streak'), None)
        if streak_pattern_info and streak_pattern_info['length'] >= 2:
            current_color = streak_pattern_info['color']
            streak_length = streak_pattern_info['length']
            strength = pattern_strengths.get('streak', 0.0)

            if streak_length >= 5: # Sequências muito longas (5+), forte indício de quebra
                other_colors = [c for c in ['C', 'V'] if c != current_color]
                if other_colors:
                    prediction['color'] = np.random.choice(other_colors)
                    prediction['confidence'] = min(90, 70 + (streak_length * 4)) # Alta confiança para quebra
                    prediction['reason'] = f'Forte indício de quebra de sequência ({streak_length}x {get_color_name(current_color)}).'
            elif streak_length >= 3: # Sequências médias (3-4), ainda com tendência a quebrar, mas menos certeza
                other_colors = [c for c in ['C', 'V'] if c != current_color]
                if other_colors:
                    prediction['color'] = np.random.choice(other_colors)
                    prediction['confidence'] = min(80, 55 + (streak_length * 5))
                    prediction['reason'] = f'Potencial quebra de sequência ({streak_length}x {get_color_name(current_color)}).'
            else: # Sequências curtas (2), tendem a continuar
                prediction['color'] = current_color
                prediction['confidence'] = min(70, 45 + (streak_length * 10))
                prediction['reason'] = f'Continuação de sequência curta ({streak_length}x {get_color_name(current_color)}).'
            
            # Aplica a força do padrão à confiança
            prediction['confidence'] = int(prediction['confidence'] * strength)


        # Outros padrões (Alternância, 2x2, ZigZag) - se não houver previsão de streak forte
        if prediction['confidence'] < 70: # Se a previsão da streak não for superconfiante
            if next((p for p in st.session_state.analysis['patterns'] if p['type'] == 'alternating'), None):
                prediction['color'] = 'V' if last_result == 'C' else 'C'
                prediction['confidence'] = int(75 * pattern_strengths.get('alternating', 0.0))
                prediction['reason'] = 'Continuação de padrão alternado.'
            elif next((p for p in st.session_state.analysis['patterns'] if p['type'] == 'zigzag'), None):
                prediction['color'] = 'V' if last_result == 'C' else 'C'
                prediction['confidence'] = int(70 * pattern_strengths.get('zigzag', 0.0))
                prediction['reason'] = 'Continuação de padrão ZigZag.'
            elif next((p for p in st.session_state.analysis['patterns'] if p['type'] == '2x2'), None):
                # Se o último foi C C V V, prevê V (continua o bloco)
                if len(all_results) >= 2 and all_results[-1] == all_results[-2]:
                    prediction['color'] = all_results[-1]
                else: # Se o último foi V V C C, prevê C
                    prediction['color'] = 'V' if last_result == 'C' else 'C'
                prediction['confidence'] = int(65 * pattern_strengths.get('2x2', 0.0))
                prediction['reason'] = 'Continuação de padrão 2x2.'

    # 3. Considerar Empate com Alta Frequência (pode sobrescrever outras previsões se for muito forte)
    if 'high-empate' in pattern_strengths:
        empate_strength = pattern_strengths['high-empate']
        if empate_strength > 0.7 and prediction['confidence'] < 80: # Se empate for MUITO forte
            prediction['color'] = 'E'
            prediction['confidence'] = min(95, int(empate_strength * 100))
            prediction['reason'] = 'Alta frequência de empates detectada.'
    
    # 4. Fallback: Análise estatística simples (se nada acima gerar alta confiança)
    if prediction['color'] is None or prediction['confidence'] < 50:
        recent_non_empate = [r for r in all_results[-12:] if r != 'E'] # Mais dados para estatística simples
        if len(recent_non_empate) > 0:
            color_counts = Counter(recent_non_empate)
            
            if color_counts['C'] < color_counts['V']:
                prediction['color'] = 'C'
                prediction['confidence'] = 55
                prediction['reason'] = 'Tendência de equalização (menos Vermelhos recentes).'
            elif color_counts['V'] < color_counts['C']:
                prediction['color'] = 'V'
                prediction['confidence'] = 55
                prediction['reason'] = 'Tendência de equalização (menos Azuis recentes).'
            else:
                prediction['color'] = np.random.choice(['C', 'V'])
                prediction['confidence'] = 45
                prediction['reason'] = 'Frequência de cores equilibrada, previsão aleatória.'
        else:
            prediction['color'] = np.random.choice(['C', 'V', 'E']) # Inclui E no chute
            prediction['confidence'] = 30
            prediction['reason'] = 'Sem dados suficientes ou padrões claros para previsão.'

    return prediction

# Ajuste no assess_risk para ser mais sensível
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

    if max_streak >= 6: # Sequência muito perigosa
        risk_score += 80
    elif max_streak >= 5: 
        risk_score += 60
    elif max_streak >= 4: 
        risk_score += 40
    elif max_streak >= 3: 
        risk_score += 20

    empate_streak = 0
    for i in range(len(results)-1, -1, -1):
        if results[i] == 'E':
            empate_streak += 1
        else:
            break
            
    if empate_streak >= 2: 
        risk_score += 35 # Maior impacto para sequências de empate
    if empate_streak >= 3:
        risk_score += 50 # Risco muito alto para 3+ empates seguidos

    # Avalia a variabilidade: Se as cores se alternam muito rapidamente (muita volatilidade)
    alternating_count = 0
    for i in range(len(results) - 1):
        if results[i] != results[i+1] and results[i] != 'E' and results[i+1] != 'E':
            alternating_count += 1
    if len(results) > 5 and (alternating_count / (len(results) - 1)) > 0.7: # Mais de 70% de alternância
        risk_score += 25 # Indica um ambiente mais imprevisível
        
    if risk_score >= 70: # Limiar para HIGH
        return 'high'
    if risk_score >= 40: # Limiar para MEDIUM
        return 'medium'
    return 'low'

# Ajuste no detect_manipulation (mais sensível a padrões suspeitos)
def detect_manipulation(data):
    results = [d['result'] for d in data]
    manipulation_score = 0

    empate_count = results.count('E')
    empate_ratio = empate_count / len(results) if len(results) > 0 else 0
    if empate_ratio > 0.30: # Mais de 30% de empates no histórico recente
        manipulation_score += 40
    elif empate_ratio > 0.20:
        manipulation_score += 20

    if len(results) >= 6:
        recent6 = results[-6:]
        pattern1 = recent6[:3]
        pattern2 = recent6[3:6]
        
        if (all(r == pattern1[0] for r in pattern1) and 
            all(r == pattern2[0] for r in pattern2) and 
            pattern1[0] != pattern2[0]):
            manipulation_score += 35 # Aumenta o peso

    # Padrão de 1x1x1x... por muito tempo (muito previsível para ser natural)
    if len(results) >= 8:
        if all(results[i] != results[i+1] for i in range(len(results)-1)):
            manipulation_score += 30 # Alta alternância pode ser forçada

    if manipulation_score >= 50: # Limiar para HIGH
        return 'high'
    if manipulation_score >= 25: # Limiar para MEDIUM
        return 'medium'
    return 'low'

# Ajuste no get_recommendation (mais cautelosa com risco/manipulação)
def get_recommendation(risk, manipulation, patterns, prediction_confidence):
    # Se o risco ou manipulação forem altos, a recomendação é evitar
    if risk == 'high' or manipulation == 'high':
        return 'avoid'
    # Se houver alta frequência de empates, também é recomendado evitar
    if any(p['type'] == 'high-empate' for p in patterns) and risk in ['medium', 'high']:
        return 'avoid'
    
    # Se a confiança da previsão for baixa, melhor observar
    if prediction_confidence < 55: # Pode ajustar este limiar
        return 'watch'

    # Se houver padrões e o risco for baixo, a recomendação é apostar
    if patterns and risk == 'low' and prediction_confidence >= 60:
        return 'bet'
    
    # Se o risco for médio, e a confiança da previsão for razoável, pode ser 'watch'
    if risk == 'medium' and prediction_confidence >= 55:
        return 'watch'

    # Caso contrário, a recomendação é observar
    return 'watch'


# --- Funções Auxiliares de Exibição (sem alterações significativas) ---
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
        'more-data': 'background-color: #E5E7EB; color: #4B5563; borde
