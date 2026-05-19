from bridge_logic import ROI, NeuroSocialBridge, SocialParams


class TestNeuroSocialBridge:
    def test_attention_weight_strong_content(self):
        roi = ROI(A5=0.85, LO=0.82, Area45=0.75, TPJ=0.70)
        W_attn = NeuroSocialBridge.calculate_attention_weight(roi)
        assert 0.82 <= W_attn <= 0.83

    def test_attention_weight_weak_content(self):
        roi = ROI(A5=0.30, LO=0.25, Area45=0.20, TPJ=0.35)
        W_attn = NeuroSocialBridge.calculate_attention_weight(roi)
        expected = round(0.7 * 0.25 + 0.3 * 0.30, 4)
        assert W_attn == expected

    def test_skip_probability(self):
        W_attn = 0.75
        P_skip = NeuroSocialBridge.calculate_skip_probability(W_attn)
        assert P_skip == 0.25

    def test_share_probability_capped(self):
        roi = ROI(A5=0.9, LO=0.9, Area45=0.95, TPJ=0.8)
        P_share = NeuroSocialBridge.calculate_share_probability(roi)
        assert P_share <= 1.0

    def test_stage_gate_pass(self):
        roi = ROI(A5=0.85, LO=0.82, Area45=0.75, TPJ=0.70)
        W_attn = NeuroSocialBridge.calculate_attention_weight(roi)
        passed, msg = NeuroSocialBridge.stage_gate_check(W_attn)
        assert passed is True
        assert "passed" in msg.lower()

    def test_stage_gate_fail(self):
        roi = ROI(A5=0.30, LO=0.25, Area45=0.20, TPJ=0.35)
        W_attn = NeuroSocialBridge.calculate_attention_weight(roi)
        passed, msg = NeuroSocialBridge.stage_gate_check(W_attn)
        assert passed is False
        assert "aborted" in msg.lower()

    def test_compute_social_params(self):
        roi = ROI(A5=0.8, LO=0.7, Area45=0.6, TPJ=0.5)
        params = NeuroSocialBridge.compute_social_params(roi)
        assert isinstance(params, SocialParams)
        assert 0 <= params.W_attn <= 1
        assert 0 <= params.P_skip <= 1
        assert 0 <= params.P_share <= 1
        assert params.viral_coefficient > 0

    def test_recommendations_low_visual(self):
        roi = ROI(A5=0.8, LO=0.3, Area45=0.6, TPJ=0.5)
        params = NeuroSocialBridge.compute_social_params(roi)
        recs = NeuroSocialBridge.generate_recommendations(roi, params)
        visual_recs = [r for r in recs if r["type"] == "visual"]
        assert len(visual_recs) > 0
        assert "low visual" in visual_recs[0]["issue"].lower()

    def test_recommendations_high_viral(self):
        roi = ROI(A5=0.8, LO=0.8, Area45=0.85, TPJ=0.7)
        params = NeuroSocialBridge.compute_social_params(roi)
        recs = NeuroSocialBridge.generate_recommendations(roi, params)
        social_recs = [r for r in recs if r["type"] == "social"]
        assert len(social_recs) > 0
