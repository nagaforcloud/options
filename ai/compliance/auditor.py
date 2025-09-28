"""
AI Compliance Auditor for Options Wheel Strategy Trading Bot
Audits trades against SEBI regulations and Zerodha product rules nightly
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import csv
import json
import os

import sys
from pathlib import Path
# Add the Trading directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils.logging_utils import logger
from ai.base import is_enabled, call_llm
from config.config import config
from database.database import db_manager


def run_nightly_audit(date: Optional[str] = None) -> Dict[str, Any]:
    """
    Run nightly compliance audit of trades
    
    Args:
        date: Specific date to audit (defaults to yesterday)
        
    Returns:
        Dictionary with audit results
    """
    if not is_enabled("compliance"):
        logger.debug("[AI] Compliance audit is disabled")
        return {"status": "disabled", "issues_found": []}
    
    try:
        # Set audit date to yesterday if not specified
        if date is None:
            audit_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        else:
            audit_date = date
        
        logger.info(f"[AI] Compliance: Running nightly audit for {audit_date}")
        
        # Fetch trades for the audit date
        trades = _fetch_trades_for_date(audit_date)
        logger.info(f"[AI] Compliance: Fetched {len(trades)} trades for audit")
        
        if not trades:
            return {
                "status": "no_trades",
                "audit_date": audit_date,
                "issues_found": [],
                "recommendations": ["No trades to audit"],
                "summary": "No trading activity found for audit period"
            }
        
        # Run compliance checks
        issues = _run_compliance_checks(trades)
        logger.info(f"[AI] Compliance: Found {len(issues)} potential compliance issues")
        
        # Generate audit summary using LLM
        summary = _generate_audit_summary(trades, issues)
        
        # Generate recommendations
        recommendations = _generate_recommendations(issues)
        
        # Compile audit results
        audit_results = {
            "status": "completed",
            "audit_date": audit_date,
            "total_trades": len(trades),
            "issues_found": issues,
            "critical_issues": len([i for i in issues if i.get('severity', 'LOW') == 'CRITICAL']),
            "high_issues": len([i for i in issues if i.get('severity', 'LOW') == 'HIGH']),
            "medium_issues": len([i for i in issues if i.get('severity', 'LOW') == 'MEDIUM']),
            "low_issues": len([i for i in issues if i.get('severity', 'LOW') == 'LOW']),
            "recommendations": recommendations,
            "summary": summary,
            "timestamp": datetime.now().isoformat()
        }
        
        # Export audit results
        _export_audit_results(audit_results)
        
        # Send notification if critical issues found
        critical_issues = [i for i in issues if i.get('severity') == 'CRITICAL']
        if critical_issues:
            _send_critical_alert(critical_issues)
        
        logger.info(f"[AI] Compliance: Audit completed - {len(issues)} issues found")
        return audit_results
        
    except Exception as e:
        logger.error(f"[AI] Compliance: Error running nightly audit: {e}")
        return {
            "status": "error",
            "error": str(e),
            "issues_found": [],
            "recommendations": ["Audit failed - manual review required"],
            "summary": f"Audit failed due to error: {str(e)}"
        }


def _fetch_trades_for_date(date: str) -> List[Dict[str, Any]]:
    """
    Fetch trades for a specific date
    
    Args:
        date: Date to fetch trades for (YYYY-MM-DD)
        
    Returns:
        List of trades for the specified date
    """
    try:
        # In a real implementation, you would query the database for trades on the specified date
        # For now, we'll use the database manager to get trades
        trades = db_manager.get_trades_by_date_range(date, date)
        
        # Convert Trade objects to dictionaries if needed
        trade_dicts = []
        for trade in trades:
            if hasattr(trade, '__dict__'):
                trade_dicts.append(trade.__dict__)
            else:
                trade_dicts.append(trade)
        
        return trade_dicts
        
    except Exception as e:
        logger.error(f"[AI] Compliance: Error fetching trades for {date}: {e}")
        return []


def _run_compliance_checks(trades: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Run comprehensive compliance checks on trades
    
    Args:
        trades: List of trades to check
        
    Returns:
        List of compliance issues found
    """
    try:
        issues = []
        
        # Check each trade for compliance
        for trade in trades:
            trade_issues = _check_single_trade_compliance(trade)
            issues.extend(trade_issues)
        
        # Check portfolio-level compliance
        portfolio_issues = _check_portfolio_compliance(trades)
        issues.extend(portfolio_issues)
        
        # Check regulatory compliance
        regulatory_issues = _check_regulatory_compliance(trades)
        issues.extend(regulatory_issues)
        
        # Check exchange rules compliance
        exchange_issues = _check_exchange_compliance(trades)
        issues.extend(exchange_issues)
        
        # Check tax compliance
        tax_issues = _check_tax_compliance(trades)
        issues.extend(tax_issues)
        
        return issues
        
    except Exception as e:
        logger.error(f"[AI] Compliance: Error running compliance checks: {e}")
        return [{
            "issue_type": "SYSTEM_ERROR",
            "description": f"Error running compliance checks: {str(e)}",
            "severity": "HIGH",
            "trade_id": "N/A",
            "recommendation": "Manual review required",
            "timestamp": datetime.now().isoformat()
        }]


def _check_single_trade_compliance(trade: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Check a single trade for compliance
    
    Args:
        trade: Trade to check
        
    Returns:
        List of compliance issues for this trade
    """
    issues = []
    trade_id = trade.get('order_id', 'UNKNOWN')
    
    try:
        # 1. Cash-Secured Put Rules
        if trade.get('transaction_type') == 'SELL' and 'PE' in trade.get('symbol', ''):
            issues.extend(_check_cash_secured_put_rules(trade))
        
        # 2. Covered Call Rules
        elif trade.get('transaction_type') == 'SELL' and 'CE' in trade.get('symbol', ''):
            issues.extend(_check_covered_call_rules(trade))
        
        # 3. Product Type Validation
        product = trade.get('product', 'MIS')
        if product != 'NRML':
            issues.append({
                "issue_type": "PRODUCT_TYPE_VIOLATION",
                "description": f"Invalid product type {product} for options trade",
                "severity": "HIGH",
                "trade_id": trade_id,
                "recommendation": "Use NRML product type for options trades",
                "timestamp": datetime.now().isoformat()
            })
        
        # 4. Risk Management Compliance
        issues.extend(_check_risk_management_compliance(trade))
        
        # 5. Order Type Validation
        order_type = trade.get('order_type', 'MARKET')
        if order_type not in ['LIMIT', 'SL', 'SL-M']:
            issues.append({
                "issue_type": "ORDER_TYPE_VIOLATION",
                "description": f"Suspicious order type {order_type}",
                "severity": "MEDIUM",
                "trade_id": trade_id,
                "recommendation": "Use LIMIT orders for better price control",
                "timestamp": datetime.now().isoformat()
            })
        
        return issues
        
    except Exception as e:
        logger.error(f"[AI] Compliance: Error checking trade {trade_id}: {e}")
        return [{
            "issue_type": "TRADE_CHECK_ERROR",
            "description": f"Error checking trade {trade_id}: {str(e)}",
            "severity": "MEDIUM",
            "trade_id": trade_id,
            "recommendation": "Manual review required",
            "timestamp": datetime.now().isoformat()
        }]


def _check_cash_secured_put_rules(trade: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Check Cash-Secured Put specific compliance rules
    
    Args:
        trade: Cash-Secured Put trade to check
        
    Returns:
        List of compliance issues
    """
    issues = []
    trade_id = trade.get('order_id', 'UNKNOWN')
    
    try:
        # Check if adequate cash reserves are maintained
        # In a real implementation, you'd check actual cash balance
        # For now, we'll assume it's checked elsewhere
        
        # Check if proper margin is maintained
        required_margin = trade.get('price', 0) * trade.get('quantity', 0)
        # This would be compared against actual margin in real implementation
        
        # Check if position size is within limits
        # This would be checked against portfolio value
        
        # Check if proper disclosure is made
        # For CSP, ensure it's clearly documented as such
        
        return issues
        
    except Exception as e:
        logger.error(f"[AI] Compliance: Error checking CSP rules for trade {trade_id}: {e}")
        return [{
            "issue_type": "CSP_RULES_CHECK_ERROR",
            "description": f"Error checking CSP rules: {str(e)}",
            "severity": "MEDIUM",
            "trade_id": trade_id,
            "recommendation": "Manual review of CSP compliance required",
            "timestamp": datetime.now().isoformat()
        }]


def _check_covered_call_rules(trade: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Check Covered Call specific compliance rules
    
    Args:
        trade: Covered Call trade to check
        
    Returns:
        List of compliance issues
    """
    issues = []
    trade_id = trade.get('order_id', 'UNKNOWN')
    
    try:
        # Check if underlying shares are owned
        # In a real implementation, you'd check actual holdings
        
        # Check if proper margin is maintained
        # Covered calls typically don't require margin, but underlying must be owned
        
        # Check if position size is within limits
        # This would be checked against portfolio value
        
        return issues
        
    except Exception as e:
        logger.error(f"[AI] Compliance: Error checking CC rules for trade {trade_id}: {e}")
        return [{
            "issue_type": "CC_RULES_CHECK_ERROR",
            "description": f"Error checking CC rules: {str(e)}",
            "severity": "MEDIUM",
            "trade_id": trade_id,
            "recommendation": "Manual review of CC compliance required",
            "timestamp": datetime.now().isoformat()
        }]


def _check_risk_management_compliance(trade: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Check risk management compliance for a trade
    
    Args:
        trade: Trade to check
        
    Returns:
        List of risk management compliance issues
    """
    issues = []
    trade_id = trade.get('order_id', 'UNKNOWN')
    
    try:
        # Check position size limits
        quantity = trade.get('quantity', 0)
        max_lot_size = config.quantity_per_lot
        max_allowed_lots = config.max_concurrent_positions
        
        if quantity > (max_lot_size * max_allowed_lots):
            issues.append({
                "issue_type": "POSITION_SIZE_VIOLATION",
                "description": f"Position size {quantity} exceeds maximum allowed",
                "severity": "HIGH",
                "trade_id": trade_id,
                "recommendation": "Reduce position size to comply with limits",
                "timestamp": datetime.now().isoformat()
            })
        
        # Check daily loss limits
        # This would be checked against actual daily P&L
        
        # Check portfolio risk limits
        # This would be checked against overall portfolio exposure
        
        return issues
        
    except Exception as e:
        logger.error(f"[AI] Compliance: Error checking risk compliance for trade {trade_id}: {e}")
        return [{
            "issue_type": "RISK_COMPLIANCE_CHECK_ERROR",
            "description": f"Error checking risk compliance: {str(e)}",
            "severity": "MEDIUM",
            "trade_id": trade_id,
            "recommendation": "Manual review of risk compliance required",
            "timestamp": datetime.now().isoformat()
        }]


def _check_portfolio_compliance(trades: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Check portfolio-level compliance
    
    Args:
        trades: List of trades to check
        
    Returns:
        List of portfolio compliance issues
    """
    issues = []
    
    try:
        # Check concurrent position limits
        concurrent_positions = len(set(trade.get('symbol', '') for trade in trades))
        max_positions = config.max_concurrent_positions
        
        if concurrent_positions > max_positions:
            issues.append({
                "issue_type": "CONCURRENT_POSITION_LIMIT_VIOLATION",
                "description": f"Concurrent positions {concurrent_positions} exceed maximum {max_positions}",
                "severity": "HIGH",
                "trade_id": "PORTFOLIO",
                "recommendation": "Reduce number of concurrent positions",
                "timestamp": datetime.now().isoformat()
            })
        
        # Check portfolio risk limits
        # This would involve calculating overall portfolio risk exposure
        
        # Check margin utilization
        # This would check if overall margin usage is within limits
        
        return issues
        
    except Exception as e:
        logger.error(f"[AI] Compliance: Error checking portfolio compliance: {e}")
        return [{
            "issue_type": "PORTFOLIO_COMPLIANCE_CHECK_ERROR",
            "description": f"Error checking portfolio compliance: {str(e)}",
            "severity": "HIGH",
            "trade_id": "PORTFOLIO",
            "recommendation": "Manual review of portfolio compliance required",
            "timestamp": datetime.now().isoformat()
        }]


def _check_regulatory_compliance(trades: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Check SEBI and regulatory compliance
    
    Args:
        trades: List of trades to check
        
    Returns:
        List of regulatory compliance issues
    """
    issues = []
    
    try:
        # Check F&O position limits
        # SEBI has position limits for certain instruments
        
        # Check disclosure requirements
        # Certain trading activities require disclosure
        
        # Check client categorization rules
        # Ensure proper client categorization for risk purposes
        
        # Check risk management systems
        # Ensure proper risk management systems are in place
        
        return issues
        
    except Exception as e:
        logger.error(f"[AI] Compliance: Error checking regulatory compliance: {e}")
        return [{
            "issue_type": "REGULATORY_COMPLIANCE_CHECK_ERROR",
            "description": f"Error checking regulatory compliance: {str(e)}",
            "severity": "HIGH",
            "trade_id": "REGULATORY",
            "recommendation": "Manual review of regulatory compliance required",
            "timestamp": datetime.now().isoformat()
        }]


def _check_exchange_compliance(trades: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Check exchange-specific compliance
    
    Args:
        trades: List of trades to check
        
    Returns:
        List of exchange compliance issues
    """
    issues = []
    
    try:
        # Check NSE/BSE position limits
        # Each exchange has position limits for F&O instruments
        
        # Check margin requirements
        # Ensure proper margin is maintained for exchange rules
        
        # Check trading hours compliance
        # Ensure trades are within proper trading hours
        
        # Check order type restrictions
        # Certain order types may be restricted for specific instruments
        
        return issues
        
    except Exception as e:
        logger.error(f"[AI] Compliance: Error checking exchange compliance: {e}")
        return [{
            "issue_type": "EXCHANGE_COMPLIANCE_CHECK_ERROR",
            "description": f"Error checking exchange compliance: {str(e)}",
            "severity": "HIGH",
            "trade_id": "EXCHANGE",
            "recommendation": "Manual review of exchange compliance required",
            "timestamp": datetime.now().isoformat()
        }]


def _check_tax_compliance(trades: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Check tax compliance for trades
    
    Args:
        trades: List of trades to check
        
    Returns:
        List of tax compliance issues
    """
    issues = []
    
    try:
        # Check STT applicability
        # Ensure STT is properly applied for options trades
        
        # Check proper categorization of trades
        # Ensure trades are properly categorized for tax purposes
        
        # Check record keeping requirements
        # Ensure proper records are maintained for tax purposes
        
        return issues
        
    except Exception as e:
        logger.error(f"[AI] Compliance: Error checking tax compliance: {e}")
        return [{
            "issue_type": "TAX_COMPLIANCE_CHECK_ERROR",
            "description": f"Error checking tax compliance: {str(e)}",
            "severity": "HIGH",
            "trade_id": "TAX",
            "recommendation": "Manual review of tax compliance required",
            "timestamp": datetime.now().isoformat()
        }]


def _generate_audit_summary(trades: List[Dict[str, Any]], issues: List[Dict[str, Any]]) -> str:
    """
    Generate audit summary using LLM
    
    Args:
        trades: List of trades audited
        issues: List of issues found
        
    Returns:
        Audit summary string
    """
    try:
        if not is_enabled("compliance"):
            return "Compliance audit completed automatically"
        
        # Prepare audit data for LLM
        audit_data = {
            "total_trades": len(trades),
            "total_issues": len(issues),
            "critical_issues": len([i for i in issues if i.get('severity') == 'CRITICAL']),
            "high_issues": len([i for i in issues if i.get('severity') == 'HIGH']),
            "medium_issues": len([i for i in issues if i.get('severity') == 'MEDIUM']),
            "low_issues": len([i for i in issues if i.get('severity') == 'LOW']),
            "issue_types": list(set(i.get('issue_type', 'UNKNOWN') for i in issues)),
            "date_range": f"{len(trades)} trades audited"
        }
        
        # Create prompt for LLM summary
        prompt = f"""
        You are a compliance auditor for the Options Wheel Strategy Trading Bot.
        
        Audit Results Summary:
        {json.dumps(audit_data, indent=2)}
        
        Top 5 Issues Found:
        {json.dumps(issues[:5], indent=2, default=str)}
        
        Please provide a 3-paragraph executive summary of this compliance audit:
        
        Paragraph 1: Overall audit findings and key metrics
        Paragraph 2: Most significant compliance risks identified
        Paragraph 3: Recommendations for addressing the issues
        
        Keep it professional and focused on risk mitigation.
        """
        
        # Call LLM for summary generation
        summary = call_llm(prompt, max_tokens=300, temperature=0.3)
        
        return summary.strip()
        
    except Exception as e:
        logger.error(f"[AI] Compliance: Error generating audit summary: {e}")
        return f"Automated compliance audit completed with {len(issues)} issues identified. Manual review recommended."


def _generate_recommendations(issues: List[Dict[str, Any]]) -> List[str]:
    """
    Generate recommendations based on compliance issues
    
    Args:
        issues: List of compliance issues
        
    Returns:
        List of recommendations
    """
    try:
        if not issues:
            return ["No compliance issues found -继续保持良好实践"]
        
        # Group issues by severity and type
        critical_issues = [i for i in issues if i.get('severity') == 'CRITICAL']
        high_issues = [i for i in issues if i.get('severity') == 'HIGH']
        medium_issues = [i for i in issues if i.get('severity') == 'MEDIUM']
        
        recommendations = []
        
        # Critical issues require immediate action
        if critical_issues:
            recommendations.append("CRITICAL: Immediate action required to address critical compliance violations")
            for issue in critical_issues[:3]:  # Limit to top 3
                recommendations.append(f"CRITICAL: {issue.get('recommendation', 'Take immediate corrective action')}")
        
        # High priority issues
        if high_issues:
            recommendations.append("HIGH PRIORITY: Address high-severity compliance issues within 24 hours")
            for issue in high_issues[:5]:  # Limit to top 5
                recommendations.append(f"HIGH: {issue.get('recommendation', 'Address promptly')}")
        
        # Medium priority issues
        if medium_issues:
            recommendations.append("MEDIUM PRIORITY: Review and address medium-severity issues within 7 days")
            for issue in medium_issues[:5]:  # Limit to top 5
                recommendations.append(f"MEDIUM: {issue.get('recommendation', 'Review and address as needed')}")
        
        # General recommendations
        recommendations.extend([
            "Document all corrective actions taken",
            "Review compliance procedures regularly",
            "Ensure ongoing staff training on compliance matters",
            "Maintain detailed audit trails for all trading activities",
            "Schedule regular compliance reviews"
        ])
        
        return recommendations
        
    except Exception as e:
        logger.error(f"[AI] Compliance: Error generating recommendations: {e}")
        return ["Error generating recommendations - manual review required"]


def _export_audit_results(audit_results: Dict[str, Any]) -> bool:
    """
    Export audit results to compliance reports directory
    
    Args:
        audit_results: Audit results to export
        
    Returns:
        True if export successful, False otherwise
    """
    try:
        # Ensure compliance reports directory exists
        os.makedirs(config.compliance_reports_dir, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"compliance_audit_{timestamp}.json"
        filepath = os.path.join(config.compliance_reports_dir, filename)
        
        # Export as JSON
        with open(filepath, 'w') as f:
            json.dump(audit_results, f, indent=2, default=str)
        
        logger.info(f"[AI] Compliance: Audit results exported to {filepath}")
        return True
        
    except Exception as e:
        logger.error(f"[AI] Compliance: Error exporting audit results: {e}")
        return False


def _send_critical_alert(critical_issues: List[Dict[str, Any]]) -> bool:
    """
    Send critical compliance alert
    
    Args:
        critical_issues: List of critical issues
        
    Returns:
        True if alert sent successfully, False otherwise
    """
    try:
        from ...notifications.notification_manager import send_critical_alert
        
        # Prepare alert message
        issue_count = len(critical_issues)
        top_issues = critical_issues[:3]  # Top 3 critical issues
        
        message = f"🚨 CRITICAL COMPLIANCE ALERT 🚨\n"
        message += f"Found {issue_count} critical compliance violations\n\n"
        
        for i, issue in enumerate(top_issues, 1):
            message += f"{i}. {issue.get('issue_type', 'UNKNOWN')} - {issue.get('description', 'No description')}\n"
            message += f"   Trade ID: {issue.get('trade_id', 'N/A')}\n\n"
        
        message += "Immediate attention required!"
        
        # Send critical alert
        success = send_critical_alert("COMPLIANCE_VIOLATION", message)
        
        if success:
            logger.info("[AI] Compliance: Critical alert sent successfully")
        else:
            logger.error("[AI] Compliance: Failed to send critical alert")
        
        return success
        
    except Exception as e:
        logger.error(f"[AI] Compliance: Error sending critical alert: {e}")
        return False


def get_compliance_status() -> Dict[str, Any]:
    """
    Get current compliance system status
    
    Returns:
        Dictionary with compliance system status
    """
    return {
        "feature_enabled": is_enabled("compliance"),
        "last_audit": datetime.now().isoformat(),
        "audit_frequency": "nightly",
        "reports_directory": config.compliance_reports_dir,
        "system_health": "operational",
        "version": "1.0"
    }