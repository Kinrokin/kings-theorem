from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts.run_research_loop import LoopState, ResearchLoop
from src.crucibles.level7_generator import Level7ParadoxGenerator


class TestSafetyControls:
    @pytest.fixture
    def loop(self, tmp_path: Path):
        data_dir = tmp_path / "data"
        models_dir = tmp_path / "models"
        loop = ResearchLoop(data_dir=data_dir, models_dir=models_dir, dry_run=True)
        # Use tmp dirs
        loop.data_dir = data_dir
        loop.models_dir = models_dir
        data_dir.mkdir(parents=True, exist_ok=True)
        models_dir.mkdir(parents=True, exist_ok=True)
        # Initial state
        state = LoopState(level=1, epoch=0, best_metric=0.0, safety_violations=0, crash_counter=0, last_update_ts=0.0)
        return loop, state

    def test_pause_signal_halts_execution(self, loop):
        rl, state = loop
        # Create PAUSE signal
        (rl.data_dir / "PAUSE").touch()
        # Mock time.sleep to avoid infinite loop
        with patch("time.sleep", side_effect=[None, InterruptedError("Loop worked")]):
            with pytest.raises(InterruptedError):
                rl._check_human_intervention(state)

    def test_stop_signal_exits_process(self, loop):
        rl, state = loop
        (rl.data_dir / "STOP").touch()
        # Mock save_state to avoid I/O
        rl.save_state = MagicMock()
        with pytest.raises(SystemExit):
            rl._check_human_intervention(state)
        rl.save_state.assert_called_once()

    def test_level_up_gate_locking(self, loop):
        rl, state = loop
        # Simulate ready to promote from level 4 to 5
        state = LoopState(level=4, epoch=0, best_metric=0.95, safety_violations=0, crash_counter=0, last_update_ts=0.0)
        rl.ready_to_promote = True
        next_level = state.level + 1
        allow_file = rl.data_dir / f"ALLOW_LEVEL_{next_level}"
        if allow_file.exists():
            allow_file.unlink()
        # Break wait loop via sleep mock
        with patch("time.sleep", side_effect=InterruptedError("Wait loop entered")):
            with pytest.raises(InterruptedError):
                rl._check_human_intervention(state)

    def test_level7_generator_output_shape(self, tmp_path: Path):
        gen = Level7ParadoxGenerator()
        entry = gen.generate().to_dict()
        assert entry["difficulty"] == 7
        assert entry["id"].startswith("L7-")
        assert "constraints" in entry and len(entry["constraints"]) > 0
        assert "scenario" in entry and isinstance(entry["scenario"], str)

    def test_dead_man_switch_pause_alias(self, loop):
        rl, state = loop
        (rl.data_dir / "PAUSE").touch()
        with patch("time.sleep", side_effect=InterruptedError("PAUSE_ACTIVE")):
            with pytest.raises(InterruptedError, match="PAUSE_ACTIVE"):
                rl._check_signals(state)

    def test_run_calls_signal_check_first(self, loop):
        rl, state = loop
        # Force the signal check to raise immediately so we know it's called
        with patch.object(rl, "_check_human_intervention", side_effect=RuntimeError("SENTINEL")) as spy:
            with pytest.raises(RuntimeError, match="SENTINEL"):
                rl.run(max_steps=1)
            assert spy.called, "_check_human_intervention was not called at loop start"
