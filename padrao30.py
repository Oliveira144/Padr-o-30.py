import streamlit as st
import numpy as np
from datetime import datetime
from collections import Counter
import math
from scipy import stats
import random

# Inicialização do estado da sessão (inalterado)
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

# Funções auxiliares (inalteradas)
def add_result(result):
    st.session_state.history.append({
        'result': result,
        'timestamp': datetime.now()
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
        'recommendation': 'watch'
    }

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

# Núcleo de análise preditiva (estrutura mantida, lógica interna aprimorada)
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

    recent = data[-27:]  # Janela de análise aumentada para capturar mais padrões
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
        'recommendation': get_recommendation(risk_level, manipulation, prediction['confidence'])
    }

# Camada 1: Detecção de padrões com algoritmos avançados
def detect_patterns(data):
    patterns = []
    results = [d['result'] for d in data]
    
    if not results:
        return patterns

    # Análise de entropia para detectar aleatoriedade
    entropy = calculate_entropy(results)
    if entropy > 0.9:
        patterns.append({
            'type': 'high-entropy',
            'description': f'Alta aleatoriedade detectada (entropia: {entropy:.2f})'
        })

    # Detecção de padrões ocultos usando Markov
    markov_patterns = detect_markov_patterns(results)
    patterns.extend(markov_patterns)

    # Detecção de ciclos usando autocorrelação
    cycle_patterns = detect_cycles(results)
    patterns.extend(cycle_patterns)

    # Padrões tradicionais (mantidos para compatibilidade)
    patterns.extend(detect_basic_patterns(results))
    
    # Padrões quânticos simulados (não lineares)
    quantum_patterns = detect_quantum_patterns(results)
    patterns.extend(quantum_patterns)

    return patterns

def detect_basic_patterns(results):
    basic_patterns = []
    # Sequências repetidas
    current_streak = 1
    current_color = results[-1]
    for i in range(len(results)-2, -1, -1):
        if results[i] == current_color:
            current_streak += 1
        else:
            break

    if current_streak >= 2:
        basic_patterns.append({
            'type': 'streak',
            'color': current_color,
            'length': current_streak,
            'description': f'{current_streak}x {get_color_name(current_color)} seguidas'
        })

    # Alternância
    if len(results) >= 4:
        alternating = all(results[i] != results[i+1] for i in range(len(results)-4, len(results)-1))
        if alternating:
            basic_patterns.append({
                'type': 'alternating',
                'description': 'Padrão alternado detectado'
            })

    # Padrões 2x2
    if len(results) >= 4:
        last4 = results[-4:]
        if last4[0] == last4[1] and last4[2] == last4[3] and last4[0] != last4[2]:
            basic_patterns.append({
                'type': '2x2',
                'description': 'Padrão 2x2 detectado'
            })
            
    # Padrões com empates
    if len(results) >= 5:
        last5 = results[-5:]
        if last5.count('E') >= 3:
            basic_patterns.append({
                'type': 'high-empate',
                'description': 'Alta frequência de empates'
            })
            
    # Padrão ZigZag
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
            basic_patterns.append({
                'type': 'zigzag',
                'color': last5[4],
                'description': 'Padrão ZigZag detectado'
            })
    
    return basic_patterns

def calculate_entropy(sequence):
    counts = Counter(sequence)
    probs = [count/len(sequence) for count in counts.values()]
    return -sum(p * math.log2(p) for p in probs)

def detect_markov_patterns(results, order=2):
    patterns = []
    if len(results) < order + 1:
        return patterns
    
    # Matriz de transição de Markov
    transitions = {}
    for i in range(len(results) - order):
        state = tuple(results[i:i+order])
        next_state = results[i+order]
        
        if state not in transitions:
            transitions[state] = {'C': 0, 'V': 0, 'E': 0}
        transitions[state][next_state] += 1
    
    # Analisar transições significativas
    current_state = tuple(results[-order:])
    if current_state in transitions:
        total = sum(transitions[current_state].values())
        if total > 0:
            for color, count in transitions[current_state].items():
                prob = count / total
                if prob > 0.7:  # Probabilidade significativa
                    patterns.append({
                        'type': f'markov-{order}',
                        'color': color,
                        'description': f'Padrão Markov (ordem {order}): {prob*100:.1f}% para {get_color_name(color)}'
                    })
    
    return patterns

def detect_cycles(results):
    patterns = []
    if len(results) < 8:
        return patterns
    
    # Converter para valores numéricos para análise
    numeric = [1 if r == 'C' else (-1 if r == 'V' else 0) for r in results]
    
    # Autocorrelação para detectar ciclos
    max_lag = min(10, len(numeric)//2)
    autocorr = []
    for lag in range(1, max_lag+1):
        corr = np.corrcoef(numeric[:-lag], numeric[lag:])[0,1]
        if not np.isnan(corr):
            autocorr.append((lag, corr))
    
    # Identificar ciclos significativos
    significant_lags = [lag for lag, corr in autocorr if abs(corr) > 0.5]
    for lag in significant_lags:
        patterns.append({
            'type': 'cycle',
            'length': lag,
            'description': f'Ciclo detectado (tamanho {lag})'
        })
    
    return patterns

def detect_quantum_patterns(results):
    patterns = []
    if len(results) < 6:
        return patterns
    
    # Simulação de superposição quântica
    recent = results[-6:]
    c_probs = []
    v_probs = []
    
    for i in range(len(recent)-1):
        if recent[i] == 'C':
            c_probs.append(1.0)
            v_probs.append(0.0)
        elif recent[i] == 'V':
            c_probs.append(0.0)
            v_probs.append(1.0)
        else:  # Empate cria superposição
            c_probs.append(0.5)
            v_probs.append(0.5)
    
    # Efeito de interferência quântica
    c_interference = sum(c_probs) / len(c_probs)
    v_interference = sum(v_probs) / len(v_probs)
    
    if abs(c_interference - v_interference) > 0.3:
        dominant = 'C' if c_interference > v_interference else 'V'
        patterns.append({
            'type': 'quantum-interference',
            'color': dominant,
            'description': f'Padrão quântico dominante: {get_color_name(dominant)}'
        })
    
    return patterns

# Camada 2: Avaliação de risco aprimorada
def assess_risk(data):
    results = [d['result'] for d in data]
    if not results:
        return 'low'
    
    risk_score = 0
    
    # 1. Análise de entropia
    entropy = calculate_entropy(results)
    if entropy < 0.5:
        risk_score += 30  # Padrões muito definidos têm maior risco de quebra
    
    # 2. Análise de distribuição
    c_count = results.count('C')
    v_count = results.count('V')
    e_count = results.count('E')
    total = len(results)
    
    imbalance = abs(c_count - v_count) / (total - e_count) if (total - e_count) > 0 else 0
    if imbalance > 0.4:
        risk_score += 40
    
    # 3. Teste de aleatoriedade (Runs Test)
    try:
        numeric_results = [1 if r == 'C' else (2 if r == 'V' else 3) for r in results]
        z_score, p_value = stats.runstest_1samp(numeric_results)
        if p_value < 0.05:  # Não aleatório
            risk_score += 20
    except:
        pass
    
    # 4. Sequências extremas
    max_streak = calculate_max_streak(results)
    if max_streak >= 5:
        risk_score += min(50, max_streak * 10)
    
    # 5. Empates consecutivos
    empate_streak = calculate_empate_streak(results)
    if empate_streak >= 2:
        risk_score += empate_streak * 15
    
    # Mapeamento final do risco
    if risk_score >= 70:
        return 'high'
    elif risk_score >= 40:
        return 'medium'
    return 'low'

def calculate_max_streak(results):
    if not results:
        return 0
    
    max_streak = 1
    current_streak = 1
    current_color = results[0]
    
    for i in range(1, len(results)):
        if results[i] == current_color and results[i] != 'E':
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 1
            current_color = results[i]
    
    return max_streak

def calculate_empate_streak(results):
    if not results:
        return 0
    
    max_streak = 0
    current_streak = 0
    
    for result in results:
        if result == 'E':
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 0
    
    return max_streak

# Camada 3: Detecção de manipulação avançada
def detect_manipulation(data):
    results = [d['result'] for d in data]
    if not results:
        return 'low'
    
    manipulation_score = 0
    
    # 1. Análise de frequência de empates
    e_ratio = results.count('E') / len(results)
    if e_ratio > 0.25:
        manipulation_score += min(40, e_ratio * 100)
    
    # 2. Padrões anti-naturais (sequências perfeitas demais)
    if len(results) >= 10:
        perfect_alternating = all(results[i] != results[i+1] for i in range(len(results)-10, len(results)-1))
        if perfect_alternating:
            manipulation_score += 30
    
    # 3. Mudanças bruscas de padrão
    if len(results) >= 8:
        first_half = results[-8:-4]
        second_half = results[-4:]
        
        first_c = first_half.count('C')
        first_v = first_half.count('V')
        second_c = second_half.count('C')
        second_v = second_half.count('V')
        
        if (first_c - first_v) * (second_c - second_v) < 0:  # Inversão completa
            manipulation_score += 25
    
    # 4. Distribuição temporal de empates
    e_positions = [i for i, r in enumerate(results) if r == 'E']
    if len(e_positions) >= 3:
        intervals = [e_positions[i+1] - e_positions[i] for i in range(len(e_positions)-1)]
        if np.std(intervals) < 1.0:  # Empates muito regulares
            manipulation_score += 30
    
    # 5. Teste de Benford para resultados (adaptado)
    if len(results) >= 20:
        first_digits = [int(str(i)[0]) for i in range(len(results)) if results[i] != 'E']
        digit_counts = Counter(first_digits)
        benford_law = {1: 0.301, 2: 0.176, 3: 0.125, 4: 0.097, 5: 0.079, 6: 0.067, 7: 0.058, 8: 0.051, 9: 0.046}
        
        chi_square = 0
        for d in range(1, 10):
            expected = benford_law[d] * len(first_digits)
            observed = digit_counts.get(d, 0)
            if expected > 0:
                chi_square += (observed - expected)**2 / expected
        
        if chi_square > 15:  # Desvio significativo
            manipulation_score += 35
    
    # Mapeamento final
    if manipulation_score >= 65:
        return 'high'
    elif manipulation_score >= 35:
        return 'medium'
    return 'low'

# Camada de previsão multi-nível
def make_prediction(data, patterns):
    results = [d['result'] for d in data]
    if not results:
        return {'color': None, 'confidence': 0}
    
    last_result = results[-1]
    
    # Previsões por nível (9 camadas)
    predictions = []
    weights = []
    
    # Nível 1: Análise de Markov
    markov_pred = markov_prediction(results)
    predictions.append(markov_pred['color'])
    weights.append(markov_pred['confidence'] * 0.15)
    
    # Nível 2: Análise de entropia
    entropy_pred = entropy_prediction(results)
    predictions.append(entropy_pred['color'])
    weights.append(entropy_pred['confidence'] * 0.10)
    
    # Nível 3: Padrões detectados
    pattern_pred = pattern_based_prediction(results, patterns)
    predictions.append(pattern_pred['color'])
    weights.append(pattern_pred['confidence'] * 0.20)
    
    # Nível 4: Análise de ciclos
    cycle_pred = cycle_based_prediction(results)
    predictions.append(cycle_pred['color'])
    weights.append(cycle_pred['confidence'] * 0.15)
    
    # Nível 5: Análise de tendências
    trend_pred = trend_analysis_prediction(results)
    predictions.append(trend_pred['color'])
    weights.append(trend_pred['confidence'] * 0.10)
    
    # Nível 6: Simulação quântica
    quantum_pred = quantum_simulation_prediction(results)
    predictions.append(quantum_pred['color'])
    weights.append(quantum_pred['confidence'] * 0.10)
    
    # Nível 7: Análise de risco
    risk_pred = risk_based_prediction(results)
    predictions.append(risk_pred['color'])
    weights.append(risk_pred['confidence'] * 0.10)
    
    # Nível 8: Meta-análise
    meta_pred = meta_analysis_prediction(results)
    predictions.append(meta_pred['color'])
    weights.append(meta_pred['confidence'] * 0.05)
    
    # Nível 9: Random Forest simulado
    rf_pred = simulated_rf_prediction(results)
    predictions.append(rf_pred['color'])
    weights.append(rf_pred['confidence'] * 0.05)
    
    # Combinação ponderada das previsões
    c_score, v_score = 0, 0
    total_weight = sum(weights)
    
    for i in range(len(predictions)):
        if predictions[i] == 'C':
            c_score += weights[i]
        elif predictions[i] == 'V':
            v_score += weights[i]
    
    if total_weight > 0:
        c_prob = c_score / total_weight
        v_prob = v_score / total_weight
        
        if abs(c_prob - v_prob) < 0.1:  # Empate técnico
            final_color = last_result if last_result in ['C', 'V'] else random.choice(['C', 'V'])
            confidence = max(c_prob, v_prob) * 100 * 0.7  # Reduz confiança em empates
        else:
            final_color = 'C' if c_prob > v_prob else 'V'
            confidence = max(c_prob, v_prob) * 100
    else:
        final_color = random.choice(['C', 'V'])
        confidence = 50
    
    # Ajuste final baseado em manipulação detectada
    manipulation = detect_manipulation(data)
    if manipulation == 'high':
        confidence *= 0.7  # Reduz confiança se manipulação alta
    elif manipulation == 'medium':
        confidence *= 0.85
    
    return {
        'color': final_color,
        'confidence': min(95, max(5, int(confidence)))  # Limites de 5% a 95%
    }

# Algoritmos de previsão por nível
def markov_prediction(results, order=2):
    if len(results) < order + 1:
        return {'color': random.choice(['C', 'V']), 'confidence': 50}
    
    # Matriz de transição de Markov
    transitions = {}
    for i in range(len(results) - order):
        state = tuple(results[i:i+order])
        next_state = results[i+order]
        
        if state not in transitions:
            transitions[state] = {'C': 0, 'V': 0, 'E': 0}
        transitions[state][next_state] += 1
    
    # Prever com base no estado atual
    current_state = tuple(results[-order:])
    if current_state in transitions:
        total = sum(transitions[current_state].values())
        if total > 0:
            c_prob = transitions[current_state]['C'] / total
            v_prob = transitions[current_state]['V'] / total
            e_prob = transitions[current_state]['E'] / total
            
            if c_prob > v_prob and c_prob > e_prob:
                return {'color': 'C', 'confidence': int(c_prob * 80 + 20)}  # Escala ajustada
            elif v_prob > c_prob and v_prob > e_prob:
                return {'color': 'V', 'confidence': int(v_prob * 80 + 20)}
    
    # Padrão não reconhecido - usar tendência geral
    c_count = results.count('C')
    v_count = results.count('V')
    
    if c_count > v_count:
        return {'color': 'V', 'confidence': 55}  # Tendência de reversão
    elif v_count > c_count:
        return {'color': 'C', 'confidence': 55}
    return {'color': random.choice(['C', 'V']), 'confidence': 50}

def entropy_prediction(results):
    entropy = calculate_entropy(results)
    
    if entropy > 0.9:  # Alto grau de aleatoriedade
        return {'color': random.choice(['C', 'V']), 'confidence': 50}
    elif entropy < 0.5:  # Padrão definido
        last_result = results[-1]
        if last_result == 'E':
            return {'color': random.choice(['C', 'V']), 'confidence': 60}
        
        # Continuar padrão com confiança baseada na entropia
        return {'color': last_result, 'confidence': int((1 - entropy) * 70 + 30)}
    else:  # Meio-termo
        c_count = results.count('C')
        v_count = results.count('V')
        
        if c_count > v_count:
            return {'color': 'V', 'confidence': 60}  # Reversão para média
        else:
            return {'color': 'C', 'confidence': 60}

def pattern_based_prediction(results, patterns):
    if not patterns:
        return {'color': random.choice(['C', 'V']), 'confidence': 50}
    
    # Priorizar certos tipos de padrões
    priority_patterns = ['quantum-interference', 'markov-3', 'cycle', 'streak']
    for p_type in priority_patterns:
        for pattern in patterns:
            if pattern['type'] == p_type:
                if 'color' in pattern:
                    return {'color': pattern['color'], 'confidence': 70}
                elif p_type == 'streak' and pattern['length'] >= 3:
                    return {'color': 'V' if pattern['color'] == 'C' else 'C', 'confidence': 65}
    
    # Padrões secundários
    for pattern in patterns:
        if pattern['type'] == 'alternating':
            last_result = results[-1]
            return {'color': 'V' if last_result == 'C' else 'C', 'confidence': 65}
        elif pattern['type'] == 'zigzag':
            last_result = results[-1]
            return {'color': 'V' if last_result == 'C' else 'C', 'confidence': 60}
        elif pattern['type'] == '2x2':
            last2 = results[-2:]
            if len(set(last2)) == 1:
                return {'color': 'V' if last2[0] == 'C' else 'C', 'confidence': 60}
    
    # Padrão não reconhecido
    return {'color': random.choice(['C', 'V']), 'confidence': 50}

def cycle_based_prediction(results):
    if len(results) < 8:
        return {'color': random.choice(['C', 'V']), 'confidence': 50}
    
    # Converter para valores numéricos
    numeric = [1 if r == 'C' else (-1 if r == 'V' else 0) for r in results]
    
    # Autocorrelação para detectar ciclos
    max_lag = min(5, len(numeric)//2)
    best_lag = None
    best_corr = 0
    
    for lag in range(1, max_lag+1):
        corr = np.corrcoef(numeric[:-lag], numeric[lag:])[0,1]
        if not np.isnan(corr) and abs(corr) > abs(best_corr):
            best_corr = corr
            best_lag = lag
    
    if best_lag and abs(best_corr) > 0.4:
        # Prever baseado no ciclo detectado
        cycle_values = numeric[-best_lag:]
        pred_value = np.mean(cycle_values)
        pred_color = 'C' if pred_value > 0 else 'V'
        return {'color': pred_color, 'confidence': int((abs(best_corr) * 70) + 30)}
    
    return {'color': random.choice(['C', 'V']), 'confidence': 50}

def trend_analysis_prediction(results):
    if len(results) < 5:
        return {'color': random.choice(['C', 'V']), 'confidence': 50}
    
    # Remover empates para análise de tendência
    filtered = [r for r in results if r != 'E']
    if len(filtered) < 3:
        return {'color': random.choice(['C', 'V']), 'confidence': 50}
    
    # Converter para série numérica
    series = [1 if r == 'C' else -1 for r in filtered]
    
    # Calcular tendência linear
    x = np.arange(len(series))
    slope, _, _, _, _ = stats.linregress(x, series)
    
    if slope > 0.05:  # Tendência de alta para C
        return {'color': 'C', 'confidence': 65}
    elif slope < -0.05:  # Tendência de alta para V
        return {'color': 'V', 'confidence': 65}
    else:  # Sem tendência clara
        last_result = filtered[-1]
        return {'color': 'V' if last_result == 'C' else 'C', 'confidence': 55}

def quantum_simulation_prediction(results):
    if len(results) < 6:
        return {'color': random.choice(['C', 'V']), 'confidence': 50}
    
    recent = results[-6:]
    c_probs = []
    v_probs = []
    
    for i in range(len(recent)-1):
        if recent[i] == 'C':
            c_probs.append(1.0)
            v_probs.append(0.0)
        elif recent[i] == 'V':
            c_probs.append(0.0)
            v_probs.append(1.0)
        else:  # Empate cria superposição
            c_probs.append(0.5)
            v_probs.append(0.5)
    
    # Efeito de interferência quântica
    c_interference = sum(c_probs) / len(c_probs)
    v_interference = sum(v_probs) / len(v_probs)
    
    if abs(c_interference - v_interference) > 0.3:
        dominant = 'C' if c_interference > v_interference else 'V'
        return {'color': dominant, 'confidence': 70}
    else:
        return {'color': random.choice(['C', 'V']), 'confidence': 50}

def risk_based_prediction(results):
    risk = assess_risk([{'result': r} for r in results])
    
    if risk == 'high':
        # Em alto risco, prever quebra de padrão
        last_result = results[-1]
        if last_result in ['C', 'V']:
            return {'color': 'V' if last_result == 'C' else 'C', 'confidence': 65}
    elif risk == 'medium':
        # Risco médio - prever continuação com menor confiança
        last_result = results[-1]
        if last_result in ['C', 'V']:
            return {'color': last_result, 'confidence': 55}
    
    return {'color': random.choice(['C', 'V']), 'confidence': 50}

def meta_analysis_prediction(results):
    if len(results) < 10:
        return {'color': random.choice(['C', 'V']), 'confidence': 50}
    
    # Análise de múltiplas janelas temporais
    windows = [
        results[-10:],  # Curto prazo
        results[-20:],  # Médio prazo
        results[-30:]   # Longo prazo
    ]
    
    predictions = []
    for window in windows:
        c_count = window.count('C')
        v_count = window.count('V')
        
        if c_count > v_count:
            predictions.append('V')  # Reversão para média
        else:
            predictions.append('C')
    
    # Votação majoritária
    c_pred = predictions.count('C')
    v_pred = predictions.count('V')
    
    if c_pred > v_pred:
        return {'color': 'C', 'confidence': 60}
    elif v_pred > c_pred:
        return {'color': 'V', 'confidence': 60}
    else:
        return {'color': random.choice(['C', 'V']), 'confidence': 50}

def simulated_rf_prediction(results):
    if len(results) < 15:
        return {'color': random.choice(['C', 'V']), 'confidence': 50}
    
    # Simulação simplificada de Random Forest
    features = [
        results.count('C') - results.count('V'),  # Diferença C-V
        calculate_max_streak(results),           # Maior sequência
        results[-1] == results[-2],              # Últimos iguais?
        results.count('E'),                      # Número de empates
        calculate_entropy(results)               # Entropia
    ]
    
    # "Árvores de decisão" simuladas
    tree1 = 'C' if features[0] < -2 else 'V'
    tree2 = 'C' if features[1] >= 4 else 'V'
    tree3 = 'C' if features[2] else 'V'
    tree4 = 'V' if features[3] > 3 else 'C'
    tree5 = 'C' if features[4] < 0.7 else 'V'
    
    predictions = [tree1, tree2, tree3, tree4, tree5]
    c_count = predictions.count('C')
    v_count = predictions.count('V')
    
    if c_count > v_count:
        return {'color': 'C', 'confidence': 60 + (c_count - v_count) * 5}
    else:
        return {'color': 'V', 'confidence': 60 + (v_count - c_count) * 5}

# Recomendação baseada em múltiplos fatores
def get_recommendation(risk, manipulation, confidence):
    if risk == 'high' or manipulation == 'high':
        return 'avoid'
    elif confidence >= 70:
        return 'bet'
    elif confidence >= 55:
        return 'watch'
    else:
        return 'more-data'

# Interface do usuário (totalmente mantida)
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

# Interface Streamlit (inalterada)
st.set_page_config(page_title="Análise Preditiva", layout="wide")
st.title("🎰 Sistema de Análise Preditiva")

cols = st.columns(4)
with cols[0]:
    st.button("🔴 Vermelho (C)", on_click=lambda: add_result('C'), help="Registrar resultado Vermelho")
with cols[1]:
    st.button("🔵 Azul (V)", on_click=lambda: add_result('V'), help="Registrar resultado Azul")
with cols[2]:
    st.button("🟡 Empate (E)", on_click=lambda: add_result('E'), help="Registrar Empate")
with cols[3]:
    st.button("🔄 Reset", on_click=reset_history, help="Limpar histórico")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📊 Histórico de Resultados")
    display_history_corrected()

with col2:
    with st.container():
        st.subheader("🧠 Padrões Detectados")
        if st.session_state.analysis['patterns']:
            for pattern in st.session_state.analysis['patterns']:
                st.info(f"**{pattern['type'].upper()}**: {pattern['description']}")
        else:
            st.info("Nenhum padrão detectado")
    
    with st.container():
        st.subheader("⚠️ Análise de Risco")
        cols = st.columns(2)
        with cols[0]:
            risk_level = st.session_state.analysis['riskLevel']
            st.metric("Risco de Quebra", risk_level.upper(), 
                      help="Probabilidade de quebra do padrão atual")
        with cols[1]:
            manipulation = st.session_state.analysis['manipulation']
            st.metric("Manipulação", manipulation.upper(),
                     help="Indícios de manipulação nos resultados")
    
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

with st.expander("ℹ️ Sobre o Sistema"):
    st.write("""
    **Sistema de análise preditiva para identificação de padrões em sequências.**
    
    Funcionalidades:
    - Detecção de padrões recorrentes
    - Avaliação de risco de quebra
    - Identificação de possíveis manipulações
    - Previsões com nível de confiança
    - Recomendações estratégicas
    
    Como usar:
    1. Insira resultados usando os botões
    2. O sistema analisará automaticamente
    3. Siga as recomendações
    
    Legenda:
    - 🔴 Vermelho (C)
    - 🔵 Azul (V)
    - 🟡 Empate (E)
    """)
    st.caption("Versão 2.0 - Inteligência Avançada - Para fins educacionais")

st.markdown("""
    <style>
    div[data-testid="stMetric"] > div {
        border-radius: 10px;
        padding: 10px;
        text-align: center;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.5rem;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)
