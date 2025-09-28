"""
Explainable Greeks for Options Wheel Strategy Trading Bot
Provides plain language explanations of option Greeks and risk metrics
"""
from typing import Dict, Any, List, Optional
import json
from datetime import datetime

import sys
from pathlib import Path
# Add the Trading directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils.logging_utils import logger
from ai.base import is_enabled, call_llm
from config.config import config


def explain_greeks(
    position: Dict[str, Any], 
    language: str = "en",
    detail_level: str = "intermediate"
) -> Dict[str, Any]:
    """
    Explain the Greeks of a position in plain language
    
    Args:
        position: Position dictionary containing Greeks and details
        language: Language for explanation (en, hi, ta, gu, etc.)
        detail_level: Detail level (beginner, intermediate, advanced)
        
    Returns:
        Dictionary with plain language explanation
    """
    if not is_enabled("explain"):
        logger.debug("[AI] Explainable Greeks is disabled")
        return {
            "explanation": "Feature disabled",
            "risk_factors": [],
            "mitigation_strategies": [],
            "detail_level": detail_level
        }
    
    try:
        logger.info(f"[AI] Explain: Generating Greek explanation for position {position.get('symbol', 'unknown')}")
        
        # Extract Greek values
        greeks = {
            "delta": position.get('delta', 0),
            "gamma": position.get('gamma', 0),
            "theta": position.get('theta', 0),
            "vega": position.get('vega', 0),
            "rho": position.get('rho', 0)
        }
        
        # Extract position details
        position_details = {
            "symbol": position.get('symbol', 'UNKNOWN'),
            "quantity": position.get('quantity', 0),
            "transaction_type": position.get('transaction_type', 'BUY'),
            "option_type": position.get('option_type', 'CALL'),
            "strike_price": position.get('strike_price', 0),
            "underlying_price": position.get('underlying_price', 0),
            "days_to_expiry": position.get('days_to_expiry', 30),
            "implied_volatility": position.get('implied_volatility', 0.20)
        }
        
        # In a real implementation, you would:
        # 1. Generate plain language explanation using LLM
        # 2. Provide risk factors based on Greek values
        # 3. Suggest mitigation strategies
        
        # For now, generate using rules-based approach with LLM enhancement
        explanation = _generate_plain_language_explanation(greeks, position_details, language, detail_level)
        risk_factors = _identify_risk_factors(greeks, position_details)
        mitigation_strategies = _suggest_mitigation_strategies(greeks, position_details, risk_factors)
        
        result = {
            "explanation": explanation,
            "risk_factors": risk_factors,
            "mitigation_strategies": mitigation_strategies,
            "greeks": greeks,
            "position_details": position_details,
            "language": language,
            "detail_level": detail_level,
            "generated_at": datetime.now().isoformat()
        }
        
        logger.info(f"[AI] Explain: Generated Greek explanation for {position_details['symbol']}")
        return result
        
    except Exception as e:
        logger.error(f"[AI] Explain: Error generating Greek explanation: {e}")
        return {
            "explanation": f"Error generating explanation: {str(e)}",
            "risk_factors": ["System error occurred"],
            "mitigation_strategies": ["Contact support for assistance"],
            "error": str(e)
        }


def _generate_plain_language_explanation(
    greeks: Dict[str, float], 
    position_details: Dict[str, Any],
    language: str,
    detail_level: str
) -> str:
    """
    Generate plain language explanation of Greeks
    
    Args:
        greeks: Dictionary of Greek values
        position_details: Position details
        language: Language for explanation
        detail_level: Detail level
        
    Returns:
        Plain language explanation
    """
    try:
        symbol = position_details['symbol']
        quantity = position_details['quantity']
        transaction_type = position_details['transaction_type']
        option_type = position_details['option_type']
        delta = greeks['delta']
        gamma = greeks['gamma']
        theta = greeks['theta']
        vega = greeks['vega']
        days_to_expiry = position_details['days_to_expiry']
        implied_volatility = position_details['implied_volatility']
        
        # Determine position type (long/short, call/put)
        is_long = transaction_type == 'BUY'
        is_call = option_type == 'CALL'
        is_put = option_type == 'PUT'
        
        explanations = []
        
        # Delta explanation
        if abs(delta) > 0.01:  # Only explain meaningful delta
            if is_call:
                if is_long:
                    direction = "up" if delta > 0 else "down"
                    explanation = f"For each ₹1 {direction} in the underlying, your {symbol} position gains/loses approximately ₹{abs(delta)*quantity:.2f}"
                else:  # Short call
                    direction = "up" if delta < 0 else "down"
                    explanation = f"For each ₹1 {direction} in the underlying, your {symbol} position loses/gains approximately ₹{abs(delta)*quantity:.2f}"
            else:  # Put
                if is_long:
                    direction = "down" if delta < 0 else "up"
                    explanation = f"For each ₹1 {direction} in the underlying, your {symbol} position gains/loses approximately ₹{abs(delta)*quantity:.2f}"
                else:  # Short put
                    direction = "down" if delta > 0 else "up"
                    explanation = f"For each ₹1 {direction} in the underlying, your {symbol} position loses/gains approximately ₹{abs(delta)*quantity:.2f}"
            
            explanations.append(f"Delta ({delta:+.3f}): {explanation}")
        
        # Theta explanation
        if abs(theta) > 0.01:  # Only explain meaningful theta
            if theta < 0:
                explanation = f"You lose approximately ₹{abs(theta)*quantity:.2f} per day due to time decay"
                if days_to_expiry <= 7:
                    explanation += " (accelerating as expiry approaches)"
            else:
                explanation = f"You gain approximately ₹{abs(theta)*quantity:.2f} per day from time decay"
            
            explanations.append(f"Theta ({theta:+.3f}): {explanation}")
        
        # Gamma explanation
        if abs(gamma) > 0.001:  # Only explain meaningful gamma
            if gamma > 0:
                explanation = f"Your delta changes by approximately {gamma*quantity:+.3f} for each ₹1 move in the underlying"
            else:
                explanation = f"Your delta changes by approximately {gamma*quantity:+.3f} for each ₹1 move in the underlying"
            
            explanations.append(f"Gamma ({gamma:+.3f}): {explanation}")
        
        # Vega explanation
        if abs(vega) > 0.01:  # Only explain meaningful vega
            if vega > 0:
                explanation = f"You gain approximately ₹{vega*quantity:.2f} for each 1% increase in volatility"
            else:
                explanation = f"You lose approximately ₹{abs(vega)*quantity:.2f} for each 1% increase in volatility"
            
            explanations.append(f"Vega ({vega:+.3f}): {explanation}")
        
        # Combine explanations
        if explanations:
            full_explanation = f"Position: {quantity} {symbol} ({'Long' if is_long else 'Short'} {'Call' if is_call else 'Put'})\n\n"
            full_explanation += "\n".join(explanations)
        else:
            full_explanation = f"Position: {quantity} {symbol} - Greeks are minimal or not significant at this time."
        
        return full_explanation
        
    except Exception as e:
        logger.error(f"[AI] Explain: Error generating plain language explanation: {e}")
        return "Unable to generate explanation due to system error"


def _identify_risk_factors(greeks: Dict[str, float], position_details: Dict[str, Any]) -> List[str]:
    """
    Identify risk factors based on Greeks and position details
    
    Args:
        greeks: Dictionary of Greek values
        position_details: Position details
        
    Returns:
        List of risk factors
    """
    try:
        risk_factors = []
        delta = greeks['delta']
        gamma = greeks['gamma']
        theta = greeks['theta']
        vega = greeks['vega']
        days_to_expiry = position_details['days_to_expiry']
        implied_volatility = position_details['implied_volatility']
        option_type = position_details['option_type']
        
        # High delta risk (directional exposure)
        if abs(delta) > 0.7:
            risk_factors.append("High directional risk - large gains/losses with underlying movement")
        
        # High gamma risk (delta acceleration)
        if abs(gamma) > 0.05:
            risk_factors.append("High gamma risk - rapid delta changes with underlying movement")
        
        # High theta risk (time decay acceleration)
        if days_to_expiry <= 7 and theta < -1.0:
            risk_factors.append("Accelerated time decay risk in final week")
        
        # High vega risk (volatility exposure)
        if abs(vega) > 10.0:
            risk_factors.append("High volatility risk - significant P&L swings with volatility changes")
        
        # Low time premium risk
        if days_to_expiry <= 3 and abs(theta) < 0.5:
            risk_factors.append("Low time premium remaining - limited profit potential")
        
        # Deep ITM risk
        underlying_price = position_details.get('underlying_price', 0)
        strike_price = position_details.get('strike_price', 0)
        if underlying_price > 0 and strike_price > 0:
            moneyness = underlying_price / strike_price if option_type == 'CALL' else strike_price / underlying_price
            if moneyness > 1.1:
                risk_factors.append("Deep in-the-money option - behaves more like underlying stock")
            elif moneyness < 0.9:
                risk_factors.append("Deep out-of-the-money option - high probability of expiring worthless")
        
        # High IV risk
        if implied_volatility > 0.40:
            risk_factors.append("High implied volatility - elevated option premiums")
        elif implied_volatility < 0.15:
            risk_factors.append("Low implied volatility - reduced premium collection opportunities")
        
        # No significant risks identified
        if not risk_factors:
            risk_factors.append("No significant Greek-based risks identified at current levels")
        
        return risk_factors
        
    except Exception as e:
        logger.error(f"[AI] Explain: Error identifying risk factors: {e}")
        return ["Error identifying risk factors - system error"]


def _suggest_mitigation_strategies(
    greeks: Dict[str, float], 
    position_details: Dict[str, Any], 
    risk_factors: List[str]
) -> List[str]:
    """
    Suggest mitigation strategies based on Greeks and risk factors
    
    Args:
        greeks: Dictionary of Greek values
        position_details: Position details
        risk_factors: List of identified risk factors
        
    Returns:
        List of mitigation strategies
    """
    try:
        strategies = []
        delta = greeks['delta']
        gamma = greeks['gamma']
        theta = greeks['theta']
        vega = greeks['vega']
        days_to_expiry = position_details['days_to_expiry']
        option_type = position_details['option_type']
        
        # Mitigation for high delta risk
        if any("directional risk" in rf for rf in risk_factors):
            strategies.append("Consider hedging directional exposure with underlying stock/futures")
            strategies.append("Reduce position size to limit directional impact")
            strategies.append("Use stop-loss orders to limit directional losses")
        
        # Mitigation for high gamma risk
        if any("gamma risk" in rf for rf in risk_factors):
            strategies.append("Monitor delta frequently as underlying price moves")
            strategies.append("Consider dynamic hedging for large gamma positions")
            strategies.append("Be prepared for accelerated P&L changes with large moves")
        
        # Mitigation for time decay risk
        if any("time decay" in rf for rf in risk_factors) or days_to_expiry <= 7:
            strategies.append("Consider closing positions before final week for short options")
            strategies.append("Monitor theta decay acceleration daily")
            strategies.append("Evaluate early exit if time decay becomes excessive")
        
        # Mitigation for volatility risk
        if any("volatility" in rf for rf in risk_factors):
            strategies.append("Monitor implied volatility levels closely")
            strategies.append("Consider volatility trading strategies (long/short vega)")
            strategies.append("Use volatility stops to limit vega exposure")
        
        # General risk management
        strategies.extend([
            "Maintain proper position sizing limits",
            "Use stop-loss orders consistently",
            "Monitor Greeks daily, especially near expiry",
            "Keep adequate cash reserves for assignments",
            "Review and adjust strategy based on market conditions"
        ])
        
        return strategies
        
    except Exception as e:
        logger.error(f"[AI] Explain: Error suggesting mitigation strategies: {e}")
        return ["Error generating mitigation strategies - contact support"]


def compare_greek_profiles(
    position1: Dict[str, Any], 
    position2: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Compare Greek profiles of two positions
    
    Args:
        position1: First position to compare
        position2: Second position to compare
        
    Returns:
        Dictionary with comparison results
    """
    try:
        # Extract Greeks for both positions
        greeks1 = {
            "delta": position1.get('delta', 0),
            "gamma": position1.get('gamma', 0),
            "theta": position1.get('theta', 0),
            "vega": position1.get('vega', 0),
            "rho": position1.get('rho', 0)
        }
        
        greeks2 = {
            "delta": position2.get('delta', 0),
            "gamma": position2.get('gamma', 0),
            "theta": position2.get('theta', 0),
            "vega": position2.get('vega', 0),
            "rho": position2.get('rho', 0)
        }
        
        # Calculate differences
        differences = {}
        for greek in ['delta', 'gamma', 'theta', 'vega', 'rho']:
            differences[greek] = greeks2[greek] - greeks1[greek]
        
        # Determine which position has higher exposure in each Greek
        comparison = {}
        for greek in ['delta', 'gamma', 'theta', 'vega', 'rho']:
            if abs(differences[greek]) < 0.01:
                comparison[greek] = "similar"
            elif differences[greek] > 0:
                comparison[greek] = f"position2_higher"
            else:
                comparison[greek] = f"position1_higher"
        
        # Generate summary using LLM if enabled
        if is_enabled("explain"):
            prompt = f"""
            Compare these two option positions based on their Greek profiles:
            
            Position 1: {position1.get('symbol', 'Unknown')}
            Greeks: {json.dumps(greeks1, indent=2)}
            
            Position 2: {position2.get('symbol', 'Unknown')}
            Greeks: {json.dumps(greeks2, indent=2)}
            
            Provide a comparison in 3 paragraphs:
            1. Overall risk profile comparison
            2. Key differences in each Greek
            3. Recommendation on which position might be better suited for current market conditions
            """
            
            comparison_summary = call_llm(prompt, max_tokens=300, temperature=0.3)
        else:
            comparison_summary = "Greek comparison completed automatically"
        
        return {
            "position1_greeks": greeks1,
            "position2_greeks": greeks2,
            "differences": differences,
            "comparison": comparison,
            "summary": comparison_summary,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"[AI] Explain: Error comparing Greek profiles: {e}")
        return {
            "error": str(e),
            "comparison": {},
            "summary": "Error comparing positions"
        }


def generate_portfolio_greek_summary(positions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate summary of portfolio Greeks exposure
    
    Args:
        positions: List of positions in portfolio
        
    Returns:
        Dictionary with portfolio Greek summary
    """
    try:
        # Aggregate Greeks across all positions
        total_greeks = {
            "delta": 0,
            "gamma": 0,
            "theta": 0,
            "vega": 0,
            "rho": 0
        }
        
        position_count = 0
        total_quantity = 0
        
        for position in positions:
            try:
                # Add weighted Greeks to totals
                quantity = position.get('quantity', 0)
                total_greeks['delta'] += position.get('delta', 0) * quantity
                total_greeks['gamma'] += position.get('gamma', 0) * quantity
                total_greeks['theta'] += position.get('theta', 0) * quantity
                total_greeks['vega'] += position.get('vega', 0) * quantity
                total_greeks['rho'] += position.get('rho', 0) * quantity
                
                position_count += 1
                total_quantity += abs(quantity)
                
            except Exception as e:
                logger.warning(f"[AI] Explain: Error processing position for Greek aggregation: {e}")
                continue
        
        # Generate portfolio risk summary
        risk_summary = []
        
        # Delta risk assessment
        if abs(total_greeks['delta']) > 100:  # Significant directional exposure
            direction = "long" if total_greeks['delta'] > 0 else "short"
            risk_summary.append(f"Significant {direction} directional exposure: ₹{abs(total_greeks['delta']):.0f} per point")
        
        # Theta (time decay) assessment
        if total_greeks['theta'] < -50:  # Significant daily time decay
            risk_summary.append(f"Daily time decay: -₹{abs(total_greeks['theta']):.0f}")
        elif total_greeks['theta'] > 50:  # Benefiting from time decay
            risk_summary.append(f"Daily time benefit: +₹{total_greeks['theta']:.0f}")
        
        # Vega (volatility) assessment
        if abs(total_greeks['vega']) > 100:  # Significant volatility exposure
            direction = "long" if total_greeks['vega'] > 0 else "short"
            risk_summary.append(f"Significant {direction} volatility exposure: ₹{abs(total_greeks['vega']):.0f} per 1% vol change")
        
        # Gamma assessment
        if abs(total_greeks['gamma']) > 50:  # Significant gamma exposure
            risk_summary.append(f"Significant gamma exposure: delta changes by ₹{abs(total_greeks['gamma']):.0f} per point move")
        
        # Generate LLM explanation if enabled
        if is_enabled("explain"):
            prompt = f"""
            Summarize this portfolio Greek exposure:
            
            Total Greeks:
            Delta: {total_greeks['delta']:+.0f} (Directional risk)
            Gamma: {total_greeks['gamma']:+.0f} (Delta acceleration)
            Theta: {total_greeks['theta']:+.0f} (Time decay per day)
            Vega:  {total_greeks['vega']:+.0f} (Volatility exposure per 1%)
            Rho:   {total_greeks['rho']:+.0f} (Interest rate sensitivity)
            
            Portfolio consists of {position_count} positions with {total_quantity} total contracts.
            
            Provide a 2-paragraph summary:
            1. Overall portfolio risk profile
            2. Key recommendations for risk management
            """
            
            portfolio_summary = call_llm(prompt, max_tokens=250, temperature=0.3)
        else:
            portfolio_summary = "Portfolio Greek summary generated automatically"
        
        return {
            "total_greeks": total_greeks,
            "position_count": position_count,
            "total_contracts": total_quantity,
            "risk_summary": risk_summary,
            "portfolio_summary": portfolio_summary,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"[AI] Explain: Error generating portfolio Greek summary: {e}")
        return {
            "error": str(e),
            "total_greeks": {"delta": 0, "gamma": 0, "theta": 0, "vega": 0, "rho": 0},
            "position_count": 0,
            "total_contracts": 0,
            "risk_summary": ["Error generating portfolio summary"],
            "portfolio_summary": "Error in portfolio analysis"
        }