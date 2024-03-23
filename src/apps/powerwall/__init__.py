import datetime as dt
import powerwall_tariff as tariff
import teslapy_wrapper as api_wrapper


def get_mpan(config_key, required):
    v = pyscript.app_config.get(config_key)
    if v is None and required:
        raise KeyError(f"{config_key} missing")
    if type(v) is int:
        v = str(v)
    return v


IMPORT_MPAN = get_mpan("import_mpan", True)
EXPORT_MPAN = get_mpan("export_mpan", False)

IMPORT_RATES = tariff.Rates()
EXPORT_RATES = tariff.Rates()


def debug(msg):
    log.debug(msg)


def get_rates(mpan):
    if mpan == IMPORT_MPAN:
        return IMPORT_RATES
    elif mpan == EXPORT_MPAN:
        return EXPORT_RATES
    else:
        return None


@event_trigger("octopus_energy_electricity_previous_day_rates")
def refresh_previous_day_rates(mpan, rates, **kwargs):
    debug(f"Previous day rates for mpan {mpan}:\n{rates}")
    mpan_rates = get_rates(mpan)
    if mpan_rates is not None:
        mpan_rates.update_previous_day(rates)
        update_powerwall_tariff()


@event_trigger("octopus_energy_electricity_current_day_rates")
def refresh_current_day_rates(mpan, rates, **kwargs):
    debug(f"Current day rates for mpan {mpan}:\n{rates}")
    mpan_rates = get_rates(mpan)
    if mpan_rates is not None:
        mpan_rates.update_current_day(rates)
        update_powerwall_tariff()


@event_trigger("octopus_energy_electricity_next_day_rates")
def refresh_next_day_rates(mpan, rates, **kwargs):
    debug(f"Next day rates for mpan {mpan}:\n{rates}")
    mpan_rates = get_rates(mpan)
    if mpan_rates is not None:
        mpan_rates.update_next_day(rates)
        update_powerwall_tariff()


def set_status_message(value):
    try:
        input_text.powerwall_tariff_update_status = value
    except:
        pass


def update_powerwall_tariff():
    try:
        IMPORT_RATES.is_valid()
    except ValueError as err:
        debug(str(err))
        set_status_message("Waiting for updated import tariffs")
        return

    if EXPORT_MPAN:
        try:
            EXPORT_RATES.is_valid()
        except ValueError as err:
            debug(str(err))
            set_status_message("Waiting for updated export tariffs")
            return

    _update_powerwall_tariff()

    IMPORT_RATES.reset()
    EXPORT_RATES.reset()


def _update_powerwall_tariff():
    schedules = tariff.get_schedules(pyscript.app_config, dt.date.today(), IMPORT_RATES, EXPORT_RATES)
    if schedules is None:
        return

    tariff_data = tariff.to_tariff_data(pyscript.app_config, schedules)

    debug(f"Tariff data:\n{tariff_data}")

    api_wrapper.set_powerwall_tariff(
        email=pyscript.app_config["email"],
        refresh_token=pyscript.app_config["refresh_token"],
        tariff_data=tariff_data
    )

    debug("Powerwall updated")
    breaks = [s.upper_bound for s in schedules if s.upper_bound is not None]
    set_status_message(f"Tariff data updated at {dt.datetime.now()} (breaks: {breaks})")


@service("powerwall.refresh_tariff_data")
def refresh_tariff_data():
    """yaml
    name: Refresh Powerwall tariff data
    description: Immediately refreshes Powerwall tariff data with the current values
    """
    _update_powerwall_tariff()


@service("powerwall.set_settings")
def set_settings(reserve_percentage=None, mode=None, allow_grid_charging=None, allow_battery_export=None):
    """yaml
    name: Set Powerwall settings
    description: Changes Powerwall settings
    fields:
        reserve_percentage:
            description: backup reserve percentage
            selector:
                number:
                    min: 0
                    max: 100
        mode:
            description: battery operation mode
            selector:
                select:
                    options:
                        - self_consumption
                        - backup
                        - autonomous
        allow_grid_charging:
            description: enable grid charging
            selector:
                boolean:
        allow_battery_export:
            description: enable battery export else PV only
            selector:
                boolean:
    """
    api_wrapper.set_powerwall_settings(
        email=pyscript.app_config["email"],
        refresh_token=pyscript.app_config["refresh_token"],
        reserve_percentage=reserve_percentage,
        mode=mode,
        allow_grid_charging=allow_grid_charging,
        allow_battery_export=allow_battery_export
    )
