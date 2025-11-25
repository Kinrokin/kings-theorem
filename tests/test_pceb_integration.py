from src.arbitration.pce_bundle import PCEBundle, StepResult, hash_blob


def test_pceb_hash_chain_basic():
    steps = [
        StepResult(step_id="s1", verdict="PASS", output_artifact={"val": 1}),
        StepResult(step_id="s2", verdict="CONTINUE", output_artifact={"val": 2}),
    ]
    bundle = PCEBundle(
        bundle_id="pceb-test",
        initial_input_hash=hash_blob({"input": "x"}),
        steps=steps,
        final_output_hash=hash_blob({"out": "y"}),
    )
    assert bundle.get_current_state_hash(), "State hash should compute"
    assert not bundle.is_vetoed_locally(), "Bundle should not be vetoed"
