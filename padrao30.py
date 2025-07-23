import streamlit as st
import numpy as np
from datetime import datetime
from collections import defaultdict, Counter
import math # Importar para logaritmo ou outras operações matemáticas

# --- Inicialização do estado da sessão ---
# Garante que o histórico existe e é uma lista vazia se a sessão for nova
if 'history' not in st.session_state:
    st.session_state.history = []
    
# Garante que a análise existe e é um dicionário com valores padrão se a sessão for nova
if 'analysis' not in st.session_state:
    st.session_state.analysis = {
        'patterns': [],
        'riskLevel': 'low',
        'manipulation': 'low',
        'prediction': None,
        'confidence': 0,
        'recommendation': 'watch',
        'prediction_reason': '' # Motivo da previsão para maior assertividade
    }

# Garante que as métricas de performance existem e são um dicionário completo se a sessão for nova
if 'performance_metrics' not in st.session_state:
    st.session_state.performance_metrics = {
        'total_predictions': 0,
        'correct_predictions': 0,
        'wrong_predictions': 0,
        'g1_hits': 0,
        'accuracy_history': [], # Histórico de acurácia para análise constante
        'g1_accuracy_history': [] # Histórico de acurácia de G1 para análise constante
    }

# --- Funções Auxiliares ---
def get_color_name(color_code):
    """Retorna o nome completo da cor para exibição na interface."""
    if color_code == 'C':
        return 'Azul'
    elif color_code == 'V':
        return 'Vermelho'
    elif color_code == 'E':
        return 'Empate'
    return 'Desconhecido'

def calculate_accuracy():
    """Calcula a acurácia geral das previsões feitas."""
    if st.session_state.performance_metrics['total_predictions'] == 0:
        return 0
    return (st.session_state.performance_metrics['correct_predictions'] / 
            st.session_state.performance_metrics['total_predictions']) * 100

def calculate_g1_accuracy():
    """
    Calcula a acurácia das previsões que foram feitas com recomendação 'bet' (G1 hits).
    Considera apenas as oportunidades onde houve uma recomendação de aposta.
    """
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
    """
    Adiciona um novo resultado ao histórico, atualiza as métricas de performance 
    e dispara a reanálise dos dados.
    """
    # Validação de entrada para garantir que o resultado é um dos esperados
    if result not in ['C', 'V', 'E']:
        st.error("Resultado inválido. Por favor, use 'C' (Azul), 'V' (Vermelho) ou 'E' (Empate).")
        return

    # Apenas computa métricas se havia uma previsão ativa e histórico suficiente para considerar
    if st.session_state.analysis['prediction'] is not None and len(st.session_state.history) >= 4:
        predicted_color = st.session_state.analysis['prediction']
        recommendation = st.session_state.analysis['recommendation']
        
        st.session_state.performance_metrics['total_predictions'] += 1
        
        if predicted_color == result:
            st.session_state.performance_metrics['correct_predictions'] += 1
            if recommendation == 'bet': # Incrementa G1 hits apenas se a recomendação era 'bet'
                st.session_state.performance_metrics['g1_hits'] += 1
        else:
            st.session_state.performance_metrics['wrong_predictions'] += 1
            
        # Registrar acurácia após cada nova previsão para análise constante
        st.session_state.performance_metrics['accuracy_history'].append(calculate_accuracy())
        if recommendation == 'bet': # Registrar acurácia G1 apenas se houve oportunidade 'bet'
            st.session_state.performance_metrics['g1_accuracy_history'].append(calculate_g1_accuracy())


    st.session_state.history.append({
        'result': result,
        'timestamp': datetime.now(),
        'prediction_at_time': st.session_state.analysis['prediction'],
        'recommendation_at_time': st.session_state.analysis['recommendation'] # Armazena a recomendação no momento da previsão
    })
    analyze_data(st.session_state.history)

def reset_history():
    """Reseta todo o histórico de resultados, análise e métricas de performance."""
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
    # MUITO IMPORTANTE: Reinicializar COMPLETAMENTE o dicionário performance_metrics
    st.session_state.performance_metrics = {
        'total_predictions': 0,
        'correct_predictions': 0,
        'wrong_predictions': 0,
        'g1_hits': 0,
        'accuracy_history': [],  # Garante que estas listas estejam sempre presentes
        'g1_accuracy_history': [] # Garante que estas listas estejam sempre presentes
    }
    st.success("Histórico e análises resetados!")

def undo_last_result():
    """
    Desfaz o último resultado adicionado, revertendo o histórico, as métricas de performance
    e reanalisando os dados.
    """
    if st.session_state.history:
        removed_item = st.session_state.history.pop() # Remove o último item
        
        # Lógica para reverter as métricas de performance de forma precisa
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
            
            # Remover a última entrada de acurácia dos históricos (para manter a consistência)
            if st.session_state.performance_metrics['accuracy_history']:
                st.session_state.performance_metrics['accuracy_history'].pop()
            if st.session_state.performance_metrics['g1_accuracy_history'] and removed_item['recommendation_at_time'] == 'bet':
                st.session_state.performance_metrics['g1_accuracy_history'].pop()


        analyze_data(st.session_state.history) # Reanalisa com o histórico atualizado
        st.info("Último resultado desfeito.")
    else:
        st.warning("Não há resultados para desfazer.")

# --- NÚCLEO DE ANÁLISE PREDITIVA INTELIGENTE ---

def get_last_n_results(data, n):
    """Retorna os resultados dos últimos N itens do histórico, útil para análises de janela."""
    return [d['result'] for d in data[-n:]]

def detect_patterns(data):
    """
    Detecta padrões específicos nos resultados do histórico.
    Aplica diferentes lógicas para identificar sequências, alternâncias, etc.
    """
    patterns = []
    results = [d['result'] for d in data] # Usa todos os dados para padrões de longo prazo

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

    # Padrão de Alternância (Ex: C V C V C V) - Verifica os últimos 6 para ser mais robusto
    if len(results) >= 6:
        is_alternating = True
        # Filtra empates para não quebrar a lógica de alternância C/V
        temp_results = [r for r in results[-6:] if r != 'E']
        if len(temp_results) >= 4: # Pelo menos 4 não-empates para validar alternância
            for i in range(len(temp_results) - 1):
                if temp_results[i] == temp_results[i+1]: # Se duas cores seguidas são iguais, não é alternância
                    is_alternating = False
                    break
            if is_alternating:
                patterns.append({
                    'type': 'alternating',
                    'description': "Padrão alternado (ex: C V C V C V)"
                })
    
    # Padrão 2x2 (Ex: C C V V C C) - Verifica os últimos 4
    if len(results) >= 4:
        last_4 = results[-4:]
        if (last_4[0] == last_4[1] and last_4[2] == last_4[3] and # Dois pares de cores
            last_4[0] != last_4[2] and 'E' not in last_4): # Pares diferentes e sem empate
            patterns.append({
                'type': '2x2',
                'description': "Padrão 2x2 (ex: C C V V)"
            })

    # Padrão ZigZag (Ex: C V V C C V) - Verifica os últimos 6
    if len(results) >= 6:
        last_6 = results[-6:]
        # Ex: C V V C C V (1 igual ao 4, 2 ao 5, 3 ao 6, mas 1 != 2)
        if (last_6[0] == last_6[3] and last_6[1] == last_6[4] and last_6[2] == last_6[5] and
            last_6[0] != last_6[1] and last_6[1] == last_6[2] and 'E' not in last_6):
             patterns.append({
                'type': 'zigzag',
                'description': "Padrão ZigZag (ex: C V V C C V)"
            })
        # Ex: C V C C V C (1 igual ao 3, 1 igual ao 6, 2 igual ao 4)
        elif (last_6[0] == last_6[2] and last_6[1] == last_6[4] and last_6[0] == last_6[5] and 
              last_6[0] != last_6[1] and 'E' not in last_6):
            patterns.append({
                'type': 'zigzag_complex',
                'description': "Padrão ZigZag Complexo (ex: C V C C V C)"
            })

    # Alta frequência de Empates (em uma janela maior para ser mais robusto)
    empate_count_recent = results[-15:].count('E') # Conta empates nos últimos 15 resultados
    # Se a proporção de empates for alta em um número razoável de resultados
    if len(results[-15:]) >= 7 and (empate_count_recent / len(results[-15:])) > 0.35: # Mais de 35% de empates
        patterns.append({
            'type': 'high-empate',
            'description': f"Alta frequência de empates ({empate_count_recent} nos últimos {len(results[-15:])})"
        })
        
    return patterns

def analyze_data(data):
    """
    Orquestra todas as etapas da análise: detecção de padrões, cálculo de probabilidades,
    avaliação de risco e manipulação, e finalmente a previsão inteligente.
    """
    if len(data) < 5: # Mínimo de dados para começar uma análise significativa
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

    # Define janelas de dados para diferentes tipos de análise
    recent_short_term = data[-10:] # Para risco/manipulação imediata
    recent_medium_term = data[-30:] # Para padrões gerais e probabilidades condicionais (mais profundidade)
    all_results = [d['result'] for d in data] # Todos os resultados para padrões de longo prazo

    # 1. Detecção de Padrões
    patterns = detect_patterns(all_results) 
    pattern_strengths = calculate_pattern_strength(patterns, all_results)

    # 2. Análise de Probabilidades Condicionais (Cadeia de Markov simplificada)
    conditional_probs = get_conditional_probabilities(all_results, lookback=3) # Lookback de 3 para um bom equilíbrio

    # 3. Avaliação de Risco e Manipulação (usando dados mais recentes)
    risk_level = assess_risk(recent_short_term)
    manipulation = detect_manipulation(recent_short_term)

    # 4. Previsão Inteligente
    prediction_info = make_smarter_prediction(all_results, pattern_strengths, conditional_probs, risk_level, manipulation)

    # 5. Recomendação Final
    recommendation = get_recommendation(risk_level, manipulation, patterns, prediction_info['confidence'])

    # Atualiza o estado da sessão com os resultados da análise
    st.session_state.analysis = {
        'patterns': patterns,
        'riskLevel': risk_level,
        'manipulation': manipulation,
        'prediction': prediction_info['color'],
        'confidence': prediction_info['confidence'],
        'recommendation': recommendation,
        'prediction_reason': prediction_info['reason']
    }

def calculate_pattern_strength(patterns, all_results):
    """
    Calcula uma "força" ou peso para cada padrão detectado.
    Isso ajuda a priorizar padrões na hora da previsão.
    """
    strengths = {}
    
    # Pesos base para diferentes tipos de padrões (ajustados para calibração)
    base_weights = {
        'streak': 0.7,
        'alternating': 0.8, # Alternância é um padrão forte
        '2x2': 0.6,
        'high-empate': 0.9, # Empate é um sinal importante, especialmente em "reset" de padrão
        'zigzag': 0.5,
        'zigzag_complex': 0.5
    }

    for p in patterns:
        strength = base_weights.get(p['type'], 0.1) # Padrões desconhecidos têm peso baixo

        if p['type'] == 'streak':
            # Sequências muito longas podem indicar quebra iminente (maior força para prever a QUEBRA)
            if p['length'] >= 6: 
                strength = 1.0 # Força máxima para quebra iminente
            elif p['length'] >= 4: # Sequência média, alta chance de continuação ou quebra
                strength *= 0.8
            else: # Sequência curta, maior chance de continuação
                strength *= 0.6
        
        # Outros ajustes de força podem ser adicionados aqui conforme a observação do jogo
        
        strengths[p['type']] = strength
    return strengths

def get_conditional_probabilities(history_list, lookback=3):
    """
    Calcula probabilidades condicionais do próximo resultado dados os 'lookback' resultados anteriores.
    Usa uma abordagem de Cadeia de Markov simplificada.
    """
    transitions = defaultdict(lambda: defaultdict(int)) # Dicionário de dicionários para contar transições (estado -> próximo resultado)
    outcomes = defaultdict(int) # Conta o total de vezes que um estado ocorreu

    # Constrói as transições
    if len(history_list) < lookback + 1: # Precisa de pelo menos lookback + 1 resultados para formar uma transição válida
        return defaultdict(lambda: Counter())

    for i in range(len(history_list) - lookback):
        state = tuple(history_list[i : i + lookback]) # O estado é a sequência dos 'lookback' resultados anteriores
        next_result = history_list[i + lookback] # O resultado que veio após esse estado
        transitions[state][next_result] += 1
        outcomes[state] += 1
    
    # Calcula as probabilidades
    probabilities = defaultdict(lambda: Counter()) 
    for state, counts in transitions.items():
        total = sum(counts.values())
        if total > 0:
            for next_res, count in counts.items():
                probabilities[state][next_res] = count / total # Probabilidade = (contagem da transição) / (total do estado)
    
    return probabilities

def make_smarter_prediction(all_results, pattern_strengths, conditional_probs, risk_level, manipulation_level):
    """
    Executa a lógica principal de previsão, priorizando diferentes fontes de informação:
    Manipulação > Probabilidades Condicionais > Padrões > Estatística Simples.
    """
    prediction = {'color': None, 'confidence': 0, 'reason': 'Analisando dados...'}
    
    if len(all_results) < 3: # Mínimo de resultados para formar um estado (lookback=3)
        prediction['reason'] = 'Poucos resultados para análise preditiva avançada.'
        return prediction

    current_state = tuple(all_results[-3:]) # Pega os 3 últimos resultados para o estado atual
    last_result = all_results[-1] # O último resultado adicionado

    # Prioridade 1: ALERTA DE MANIPULAÇÃO - Se houver alta manipulação, não prevê, apenas alerta.
    if manipulation_level == 'high':
        prediction['color'] = None
        prediction['confidence'] = 0
        prediction['reason'] = 'ALTO NÍVEL DE MANIPULAÇÃO DETECTADO. NÃO RECOMENDADO APOSTAR AGORA.'
        return prediction

    # Prioridade 2: PREVISÃO POR PROBABILIDADES CONDICIONAIS - A mais inteligente, se houver histórico.
    if current_state in conditional_probs:
        state_probs = conditional_probs[current_state]
        
        most_likely_color = None
        max_prob = 0.0
        
        # Prioriza a previsão de C ou V se houver boa probabilidade
        filtered_cv_probs = {k: v for k, v in state_probs.items() if k in ['C', 'V']}
        if filtered_cv_probs:
            most_likely_color = max(filtered_cv_probs, key=filtered_cv_probs.get)
            max_prob = filtered_cv_probs[most_likely_color]
            
            prediction['color'] = most_likely_color
            prediction['confidence'] = int(max_prob * 100) # Confiança inicial baseada na probabilidade
            prediction['reason'] = f'Alta probabilidade condicional para {get_color_name(most_likely_color)} após {current_state}.'
        
        # Avalia o Empate: Se a probabilidade de Empate for significativamente alta, pode sobrescrever C/V
        empate_prob = state_probs.get('E', 0.0)
        if empate_prob > 0.35 and empate_prob > max_prob + 0.1: # Empate tem que ser bem mais provável que C/V
            prediction['color'] = 'E'
            prediction['confidence'] = min(95, int(empate_prob * 100))
            prediction['reason'] = f'Probabilidade muito alta de Empate ({int(empate_prob*100)}%) após {current_state}.'
        
        # Ajusta a confiança com base no nível de risco geral
        if risk_level == 'medium':
            prediction['confidence'] = int(prediction['confidence'] * 0.8) # Reduz 20% da confiança
            prediction['reason'] += ' (Risco médio no ambiente).'
        elif risk_level == 'high':
            prediction['confidence'] = int(prediction['confidence'] * 0.5) # Reduz 50% da confiança
            prediction['reason'] += ' (ALTO RISCO no ambiente).'

    # Prioridade 3: REFINAMENTO/FALLBACK POR PADRÕES DETECTADOS
    # Só tenta usar padrões se a previsão condicional não foi forte o suficiente (confiança < 60)
    if prediction['confidence'] < 60: 
        
        streak_pattern_info = next((p for p in st.session_state.analysis['patterns'] if p['type'] == 'streak'), None)
        if streak_pattern_info:
            current_color = streak_pattern_info['color']
            streak_length = streak_pattern_info['length']
            strength = pattern_strengths.get('streak', 0.0)

            if streak_length >= 6: # Sequências muito longas (6+), forte indício de QUEBRA
                other_colors = [c for c in ['C', 'V'] if c != current_color]
                if other_colors:
                    prediction['color'] = np.random.choice(other_colors) # Escolhe aleatoriamente a cor oposta
                    prediction['confidence'] = min(90, 75 + (streak_length - 5) * 5) # Alta confiança para quebra
                    prediction['reason'] = f'Forte indício de quebra de sequência ({streak_length}x {get_color_name(current_color)}).'
                else: # Caso a sequência seja de Empate, prevê C ou V como quebra
                    prediction['color'] = np.random.choice(['C', 'V'])
                    prediction['confidence'] = min(80, 60 + (streak_length - 5) * 5)
                    prediction['reason'] = f'Sequência de Empate longa ({streak_length}x), prevendo C ou V.'

            elif streak_length >= 3: # Sequências médias (3-5), maior chance de CONTINUAÇÃO
                prediction['color'] = current_color
                prediction['confidence'] = min(70, 50 + (streak_length * 5))
                prediction['reason'] = f'Continuação provável de sequência ({streak_length}x {get_color_name(current_color)}).'
            
            # Ajusta a confiança final pela força do padrão
            prediction['confidence'] = int(prediction['confidence'] * strength)


        # Outros padrões (Alternância, 2x2, ZigZag) - só se a previsão da streak não for superconfiante
        if prediction['confidence'] < 60: 
            if next((p for p in st.session_state.analysis['patterns'] if p['type'] == 'alternating'), None):
                prediction['color'] = 'V' if last_result == 'C' else 'C' # Alterna a cor
                prediction['confidence'] = int(75 * pattern_strengths.get('alternating', 0.0))
                prediction['reason'] = 'Continuação de padrão alternado (C V C V).'
            elif next((p for p in st.session_state.analysis['patterns'] if p['type'] == 'zigzag_complex'), None):
                # A lógica exata para ZigZag complexo depende do padrão, aqui um chute básico
                prediction['color'] = 'V' if last_result == 'C' else 'C' 
                prediction['confidence'] = int(70 * pattern_strengths.get('zigzag_complex', 0.0))
                prediction['reason'] = 'Continuação de padrão ZigZag Complexo.'
            elif next((p for p in st.session_state.analysis['patterns'] if p['type'] == 'zigzag'), None):
                # A lógica exata para ZigZag depende do padrão, aqui um chute básico
                prediction['color'] = 'V' if last_result == 'C' else 'C' 
                prediction['confidence'] = int(65 * pattern_strengths.get('zigzag', 0.0))
                prediction['reason'] = 'Continuação de padrão ZigZag.'
            elif next((p for p in st.session_state.analysis['patterns'] if p['type'] == '2x2'), None):
                # Padrão 2x2: C C V V (se os dois últimos são iguais, prevê o oposto para quebrar o bloco de 2)
                if len(all_results) >= 2 and all_results[-1] == all_results[-2]:
                    prediction['color'] = 'V' if last_result == 'C' else 'C' 
                    prediction['reason'] = 'Padrão 2x2: Prevendo mudança de bloco.'
                else: # Se os dois últimos são diferentes, significa que um bloco já terminou (ex: C C V), prevê a continuação do bloco oposto (V)
                    prediction['color'] = 'V' if last_result == 'V' else 'C' # Se C V, prevê V; se V C, prevê C
                    prediction['reason'] = 'Padrão 2x2: Prevendo continuação do bloco atual.'

                prediction['confidence'] = int(60 * pattern_strengths.get('2x2', 0.0))

    # Prioridade 4: EMPATE COM ALTA FREQUÊNCIA - Pode sobrescrever outras previsões se for muito forte.
    if 'high-empate' in pattern_strengths and pattern_strengths['high-empate'] > 0.6: # Limiar alto para priorizar
        empate_strength = pattern_strengths['high-empate']
        # Se a confiança da previsão atual não for super alta, e o sinal de empate for forte
        if prediction['confidence'] < 85: 
            prediction['color'] = 'E'
            prediction['confidence'] = min(95, int(empate_strength * 100)) # Confiança alta para empate
            prediction['reason'] = 'ALERTA: Alta frequência de empates detectada, forte indicativo de empate.'
    
    # Prioridade 5: FALLBACK - ANÁLISE ESTATÍSTICA SIMPLES (se nada acima gerar alta confiança)
    if prediction['color'] is None or prediction['confidence'] < 50:
        recent_non_empate = [r for r in all_results[-15:] if r != 'E'] # Analisa as 15 últimas cores (sem empates)
        if len(recent_non_empate) > 0:
            color_counts = Counter(recent_non_empate)
            
            # Tenta prever a cor que está "menos presente" para buscar um equilíbrio
            if color_counts['C'] < color_counts['V']:
                prediction['color'] = 'C'
                prediction['confidence'] = 50
                prediction['reason'] = 'Tendência de equalização: Azul em menor frequência recente.'
            elif color_counts['V'] < color_counts['C']:
                prediction['color'] = 'V'
                prediction['confidence'] = 50
                prediction['reason'] = 'Tendência de equalização: Vermelho em menor frequência recente.'
            else: # Se as frequências C/V estão equilibradas, um chute aleatório
                prediction['color'] = np.random.choice(['C', 'V'])
                prediction['confidence'] = 40
                prediction['reason'] = 'Frequência de cores equilibrada, previsão aleatória (C/V).'
        else: # Se não há resultados C/V suficientes ou só empates
            prediction['color'] = np.random.choice(['C', 'V', 'E']) # Chute completamente aleatório (inclui E)
            prediction['confidence'] = 25
            prediction['reason'] = 'Dados insuficientes ou apenas empates, previsão aleatória.'

    return prediction

def assess_risk(data):
    """
    Avalia o nível de risco do ambiente de jogo com base em padrões de risco, 
    como sequências longas e volatilidade.
    """
    results = [d['result'] for d in data]
    risk_score = 0

    # Risco por Sequência Extrema (cores C/V)
    max_streak = 0
    if results:
        current_streak = 1
        current_color = results[0]
        max_streak = 1 # Inicializa com 1 para o primeiro elemento

        for i in range(1, len(results)):
            if results[i] == current_color:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 1 # Reseta a sequência
                current_color = results[i]
    
    # Adiciona pontos de risco com base no comprimento da sequência máxima
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
    for i in range(len(results)-1, -1, -1): # Começa do fim para pegar a sequência mais recente de empates
        if results[i] == 'E':
            empate_streak += 1
        else:
            break
            
    if empate_streak >= 3: # Muito alto para 3+ empates seguidos
        risk_score += 60 
    elif empate_streak >= 2:
        risk_score += 30 

    # Risco por Volatilidade (alternância muito rápida entre C e V)
    alternating_count = 0
    for i in range(len(results) - 1):
        if results[i] != results[i+1] and results[i] != 'E' and results[i+1] != 'E':
            alternating_count += 1
    if len(results) > 5 and (alternating_count / (len(results) - 1)) > 0.75: # Mais de 75% de alternância em curto período
        risk_score += 30 # Indica um ambiente mais imprevisível e arriscado
        
    # Risco por falta de equilíbrio recente (se uma cor sumiu ou dominou muito nos últimos 10)
    if len(results) > 10:
        recent_counts = Counter([r for r in results[-10:] if r != 'E'])
        if len(recent_counts) == 1 and ('C' in recent_counts or 'V' in recent_counts): # Apenas uma cor (C ou V) em 10+ resultados recentes
            risk_score += 40 # Indica um desequilíbrio forte, potencial para virada ou manipulação
        
    # Define o nível de risco final com base na pontuação acumulada
    if risk_score >= 80:
        return 'high'
    if risk_score >= 50:
        return 'medium'
    return 'low'

def detect_manipulation(data):
    """
    Detecta possíveis sinais de manipulação no jogo com base em anomalias e desequilíbrios.
    """
    results = [d['result'] for d in data]
    manipulation_score = 0

    if len(results) < 10: # Precisa de mais dados para começar a detectar manipulação de forma confiável
        return 'low'

    # 1. Anomalia na frequência de Empates
    empate_count = results.count('E')
    total_non_empate = len(results) - empate_count
    
    if len(results) > 10:
        empate_ratio = empate_count / len(results)
        # Limiares de alerta para proporção de empates (precisam de calibração para o jogo específico)
        if empate_ratio > 0.45: # Mais de 45% de empates recentes é suspeito
            manipulation_score += 60
        elif empate_ratio < 0.05 and total_non_empate > 5: # Quase nenhum empate onde antes havia
             manipulation_score += 30

    # 2. Sequências de cores C/V extremamente longas e incomuns
    max_streak = 0
    if results:
        current_streak = 1
        for i in range(1, len(results)):
            if results[i] == results[i-1]:
                current_streak += 1
            else:
                max_streak = max(max_streak, current_streak)
                current_streak = 1
        max_streak = max(max_streak, current_streak) # Para pegar a última sequência também
    
    if max_streak >= 8: # Sequências de 8+ da mesma cor são altamente suspeitas
        manipulation_score += 70 
    elif max_streak >= 7: # Sequências de 7 da mesma cor já acendem um alerta
        manipulation_score += 50

    # 3. Desequilíbrio extremo nas últimas N rodadas (ex: uma cor completamente ausente)
    recent_non_empate = [r for r in results[-15:] if r != 'E'] # Analisa as 15 últimas sem empates
    if len(recent_non_empate) >= 10:
        counts = Counter(recent_non_empate)
        if len(counts) == 1: # Apenas uma cor (C ou V) em 10+ resultados recentes
            manipulation_score += 50 # Forte indício de desequilíbrio forçado
        elif counts['C'] == 0 and counts['V'] > 0: # Só tem Vermelho, por exemplo
             manipulation_score += 40
        elif counts['V'] == 0 and counts['C'] > 0: # Só tem Azul
             manipulation_score += 40

    # Define o nível de manipulação com base na pontuação acumulada
    if manipulation_score >= 90:
        return 'high'
    if manipulation_score >= 60:
        return 'medium'
    return 'low'

def get_recommendation(risk_level, manipulation_level, patterns, confidence):
    """
    Gera a recomendação final para o usuário, priorizando segurança.
    """
    if manipulation_level == 'high':
        return 'STOP - Manipulação Detectada!' # Mais alta prioridade: segurança
    if risk_level == 'high':
        return 'AVISO - Risco Alto, não apostar.' # Segunda prioridade: alto risco
    
    # Recomendações baseadas na confiança da previsão
    if confidence < 50:
        return 'watch' # Baixa confiança, melhor observar mais
    if confidence >= 50 and confidence < 70:
        return 'consider' # Confiança razoável, considerar com cautela
    if confidence >= 70:
        return 'bet' # Boa confiança, recomendar aposta

    return 'watch' # Recomendação padrão se nenhuma condição for atendida

---

# Interface do Streamlit

st.set_page_config(layout="wide", page_title="Analisador de Padrões de Cores")

st.title("🔮 Analisador Inteligente de Padrões de Cores")
st.markdown("---")

# Layout de colunas para organizar a interface
col1, col2, col3 = st.columns(3)

with col1:
    st.header("Entrada de Resultados")
    st.write("Adicione os resultados um por um para iniciar a análise:")
    
    # Botões para adicionar resultados
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
    # Botões de controle para desfazer e resetar o histórico
    st.button("↩️ Desfazer Último", on_click=undo_last_result, use_container_width=True)
    st.button("🗑️ Resetar Histórico", on_click=reset_history, use_container_width=True)

with col2:
    st.header("Previsão e Recomendação")

    analysis = st.session_state.analysis # Acessa os dados da análise do estado da sessão
    
    if analysis['prediction']:
        predicted_color_name = get_color_name(analysis['prediction'])
        st.metric(label="Próxima Previsão", value=f"{predicted_color_name} ({analysis['prediction']})")
        st.metric(label="Confiança", value=f"{analysis['confidence']:.0f}%")
        st.info(f"**Motivo:** {analysis['prediction_reason']}")
    else:
        st.info("Aguardando mais dados (mínimo de 5 resultados) para previsão...")
    
    st.markdown("---")
    st.subheader("Recomendação Atual")
    rec_text = analysis['recommendation']
    # Exibe a recomendação com cores e mensagens claras
    if rec_text == 'bet':
        st.success(f"**🟢 RECOMENDADO: {rec_text.upper()}** - Oportunidade identificada!")
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
    # Exibe os níveis de risco e manipulação
    st.write(f"**Nível de Risco:** :red[{analysis['riskLevel'].upper()}]")
    st.write(f"**Potencial Manipulação:** :orange[{analysis['manipulation'].upper()}]")

with col3:
    st.header("Métricas de Performance")
    perf = st.session_state.performance_metrics # Acessa as métricas de performance
    
    # Calcula e exibe a acurácia geral e a acurácia G1
    accuracy = calculate_accuracy()
    g1_accuracy = calculate_g1_accuracy()

    st.metric(label="Acurácia Geral", value=f"{accuracy:.2f}%")
    st.metric(label="Acurácia G1 (Recomendação 'Bet')", value=f"{g1_accuracy:.2f}%")
    st.write(f"Previsões Totais: **{perf['total_predictions']}**")
    st.write(f"Acertos: **{perf['correct_predictions']}**")
    st.write(f"Erros: **{perf['wrong_predictions']}**")
    st.write(f"G1 Hits (Acertos quando recomendado 'Bet'): **{perf['g1_hits']}**")

    st.markdown("---")
    st.header("Padrões Detectados")
    if analysis['patterns']:
        for p in analysis['patterns']:
            st.code(p['description'], language='text') # Exibe a descrição dos padrões detectados
    else:
        st.info("Nenhum padrão claro detectado ainda.")

st.markdown("---")
st.header("Histórico de Resultados")

# Exibição do histórico de forma mais organizada e limitada (últimos 20 na área de texto)
display_history = st.session_state.history[-20:] 
if display_history:
    history_str = " | ".join([
        f"{get_color_name(item['result'])} ({item['result']})"
        for item in display_history
    ])
    st.text_area("Últimos Resultados (20)", history_str, height=100, disabled=True)

    # Exibe o histórico completo em formato de tabela para detalhes adicionais
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
