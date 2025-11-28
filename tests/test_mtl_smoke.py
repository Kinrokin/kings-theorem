from src.primitives.mtl import MTLOp, MTLProperty, check_property_trivial, define_axiom_six_mtl


def test_mtl_always_passes():
    prop = MTLProperty(MTLOp.ALWAYS, "ethics >= 0.7")
    trace = [
        {"time": 0.0, "values": {"ethics": 0.8}},
        {"time": 1.0, "values": {"ethics": 0.9}},
    ]
    assert check_property_trivial(prop, trace)


def test_mtl_always_fails():
    prop = MTLProperty(MTLOp.ALWAYS, "ethics >= 0.7")
    trace = [
        {"time": 0.0, "values": {"ethics": 0.8}},
        {"time": 1.0, "values": {"ethics": 0.5}},
    ]
    assert not check_property_trivial(prop, trace)


def test_axiom_six_mtl_definition():
    prop = define_axiom_six_mtl()
    assert prop.operator == MTLOp.ALWAYS
    assert "ethics" in prop.predicate
