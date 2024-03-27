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


def get_breaks(config_key, default_value=None, required=True):
    breaks = pyscript.app_config.get(config_key, default_value)
    if breaks is None and required:
        raise ValueError(f"Missing breaks config for {config_key}")
    if breaks is not None and type(breaks) == list and len(breaks) != len(tariff.CHARGE_NAMES)-1:
        raise ValueError(f"{len(tariff.CHARGE_NAMES)-1} breaks must be specified for {config_key}")
    return breaks


def get_pricing(config_key, default_value=None, required=True):
    pricing = pyscript.app_config.get(config_key, default_value)
    if pricing is None and required:
        raise ValueError(f"Missing pricing config for {config_key}")
    if pricing is not None and len(pricing) != len(tariff.CHARGE_NAMES):
        raise ValueError(f"{len(tariff.CHARGE_NAMES)} pricing functions must be specified for {config_key}")
    return pricing


def get_sensor_value(config_key, default_value):
    value = pyscript.app_config.get(config_key, default_value)
    if type(value) == str:
        value = float(state.get(value))
    return value


def _update_powerwall_tariff():
    config = pyscript.app_config

    today = dt.date.today()

    # filter down to the given day
    import_rates = IMPORT_RATES.cover_day(today)
    export_rates = EXPORT_RATES.cover_day(today)

    import_breaks = get_breaks("import_tariff_breaks", required=False)
    # backwards compatibility
    if import_breaks is None:
        import_breaks = get_breaks("tariff_breaks")
    import_plunge_pricing_breaks = get_breaks("plunge_pricing_tariff_breaks", required=False)
    import_pricing = get_pricing("import_tariff_pricing", required=False)
    # backwards compatibility
    if import_pricing is None:
        import_pricing = get_pricing("tariff_pricing")

    import_schedules = tariff.get_schedules(import_breaks, import_plunge_pricing_breaks, import_pricing, import_rates)
    if import_schedules is None:
        return

    if export_rates:
        export_breaks = get_breaks("export_tariff_breaks", required=False)
        export_pricing = get_pricing("export_tariff_pricing")
        if export_breaks:
            pricing_key = tariff.PRICE_KEY
            _export_rates = export_rates
        else:
            # backwards compatibility
            export_breaks = import_breaks
            pricing_key = "export_price"
            _export_rates = []
            for ir, er in zip(import_rates, export_rates):
                r = {**ir, pricing_key: er[tariff.PRICE_KEY]}
                _export_rates.append(r)
        export_schedules = tariff.get_schedules(export_breaks, None, export_pricing, _export_rates, pricing_key=pricing_key)
    else:
        export_schedules = None

    import_standing_charge = get_sensor_value("import_standing_charge", 0)
    export_standing_charge = get_sensor_value("export_standing_charge", 0)
    tariff_data = tariff.to_tariff_data(config, import_standing_charge, export_standing_charge, import_schedules, export_schedules)

    debug(f"Tariff data:\n{tariff_data}")

    api_wrapper.set_powerwall_tariff(
        email=config["email"],
        refresh_token=config["refresh_token"],
        tariff_data=tariff_data
    )

    debug("Powerwall updated")
    status_msg = f"Tariff data updated at {dt.datetime.now()}"
    if import_schedules or export_schedules:
        status_msg += "("
        sep = ""
        if import_schedules:
            import_breaks = [s.upper_bound for s in import_schedules if s.upper_bound is not None]
            status_msg += f"{sep}import breaks: {import_breaks}"
            sep = ", "
        if export_schedules:
            export_breaks = [s.upper_bound for s in export_schedules if s.upper_bound is not None]
            status_msg += f"{sep}export breaks: {export_breaks}"
            sep = ", "
        status_msg += ")"
    set_status_message(status_msg)


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
