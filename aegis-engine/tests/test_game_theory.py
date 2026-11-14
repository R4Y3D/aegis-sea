"""Unit tests for Phase 4 Stackelberg Game-Theoretic Security Model."""

import pytest
from aegis.game_theory import (
    StackelbergSecurityGame,
    GameParameters,
    StackelbergEquilibriumResult,
)


@pytest.fixture
def game():
    return StackelbergSecurityGame()


def test_threat_score_monotonicity(game):
    """Lower dragging speed over cable increases threat score."""
    score_fast = game.threat_score_function(v=3.8)
    score_slow = game.threat_score_function(v=1.2)
    assert score_slow > score_fast
    assert score_slow >= 70.0


def test_detection_probability_bounds(game):
    """Detection probability is between 0 and 1, decreasing with higher threshold."""
    p_low_th = game.detection_probability(v=1.2, theta=50.0)
    p_high_th = game.detection_probability(v=1.2, theta=90.0)
    assert 0.0 <= p_low_th <= 1.0
    assert 0.0 <= p_high_th <= 1.0
    assert p_low_th > p_high_th


def test_attacker_best_response(game):
    """Attacker finds a finite optimal speed for any threshold."""
    v_star, u_star = game.attacker_best_response(theta=70.0)
    assert 0.5 <= v_star <= 4.0
    assert isinstance(u_star, float)


def test_solve_stackelberg_equilibrium(game):
    """Solves the leader-follower game and returns valid equilibrium."""
    se: StackelbergEquilibriumResult = game.solve_stackelberg_equilibrium()
    assert 50.0 <= se.optimal_threshold_theta <= 85.0
    assert 0.5 <= se.optimal_attacker_speed_knots <= 4.0
    assert 0.0 <= se.detection_probability <= 1.0
    assert 0.0 <= se.false_alarm_probability <= 1.0
    assert isinstance(se.defender_equilibrium_utility, float)


def test_game_theory_curves_generation(game):
    """Generates smooth curves for plotting and analysis."""
    curves = game.generate_curves(n_points=30)
    assert "thresholds" in curves
    assert "defender_utilities" in curves
    assert "attacker_optimal_speeds" in curves
    assert len(curves["thresholds"]) == 30
    assert len(curves["defender_utilities"]) == 30
