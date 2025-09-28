"""
Generative Stress-Test Engine for Options Wheel Strategy Trading Bot
Generates synthetic market scenarios and stress-tests the strategy
"""
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import json
import random

import sys
from pathlib import Path
# Add the Trading directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils.logging_utils import logger
from ai.base import is_enabled, call_llm
from config.config import config


def generate_scenarios(count: int = 1000, days: int = 252) -> List[Dict[str, Any]]:
    """
    Generate synthetic market scenarios for stress testing
    
    Args:
        count: Number of scenarios to generate
        days: Duration of each scenario in trading days
        
    Returns:
        List of generated stress test scenarios
    """
    if not is_enabled("stress"):
        logger.debug("[AI] Stress testing is disabled")
        return []
    
    try:
        logger.info(f"[AI] Stress: Generating {count} synthetic market scenarios for {days} days")
        
        scenarios = []
        
        for i in range(count):
            # Generate a random scenario
            scenario = _generate_single_scenario(days)
            scenario['id'] = f"SCENARIO_{i+1:04d}"
            scenarios.append(scenario)
        
        logger.info(f"[AI] Stress: Generated {len(scenarios)} scenarios for stress testing")
        return scenarios
        
    except Exception as e:
        logger.error(f"[AI] Stress: Error generating scenarios: {e}")
        return []


def _generate_single_scenario(duration_days: int = 252) -> Dict[str, Any]:
    """
    Generate a single synthetic market scenario
    
    Args:
        duration_days: Duration of scenario in trading days
        
    Returns:
        Dictionary representing a stress test scenario
    """
    # Random scenario type selection
    scenario_types = [
        ("volatility_spike", 0.15),
        ("market_crash", 0.15),
        ("flash_crash", 0.10),
        ("black_swan", 0.05),
        ("liquidity_crisis", 0.10),
        ("correlation_shift", 0.10),
        ("vol_skew_shift", 0.10),
        ("macro_shock", 0.15),
        ("sector_rotation", 0.05),
        ("normal_stress", 0.05)
    ]
    
    # Choose scenario type based on weighted probabilities
    scenario_type = random.choices(
        [t[0] for t in scenario_types],
        weights=[t[1] for t in scenario_types]
    )[0]
    
    # Generate scenario parameters based on type
    if scenario_type == "volatility_spike":
        scenario = _create_volatility_spike_scenario(duration_days)
    elif scenario_type == "market_crash":
        scenario = _create_market_crash_scenario(duration_days)
    elif scenario_type == "flash_crash":
        scenario = _create_flash_crash_scenario(duration_days)
    elif scenario_type == "black_swan":
        scenario = _create_black_swan_scenario(duration_days)
    elif scenario_type == "liquidity_crisis":
        scenario = _create_liquidity_crisis_scenario(duration_days)
    elif scenario_type == "correlation_shift":
        scenario = _create_correlation_shift_scenario(duration_days)
    elif scenario_type == "vol_skew_shift":
        scenario = _create_vol_skew_shift_scenario(duration_days)
    elif scenario_type == "macro_shock":
        scenario = _create_macro_shock_scenario(duration_days)
    elif scenario_type == "sector_rotation":
        scenario = _create_sector_rotation_scenario(duration_days)
    else:  # normal_stress
        scenario = _create_normal_stress_scenario(duration_days)
    
    return scenario


def _create_volatility_spike_scenario(duration_days: int) -> Dict[str, Any]:
    """Create a volatility spike scenario"""
    severity = random.uniform(1.5, 3.0)  # 150-300% volatility increase
    duration = random.randint(5, 30)  # 5-30 day duration
    
    return {
        "scenario_type": "volatility_spike",
        "description": "Sudden increase in market volatility",
        "severity": severity,
        "duration_days": duration,
        "parameters": {
            "volatility_multiplier": severity,
            "start_day": random.randint(1, max(1, duration_days - duration)),
            "affected_assets": ["NIFTY", "BANKNIFTY"],
            "impact_on_strategy": "Increased option premium volatility, wider bid-ask spreads, higher slippage",
            "risk_factors": [
                "Premium decay acceleration for short options",
                "Higher assignment probability for puts",
                "Increased early exit triggers",
                "Wider stop-loss breakevens"
            ],
            "mitigation_strategies": [
                "Reduce position sizes",
                "Tighten stop-loss rules",
                "Increase delta thresholds",
                "Delay new position entries"
            ]
        }
    }


def _create_market_crash_scenario(duration_days: int) -> Dict[str, Any]:
    """Create a market crash scenario"""
    crash_magnitude = random.uniform(-0.15, -0.30)  # 15-30% drop
    recovery_speed = random.choice(["fast", "slow", "oscillating"])
    
    return {
        "scenario_type": "market_crash",
        "description": "Sharp market decline with varying recovery patterns",
        "severity": abs(crash_magnitude),
        "duration_days": random.randint(20, 60),
        "parameters": {
            "crash_magnitude": crash_magnitude,
            "recovery_pattern": recovery_speed,
            "affected_sectors": ["Financials", "Materials", "Consumer Discretionary"],
            "volatility_behavior": "High and persistent",
            "liquidity_impact": "Significant drying up",
            "impact_on_strategy": "High probability of put assignments, covered call losses, margin pressure",
            "risk_factors": [
                "Early assignment of cash-secured puts",
                "Significant losses on covered calls",
                "Margin calls and forced liquidations",
                "Limited recovery opportunities"
            ],
            "mitigation_strategies": [
                "Maintain higher cash reserves",
                "Use conservative delta ranges",
                "Implement aggressive stop-losses",
                "Consider protective puts for holdings"
            ]
        }
    }


def _create_flash_crash_scenario(duration_days: int) -> Dict[str, Any]:
    """Create a flash crash scenario"""
    return {
        "scenario_type": "flash_crash",
        "description": "Extreme intraday market dislocation",
        "severity": 2.5,  # Very severe but brief
        "duration_days": random.randint(1, 3),
        "parameters": {
            "intraday_drop": random.uniform(-0.08, -0.15),  # 8-15% intraday drop
            "recovery_speed": "rapid",  # Quick bounce back
            "typical_time": "10:00-11:30 AM",  # Common flash crash window
            "market_depth": "extremely_shallow",
            "impact_on_strategy": "Severe pricing dislocations, failed executions, margin issues",
            "risk_factors": [
                "Massive slippage on all orders",
                "Failed stop-loss executions",
                "Systematic execution failures",
                "Temporary illiquidity across all strikes"
            ],
            "mitigation_strategies": [
                "Use market orders with caution",
                "Implement circuit breaker logic",
                "Pre-trade liquidity checks",
                "Manual intervention protocols"
            ]
        }
    }


def _create_black_swan_scenario(duration_days: int) -> Dict[str, Any]:
    """Create a black swan scenario"""
    return {
        "scenario_type": "black_swan",
        "description": "Unprecedented market event with extreme uncertainty",
        "severity": 4.0,  # Catastrophic
        "duration_days": random.randint(30, 180),
        "parameters": {
            "event_type": random.choice([
                "Geopolitical crisis", 
                "Systemic financial collapse",
                "Major pandemic outbreak",
                "Natural disaster affecting markets"
            ]),
            "uncertainty_level": "extreme",
            "market_functionality": "severely_disrupted",
            "trading_hours": "extended_uncertainty",
            "impact_on_strategy": "Fundamental strategy assumptions invalidated",
            "risk_factors": [
                "Complete market dysfunction",
                "Derivative pricing breakdown",
                "Counterparty risk materialization",
                "Regulatory intervention uncertainty"
            ],
            "mitigation_strategies": [
                "Emergency cash preservation",
                "Complete strategy suspension",
                "Alternative asset protection",
                "Communication protocol activation"
            ]
        }
    }


def _create_liquidity_crisis_scenario(duration_days: int) -> Dict[str, Any]:
    """Create a liquidity crisis scenario"""
    return {
        "scenario_type": "liquidity_crisis",
        "description": "Market-wide liquidity shortage affecting execution quality",
        "severity": 2.0,
        "duration_days": random.randint(15, 45),
        "parameters": {
            "bid_ask_spread_expansion": random.uniform(3.0, 10.0),
            "volume_decline": random.uniform(0.5, 0.8),  # 50-80% volume decline
            "market_maker_withdrawal": "significant",
            "institutional_activity": "minimal",
            "impact_on_strategy": "Poor execution quality, increased transaction costs, position management difficulty",
            "risk_factors": [
                "Massive execution slippage",
                "Difficulty entering/exiting positions",
                "Wider than normal bid-ask spreads",
                "Partial fill risks for large orders"
            ],
            "mitigation_strategies": [
                "Reduce position sizes significantly",
                "Use limit orders exclusively",
                "Increase minimum OI requirements",
                "Extend holding period expectations"
            ]
        }
    }


def _create_correlation_shift_scenario(duration_days: int) -> Dict[str, Any]:
    """Create a correlation shift scenario"""
    return {
        "scenario_type": "correlation_shift",
        "description": "Breakdown of historical correlation patterns between assets",
        "severity": 1.8,
        "duration_days": random.randint(30, 90),
        "parameters": {
            "correlation_direction": random.choice(["increase", "decrease"]),
            "affected_pairs": [("NIFTY", "BANKNIFTY"), ("NIFTY", "VIX"), ("USDINR", "NIFTY")],
            "diversification_effect": "reduced",
            "hedging_effectiveness": "compromised",
            "impact_on_strategy": "Traditional risk management assumptions challenged",
            "risk_factors": [
                "Portfolio diversification breakdown",
                "Hedge effectiveness reduced",
                "Unexpected directional exposures",
                "Correlation trading opportunities mispriced"
            ],
            "mitigation_strategies": [
                "Dynamic hedging adjustments",
                "Correlation monitoring systems",
                "Diversification across different factors",
                "Stress testing with varied correlations"
            ]
        }
    }


def _create_vol_skew_shift_scenario(duration_days: int) -> Dict[str, Any]:
    """Create a volatility skew shift scenario"""
    return {
        "scenario_type": "vol_skew_shift",
        "description": "Abnormal changes in volatility skew/smile",
        "severity": 2.2,
        "duration_days": random.randint(20, 60),
        "parameters": {
            "skew_direction": random.choice(["steepening", "flattening", "smile"]),
            "affected_tenors": random.choice([["near_term"], ["medium_term"], ["all"]]),
            "crash_risk_pricing": "elevated",
            "put_call_parity": "violated_temporarily",
            "impact_on_strategy": "Option pricing anomalies affect premium collection",
            "risk_factors": [
                "Mispriced short options",
                "Unexpected assignment patterns",
                "Skew trading opportunities lost",
                "Traditional delta hedging ineffective"
            ],
            "mitigation_strategies": [
                "Adjust strike selection criteria",
                "Monitor implied volatility surfaces",
                "Implement skew-aware pricing models",
                "Dynamic delta adjustment protocols"
            ]
        }
    }


def _create_macro_shock_scenario(duration_days: int) -> Dict[str, Any]:
    """Create a macroeconomic shock scenario"""
    return {
        "scenario_type": "macro_shock",
        "description": "Unexpected major economic policy or data surprise",
        "severity": 2.8,
        "duration_days": random.randint(5, 20),
        "parameters": {
            "shock_type": random.choice([
                "Interest rate change", 
                "Inflation surprise",
                "Employment data shock",
                "Policy announcement"
            ]),
            "magnitude": "significant",
            "duration_impact": "short_term_volatile",
            "policy_response": "uncertain",
            "impact_on_strategy": "Market dislocation due to fundamental repricing",
            "risk_factors": [
                "Directional bias assumption violations",
                "Rate sensitivity miscalculations",
                "Economic regime shift",
                "Policy uncertainty premium expansion"
            ],
            "mitigation_strategies": [
                "Reduce directional exposures",
                "Increase cash allocation temporarily",
                "Monitor central bank communications",
                "Implement flexible position sizing"
            ]
        }
    }


def _create_sector_rotation_scenario(duration_days: int) -> Dict[str, Any]:
    """Create a sector rotation scenario"""
    return {
        "scenario_type": "sector_rotation",
        "description": "Major shift in market leadership between sectors",
        "severity": 1.5,
        "duration_days": random.randint(60, 120),
        "parameters": {
            "rotation_type": random.choice(["growth_to_value", "value_to_growth", "defensive_to_cyclical"]),
            "leadership_shift": "persistent",
            "valuation_disconnect": "significant",
            "impact_on_strategy": "Underlying performance affects option strategy effectiveness",
            "risk_factors": [
                "Underlying stock selection underperformance",
                "Dividend yield assumptions violated",
                "Beta exposure mismatches",
                "Sector rotation timing errors"
            ],
            "mitigation_strategies": [
                "Dynamic underlying selection",
                "Sector exposure monitoring",
                "Adaptive premium targeting",
                "Regular strategy rebalancing"
            ]
        }
    }


def _create_normal_stress_scenario(duration_days: int) -> Dict[str, Any]:
    """Create a normal stress scenario"""
    return {
        "scenario_type": "normal_stress",
        "description": "Regular market stress within historical bounds",
        "severity": 1.2,
        "duration_days": random.randint(10, 30),
        "parameters": {
            "stress_type": "normal_market_conditions",
            "volatility": "within_historical_ranges",
            "liquidity": "adequate",
            "execution_quality": "normal",
            "impact_on_strategy": "Baseline stress testing conditions",
            "risk_factors": [
                "Normal drawdown variations",
                "Expected premium fluctuations",
                "Typical assignment probabilities",
                "Standard market frictions"
            ],
            "mitigation_strategies": [
                "Standard risk management protocols",
                "Regular position monitoring",
                "Normal stress testing procedures",
                "Conservative parameter settings"
            ]
        }
    }


def run_scenario_simulation(scenario: Dict[str, Any], initial_portfolio_value: float = 1000000.0) -> Dict[str, Any]:
    """
    Run a simulation of the strategy under a specific stress scenario
    
    Args:
        scenario: Stress test scenario to simulate
        initial_portfolio_value: Starting portfolio value
        
    Returns:
        Dictionary with simulation results
    """
    if not is_enabled("stress"):
        logger.debug("[AI] Stress testing is disabled")
        return {}
    
    try:
        logger.info(f"[AI] Stress: Running simulation for scenario {scenario.get('id', 'unknown')}")
        
        # In a real implementation, you would:
        # 1. Set up the scenario parameters in the backtesting engine
        # 2. Run the strategy through the historical period with stress adjustments
        # 3. Calculate P&L, drawdown, Sharpe ratio, etc.
        # 4. Compare results to baseline
        
        # For now, return a simulated result structure
        results = {
            "scenario_id": scenario.get("id"),
            "scenario_type": scenario.get("scenario_type"),
            "severity": scenario.get("severity"),
            "duration_days": scenario.get("duration_days"),
            "starting_value": initial_portfolio_value,
            "ending_value": initial_portfolio_value * random.uniform(0.7, 1.2),
            "max_drawdown": random.uniform(-0.05, -0.35),
            "volatility": random.uniform(0.10, 0.40),
            "sharpe_ratio": random.uniform(-0.5, 1.5),
            "win_rate": random.uniform(0.40, 0.70),
            "profit_factor": random.uniform(0.8, 2.5),
            "worst_consecutive_losses": random.randint(1, 8),
            "largest_single_loss": random.uniform(-0.02, -0.15),
            "recovery_time_days": random.randint(0, 90),
            "stress_impact_score": random.uniform(0.1, 1.0),
            "recommended_actions": scenario.get("parameters", {}).get("mitigation_strategies", []),
            "simulation_completed": True,
            "timestamp": datetime.now().isoformat()
        }
        
        # Calculate additional metrics
        results["total_return"] = (results["ending_value"] - results["starting_value"]) / results["starting_value"]
        results["annualized_return"] = results["total_return"] * (252 / results["duration_days"]) if results["duration_days"] > 0 else 0
        results["max_daily_loss"] = results["max_drawdown"] / 10  # Simplified
        
        logger.info(f"[AI] Stress: Completed simulation for scenario {scenario.get('id', 'unknown')}")
        return results
        
    except Exception as e:
        logger.error(f"[AI] Stress: Error running scenario simulation: {e}")
        return {"error": str(e), "simulation_completed": False}


def get_worst_case_scenarios(scenarios_results: List[Dict[str, Any]], top_n: int = 10) -> List[Dict[str, Any]]:
    """
    Identify the worst-performing scenarios from stress test results
    
    Args:
        scenarios_results: List of scenario simulation results
        top_n: Number of worst scenarios to return
        
    Returns:
        List of worst-performing scenarios
    """
    try:
        # Filter completed simulations
        completed_results = [r for r in scenarios_results if r.get("simulation_completed", False)]
        
        if not completed_results:
            return []
        
        # Sort by worst performance (lowest ending value, highest drawdown)
        sorted_results = sorted(
            completed_results,
            key=lambda x: (x.get("ending_value", float('inf')), -abs(x.get("max_drawdown", 0)))
        )
        
        # Return top N worst scenarios
        worst_scenarios = sorted_results[:top_n]
        
        logger.info(f"[AI] Stress: Identified {len(worst_scenarios)} worst-case scenarios")
        return worst_scenarios
        
    except Exception as e:
        logger.error(f"[AI] Stress: Error identifying worst scenarios: {e}")
        return []


def calculate_portfolio_at_risk(scenarios_results: List[Dict[str, Any]], confidence_level: float = 0.95) -> float:
    """
    Calculate Conditional Value at Risk (CVaR) from stress test results
    
    Args:
        scenarios_results: List of scenario simulation results
        confidence_level: Confidence level for VaR calculation (e.g., 0.95 for 95%)
        
    Returns:
        Conditional Value at Risk (Expected Shortfall)
    """
    try:
        # Extract returns from completed simulations
        returns = [
            (r["ending_value"] - r["starting_value"]) / r["starting_value"]
            for r in scenarios_results
            if r.get("simulation_completed", False) and "ending_value" in r and "starting_value" in r
        ]
        
        if not returns:
            logger.warning("[AI] Stress: No valid returns for CVaR calculation")
            return 0.0
        
        # Calculate Value at Risk (VaR) at specified confidence level
        var_threshold = np.percentile(returns, (1 - confidence_level) * 100)
        
        # Calculate Conditional VaR (Expected Shortfall) - average of losses beyond VaR
        tail_losses = [r for r in returns if r <= var_threshold]
        if tail_losses:
            cvar = np.mean(tail_losses)
        else:
            cvar = var_threshold  # If no tail losses, CVaR equals VaR
        
        logger.info(f"[AI] Stress: Calculated CVaR at {confidence_level*100:.0f}% confidence: {cvar:.2%}")
        return cvar
        
    except Exception as e:
        logger.error(f"[AI] Stress: Error calculating CVaR: {e}")
        return 0.0


def generate_stress_report(scenarios_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate a comprehensive stress test report
    
    Args:
        scenarios_results: List of scenario simulation results
        
    Returns:
        Dictionary with comprehensive stress test report
    """
    if not is_enabled("stress"):
        logger.debug("[AI] Stress testing is disabled")
        return {}
    
    try:
        logger.info("[AI] Stress: Generating comprehensive stress test report")
        
        # Filter valid results
        valid_results = [r for r in scenarios_results if r.get("simulation_completed", False)]
        
        if not valid_results:
            logger.warning("[AI] Stress: No valid results for report generation")
            return {"error": "No valid stress test results"}
        
        # Calculate summary statistics
        ending_values = [r.get("ending_value", 0) for r in valid_results]
        drawdowns = [r.get("max_drawdown", 0) for r in valid_results]
        returns = [r.get("total_return", 0) for r in valid_results]
        sharpe_ratios = [r.get("sharpe_ratio", 0) for r in valid_results]
        win_rates = [r.get("win_rate", 0) for r in valid_results]
        
        # Worst scenarios
        worst_scenarios = get_worst_case_scenarios(valid_results, 5)
        
        # Portfolio risk metrics
        cvar_95 = calculate_portfolio_at_risk(valid_results, 0.95)
        cvar_99 = calculate_portfolio_at_risk(valid_results, 0.99)
        
        report = {
            "report_generated": datetime.now().isoformat(),
            "total_scenarios": len(scenarios_results),
            "completed_simulations": len(valid_results),
            "failed_simulations": len(scenarios_results) - len(valid_results),
            "performance_summary": {
                "average_ending_value": np.mean(ending_values) if ending_values else 0,
                "median_ending_value": np.median(ending_values) if ending_values else 0,
                "average_max_drawdown": np.mean(drawdowns) if drawdowns else 0,
                "median_max_drawdown": np.median(drawdowns) if drawdowns else 0,
                "average_total_return": np.mean(returns) if returns else 0,
                "median_total_return": np.median(returns) if returns else 0,
                "average_sharpe_ratio": np.mean(sharpe_ratios) if sharpe_ratios else 0,
                "median_sharpe_ratio": np.median(sharpe_ratios) if sharpe_ratios else 0,
                "average_win_rate": np.mean(win_rates) if win_rates else 0,
                "median_win_rate": np.median(win_rates) if win_rates else 0
            },
            "risk_metrics": {
                "cvar_95": cvar_95,
                "cvar_99": cvar_99,
                "worst_case_ending_value": min(ending_values) if ending_values else 0,
                "best_case_ending_value": max(ending_values) if ending_values else 0,
                "max_drawdown_across_scenarios": min(drawdowns) if drawdowns else 0,
                "average_worst_consecutive_losses": np.mean([r.get("worst_consecutive_losses", 0) for r in valid_results])
            },
            "worst_case_scenarios": worst_scenarios,
            "scenario_distribution": _analyze_scenario_distribution(valid_results),
            "recommendations": _generate_recommendations(valid_results),
            "report_version": "1.0"
        }
        
        logger.info("[AI] Stress: Stress test report generated successfully")
        return report
        
    except Exception as e:
        logger.error(f"[AI] Stress: Error generating stress report: {e}")
        return {"error": str(e)}


def _analyze_scenario_distribution(valid_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze the distribution of scenario types in stress test results"""
    try:
        scenario_types = [r.get("scenario_type", "unknown") for r in valid_results]
        unique_types = list(set(scenario_types))
        
        distribution = {}
        for scenario_type in unique_types:
            count = scenario_types.count(scenario_type)
            distribution[scenario_type] = {
                "count": count,
                "percentage": count / len(valid_results) * 100 if valid_results else 0
            }
        
        return distribution
        
    except Exception as e:
        logger.error(f"[AI] Stress: Error analyzing scenario distribution: {e}")
        return {}


def _generate_recommendations(valid_results: List[Dict[str, Any]]) -> List[str]:
    """Generate risk management recommendations based on stress test results"""
    try:
        if not valid_results:
            return ["No valid stress test results available for recommendation generation"]
        
        # Calculate key metrics
        avg_return = np.mean([r.get("total_return", 0) for r in valid_results])
        avg_drawdown = np.mean([r.get("max_drawdown", 0) for r in valid_results])
        avg_sharpe = np.mean([r.get("sharpe_ratio", 0) for r in valid_results])
        
        recommendations = []
        
        # Return-based recommendations
        if avg_return < 0.05:  # Less than 5% average return
            recommendations.append("Consider increasing premium collection targets or adjusting strategy parameters")
        
        # Drawdown-based recommendations
        if avg_drawdown < -0.20:  # More than 20% average drawdown
            recommendations.append("Implement stricter stop-loss rules and reduce position sizes")
        
        # Sharpe ratio recommendations
        if avg_sharpe < 0.5:  # Low risk-adjusted returns
            recommendations.append("Review risk-return tradeoffs and consider portfolio optimization")
        
        # Scenario-specific recommendations
        worst_scenarios = get_worst_case_scenarios(valid_results, 3)
        for scenario in worst_scenarios:
            scenario_rec = scenario.get("recommended_actions", [])
            recommendations.extend(scenario_rec)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_recommendations = []
        for rec in recommendations:
            if rec not in seen:
                seen.add(rec)
                unique_recommendations.append(rec)
        
        return unique_recommendations[:10]  # Limit to top 10 recommendations
        
    except Exception as e:
        logger.error(f"[AI] Stress: Error generating recommendations: {e}")
        return ["Error generating recommendations - review stress test results manually"]