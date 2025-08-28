"""
Layout Intelligence System for EZ Pillow Dashboard Components.

This module provides intelligent layout selection based on data analysis,
automatically choosing the best layout type without requiring manual configuration.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import re
from .kpi_layouts import KPILayoutType


class DataImportance(Enum):
    """Levels of data importance for layout prioritization."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ContentType(Enum):
    """Types of content for specialized layout handling."""
    FINANCIAL = "financial"
    MARKETING = "marketing"
    OPERATIONAL = "operational"
    EXECUTIVE = "executive"
    TECHNICAL = "technical"
    GENERIC = "generic"


@dataclass
class LayoutAnalysis:
    """Results of layout analysis with recommendations."""
    recommended_layout: KPILayoutType
    confidence: float
    reasoning: str
    alternative_layouts: List[KPILayoutType]
    detected_importance_levels: List[DataImportance]
    content_type: ContentType


class LayoutIntelligenceEngine:
    """
    Intelligent engine that analyzes data and automatically selects optimal layouts.

    Uses heuristics based on:
    - Number of KPIs
    - Value patterns and importance
    - Content type detection
    - Visual hierarchy needs
    """

    def __init__(self):
        """Initialize the intelligence engine with pattern definitions."""
        self.financial_patterns = [
            r'revenue|profit|margin|cost|ebitda|roi|roas',
            r'€|£|\$|%|k€|m€|k\$|m\$',
            r'quarterly|monthly|ytd|yoy|qoq'
        ]

        self.marketing_patterns = [
            r'users?|customers?|visitors?|traffic|conversion|ctr|cpc|cpm',
            r'acquisition|retention|churn|ltv|cac|funnel',
            r'impressions?|clicks?|views?|engagement'
        ]

        self.executive_patterns = [
            r'kpi|dashboard|performance|growth|target',
            r'strategic|overview|summary|executive',
            r'quarter|annual|goals?'
        ]

        # Value importance indicators
        self.high_value_indicators = [
            r'total|main|primary|key|principal|core',
            r'overall|global|company|business'
        ]

        self.temporal_indicators = [
            r'daily|weekly|monthly|quarterly|yearly|ytd|mtd|qtd'
        ]

    def analyze_kpi_data(self, kpi_data: List[Dict[str, Any]]) -> LayoutAnalysis:
        """
        Analyze KPI data and recommend optimal layout.

        Args:
            kpi_data: List of KPI dictionaries

        Returns:
            LayoutAnalysis with recommendations
        """
        if not kpi_data:
            return LayoutAnalysis(
                recommended_layout=KPILayoutType.HORIZONTAL,
                confidence=1.0,
                reasoning="No KPIs provided",
                alternative_layouts=[],
                detected_importance_levels=[],
                content_type=ContentType.GENERIC
            )

        # Basic analysis
        kpi_count = len(kpi_data)
        content_type = self._detect_content_type(kpi_data)
        importance_levels = self._analyze_importance_levels(kpi_data)
        value_patterns = self._analyze_value_patterns(kpi_data)

        # Layout recommendation logic
        layout, confidence, reasoning, alternatives = self._recommend_layout(
            kpi_count, content_type, importance_levels, value_patterns
        )

        return LayoutAnalysis(
            recommended_layout=layout,
            confidence=confidence,
            reasoning=reasoning,
            alternative_layouts=alternatives,
            detected_importance_levels=importance_levels,
            content_type=content_type
        )

    def _detect_content_type(self, kpi_data: List[Dict[str, Any]]) -> ContentType:
        """Detect the type of content based on KPI titles and values."""
        all_text = " ".join([
            str(kpi.get("title", "")).lower() + " " + str(kpi.get("value", "")).lower()
            for kpi in kpi_data
        ])

        financial_score = sum(1 for pattern in self.financial_patterns
                            if re.search(pattern, all_text, re.IGNORECASE))
        marketing_score = sum(1 for pattern in self.marketing_patterns
                            if re.search(pattern, all_text, re.IGNORECASE))
        executive_score = sum(1 for pattern in self.executive_patterns
                            if re.search(pattern, all_text, re.IGNORECASE))

        if financial_score >= 2:
            return ContentType.FINANCIAL
        elif marketing_score >= 2:
            return ContentType.MARKETING
        elif executive_score >= 1:
            return ContentType.EXECUTIVE
        else:
            return ContentType.GENERIC

    def _analyze_importance_levels(self, kpi_data: List[Dict[str, Any]]) -> List[DataImportance]:
        """Analyze importance levels of each KPI."""
        importance_levels = []

        for kpi in kpi_data:
            title = str(kpi.get("title", "")).lower()
            value = str(kpi.get("value", "")).lower()
            delta = kpi.get("delta", {})

            # Check for high importance indicators
            is_high_importance = any(
                re.search(pattern, title, re.IGNORECASE)
                for pattern in self.high_value_indicators
            )

            # Check delta magnitude
            delta_pct = abs(delta.get("pct", 0)) if isinstance(delta, dict) else 0

            # Check value magnitude (rough heuristic)
            has_large_numbers = re.search(r'[0-9]{4,}|[0-9]+[km]', value)

            if is_high_importance or delta_pct > 25:
                importance_levels.append(DataImportance.CRITICAL)
            elif delta_pct > 15 or has_large_numbers:
                importance_levels.append(DataImportance.HIGH)
            elif delta_pct > 5:
                importance_levels.append(DataImportance.MEDIUM)
            else:
                importance_levels.append(DataImportance.LOW)

        return importance_levels

    def _analyze_value_patterns(self, kpi_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns in KPI values and deltas."""
        patterns = {
            "has_large_variations": False,
            "has_hierarchy": False,
            "has_temporal_data": False,
            "mixed_data_types": False,
            "primary_metric_detected": False
        }

        deltas = []
        for kpi in kpi_data:
            delta = kpi.get("delta", {})
            if isinstance(delta, dict) and "pct" in delta:
                deltas.append(abs(delta["pct"]))

        # Check for large variations in deltas
        if deltas and (max(deltas) - min(deltas)) > 20:
            patterns["has_large_variations"] = True

        # Check for hierarchy indicators in titles
        titles = [str(kpi.get("title", "")).lower() for kpi in kpi_data]
        patterns["has_hierarchy"] = any(
            any(re.search(pattern, title) for pattern in self.high_value_indicators)
            for title in titles
        )

        # Check for temporal indicators
        all_text = " ".join(titles)
        patterns["has_temporal_data"] = any(
            re.search(pattern, all_text) for pattern in self.temporal_indicators
        )

        # Check if first KPI seems to be primary
        if kpi_data and titles:
            first_title = titles[0]
            patterns["primary_metric_detected"] = any(
                re.search(pattern, first_title) for pattern in self.high_value_indicators
            )

        return patterns

    def _recommend_layout(self, count: int, content_type: ContentType,
                         importance_levels: List[DataImportance],
                         patterns: Dict[str, Any]) -> Tuple[KPILayoutType, float, str, List[KPILayoutType]]:
        """
        Core layout recommendation logic.

        Returns:
            Tuple of (layout, confidence, reasoning, alternatives)
        """

        # Handle edge cases
        if count == 0:
            return KPILayoutType.HORIZONTAL, 1.0, "No KPIs to display", []

        if count == 1:
            return KPILayoutType.HORIZONTAL, 1.0, "Single KPI uses simple horizontal layout", []

        # Check for clear hierarchy patterns
        critical_count = importance_levels.count(DataImportance.CRITICAL)
        high_count = importance_levels.count(DataImportance.HIGH)

        if critical_count == 1 and count <= 5:
            return (KPILayoutType.PRIORITY, 0.9,
                   "One critical metric detected, using priority layout to emphasize it",
                   [KPILayoutType.FEATURED, KPILayoutType.HORIZONTAL])

        if patterns.get("primary_metric_detected") and count <= 4:
            return (KPILayoutType.FEATURED, 0.85,
                   "Primary metric detected in first position, using featured layout",
                   [KPILayoutType.PRIORITY, KPILayoutType.HORIZONTAL])

        # Content-type specific recommendations
        if content_type == ContentType.FINANCIAL:
            return self._financial_layout_recommendation(count, patterns, importance_levels)
        elif content_type == ContentType.EXECUTIVE:
            return self._executive_layout_recommendation(count, patterns)
        elif content_type == ContentType.MARKETING:
            return self._marketing_layout_recommendation(count, patterns)

        # Generic count-based recommendations
        return self._count_based_recommendation(count, patterns, importance_levels)

    def _financial_layout_recommendation(self, count: int, patterns: Dict[str, Any],
                                       importance_levels: List[DataImportance]) -> Tuple[KPILayoutType, float, str, List[KPILayoutType]]:
        """Financial-specific layout recommendations."""
        if count <= 3:
            return (KPILayoutType.HORIZONTAL, 0.8,
                   "Financial metrics with few KPIs use horizontal layout for clarity",
                   [KPILayoutType.PRIORITY])

        if count == 4 and patterns.get("has_hierarchy"):
            return (KPILayoutType.PRIORITY, 0.85,
                   "Financial dashboard with hierarchy uses priority layout",
                   [KPILayoutType.GRID_2x3, KPILayoutType.HORIZONTAL])

        if count == 6:
            return (KPILayoutType.GRID_2x3, 0.9,
                   "Six financial metrics fit well in 2x3 grid for easy comparison",
                   [KPILayoutType.PYRAMID, KPILayoutType.RESPONSIVE])

        return (KPILayoutType.RESPONSIVE, 0.7,
               "Financial metrics use responsive layout for optimal arrangement",
               [KPILayoutType.GRID_2x3, KPILayoutType.PYRAMID])

    def _executive_layout_recommendation(self, count: int, patterns: Dict[str, Any]) -> Tuple[KPILayoutType, float, str, List[KPILayoutType]]:
        """Executive dashboard specific recommendations."""
        if count <= 4:
            return (KPILayoutType.PRIORITY, 0.9,
                   "Executive dashboard emphasizes key metrics with priority layout",
                   [KPILayoutType.FEATURED, KPILayoutType.HORIZONTAL])

        if count <= 6:
            return (KPILayoutType.FEATURED, 0.85,
                   "Executive summary uses featured layout for main metric emphasis",
                   [KPILayoutType.PRIORITY, KPILayoutType.PYRAMID])

        return (KPILayoutType.PYRAMID, 0.8,
               "Executive overview with many metrics uses pyramid for hierarchy",
               [KPILayoutType.RESPONSIVE, KPILayoutType.GRID_2x3])

    def _marketing_layout_recommendation(self, count: int, patterns: Dict[str, Any]) -> Tuple[KPILayoutType, float, str, List[KPILayoutType]]:
        """Marketing-specific layout recommendations."""
        if count <= 4:
            return (KPILayoutType.HORIZONTAL, 0.85,
                   "Marketing metrics displayed horizontally for easy comparison",
                   [KPILayoutType.PRIORITY])

        if patterns.get("has_temporal_data"):
            return (KPILayoutType.GRID_2x3, 0.8,
                   "Temporal marketing data organized in grid for trend analysis",
                   [KPILayoutType.RESPONSIVE, KPILayoutType.PYRAMID])

        return (KPILayoutType.RESPONSIVE, 0.75,
               "Marketing metrics use responsive layout for optimal display",
               [KPILayoutType.GRID_2x3, KPILayoutType.HORIZONTAL])

    def _count_based_recommendation(self, count: int, patterns: Dict[str, Any],
                                  importance_levels: List[DataImportance]) -> Tuple[KPILayoutType, float, str, List[KPILayoutType]]:
        """Fallback count-based recommendations."""
        if count <= 2:
            return (KPILayoutType.HORIZONTAL, 0.9,
                   f"Simple horizontal layout for {count} KPIs",
                   [])

        if count == 3:
            if patterns.get("has_hierarchy"):
                return (KPILayoutType.PRIORITY, 0.8,
                       "Three KPIs with hierarchy use priority layout",
                       [KPILayoutType.HORIZONTAL, KPILayoutType.FEATURED])
            return (KPILayoutType.HORIZONTAL, 0.85,
                   "Three KPIs displayed horizontally",
                   [KPILayoutType.PRIORITY])

        if count == 4:
            return (KPILayoutType.HORIZONTAL, 0.8,
                   "Four KPIs in horizontal layout",
                   [KPILayoutType.GRID_2x3, KPILayoutType.PRIORITY])

        if count == 5:
            return (KPILayoutType.PRIORITY, 0.85,
                   "Five KPIs use priority layout for visual balance",
                   [KPILayoutType.RESPONSIVE, KPILayoutType.PYRAMID])

        if count == 6:
            return (KPILayoutType.GRID_2x3, 0.9,
                   "Six KPIs arranged in 2x3 grid",
                   [KPILayoutType.PYRAMID, KPILayoutType.RESPONSIVE])

        if count <= 8:
            return (KPILayoutType.GRID_3x2, 0.8,
                   f"{count} KPIs arranged in grid layout",
                   [KPILayoutType.RESPONSIVE, KPILayoutType.PYRAMID])

        return (KPILayoutType.PYRAMID, 0.75,
               f"Many KPIs ({count}) use pyramid layout for hierarchy",
               [KPILayoutType.RESPONSIVE, KPILayoutType.GRID_3x2])

    def suggest_layout_automatically(self, kpi_data: List[Dict[str, Any]],
                                   user_preference: Optional[str] = None) -> KPILayoutType:
        """
        Main entry point for automatic layout suggestion.

        Args:
            kpi_data: List of KPI data
            user_preference: Optional user override

        Returns:
            Recommended KPILayoutType
        """
        # If user specifies a preference, validate and use it
        if user_preference:
            try:
                # Try to match user preference to KPILayoutType
                preference_mapping = {
                    "horizontal": KPILayoutType.HORIZONTAL,
                    "grid": KPILayoutType.GRID_2x3,
                    "grid_2x3": KPILayoutType.GRID_2x3,
                    "grid_3x2": KPILayoutType.GRID_3x2,
                    "priority": KPILayoutType.PRIORITY,
                    "pyramid": KPILayoutType.PYRAMID,
                    "featured": KPILayoutType.FEATURED,
                    "responsive": KPILayoutType.RESPONSIVE,
                    "auto": None  # Signal to use automatic
                }

                if user_preference.lower() in preference_mapping:
                    layout = preference_mapping[user_preference.lower()]
                    if layout is not None:
                        return layout
            except (AttributeError, KeyError):
                pass  # Fall through to automatic detection

        # Use intelligent analysis
        analysis = self.analyze_kpi_data(kpi_data)
        return analysis.recommended_layout

    def get_layout_explanation(self, kpi_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get detailed explanation of layout choice for debugging/transparency.

        Returns:
            Dictionary with analysis details and reasoning
        """
        analysis = self.analyze_kpi_data(kpi_data)

        return {
            "recommended_layout": analysis.recommended_layout.value,
            "confidence": analysis.confidence,
            "reasoning": analysis.reasoning,
            "alternatives": [alt.value for alt in analysis.alternative_layouts],
            "content_type": analysis.content_type.value,
            "importance_levels": [level.value for level in analysis.detected_importance_levels],
            "kpi_count": len(kpi_data),
            "analysis_summary": {
                "has_critical_metrics": DataImportance.CRITICAL in analysis.detected_importance_levels,
                "detected_hierarchy": len(set(analysis.detected_importance_levels)) > 2,
                "content_specialization": analysis.content_type != ContentType.GENERIC
            }
        }


# Factory function for easy usage
def create_layout_intelligence() -> LayoutIntelligenceEngine:
    """Create a new layout intelligence engine."""
    return LayoutIntelligenceEngine()


# Convenience function for quick layout suggestion
def suggest_smart_layout(kpi_data: List[Dict[str, Any]],
                        user_preference: Optional[str] = None) -> KPILayoutType:
    """
    Quick function to get smart layout suggestion.

    Args:
        kpi_data: List of KPI data dictionaries
        user_preference: Optional user layout preference

    Returns:
        Recommended KPILayoutType
    """
    engine = create_layout_intelligence()
    return engine.suggest_layout_automatically(kpi_data, user_preference)
