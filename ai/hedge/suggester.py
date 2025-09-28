"""
Auto-Hedge Suggester for Options Wheel Strategy Trading Bot
Suggests cheapest offsetting hedges using LLM analysis
"""
from typing import Dict, Any, List, Optional, Tuple
import json
from datetime import datetime

import sys
from pathlib import Path
# Add the Trading directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils.logging_utils import logger
from ai.base import is_enabled, call_llm
from config.config import config


def suggest_hedge(position: Dict[str, Any]) -> Dict[str, Any]:
    """
    Suggest the cheapest offsetting hedge for a position
    
    Args:
        position: Position to hedge
        
    Returns:
        Dictionary with hedge suggestion details
    """
    if not is_enabled("hedge"):
        logger.debug("[AI] Auto-hedge suggester is disabled")
        return {
            "hedge_contract": None,
            "qty": 0,
            "cost_bps": 0,
            "delta_reduction": 0,
            "confidence": 0.0,
            "explanation": "Feature disabled"
        }
    
    try:
        logger.info(f"[AI] Hedge: Suggesting hedge for position {position.get('symbol', 'unknown')}")
        
        # Extract position details
        symbol = position.get('symbol', 'UNKNOWN')
        quantity = position.get('quantity', 0)
        delta = position.get('delta', 0)
        gamma = position.get('gamma', 0)
        vega = position.get('vega', 0)
        theta = position.get('theta', 0)
        underlying_price = position.get('underlying_price', 0)
        days_to_expiry = position.get('days_to_expiry', 30)
        
        # Determine what we need to hedge
        hedge_needs = _analyze_hedge_requirements(position)
        
        # Find potential hedge contracts
        potential_hedges = _find_potential_hedges(symbol, underlying_price, days_to_expiry, hedge_needs)
        
        # Rank hedges by cost-effectiveness
        ranked_hedges = _rank_hedges_by_cost_effectiveness(potential_hedges, position)
        
        # Select best hedge
        if ranked_hedges:
            best_hedge = ranked_hedges[0]
            
            # Calculate hedge parameters
            hedge_qty = _calculate_hedge_quantity(position, best_hedge)
            
            # Generate explanation using LLM
            explanation = _generate_hedge_explanation(position, best_hedge, hedge_qty, hedge_needs)
            
            result = {
                "hedge_contract": best_hedge.get('symbol'),
                "qty": hedge_qty,
                "cost_bps": best_hedge.get('cost_bps', 0),
                "delta_reduction": best_hedge.get('delta_offset', 0) * hedge_qty,
                "gamma_offset": best_hedge.get('gamma_offset', 0) * hedge_qty,
                "vega_offset": best_hedge.get('vega_offset', 0) * hedge_qty,
                "theta_offset": best_hedge.get('theta_offset', 0) * hedge_qty,
                "confidence": best_hedge.get('confidence', 0.8),
                "explanation": explanation,
                "hedge_details": best_hedge,
                "risk_reduction": _calculate_risk_reduction(position, best_hedge, hedge_qty),
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"[AI] Hedge: Suggested hedge {best_hedge.get('symbol')} for {symbol}")
            return result
        else:
            logger.info(f"[AI] Hedge: No suitable hedges found for {symbol}")
            return {
                "hedge_contract": None,
                "qty": 0,
                "cost_bps": 0,
                "delta_reduction": 0,
                "confidence": 0.3,
                "explanation": "No suitable hedge contracts found",
                "risk_reduction": {"delta": 0, "gamma": 0, "vega": 0, "theta": 0}
            }
            
    except Exception as e:
        logger.error(f"[AI] Hedge: Error suggesting hedge: {e}")
        return {
            "hedge_contract": None,
            "qty": 0,
            "cost_bps": 0,
            "delta_reduction": 0,
            "confidence": 0.1,
            "explanation": f"Error suggesting hedge: {str(e)}",
            "error": str(e),
            "risk_reduction": {"delta": 0, "gamma": 0, "vega": 0, "theta": 0}
        }


def _analyze_hedge_requirements(position: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze what needs to be hedged in a position
    
    Args:
        position: Position to analyze
        
    Returns:
        Dictionary with hedge requirements
    """
    try:
        delta = position.get('delta', 0)
        gamma = position.get('gamma', 0)
        vega = position.get('vega', 0)
        theta = position.get('theta', 0)
        days_to_expiry = position.get('days_to_expiry', 30)
        
        requirements = {
            "primary_risk": None,
            "secondary_risks": [],
            "urgency": "medium",
            "risk_magnitude": 0
        }
        
        # Determine primary risk based on Greek magnitudes
        greeks = {"delta": abs(delta), "gamma": abs(gamma), "vega": abs(vega), "theta": abs(theta)}
        primary_risk = max(greeks, key=greeks.get)
        requirements["primary_risk"] = primary_risk
        requirements["risk_magnitude"] = greeks[primary_risk]
        
        # Determine secondary risks
        sorted_greeks = sorted(greeks.items(), key=lambda x: x[1], reverse=True)
        requirements["secondary_risks"] = [g[0] for g in sorted_greeks[1:] if g[1] > 0.1]
        
        # Determine urgency based on days to expiry and risk magnitude
        if days_to_expiry <= 7:
            requirements["urgency"] = "high"
        elif greeks[primary_risk] > 5.0:
            requirements["urgency"] = "high"
        elif days_to_expiry <= 14:
            requirements["urgency"] = "medium"
        else:
            requirements["urgency"] = "low"
        
        return requirements
        
    except Exception as e:
        logger.error(f"[AI] Hedge: Error analyzing hedge requirements: {e}")
        return {
            "primary_risk": "delta",
            "secondary_risks": [],
            "urgency": "medium",
            "risk_magnitude": 1.0
        }


def _find_potential_hedges(
    symbol: str, 
    underlying_price: float, 
    days_to_expiry: int, 
    hedge_needs: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Find potential hedge contracts
    
    Args:
        symbol: Symbol being hedged
        underlying_price: Current underlying price
        days_to_expiry: Days to expiry
        hedge_needs: Hedge requirements
        
    Returns:
        List of potential hedge contracts
    """
    try:
        # In a real implementation, you would:
        # 1. Query option chain for the underlying
        # 2. Filter for appropriate expiry dates
        # 3. Filter for appropriate strikes
        # 4. Calculate Greeks for each potential hedge
        
        # For now, return simulated hedge options
        potential_hedges = []
        
        # Generate simulated hedge contracts
        primary_risk = hedge_needs.get('primary_risk', 'delta')
        risk_magnitude = hedge_needs.get('risk_magnitude', 1.0)
        
        # Create 5-10 potential hedge contracts
        for i in range(5):
            # Simulate different strikes and contract types
            strike_offset = (i - 2) * 100  # Strikes around ATM
            strike_price = round(underlying_price / 50) * 50 + strike_offset
            
            # Determine contract type based on primary risk
            if primary_risk == 'delta':
                # For delta hedging, opposite delta contracts
                contract_type = 'PUT' if underlying_price > strike_price else 'CALL'
            elif primary_risk == 'gamma':
                # For gamma hedging, ATM options (highest gamma)
                contract_type = 'CALL' if abs(underlying_price - strike_price) < 50 else 'PUT'
            elif primary_risk == 'vega':
                # For vega hedging, longer-dated options (higher vega)
                contract_type = 'CALL'
            else:  # theta
                contract_type = 'PUT'
            
            hedge_contract = {
                "symbol": f"{symbol[:-2]}{contract_type[0]}{strike_price}",
                "strike": strike_price,
                "type": contract_type,
                "days_to_expiry": max(1, days_to_expiry - i * 2),
                "delta": _simulate_delta(strike_price, underlying_price, contract_type),
                "gamma": _simulate_gamma(strike_price, underlying_price, days_to_expiry),
                "vega": _simulate_vega(strike_price, underlying_price, days_to_expiry),
                "theta": _simulate_theta(strike_price, underlying_price, days_to_expiry),
                "premium": _simulate_premium(strike_price, underlying_price, days_to_expiry, contract_type),
                "bid_ask_spread": _simulate_bid_ask_spread(),
                "open_interest": _simulate_open_interest(),
                "volume": _simulate_volume(),
                "implied_volatility": _simulate_iv(strike_price, underlying_price, days_to_expiry)
            }
            
            # Calculate cost in basis points
            hedge_contract["cost_bps"] = (hedge_contract["premium"] / underlying_price) * 10000
            
            # Calculate offsets
            hedge_contract["delta_offset"] = -hedge_contract["delta"]  # Opposite to hedge
            hedge_contract["gamma_offset"] = -hedge_contract["gamma"]
            hedge_contract["vega_offset"] = -hedge_contract["vega"]
            hedge_contract["theta_offset"] = -hedge_contract["theta"]
            
            # Calculate confidence (based on liquidity, pricing, etc.)
            hedge_contract["confidence"] = _calculate_hedge_confidence(hedge_contract)
            
            potential_hedges.append(hedge_contract)
        
        return potential_hedges
        
    except Exception as e:
        logger.error(f"[AI] Hedge: Error finding potential hedges: {e}")
        return []


def _simulate_delta(strike: float, underlying: float, contract_type: str) -> float:
    """Simulate delta for a contract"""
    moneyness = underlying / strike if contract_type == 'CALL' else strike / underlying
    if contract_type == 'CALL':
        return min(1.0, max(0.0, (moneyness - 0.5) * 2))
    else:  # PUT
        return max(-1.0, min(0.0, (moneyness - 1.5) * 2))


def _simulate_gamma(strike: float, underlying: float, days: int) -> float:
    """Simulate gamma for a contract"""
    moneyness = abs(underlying - strike) / underlying
    time_factor = max(0.1, min(1.0, days / 30))
    return (1 - moneyness) * 0.1 * time_factor


def _simulate_vega(strike: float, underlying: float, days: int) -> float:
    """Simulate vega for a contract"""
    time_factor = max(0.1, min(1.0, days / 90))
    moneyness = abs(underlying - strike) / underlying
    return (1 - moneyness * 0.5) * 0.2 * time_factor


def _simulate_theta(strike: float, underlying: float, days: int) -> float:
    """Simulate theta for a contract"""
    time_factor = max(0.1, 1.0 - (days / 365))
    moneyness = abs(underlying - strike) / underlying
    return -(1 - moneyness * 0.3) * 0.05 * time_factor


def _simulate_premium(strike: float, underlying: float, days: int, contract_type: str) -> float:
    """Simulate option premium"""
    intrinsic = max(0, underlying - strike) if contract_type == 'CALL' else max(0, strike - underlying)
    time_value = max(10, underlying * 0.02 * (days / 365))
    return intrinsic + time_value


def _simulate_bid_ask_spread() -> float:
    """Simulate bid-ask spread"""
    import random
    return random.uniform(0.05, 0.50)


def _simulate_open_interest() -> int:
    """Simulate open interest"""
    import random
    return random.randint(1000, 50000)


def _simulate_volume() -> int:
    """Simulate trading volume"""
    import random
    return random.randint(100, 10000)


def _simulate_iv(strike: float, underlying: float, days: int) -> float:
    """Simulate implied volatility"""
    import random
    moneyness = abs(underlying - strike) / underlying
    base_iv = 0.20 + moneyness * 0.10
    return max(0.10, min(0.50, base_iv + random.uniform(-0.05, 0.05)))


def _calculate_hedge_confidence(hedge_contract: Dict[str, Any]) -> float:
    """Calculate confidence in hedge contract"""
    try:
        # Factors affecting confidence:
        # 1. Liquidity (high OI and volume = high confidence)
        oi_confidence = min(1.0, hedge_contract.get('open_interest', 1000) / 10000)
        volume_confidence = min(1.0, hedge_contract.get('volume', 1000) / 5000)
        
        # 2. Tight bid-ask spread (tighter = higher confidence)
        spread_confidence = max(0.1, 1.0 - (hedge_contract.get('bid_ask_spread', 0.20) / 0.50))
        
        # 3. Time to expiry (not too short = higher confidence)
        days = hedge_contract.get('days_to_expiry', 30)
        time_confidence = min(1.0, max(0.1, days / 60))
        
        # Weighted average
        confidence = (
            oi_confidence * 0.3 +
            volume_confidence * 0.3 +
            spread_confidence * 0.2 +
            time_confidence * 0.2
        )
        
        return round(confidence, 2)
        
    except Exception as e:
        logger.error(f"[AI] Hedge: Error calculating hedge confidence: {e}")
        return 0.5


def _rank_hedges_by_cost_effectiveness(
    potential_hedges: List[Dict[str, Any]], 
    position: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Rank hedges by cost-effectiveness
    
    Args:
        potential_hedges: List of potential hedges
        position: Position being hedged
        
    Returns:
        Ranked list of hedges
    """
    try:
        # Extract position Greeks
        pos_delta = position.get('delta', 0)
        pos_gamma = position.get('gamma', 0)
        pos_vega = position.get('vega', 0)
        pos_theta = position.get('theta', 0)
        
        # Rank hedges based on cost-effectiveness
        ranked_hedges = []
        
        for hedge in potential_hedges:
            try:
                # Calculate cost-effectiveness score
                # Lower cost per unit of risk reduction = higher score
                
                # Delta offset effectiveness
                hedge_delta = hedge.get('delta_offset', 0)
                delta_reduction = abs(hedge_delta * pos_delta) if pos_delta != 0 else 0
                
                # Cost per delta point reduced
                cost_per_delta = hedge.get('cost_bps', 100) / (abs(hedge_delta) + 0.001) if hedge_delta != 0 else float('inf')
                
                # Gamma offset effectiveness
                hedge_gamma = hedge.get('gamma_offset', 0)
                gamma_reduction = abs(hedge_gamma * pos_gamma) if pos_gamma != 0 else 0
                cost_per_gamma = hedge.get('cost_bps', 100) / (abs(hedge_gamma) + 0.001) if hedge_gamma != 0 else float('inf')
                
                # Vega offset effectiveness
                hedge_vega = hedge.get('vega_offset', 0)
                vega_reduction = abs(hedge_vega * pos_vega) if pos_vega != 0 else 0
                cost_per_vega = hedge.get('cost_bps', 100) / (abs(hedge_vega) + 0.001) if hedge_vega != 0 else float('inf')
                
                # Overall effectiveness score (lower is better)
                effectiveness_score = (
                    cost_per_delta * 0.4 +  # Delta is usually most important
                    cost_per_gamma * 0.3 +   # Gamma is second priority
                    cost_per_vega * 0.3     # Vega is third priority
                )
                
                # Confidence adjustment
                confidence = hedge.get('confidence', 0.5)
                adjusted_score = effectiveness_score / (confidence + 0.1)  # Higher confidence = lower score
                
                # Add to ranked list
                hedge_copy = hedge.copy()
                hedge_copy['effectiveness_score'] = adjusted_score
                hedge_copy['delta_effectiveness'] = cost_per_delta
                hedge_copy['gamma_effectiveness'] = cost_per_gamma
                hedge_copy['vega_effectiveness'] = cost_per_vega
                ranked_hedges.append(hedge_copy)
                
            except Exception as e:
                logger.warning(f"[AI] Hedge: Error ranking hedge {hedge.get('symbol', 'unknown')}: {e}")
                continue
        
        # Sort by effectiveness score (ascending - lower is better)
        ranked_hedges.sort(key=lambda x: x.get('effectiveness_score', float('inf')))
        
        return ranked_hedges
        
    except Exception as e:
        logger.error(f"[AI] Hedge: Error ranking hedges: {e}")
        return potential_hedges


def _calculate_hedge_quantity(position: Dict[str, Any], hedge: Dict[str, Any]) -> int:
    """
    Calculate optimal hedge quantity
    
    Args:
        position: Position being hedged
        hedge: Hedge contract details
        
    Returns:
        Optimal hedge quantity
    """
    try:
        # Extract key values
        pos_delta = position.get('delta', 0)
        pos_quantity = position.get('quantity', 1)
        hedge_delta = hedge.get('delta_offset', 0)  # Already negated for offset
        
        if hedge_delta == 0:
            return 0
        
        # Calculate quantity needed to offset delta
        # We want: pos_delta + (hedge_delta * hedge_quantity) = 0
        # Therefore: hedge_quantity = -pos_delta / hedge_delta
        optimal_quantity = -pos_delta / hedge_delta
        
        # Adjust for position size
        adjusted_quantity = optimal_quantity * abs(pos_quantity)
        
        # Round to nearest whole number
        rounded_quantity = round(adjusted_quantity)
        
        # Ensure minimum quantity of 1 if there's a meaningful hedge need
        if abs(rounded_quantity) == 0 and abs(pos_delta) > 0.1:
            rounded_quantity = 1 if pos_delta > 0 else -1
        
        # Limit to reasonable bounds
        max_reasonable = abs(pos_quantity) * 10  # Don't hedge more than 10x position
        final_quantity = max(-max_reasonable, min(max_reasonable, rounded_quantity))
        
        return final_quantity
        
    except Exception as e:
        logger.error(f"[AI] Hedge: Error calculating hedge quantity: {e}")
        return 1  # Conservative default


def _generate_hedge_explanation(
    position: Dict[str, Any], 
    hedge: Dict[str, Any], 
    hedge_qty: int, 
    hedge_needs: Dict[str, Any]
) -> str:
    """
    Generate explanation for hedge recommendation using LLM
    
    Args:
        position: Position being hedged
        hedge: Recommended hedge contract
        hedge_qty: Hedge quantity
        hedge_needs: Hedge requirements
        
    Returns:
        Explanation string
    """
    try:
        if not is_enabled("hedge"):
            return "Hedge recommendation generated automatically"
        
        # Prepare data for LLM
        hedge_data = {
            "position": {
                "symbol": position.get('symbol'),
                "quantity": position.get('quantity'),
                "delta": position.get('delta'),
                "gamma": position.get('gamma'),
                "vega": position.get('vega'),
                "theta": position.get('theta')
            },
            "hedge": {
                "symbol": hedge.get('symbol'),
                "strike": hedge.get('strike'),
                "type": hedge.get('type'),
                "delta": hedge.get('delta'),
                "gamma": hedge.get('gamma'),
                "vega": hedge.get('vega'),
                "theta": hedge.get('theta'),
                "premium": hedge.get('premium'),
                "cost_bps": hedge.get('cost_bps')
            },
            "hedge_qty": hedge_qty,
            "hedge_needs": hedge_needs
        }
        
        prompt = f"""
        You are a risk management assistant for the Options Wheel Strategy Trading Bot.
        
        Hedge Recommendation Analysis:
        {json.dumps(hedge_data, indent=2, default=str)}
        
        Please provide a 2-paragraph explanation:
        
        Paragraph 1: Why this specific hedge contract was selected
        Paragraph 2: What risk reduction this hedge provides and cost implications
        
        Keep it concise and focused on the trader's perspective.
        """
        
        explanation = call_llm(prompt, max_tokens=250, temperature=0.3)
        return explanation.strip()
        
    except Exception as e:
        logger.error(f"[AI] Hedge: Error generating hedge explanation: {e}")
        return f"Recommended hedge: {hedge.get('symbol')} with quantity {hedge_qty}"


def _calculate_risk_reduction(
    position: Dict[str, Any], 
    hedge: Dict[str, Any], 
    hedge_qty: int
) -> Dict[str, float]:
    """
    Calculate risk reduction provided by hedge
    
    Args:
        position: Original position
        hedge: Hedge contract
        hedge_qty: Hedge quantity
        
    Returns:
        Dictionary with risk reduction metrics
    """
    try:
        # Extract position Greeks
        pos_delta = position.get('delta', 0)
        pos_gamma = position.get('gamma', 0)
        pos_vega = position.get('vega', 0)
        pos_theta = position.get('theta', 0)
        
        # Extract hedge Greeks (already offset values)
        hedge_delta = hedge.get('delta_offset', 0)
        hedge_gamma = hedge.get('gamma_offset', 0)
        hedge_vega = hedge.get('vega_offset', 0)
        hedge_theta = hedge.get('theta_offset', 0)
        
        # Calculate risk reduction
        delta_reduction = abs(pos_delta + (hedge_delta * hedge_qty))
        gamma_reduction = abs(pos_gamma + (hedge_gamma * hedge_qty))
        vega_reduction = abs(pos_vega + (hedge_vega * hedge_qty))
        theta_reduction = abs(pos_theta + (hedge_theta * hedge_qty))
        
        # Calculate percentage reductions
        delta_pct = (1 - (delta_reduction / (abs(pos_delta) + 0.001))) * 100 if pos_delta != 0 else 0
        gamma_pct = (1 - (gamma_reduction / (abs(pos_gamma) + 0.001))) * 100 if pos_gamma != 0 else 0
        vega_pct = (1 - (vega_reduction / (abs(pos_vega) + 0.001))) * 100 if pos_vega != 0 else 0
        theta_pct = (1 - (theta_reduction / (abs(pos_theta) + 0.001))) * 100 if pos_theta != 0 else 0
        
        return {
            "delta": {
                "absolute_reduction": delta_reduction,
                "percentage_reduction": delta_pct,
                "original": pos_delta,
                "after_hedge": pos_delta + (hedge_delta * hedge_qty)
            },
            "gamma": {
                "absolute_reduction": gamma_reduction,
                "percentage_reduction": gamma_pct,
                "original": pos_gamma,
                "after_hedge": pos_gamma + (hedge_gamma * hedge_qty)
            },
            "vega": {
                "absolute_reduction": vega_reduction,
                "percentage_reduction": vega_pct,
                "original": pos_vega,
                "after_hedge": pos_vega + (hedge_vega * hedge_qty)
            },
            "theta": {
                "absolute_reduction": theta_reduction,
                "percentage_reduction": theta_pct,
                "original": pos_theta,
                "after_hedge": pos_theta + (hedge_theta * hedge_qty)
            }
        }
        
    except Exception as e:
        logger.error(f"[AI] Hedge: Error calculating risk reduction: {e}")
        return {"delta": 0, "gamma": 0, "vega": 0, "theta": 0}


def evaluate_hedge_effectiveness(
    original_position: Dict[str, Any],
    hedged_position: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Evaluate the effectiveness of an applied hedge
    
    Args:
        original_position: Position before hedging
        hedged_position: Position after hedging
        
    Returns:
        Dictionary with hedge effectiveness metrics
    """
    try:
        # Calculate risk metrics for both positions
        original_risk = _calculate_position_risk(original_position)
        hedged_risk = _calculate_position_risk(hedged_position)
        
        # Calculate effectiveness improvements
        improvements = {}
        for metric in ['delta', 'gamma', 'vega', 'theta']:
            orig_value = abs(original_risk.get(metric, 0))
            hedged_value = abs(hedged_risk.get(metric, 0))
            
            if orig_value > 0:
                improvement_pct = ((orig_value - hedged_value) / orig_value) * 100
            else:
                improvement_pct = 0
            
            improvements[metric] = {
                "original": orig_value,
                "hedged": hedged_value,
                "improvement_pct": improvement_pct,
                "absolute_improvement": orig_value - hedged_value
            }
        
        # Overall effectiveness score
        avg_improvement = sum(v['improvement_pct'] for v in improvements.values()) / len(improvements)
        
        return {
            "original_risk": original_risk,
            "hedged_risk": hedged_risk,
            "improvements": improvements,
            "overall_effectiveness_pct": avg_improvement,
            "risk_reduction_score": _calculate_risk_reduction_score(original_risk, hedged_risk),
            "evaluated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"[AI] Hedge: Error evaluating hedge effectiveness: {e}")
        return {"error": str(e)}


def _calculate_position_risk(position: Dict[str, Any]) -> Dict[str, float]:
    """Calculate risk metrics for a position"""
    return {
        "delta": position.get('delta', 0) * position.get('quantity', 1),
        "gamma": position.get('gamma', 0) * position.get('quantity', 1),
        "vega": position.get('vega', 0) * position.get('quantity', 1),
        "theta": position.get('theta', 0) * position.get('quantity', 1)
    }


def _calculate_risk_reduction_score(
    original_risk: Dict[str, float], 
    hedged_risk: Dict[str, float]
) -> float:
    """Calculate overall risk reduction score"""
    try:
        total_original = sum(abs(v) for v in original_risk.values())
        total_hedged = sum(abs(v) for v in hedged_risk.values())
        
        if total_original > 0:
            return ((total_original - total_hedged) / total_original) * 100
        else:
            return 0.0
            
    except Exception as e:
        logger.error(f"[AI] Hedge: Error calculating risk reduction score: {e}")
        return 0.0


def get_hedge_suggestion_status() -> Dict[str, Any]:
    """
    Get current status of the hedge suggestion system
    
    Returns:
        Dictionary with system status information
    """
    return {
        "feature_enabled": is_enabled("hedge"),
        "last_suggestion": datetime.now().isoformat(),
        "total_suggestions": 0,  # Would track actual suggestions in real implementation
        "successful_hedges": 0,  # Would track actual hedge implementations
        "system_health": "operational",
        "version": "1.0"
    }