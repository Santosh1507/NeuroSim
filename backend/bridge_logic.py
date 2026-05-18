from typing import Dict, Any, Tuple
from dataclasses import dataclass

@dataclass
class ROI:
    A5: float
    LO: float
    Area45: float
    TPJ: float

@dataclass
class SocialParams:
    W_attn: float
    P_skip: float
    P_share: float
    viral_coefficient: float

class NeuroSocialBridge:
    LO_WEIGHT = 0.7
    A5_WEIGHT = 0.3
    SOCIAL_MULTIPLIER = 1.2
    STAGE_GATE_THRESHOLD = 0.4
    
    @staticmethod
    def calculate_attention_weight(roi: ROI) -> float:
        W_attn = (NeuroSocialBridge.LO_WEIGHT * roi.LO) + (NeuroSocialBridge.A5_WEIGHT * roi.A5)
        return round(W_attn, 4)
    
    @staticmethod
    def calculate_skip_probability(W_attn: float) -> float:
        return round(1.0 - W_attn, 4)
    
    @staticmethod
    def calculate_share_probability(roi: ROI, social_multiplier: float = SOCIAL_MULTIPLIER) -> float:
        return round(min(roi.Area45 * social_multiplier, 1.0), 4)
    
    @staticmethod
    def stage_gate_check(W_attn: float, threshold: float = STAGE_GATE_THRESHOLD) -> Tuple[bool, str]:
        if W_attn < threshold:
            return False, f"Low biological engagement (W_attn={W_attn:.2f} < {threshold}). Simulation aborted."
        return True, "Stage-Gate passed. Proceeding to social simulation."
    
    @staticmethod
    def compute_social_params(roi: ROI) -> SocialParams:
        W_attn = NeuroSocialBridge.calculate_attention_weight(roi)
        P_skip = NeuroSocialBridge.calculate_skip_probability(W_attn)
        P_share = NeuroSocialBridge.calculate_share_probability(roi)
        viral_coef = round(P_share * 2.8, 2)
        
        return SocialParams(W_attn=W_attn, P_skip=P_skip, P_share=P_share, viral_coefficient=viral_coef)
    
    @staticmethod
    def generate_recommendations(roi: ROI, social_params: SocialParams) -> list:
        recs = []
        
        if roi.LO < 0.5:
            recs.append({"timestamp": "0:00-0:03", "type": "visual", "issue": "Low visual hook strength", "recommendation": "Add more visual contrast or motion in the first 3 seconds"})
        elif roi.LO > 0.75:
            recs.append({"timestamp": "0:00-0:03", "type": "visual", "issue": "Strong visual engagement", "recommendation": "Maintain current visual style - high LO activation"})
        
        if roi.A5 < 0.5:
            recs.append({"timestamp": "0:05-0:15", "type": "audio", "issue": "Audio engagement dropping", "recommendation": "Consider audio dynamic change or voice modulation"})
        
        if roi.Area45 < 0.5:
            recs.append({"timestamp": "variable", "type": "cta", "issue": "Low perceived value", "recommendation": "Strengthen value proposition or add social proof"})
        
        if social_params.viral_coefficient > 2.0:
            recs.append({"timestamp": "N/A", "type": "social", "issue": "High viral potential", "recommendation": f"High Area45 ({roi.Area45}) driving viral coefficient of {social_params.viral_coefficient}"})
        
        return recs
