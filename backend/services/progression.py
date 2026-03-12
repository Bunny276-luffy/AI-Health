from typing import Dict, Any
import random
import math

class ProgressionAnalyzerMock:
    """
    Simulates longitudinal tumor progression analysis by comparing
    a baseline scan with a current scan to detect changes.
    """
    
    def analyze(self, baseline_content: bytes, current_content: bytes) -> Dict[str, Any]:
        """
        Simulates measuring tumor volume changes between two scans.
        """
        # In a real model, this would compute 3D volume or 2D cross-sectional area
        baseline_volume_mm3 = random.uniform(120.0, 500.0)
        
        # Simulate an outcome: 30% shrinking, 30% stable, 40% growing
        outcome_prob = random.random()
        
        if outcome_prob < 0.3:
            status = "Shrinking"
            change_percent = random.uniform(-40.0, -10.0)
            current_volume_mm3 = baseline_volume_mm3 * (1 + change_percent/100)
        elif outcome_prob < 0.6:
            status = "Stable"
            change_percent = random.uniform(-5.0, 5.0)
            current_volume_mm3 = baseline_volume_mm3 * (1 + change_percent/100)
        else:
            status = "Growing"
            change_percent = random.uniform(15.0, 80.0)
            current_volume_mm3 = baseline_volume_mm3 * (1 + change_percent/100)
            
        return {
            "baseline": {
                "estimated_volume_mm3": round(baseline_volume_mm3, 2),
                "lesions_count": random.randint(1, 2)
            },
            "current": {
                "estimated_volume_mm3": round(current_volume_mm3, 2),
                "lesions_count": random.randint(1, 3) if status == "Growing" else 1
            },
            "comparison": {
                "status": status,
                "volume_change_percent": round(change_percent, 2),
                "significant_change": abs(change_percent) > 10.0
            }
        }

progression_analyzer = ProgressionAnalyzerMock()
