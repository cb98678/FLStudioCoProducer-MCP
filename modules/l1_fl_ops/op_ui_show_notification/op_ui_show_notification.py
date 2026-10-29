import ui


def op_ui_show_notification(notificationId: int) -> dict:
    """Run ui.showNotification inside FL Studio and return the outcome as a result dict."""
    bad = _check_args({"notificationId": notificationId}, {"notificationId": "i"})
    if bad:
        return bad
    return _run(ui.showNotification, notificationId)
