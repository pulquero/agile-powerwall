import datetime as dt
import itertools
import sys


if "/config/pyscript_packages" not in sys.path:
    sys.path.append("/config/pyscript_packages")
import jenkspy


EXCLUSIVE_OFFSET = 0.000001

ONE_DAY_INCREMENT = dt.timedelta(days=1)
SLOT_TIME_INCREMENT = dt.timedelta(minutes=30)

CHARGE_NAMES = ["SUPER_OFF_PEAK", "OFF_PEAK", "PARTIAL_PEAK", "ON_PEAK"]

PRICE_KEY = "value_inc_vat"
PRICE_CAP = 1.00


def get_day_bounds(day_date):
    day_start = dt.datetime.combine(day_date, dt.time.min).astimezone(dt.timezone.utc)
    day_end = dt.datetime.combine(day_date + ONE_DAY_INCREMENT, dt.time.min).astimezone(dt.timezone.utc)
    return day_start, day_end


def extend_from(rates, start_time):
    first = rates[0]
    while first["start"] > start_time:
        new_first = first.copy()
        new_first["start"] = first["start"] - SLOT_TIME_INCREMENT
        new_first["end"] = first["start"]
        rates.insert(0, new_first)
        first = new_first


def extend_to(rates, end_time):
    last = rates[-1]
    while last["end"] < end_time:
        new_last = last.copy()
        new_last["start"] = last["end"]
        new_last["end"] = last["end"] + SLOT_TIME_INCREMENT
        rates.append(new_last)
        last = new_last


class Rates:
    def __init__(self):
        self.previous_day = []
        self._previous_day_updated = False
        self.current_day = []
        self._current_day_updated = False
        self.next_day = []
        self._next_day_updated = False

    def update_previous_day(self, rates):
        self.previous_day = rates
        self._previous_day_updated = True

    def update_current_day(self, rates):
        self.current_day = rates
        self._current_day_updated = True

    def update_next_day(self, rates):
        self.next_day = rates
        self._next_day_updated = True

    def is_valid(self):
        if not self._previous_day_updated or not self._current_day_updated or not self._next_day_updated:
            pending = []
            if not self._previous_day_updated:
                pending.append("previous day")
            if not self._current_day_updated:
                pending.append("current day")
            if not self._next_day_updated:
                pending.append("next day")
            raise ValueError(f"Waiting for rate data: {', '.join(pending)}")

        if len(self.previous_day) > 0 and len(self.current_day) > 0:
            previous_day_end = self.previous_day[-1]["end"]
            current_day_start = self.current_day[0]["start"]
            if current_day_start != previous_day_end:
                raise ValueError(f"Previous to current day rates are not contiguous: {previous_day_end} {current_day_start}")

        if len(self.current_day) > 0 and len(self.next_day) > 0:
            current_day_end = self.current_day[-1]["end"]
            next_day_start = self.next_day[0]["start"]
            if next_day_start != current_day_end:
                raise ValueError(f"Current to next day rates are not contiguous: {current_day_end} {next_day_start}")

    def between(self, start, end):
        if self.previous_day or self.current_day or self.next_day:  # pyscript doesn't like empty list comprehensions
            all_rates = itertools.chain(self.previous_day, self.current_day, self.next_day)
            return [rate for rate in all_rates if rate["start"] >= start and rate["end"] <= end]
        else:
            return []

    def cover_day(self, day_date):
        day_start, day_end = get_day_bounds(day_date)
        day_rates = self.between(day_start, day_end)
        if day_rates:
            # pad rates to cover 24 hours
            extend_from(day_rates, day_start)
            extend_to(day_rates, day_end)
        return day_rates

    def reset(self):
        self._previous_day_updated = False
        self._current_day_updated = False
        self._next_day_updated = False


class Schedule:
    def __init__(self, charge_name, lower_bound, upper_bound, pricing_func, pricing_key):
        self.charge_name = charge_name
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self.pricing_func = pricing_func
        self.pricing_key = pricing_key
        self._periods = []
        self._value = None
        self._start = None
        self._end = None

    def is_in(self, cost):
        return (self.lower_bound is None or cost >= self.lower_bound) and (self.upper_bound is None or cost < self.upper_bound)

    def add(self, rate):
        if self._start is None:
            self._start = rate["start"]
            self._end = rate["end"]
        elif rate['start'] == self._end:
            self._end = rate["end"]
        else:
            self._periods.append((self._start, self._end))
            self._start = rate["start"]
            self._end = rate["end"]
        self.pricing_func.add(rate[self.pricing_key])

    def get_periods(self):
        if self._start is not None:
            self._periods.append((self._start, self._end))
            self._start = None
            self._end = None
        return self._periods

    def get_value(self):
        if self._value is None:
            self._value = self.pricing_func.get_value()
        return self._value


def lowest_rates(rates, hrs):
    prices = [r[PRICE_KEY] for r in rates]
    prices.sort()
    n = round(2.0*float(hrs))
    limit = prices[n-1] if n <= len(prices) else prices[-1]
    return limit + EXCLUSIVE_OFFSET


def highest_rates(rates, hrs):
    prices = [r[PRICE_KEY] for r in rates]
    prices.sort(reverse=True)
    n = round(2.0*float(hrs))
    limit = prices[n-1] if n <= len(prices) else prices[-1]
    return limit


RATE_FUNCS = {
    "lowest": lowest_rates,
    "highest": highest_rates
}


class AveragePricing():
    def __init__(self):
        self.sum = 0
        self.count = 0

    def add(self, price):
        self.sum += price
        self.count += 1

    def get_value(self):
        if self.count > 0:
            v = self.sum/self.count
            if v < 0.0:
                v = 0.0
            return v
        else:
            return 0.0


class MinimumPricing():
    def __init__(self):
        self.min = PRICE_CAP

    def add(self, price):
        if price < self.min:
            self.min = price

    def get_value(self):
        v = self.min
        if v < 0.0:
            v = 0.0;
        return v


class MaximumPricing():
    def __init__(self):
        self.max = 0

    def add(self, price):
        if price > self.max:
            self.max = price

    def get_value(self):
        return self.max


class FixedPricing:
    def __init__(self, v):
        self.v = float(v)

    def add(self, price):
        pass

    def get_value(self):
        return self.v


PRICING_FUNCS = {
    "average": AveragePricing,
    "minimum": MinimumPricing,
    "maximum": MaximumPricing,
    "fixed": FixedPricing,
}


def create_pricing(pricing_expr):
    if '(' in pricing_expr and pricing_expr[-1] == ')':
        sep = pricing_expr.index('(')
        func_name = pricing_expr[:sep]
        func_args = pricing_expr[sep+1:-1].split(',')
    else:
        func_name = pricing_expr
        func_args = []
    pricing_type = PRICING_FUNCS[func_name]
    return pricing_type(*func_args)


def get_breaks(break_config, rates):
    if break_config == "jenks":
        bounds = jenkspy.jenks_breaks([r[PRICE_KEY] for r in rates], n_classes=len(CHARGE_NAMES))
        breaks = [b + EXCLUSIVE_OFFSET for b in bounds[1:-1]]
    else:
        breaks = []
        for br in break_config:
            if isinstance(br, float) or isinstance(br, int):
                v = br
            elif isinstance(br, str) and '(' in br and br[-1] == ')':
                sep = br.index('(')
                func_name = br[:sep]
                func_args = br[sep+1:-1].split(',')
                v = RATE_FUNCS[func_name](rates, *func_args)
            else:
                raise ValueError(f"Invalid threshold: {br}")
            breaks.append(v)
        # ensure ascending order
        breaks.sort()

    return breaks


def populate_schedules(schedules, day_rates):
    for rate in day_rates:
        cost = rate[PRICE_KEY]
        schedule = None
        for s in schedules:
            if s.is_in(cost):
                schedule = s
                break
        schedule.add(rate)


def get_schedules(breaks_config, plunge_pricing_breaks_config, tariff_pricing_config, day_rates, pricing_key=PRICE_KEY):
    if not day_rates:
        return None

    plunge_pricing = False
    for rate in day_rates:
        if rate[PRICE_KEY] < 0.0:
            plunge_pricing = True
            break

    if plunge_pricing and plunge_pricing_breaks_config:
        configured_breaks = plunge_pricing_breaks_config
    else:
        configured_breaks = breaks_config

    breaks = get_breaks(configured_breaks, day_rates)

    schedules = []
    for i, charge_name in enumerate(CHARGE_NAMES):
        lower_bound = breaks[i-1] if i > 0 else None
        upper_bound = breaks[i] if i < len(breaks) else None
        pricing_func = create_pricing(tariff_pricing_config[i])
        schedules.append(Schedule(charge_name, lower_bound, upper_bound, pricing_func, pricing_key))

    populate_schedules(schedules, day_rates)

    return schedules


def to_charge_period_json(start_day_of_week, end_day_of_week, period):
    start_local = period[0].astimezone()
    end_local = period[1].astimezone()
    return {
        "fromDayOfWeek": start_day_of_week,
        "fromHour": start_local.hour,
        "fromMinute": start_local.minute,
        "toDayOfWeek": end_day_of_week,
        "toHour": end_local.hour,
        "toMinute": end_local.minute
    }


def schedule_to_tariff(schedules):
    tou_periods = {}
    price_info = {}

    for schedule in schedules:
        charge_periods = []
        for period in schedule.get_periods():
            charge_periods.append(to_charge_period_json(0, 6, period))
        tou_periods[schedule.charge_name] = charge_periods
        price_info[schedule.charge_name] = schedule.get_value()
    seasons = {"Summer": {"fromMonth": 1, "fromDay": 1, "toDay": 31,
                          "toMonth": 12, "tou_periods": tou_periods},
               "Winter": {"tou_periods": {}}}
    return seasons, price_info


def to_tariff_data(config, import_schedules, export_schedules):
    import_seasons, buy_price_info = schedule_to_tariff(import_schedules)
    if export_schedules:
        export_seasons, sell_price_info = schedule_to_tariff(export_schedules)
    else:
        export_seasons = import_seasons
        sell_price_info = {charge_name: 0 for charge_name in CHARGE_NAMES}

    plan = config["tariff_name"]
    provider = config["tariff_provider"]
    demand_changes = {"ALL": {"ALL": 0}, "Summer": {}, "Winter": {}}
    daily_charges = [{"name": "Charge", "amount": 0}]
    tariff_data = {
        "name": plan,
        "utility": provider,
        "daily_charges": daily_charges,
        "demand_charges": demand_changes,
        "seasons": import_seasons,
        "energy_charges": {"ALL": {"ALL": 0},
                        "Summer": buy_price_info,
                        "Winter": {}},
        "sell_tariff": {"name": plan,
                     "utility": provider,
                     "daily_charges": daily_charges,
                     "demand_charges": demand_changes,
                     "seasons": export_seasons,
                     "energy_charges": {"ALL": {"ALL": 0},
                                        "Summer": sell_price_info,
                                        "Winter": {}}}
    }
    return tariff_data
