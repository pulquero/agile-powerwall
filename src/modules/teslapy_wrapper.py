import teslapy
# use below instead if you want to use a local copy of teslapy
#
#import sys
#if "/config/pyscript_packages" not in sys.path:
#    sys.path.append("/config/pyscript_packages")
#
#import teslapy_latest as teslapy


@pyscript_executor
def set_powerwall_tariff(email, refresh_token, tariff_data):
    retry = teslapy.Retry(total=5, allowed_methods=None, backoff_factor=1, status_forcelist=(503, 504))
    with teslapy.Tesla(email, retry=retry) as tesla:
        if not tesla.authorized:
            tesla.refresh_token(refresh_token=refresh_token)
        pw = tesla.battery_list()[0]
        pw.set_tariff(tariff_data)


@pyscript_executor
def get_powerwall_tariff(email, refresh_token):
    retry = teslapy.Retry(total=5, allowed_methods=None, backoff_factor=1, status_forcelist=(503, 504))
    with teslapy.Tesla(email, retry=retry) as tesla:
        if not tesla.authorized:
            tesla.refresh_token(refresh_token=refresh_token)
        pw = tesla.battery_list()[0]
        return pw.get_tariff()


@pyscript_executor
def set_powerwall_settings(email, refresh_token, reserve_percentage=None, mode=None, allow_grid_charging=None, allow_battery_export=None):
    retry = teslapy.Retry(total=5, allowed_methods=None, backoff_factor=1, status_forcelist=(503, 504))
    with teslapy.Tesla(email, retry=retry) as tesla:
        if not tesla.authorized:
            tesla.refresh_token(refresh_token=refresh_token)
        pw = tesla.battery_list()[0]
        if reserve_percentage is not None:
            pw.set_backup_reserve_percent(reserve_percentage)
        if mode is not None:
            pw.set_operation(mode=mode)
        if allow_grid_charging is not None or allow_battery_export is not None:
            pw.set_import_export(allow_grid_charging=allow_grid_charging, allow_battery_export=allow_battery_export)

@pyscript_executor
def get_powerwall_settings(email, refresh_token):
    retry = teslapy.Retry(total=5, allowed_methods=None, backoff_factor=1, status_forcelist=(503, 504))
    with teslapy.Tesla(email, retry=retry) as tesla:
        if not tesla.authorized:
            tesla.refresh_token(refresh_token=refresh_token)
        pw = tesla.battery_list()[0]
        info = pw.get_site_info()
        return {
            "reserve_percentage": info["backup_reserve_percent"],
            "mode": info["default_real_mode"],
            "allow_grid_charging": not info["components"].get("disallow_charge_from_grid_with_solar_installed", False),
            "allow_battery_export": info["components"]["customer_preferred_export_rule"] == "battery_ok"
        }
