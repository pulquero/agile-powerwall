import sys
import datetime as dt
import itertools

import teslapy
# use below instead if you want to use a local copy of teslapy
#
#if "/config/pyscript_packages" not in sys.path:
#    sys.path.append("/config/pyscript_packages")
#
#import teslapy_latest as teslapy


CHARGE_NAMES = ["SUPER_OFF_PEAK", "OFF_PEAK", "PARTIAL_PEAK", "ON_PEAK"]

PREVIOUS_DAY_RATES = None
CURRENT_DAY_RATES = None
NEXT_DAY_RATES = None


def debug(msg):
    log.debug(msg)


class Schedule:
    def __init__(self, charge_name):
        self.charge_name = charge_name
        self.periods = []
        self.value_sum = 0.0
        self.rate_count = 0
        self.start = None
        self.end = None

    def add(self, rate):
        if self.start is None:
            self.start = rate["start"]
            self.end = rate["end"]
        elif rate['start'] == self.end:
            self.end = rate["end"]
        else:
            self.periods.append((self.start, self.end))
            self.start = rate["start"]
            self.end = rate["end"]
        self.value_sum += rate["value_inc_vat"]
        self.rate_count += 1

    def finish(self):
        if self.start is not None:
            self.periods.append((self.start, self.end))
            self.start = None
            self.end = None

        if self.rate_count > 0:
            self.value = self.value_sum/self.rate_count
            if self.value < 0.0:
                self.value = 0.0
        else:
            self.value = 0.0


@pyscript_executor
def _set_powerwall_tariff(email, refresh_token, tariff_data):
    with teslapy.Tesla(email) as tesla:
        tesla.refresh_token(refresh_token=refresh_token)
        pw = tesla.battery_list()[0]
        pw.set_tariff(tariff_data)


@pyscript_executor
def _set_powerwall_reserve(email, refresh_token, percentage):
    with teslapy.Tesla(email) as tesla:
        tesla.refresh_token(refresh_token=refresh_token)
        pw = tesla.battery_list()[0]
        pw.set_backup_reserve_percent(percentage)


@pyscript_executor
def _set_powerwall_operation(email, refresh_token, mode):
    with teslapy.Tesla(email) as tesla:
        tesla.refresh_token(refresh_token=refresh_token)
        pw = tesla.battery_list()[0]
        pw.set_operation(mode=mode)


@pyscript_executor
def _set_powerwall_import_export(email, refresh_token, allow_grid_charging=None, allow_battery_export=None):
    with teslapy.Tesla(email) as tesla:
        tesla.refresh_token(refresh_token=refresh_token)
        pw = tesla.battery_list()[0]
        pw.set_import_export(allow_grid_charging=allow_grid_charging, allow_battery_export=allow_battery_export)


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

    today = dt.date.today()
    today_start = dt.datetime.combine(today, dt.time.min).astimezone(dt.timezone.utc)
    today_end = dt.datetime.combine(today + dt.timedelta(days=1), dt.time.min).astimezone(dt.timezone.utc)

    rates = itertools.chain(PREVIOUS_DAY_RATES, CURRENT_DAY_RATES, NEXT_DAY_RATES)
    # filter down to today's rates
    rates = [rate for rate in rates if rate["start"] >= today_start and rate["end"] <= today_end]

    if len(rates) == 0:
        debug(f"No rates available for today")
        return

    # pad rates to cover 24 hours
    rates[0]["start"] = today_start
    rates[-1]["end"] = today_end

    plunge_pricing = False
    for rate in rates:
        if rate["value_inc_vat"] < 0.0:
            plunge_pricing = True
            break

    if plunge_pricing:
        breaks = pyscript.app_config["plunge_pricing_tariff_breaks"]
    else:
        breaks = pyscript.app_config["tariff_breaks"]

    # sanitise user input
    breaks = breaks[:len(CHARGE_NAMES)-1]

    schedules = [Schedule(charge_name) for charge_name in CHARGE_NAMES]

    for rate in rates:
        v = rate['value_inc_vat']
        schedule = None
        for i, br in enumerate(breaks):
            if v < br:
                schedule = schedules[i]
                break
        if schedule is None:
            schedule = schedules[-1]
        schedule.add(rate)

    tou_periods = {}
    buy_price_info = {}
    sell_price_info = {}
    for schedule in schedules:
        schedule.finish()
        charge_periods = []
        for period in schedule.periods:
            start_local = period[0].astimezone()
            end_local = period[1].astimezone()
            charge_periods.append({
                "fromDayOfWeek": 0,
                "fromHour": start_local.hour,
                "fromMinute": start_local.minute,
                "toDayOfWeek": 6,
                "toHour": end_local.hour,
                "toMinute": end_local.minute
            })
        tou_periods[schedule.charge_name] = charge_periods
        buy_price_info[schedule.charge_name] = schedule.value
        sell_price_info[schedule.charge_name] = 0.0

    plan = "Agile"
    provider = "Octopus"
    demand_changes = {"ALL": {"ALL": 0}, "Summer": {}, "Winter": {}}
    daily_charges = [{"name": "Charge", "amount": 0}]
    seasons = {"Summer": {"fromMonth": 1, "fromDay": 1, "toDay": 31,
                          "toMonth": 12, "tou_periods": tou_periods},
               "Winter": {"tou_periods": {}}}
    tariff_data = {
        "name": plan,
        "utility": provider,
        "daily_charges": daily_charges,
        "demand_charges": demand_changes,
        "seasons": seasons,
        "energy_charges": {"ALL": {"ALL": 0},
                        "Summer": buy_price_info,
                        "Winter": {}},
        "sell_tariff": {"name": plan,
                     "utility": provider,
                     "daily_charges": daily_charges,
                     "demand_charges": demand_changes,
                     "seasons": seasons,
                     "energy_charges": {"ALL": {"ALL": 0},
                                        "Summer": sell_price_info,
                                        "Winter": {}}}
    }

    debug(f"Tariff data:\n{tariff_data}")

    _set_powerwall_tariff(
        email=pyscript.app_config["email"],
        refresh_token=pyscript.app_config["refresh_token"],
        tariff_data=tariff_data
    )

    PREVIOUS_DAY_RATES = None
    CURRENT_DAY_RATES = None
    NEXT_DAY_RATES = None


@service
def set_backup_reserve(percentage):
    _set_powerwall_reserve(
        email=pyscript.app_config["email"],
        refresh_token=pyscript.app_config["refresh_token"],
        percentage=percentage
    )


@service
def set_operation(mode):
    _set_powerwall_operation(
        email=pyscript.app_config["email"],
        refresh_token=pyscript.app_config["refresh_token"],
        mode=mode
    )


@service
def set_grid_charging(enable):
    _set_powerwall_import_export(
        email=pyscript.app_config["email"],
        refresh_token=pyscript.app_config["refresh_token"],
        allow_grid_charging=enable
    )

