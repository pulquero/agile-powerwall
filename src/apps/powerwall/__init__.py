import datetime as dt
import re
import powerwall_tariff as tariff
import teslapy_wrapper as api_wrapper
from jsondiff import diff


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

WEEK_SCHEDULES = tariff.WeekSchedules()

TARIFF_CACHE = (0, None)

tariff.RATE_FUNCS.set_helpers(state.get, state.getattr)


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
def refresh_previous_day_rates(mpan, tariff_code, rates, **kwargs):
    debug(f"Previous day rates for mpan {mpan} ({tariff_code}):\n{rates}")
    mpan_rates = get_rates(mpan)
    if mpan_rates is not None:
        mpan_rates.update_previous_day(tariff_code, rates)
        update_powerwall_tariff()


@event_trigger("octopus_energy_electricity_current_day_rates")
def refresh_current_day_rates(mpan, tariff_code, rates, **kwargs):
    debug(f"Current day rates for mpan {mpan} ({tariff_code}):\n{rates}")
    mpan_rates = get_rates(mpan)
    if mpan_rates is not None:
        mpan_rates.update_current_day(tariff_code, rates)
        update_powerwall_tariff()


@event_trigger("octopus_energy_electricity_next_day_rates")
def refresh_next_day_rates(mpan, tariff_code, rates, **kwargs):
    debug(f"Next day rates for mpan {mpan} ({tariff_code}):\n{rates}")
    mpan_rates = get_rates(mpan)
    if mpan_rates is not None:
        mpan_rates.update_next_day(tariff_code, rates)
        update_powerwall_tariff()


def set_status_message(value):
    try:
        input_text.powerwall_tariff_update_status = value
    except:
        pass


def get_tariff_setting(tariff_code, config_key, default_value):
    config = pyscript.app_config
    for tariff_config in config.get("tariffs", []):
        if re.match(tariff_config["tariff_code"], tariff_code):
            if config_key in tariff_config:
                config = tariff_config
            break
    return config.get(config_key, default_value)


def update_powerwall_tariff():
    try:
        IMPORT_RATES.is_valid()
    except ValueError as err:
        msg = f"Import tariffs: {err}"
        debug(msg)
        set_status_message(msg)
        return

    if EXPORT_MPAN:
        try:
            EXPORT_RATES.is_valid()
        except ValueError as err:
            msg = f"Export tariffs: {err}"
            debug(msg)
            set_status_message(msg)
            return

    _update_powerwall_tariff()

    IMPORT_RATES.reset()
    EXPORT_RATES.reset()

    if not get_tariff_setting(IMPORT_RATES.current_tariff, "maintain_history", False):
        WEEK_SCHEDULES.reset()
    if not get_tariff_setting(EXPORT_RATES.current_tariff, "maintain_history", False):
        WEEK_SCHEDULES.reset(export=True)


def get_breaks(tariff_code, config_key, default_value=None, required=True):
    breaks = get_tariff_setting(tariff_code, config_key, default_value)
    if breaks is None and required:
        raise ValueError(f"Missing breaks config for {config_key}")
    return breaks


def get_pricing(tariff_code, config_key, default_value=None, required=True):
    pricing = get_tariff_setting(tariff_code, config_key, default_value)
    if pricing is None and required:
        raise ValueError(f"Missing pricing config for {config_key}")
    return pricing


def get_sensor_value(tariff_code, config_key, default_value):
    value = get_tariff_setting(tariff_code, config_key, default_value)
    if type(value) == str:
        value = float(state.get(value))
    return value


def _update_schedules_for_day(day_date):
    # filter down to the given day
    import_rates = IMPORT_RATES.cover_day(day_date)
    if not import_rates:
        return None, None
    export_rates = EXPORT_RATES.cover_day(day_date)

    import_breaks = get_breaks(IMPORT_RATES.current_tariff, "import_tariff_breaks", default_value=tariff.DEFAULT_BREAKS, required=True)
    plunge_pricing_breaks = get_breaks(IMPORT_RATES.current_tariff, "plunge_pricing_tariff_breaks", required=False)
    import_pricing = get_pricing(IMPORT_RATES.current_tariff, "import_tariff_pricing", default_value=tariff.DEFAULT_PRICING, required=True)
    plunge_pricing_pricing = get_pricing(IMPORT_RATES.current_tariff, "plunge_pricing_tariff_pricing", required=False)

    import_schedules = tariff.get_schedules(import_breaks, import_pricing, plunge_pricing_breaks, plunge_pricing_pricing, import_rates)
    if import_schedules is None:
        return None, None

    if export_rates:
        export_breaks = get_breaks(EXPORT_RATES.current_tariff, "export_tariff_breaks", default_value=tariff.DEFAULT_BREAKS, required=True)
        export_pricing = get_pricing(EXPORT_RATES.current_tariff, "export_tariff_pricing", default_value=tariff.DEFAULT_PRICING, required=True)
        export_schedules = tariff.get_schedules(export_breaks, export_pricing, None, None, export_rates)
    else:
        export_schedules = None

    weekday = day_date.weekday()
    WEEK_SCHEDULES.update(weekday, import_schedules, export_schedules)

    return import_schedules, export_schedules


def _get_tariff_data():
    global TARIFF_CACHE
    config = pyscript.app_config

    cache_ts, cache_data = TARIFF_CACHE
    ts = dt.datetime.now(dt.timezone.utc).timestamp()
    if ts > cache_ts + 10:
        cache_data = api_wrapper.get_powerwall_tariff(
            email=config["email"],
            refresh_token=config["refresh_token"],
        )
        TARIFF_CACHE = (ts, cache_data)
    return cache_data


def _update_powerwall_tariff():
    config = pyscript.app_config

    today = dt.date.today()
    import_schedules, export_schedules = _update_schedules_for_day(today)
    if import_schedules is None:
        set_status_message("No schedules for today!")
        return

    tomorrow = today + tariff.ONE_DAY_INCREMENT
    _update_schedules_for_day(tomorrow)

    import_plan = get_tariff_setting(IMPORT_RATES.current_tariff, "tariff_name", "Import tariff")
    export_plan = get_tariff_setting(EXPORT_RATES.current_tariff, "tariff_name", "Export tariff")
    import_standing_charge = get_sensor_value(IMPORT_RATES.current_tariff, "import_standing_charge", 0)
    export_standing_charge = get_sensor_value(EXPORT_RATES.current_tariff, "export_standing_charge", 0)
    import_schedule_type = get_tariff_setting(IMPORT_RATES.current_tariff, "schedule_type", "week")
    export_schedule_type = get_tariff_setting(EXPORT_RATES.current_tariff, "schedule_type", "week")
    tariff_data = tariff.to_tariff_data(
        config["tariff_provider"],
        import_plan, import_standing_charge, import_schedule_type,
        export_plan, export_standing_charge, export_schedule_type,
        WEEK_SCHEDULES, today
    )

    debug(f"Tariff data:\n{tariff_data}")

    current_tariff_data = _get_tariff_data()
    tariff_change = diff(tariff_data, current_tariff_data)
    debug(f"Tariff diff:\n{tariff_change}")
    if tariff_change:
        api_wrapper.set_powerwall_tariff(
            email=config["email"],
            refresh_token=config["refresh_token"],
            tariff_data=tariff_data
        )
        debug("Powerwall updated")
        status_msg = f"Tariff data updated at {dt.datetime.now()}"
    else:
        status_msg = f"Tariff data checked at {dt.datetime.now()}"

    if import_schedules or export_schedules:
        status_msg += " ("
        sep = ""
        if import_schedules:
            status_msg += f"{sep}import: "
            for i, schedule in enumerate(import_schedules):
                status_msg += f"{schedule.get_value():.3f}"
                if i < len(import_schedules) - 1:
                    if hasattr(schedule.assigner_func, "upper_bound"):
                        status_msg += f" |{schedule.assigner_func.upper_bound:.3f}| "
                    else:
                        status_msg += "|"
            sep = ", "
        if export_schedules:
            status_msg += f"{sep}export: "
            for i, schedule in enumerate(export_schedules):
                status_msg += f"{schedule.get_value():.3f}"
                if i < len(export_schedules) - 1:
                    if hasattr(schedule.assigner_func, "upper_bound"):
                        status_msg += f" |{schedule.assigner_func.upper_bound:.3f}| "
                    else:
                        status_msg += "|"
            sep = ", "
        status_msg += ")"
    set_status_message(status_msg)


@time_trigger("once(midnight + 2 min)")
def update_tariff_data_at_start_of_day(**kwargs):
    _update_powerwall_tariff()


@service("powerwall.refresh_tariff_data")
def refresh_tariff_data():
    """yaml
    name: Refresh Powerwall tariff data
    description: Immediately refreshes Powerwall tariff data with the current values
    """
    _update_powerwall_tariff()


@service("powerwall.get_tariff_data", supports_response="only")
def get_tariff_data():
    """yaml
    name: Fetches Powerwall tariff data
    description: Fetches Powerwall tariff data
    """
    return api_wrapper.get_powerwall_tariff(
        email=pyscript.app_config["email"],
        refresh_token=pyscript.app_config["refresh_token"]
    )


@service("powerwall.set_tariff_data")
def set_tariff_data(tariff_data):
    """yaml
    name: Set Powerwall tariff data
    description: Set Powerwall tariff data
    fields:
        tariff_data:
            required: true
    """
    api_wrapper.set_powerwall_tariff(
        email=pyscript.app_config["email"],
        refresh_token=pyscript.app_config["refresh_token"],
        tariff_data=tariff_data
    )


@service("powerwall.set_settings")
def set_settings(reserve_percentage=None, mode=None, allow_grid_charging=None, allow_battery_export=None, verify=False):
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
        verify:
            description: verify settings have been updated
            selector:
                boolean:
    """
    updated = False
    retry_count = 0
    while not updated:
        if retry_count == 3:
            raise Exception("Failed to update Powerwall settings")

        api_wrapper.set_powerwall_settings(
            email=pyscript.app_config["email"],
            refresh_token=pyscript.app_config["refresh_token"],
            reserve_percentage=reserve_percentage,
            mode=mode,
            allow_grid_charging=allow_grid_charging,
            allow_battery_export=allow_battery_export
        )
        updated = True
        retry_count += 1
        if verify:
            settings = api_wrapper.get_powerwall_settings(
                email=pyscript.app_config["email"],
                refresh_token=pyscript.app_config["refresh_token"]
            )
            if reserve_percentage is not None:
                if settings["reserve_percentage"] == reserve_percentage:
                    reserve_percentage = None
                else:
                    updated = False
            if mode is not None:
                if settings["mode"] == mode:
                    mode = None
                else:
                    updated = False
            if allow_grid_charging is not None:
                if settings["allow_grid_charging"] == allow_grid_charging:
                    allow_grid_charging = None
                else:
                    updated = False
            if allow_battery_export is not None:
                if settings["allow_battery_export"] == allow_battery_export:
                    allow_battery_export = None
                else:
                    updated = False


@service("powerwall.get_settings", supports_response="only")
def get_settings():
    """yaml
    name: Get Powerwall settings
    description: Gets Powerwall settings
    """
    return api_wrapper.get_powerwall_settings(
        email=pyscript.app_config["email"],
        refresh_token=pyscript.app_config["refresh_token"]
    )
