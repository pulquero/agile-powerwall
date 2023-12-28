import datetime as dt
import itertools
import powerwall_tariff as tariff
import teslapy_wrapper as api_wrapper


PREVIOUS_DAY_RATES = None
CURRENT_DAY_RATES = None
NEXT_DAY_RATES = None


def debug(msg):
    log.debug(msg)


@event_trigger("octopus_energy_electricity_previous_day_rates")
def refresh_previous_day_rates(**kwargs):
    global PREVIOUS_DAY_RATES
    PREVIOUS_DAY_RATES = kwargs["rates"]
    debug(f"Previous day rates:\n{PREVIOUS_DAY_RATES}")
    update_powerwall_tariff()


@event_trigger("octopus_energy_electricity_current_day_rates")
def refresh_current_day_rates(**kwargs):
    global CURRENT_DAY_RATES
    CURRENT_DAY_RATES = kwargs["rates"]
    debug(f"Current day rates:\n{CURRENT_DAY_RATES}")
    update_powerwall_tariff()


@event_trigger("octopus_energy_electricity_next_day_rates")
def refresh_next_day_rates(**kwargs):
    global NEXT_DAY_RATES
    NEXT_DAY_RATES = kwargs["rates"]
    debug(f"Next day rates:\n{NEXT_DAY_RATES}")
    update_powerwall_tariff()


def update_powerwall_tariff():
    global PREVIOUS_DAY_RATES
    global CURRENT_DAY_RATES
    global NEXT_DAY_RATES

    if PREVIOUS_DAY_RATES is None or CURRENT_DAY_RATES is None or NEXT_DAY_RATES is None:
        debug("Waiting for rate data")
        return

    if len(PREVIOUS_DAY_RATES) > 0 and len(CURRENT_DAY_RATES) > 0:
        previous_day_end = PREVIOUS_DAY_RATES[-1]["end"]
        current_day_start = CURRENT_DAY_RATES[0]["start"]
        if current_day_start != previous_day_end:
            debug(f"Previous to current day rates are not contiguous: {previous_day_end} {current_day_start}")
            return

    if len(CURRENT_DAY_RATES) > 0 and len(NEXT_DAY_RATES) > 0:
        current_day_end = CURRENT_DAY_RATES[-1]["end"]
        next_day_start = NEXT_DAY_RATES[0]["start"]
        if next_day_start != current_day_end:
            debug(f"Current to next day rates are not contiguous: {current_day_end} {next_day_start}")
            return

    rates = itertools.chain(PREVIOUS_DAY_RATES, CURRENT_DAY_RATES, NEXT_DAY_RATES)
    tariff_data = tariff.calculate_tariff_data(pyscript.app_config, dt.date.today(), rates)

    debug(f"Tariff data:\n{tariff_data}")

    api_wrapper.set_powerwall_tariff(
        email=pyscript.app_config["email"],
        refresh_token=pyscript.app_config["refresh_token"],
        tariff_data=tariff_data
    )

    PREVIOUS_DAY_RATES = None
    CURRENT_DAY_RATES = None
    NEXT_DAY_RATES = None


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
