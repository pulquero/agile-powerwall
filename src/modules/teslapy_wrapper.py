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
        tesla.refresh_token(refresh_token=refresh_token)
        pw = tesla.battery_list()[0]
        pw.set_tariff(tariff_data)


@pyscript_executor
def get_powerwall_tariff(email, refresh_token):
    with teslapy.Tesla(email) as tesla:
        tesla.refresh_token(refresh_token=refresh_token)
        pw = tesla.battery_list()[0]
        return pw.get_tariff()


@pyscript_executor
def set_powerwall_settings(email, refresh_token, reserve_percentage=None, mode=None, allow_grid_charging=None, allow_battery_export=None):
    retry = teslapy.Retry(total=5, allowed_methods=None, backoff_factor=1, status_forcelist=(503, 504))
    with teslapy.Tesla(email, retry=retry) as tesla:
        tesla.refresh_token(refresh_token=refresh_token)
        pw = tesla.battery_list()[0]
        if reserve_percentage is not None:
            pw.set_backup_reserve_percent(reserve_percentage)
        if mode is not None:
            pw.set_operation(mode=mode)
        if allow_grid_charging is not None or allow_battery_export is not None:
            pw.set_import_export(allow_grid_charging=allow_grid_charging, allow_battery_export=allow_battery_export)
