from coproducer.services import clear_services


def test_reports_budget(rig, ml):
    s = rig.call("check_gpu_budget").value
    assert s["free_mb"] == 16000 and s["total_mb"] == 16000 and s["resident"] == {}
    rig.call("load_model", model="acestep")
    fit = rig.call("check_gpu_budget", model="demucs").value
    assert fit["fits_now"] is True and fit["need_mb"] == 4000
    rig.call("load_model", model="demucs")
    assert rig.call("check_gpu_budget", model="vision").value["would_unload"] == ["acestep"]       # 16000 in use; dropping acestep frees enough
    both = rig.call("check_gpu_budget", model="flamingo").value
    assert both["fits_now"] is False and both["would_unload"] == ["acestep", "demucs"]


def test_unknown_model_and_no_scheduler(rig, ml):
    assert rig.call("check_gpu_budget", model="nope").error.code == "E_NOT_FOUND"
    clear_services()
    assert rig.call("check_gpu_budget").error.code == "E_UNSUPPORTED_API"
