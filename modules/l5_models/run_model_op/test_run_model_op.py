from coproducer.services import clear_services


def test_runs_an_op(rig, ml):
    r = rig.call("run_model_op", model="basicpitch", op="ping", args={})
    assert r.ok and r.value == "pong" and "basicpitch" in ml.sched.resident


def test_errors_pass_through(rig, ml):
    assert rig.call("run_model_op", model="nope", op="ping", args={}).error.code == "E_NOT_FOUND"
    assert rig.call("run_model_op", model="basicpitch", op="oom", args={}).error.code == "E_GPU_BUDGET"
    assert rig.call("run_model_op", model="basicpitch", op="sleep", args={"seconds": 3}, timeout_s=0.3).error.code == "E_TIMEOUT"
    clear_services()
    assert rig.call("run_model_op", model="basicpitch", op="ping", args={}).error.code == "E_UNSUPPORTED_API"
