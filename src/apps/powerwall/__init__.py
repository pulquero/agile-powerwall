import datetime as dt
import powerwall_tariff as tariff
import teslapy_wrapper as api_wrapper


IMPORT_RATES = tariff.Rates()


def debug(msg):
    log.debug(msg)


def get_rates(mpan):
    import_mpan = pyscript.app_config["import_mpan"]
    if mpan == import_mpan:
        return IMPORT_RATES
    else:
        return None


@event_trigger("octopus_energy_electricity_previous_DAY_IMPORT_RATES")
def refresh_previous_day_import_rates(mpan, rates):
    debug(f"Previous day rates for mpan {mpan}:\n{rates}")
    mpan_rates = get_rates(mpan)
    if mpan_rates is not None:
        mpan_rates.previous_day = rates
        update_powerwall_tariff()


@event_trigger("octopus_energy_electricity_current_DAY_IMPORT_RATES")
def refresh_current_day_import_rates(mpan, rates):
    debug(f"Current day rates for mpan {mpan}:\n{rates}")
    mpan_rates = get_rates(mpan)
    if mpan_rates is not None:
        mpan_rates.current_day = rates
        update_powerwall_tariff()


@event_trigger("octopus_energy_electricity_next_DAY_IMPORT_RATES")
def refresh_next_day_import_rates(mpan, rates):
    debug(f"Next day rates for mpan {mpan}:\n{rates}")
    mpan_rates = get_rates(mpan)
    if mpan_rates is not None:
        mpan_rates.next_day = rates
        update_powerwall_tariff()


def update_powerwall_tariff():
    try:
        IMPORT_RATES.is_valid()
    except ValueError as err:
        debug(str(err))
        return

    tariff_data = tariff.calculate_tariff_data(pyscript.app_config, dt.date.today(), IMPORT_RATES)

    debug(f"Tariff data:\n{tariff_data}")

    api_wrapper.set_powerwall_tariff(
        email=pyscript.app_config["email"],
        refresh_token=pyscript.app_config["refresh_token"],
        tariff_data=tariff_data
    )

    IMPORT_RATES.clear()


@service("powerwall.set_settings")
def set_settings(reserve_percentage=None, mode=None, allow_grid_charging=None, allow_battery_export=None):
    api_wrapper.set_powerwall_settings(
        email=pyscript.app_config["email"],
        refresh_token=pyscript.app_config["refresh_token"],
        reserve_percentage=reserve_percentage,
        mode=mode,
        allow_grid_charging=allow_grid_charging,
        allow_battery_export=allow_battery_export
    )
