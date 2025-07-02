from collections import defaultdict
import datetime as dt
import itertools
import sys


if "/config/pyscript_packages" not in sys.path:
    sys.path.append("/config/pyscript_packages")
#import jenkspy


EXCLUSIVE_OFFSET = 0.000001

ONE_DAY_INCREMENT = dt.timedelta(days=1)
SLOT_TIME_INCREMENT = dt.timedelta(minutes=30)

DEFAULT_CHARGE_NAMES = [
    ["PARTIAL_PEAK"],
    ["OFF_PEAK", "ON_PEAK"],
    ["SUPER_OFF_PEAK", "OFF_PEAK", "ON_PEAK"],
    ["SUPER_OFF_PEAK", "OFF_PEAK", "PARTIAL_PEAK", "ON_PEAK"]
]

PRICE_KEY = "value_inc_vat"
PRICE_CAP = 1.00

INDIVIDUAL_BREAKS = "individual"
JENKS_BREAKS = "jenks"

DEFAULT_BREAKS = INDIVIDUAL_BREAKS
DEFAULT_PRICING = "average"

DAYS_IN_WEEK = 7


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


def is_midweek(weekday):
    return weekday >= 0 and weekday <= 4


def _safe_less_than(x, y):
    return y is not None and x < y


class Rates:
    def __init__(self):
        self.previous_tariff = None
        self.previous_day = []
        self._previous_day_updated = None
        self.current_tariff = None
        self.current_day = []
        self._current_day_updated = None
        self.next_tariff = None
        self.next_day = []
        self._next_day_updated = None

    def update_previous_day(self, tariff_code, rates):
        self.previous_tariff = tariff_code
        self.previous_day = rates
        self._previous_day_updated = dt.date.today()

    def update_current_day(self, tariff_code, rates):
        self.current_tariff = tariff_code
        self.current_day = rates
        self._current_day_updated = dt.date.today()

    def update_next_day(self, tariff_code, rates):
        self.next_tariff = tariff_code
        self.next_day = rates
        self._next_day_updated = dt.date.today()

    def is_valid(self):
        if self._current_day_updated is None or self._previous_day_updated != self._current_day_updated or self._next_day_updated != self._current_day_updated:
            pending = []
            if self._previous_day_updated is None or _safe_less_than(self._previous_day_updated, self._current_day_updated) or _safe_less_than(self._previous_day_updated, self._next_day_updated):
                pending.append("previous day")
            if self._current_day_updated is None or _safe_less_than(self._current_day_updated, self._previous_day_updated) or _safe_less_than(self._current_day_updated, self._next_day_updated):
                pending.append("current day")
            if self._next_day_updated is None or _safe_less_than(self._next_day_updated, self._previous_day_updated) or _safe_less_than(self._next_day_updated, self._current_day_updated):
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
        self._previous_day_updated = None
        self._current_day_updated = None
        self._next_day_updated = None


class Schedule:
    def __init__(self, charge_name, assigner_func, pricing_func, pricing_key):
        self.charge_name = charge_name
        self.assigner_func = assigner_func
        self.pricing_func = pricing_func
        self.pricing_key = pricing_key
        self._periods = []
        self._value = None
        self._start = None
        self._end = None

    def is_in(self, rate):
        return self.assigner_func.is_in(rate)

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

    def to_string(self):
        return f"{self.charge_name} {self.assigner_func.__class__.__name__} {self.pricing_func.__class__.__name__}: {self.get_periods()}"


class WeekSchedules:
    def __init__(self):
        self.import_schedules = [None] * DAYS_IN_WEEK
        self.export_schedules = [None] * DAYS_IN_WEEK

    def update(self, weekday, import_schedules, export_schedules):
        self.import_schedules[weekday] = import_schedules
        self.export_schedules[weekday] = export_schedules

    def get_schedules(self, weekday, export=False):
        return self.export_schedules[weekday] if export else self.import_schedules[weekday]

    def reset(self, export=False):
        schedules = self.export_schedules if export else self.import_schedules
        for i in range(DAYS_IN_WEEK):
            schedules[i] = None

    def _str(self, name, schedules):
        s = f"{name}\n"
        for day, schs in enumerate(schedules):
            s += f" {day}: "
            if schs:
                s += "\n    ".join([str(sch) for sch in schs])
            s += "\n"
        return s

    def to_string(self):
        return self._str("Import", self.import_schedules) + self._str("Export", self.export_schedules)


class RateFunctions:
    def __init__(self):
        self.funcs = {
            "lowest": self.lowest_rates,
            "highest": self.highest_rates,
            "states": self.state_value,
            "state_attr": self.state_attribute
        }

    def set_helpers(self, state_getter, state_attr_getter):
        self.get_state = state_getter
        self.get_state_attr = state_attr_getter

    def apply(self, name, rates, *args):
        return self.funcs[name](rates, *args)

    def lowest_rates(self, rates, hrs):
        prices = [r[PRICE_KEY] for r in rates]
        prices.sort()
        n = round(2.0*float(hrs))
        limit = prices[n-1] if n <= len(prices) else prices[-1]
        return limit + EXCLUSIVE_OFFSET

    def highest_rates(self, rates, hrs):
        prices = [r[PRICE_KEY] for r in rates]
        prices.sort(reverse=True)
        n = round(2.0*float(hrs))
        limit = prices[n-1] if n <= len(prices) else prices[-1]
        return limit

    def state_value(self, rates, sensor_name):
        return float(self.get_state(sensor_name))
    
    def state_attribute(self, rates, sensor_name, attr_name):
        return float(self.get_state_attr(sensor_name)[attr_name])


RATE_FUNCS = RateFunctions()


class PriceAssigner:
    def __init__(self, price):
        self.price = price

    def is_in(self, rate):
        cost = rate[PRICE_KEY]
        return (self.price == cost)

    def get_charge_name(self):
        return f"{self.price}"


class PriceBandAssigner:
    def __init__(self, lower_bound, upper_bound):
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound

    def is_in(self, rate):
        cost = rate[PRICE_KEY]
        return (self.lower_bound is None or cost >= self.lower_bound) and (self.upper_bound is None or cost < self.upper_bound)

    def get_charge_name(self):
        l = self.lower_bound if self.lower_bound is not None else '-'
        u = self.upper_bound if self.upper_bound is not None else '-'
        return f"[{l}, {u})"


class AveragePricing:
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


class NonNegativeAveragePricing:
    def __init__(self):
        self.sum = 0
        self.count = 0

    def add(self, price):
        if price < 0.0:
            price = 0.0
        self.sum += price
        self.count += 1

    def get_value(self):
        if self.count > 0:
            v = self.sum/self.count
            return v
        else:
            return 0.0


class MinimumPricing:
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


class MaximumPricing:
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
    "nonNegativeAverage": NonNegativeAveragePricing,
    "minimum": MinimumPricing,
    "maximum": MaximumPricing,
    "fixed": FixedPricing,
}


def create_pricing(pricing_expr):
    if '(' in pricing_expr and pricing_expr[-1] == ')':
        sep = pricing_expr.index('(')
        func_name = pricing_expr[:sep]
        func_args = [arg.strip() for arg in pricing_expr[sep+1:-1].split(',')]
    else:
        func_name = pricing_expr
        func_args = []
    pricing_type = PRICING_FUNCS[func_name]
    return pricing_type(*func_args)


def get_tariff_assigners(break_config, rates):
    if break_config == INDIVIDUAL_BREAKS:
        unique_prices = set([r[PRICE_KEY] for r in rates])
        funcs = [PriceAssigner(price) for price in sorted(unique_prices)]
    else:
        if break_config == JENKS_BREAKS:
            bounds = jenkspy.jenks_breaks([r[PRICE_KEY] for r in rates], n_classes=len(DEFAULT_CHARGE_NAMES))
            breaks = [b + EXCLUSIVE_OFFSET for b in bounds[1:-1]]
        else:
            breaks = []
            for br in break_config:
                if isinstance(br, float) or isinstance(br, int):
                    v = br
                elif isinstance(br, str) and '(' in br and br[-1] == ')':
                    sep = br.index('(')
                    func_name = br[:sep]
                    func_args = [arg.strip() for arg in br[sep+1:-1].split(',')]
                    v = RATE_FUNCS.apply(func_name, rates, *func_args)
                else:
                    raise ValueError(f"Invalid threshold: {br}")
                breaks.append(v)
            # ensure ascending order
            breaks.sort()

        funcs = []
        for i in range(len(breaks)+1):
            lower_bound = breaks[i-1] if i > 0 else None
            upper_bound = breaks[i] if i < len(breaks) else None
            funcs.append(PriceBandAssigner(lower_bound, upper_bound))

    return funcs


def populate_schedules(schedules, day_rates):
    for rate in day_rates:
        schedule = None
        for s in schedules:
            if s.is_in(rate):
                schedule = s
                break
        schedule.add(rate)


def get_import_schedules(breaks_config, tariff_pricing_config, tariff_pricing_names, plunge_pricing_breaks_config, plunge_pricing_tariff_pricing_config, plunge_pricing_tariff_pricing_names, day_date, day_rates):
    plunge_pricing = False
    for rate in day_rates:
        if rate[PRICE_KEY] < 0.0:
            plunge_pricing = True
            break

    if plunge_pricing and plunge_pricing_breaks_config:
        configured_breaks = plunge_pricing_breaks_config
    else:
        configured_breaks = breaks_config

    if plunge_pricing and plunge_pricing_tariff_pricing_config:
        configured_pricing = plunge_pricing_tariff_pricing_config
    else:
        configured_pricing = tariff_pricing_config

    if plunge_pricing and plunge_pricing_tariff_pricing_names:
        configured_pricing_names = plunge_pricing_tariff_pricing_names
    else:
        configured_pricing_names = tariff_pricing_names

    return get_schedules(configured_breaks, configured_pricing, configured_pricing_names, day_date, day_rates)


def get_export_schedules(breaks_config, tariff_pricing_config, tariff_pricing_names, day_date, day_rates):
    return get_schedules(breaks_config, tariff_pricing_config, tariff_pricing_names, day_date, day_rates)


def get_schedules(breaks_config, tariff_pricing_config, tariff_pricing_names, day_date, day_rates):
    if (breaks_config is not None) and (type(breaks_config) == list) and (tariff_pricing_config is not None) and (len(breaks_config) + 1 != len(tariff_pricing_config)):
        raise ValueError(f"The number of breaks is inconsistent with the number of pricing functions.")

    if not day_rates:
        return None

    assigner_funcs = get_tariff_assigners(breaks_config, day_rates)

    charge_name_count = len(assigner_funcs)
    if tariff_pricing_names is None:
        if charge_name_count <= 4:
            charge_names = DEFAULT_CHARGE_NAMES[charge_name_count - 1]
        else:
            charge_names = [assigner_func.get_charge_name() for assigner_func in assigner_funcs]
    else:
        charge_names = tariff_pricing_names
        if charge_names < charge_name_count:
            charge_names += [assigner_func.get_charge_name() for assigner_func in assigner_funcs[charge_name_count:]]

    schedules = []
    for i in range(charge_name_count):
        pricing_expr = tariff_pricing_config[i] if type(tariff_pricing_config) == list else tariff_pricing_config
        pricing_func = create_pricing(pricing_expr)
        schedules.append(Schedule(charge_names[i], assigner_funcs[i], pricing_func, PRICE_KEY))

    populate_schedules(schedules, day_rates)

    return schedules


def to_charge_period_json(start_day_of_week, end_day_of_week, period, tz):
    start_local = period[0].astimezone(tz)
    end_local = period[1].astimezone(tz)
    return {
        "fromDayOfWeek": start_day_of_week,
        "fromHour": start_local.hour,
        "fromMinute": start_local.minute,
        "toDayOfWeek": end_day_of_week,
        "toHour": end_local.hour,
        "toMinute": end_local.minute
    }


def populate_tou_periods(tou_periods, schedules, start_day_of_week, end_day_of_week, tz):
    for schedule in schedules:
        charge_periods = tou_periods[schedule.charge_name]
        for period in schedule.get_periods():
            charge_periods.append(to_charge_period_json(start_day_of_week, end_day_of_week, period, tz))


def schedules_to_tariff(week_schedules, schedule_type, weekday, tz=None, export=False):
    tou_periods = defaultdict(list)

    if schedule_type == "week":
        # week
        today_schedules = week_schedules.get_schedules(weekday, export)
        populate_tou_periods(tou_periods, today_schedules, 0, 6, tz)
    elif schedule_type == "weekend":
        # midweek/weekend when possible
        if is_midweek(weekday):
            midweek_schedules = week_schedules.get_schedules(weekday, export)
            weekend_schedules = None
            for i in range(5, 7):
                weekend_schedules = week_schedules.get_schedules(i, export)
                if weekend_schedules:
                    break
        else:
            weekend_schedules = week_schedules.get_schedules(weekday, export)
            midweek_schedules = None
            for i in range(0, 5):
                midweek_schedules = week_schedules.get_schedules(i, export)
                if midweek_schedules:
                    break
    
        if midweek_schedules and weekend_schedules:
            populate_tou_periods(tou_periods, midweek_schedules, 0, 4, tz)
            populate_tou_periods(tou_periods, weekend_schedules, 5, 6, tz)
        elif midweek_schedules:
            populate_tou_periods(tou_periods, midweek_schedules, 0, 6, tz)
        elif weekend_schedules:
            populate_tou_periods(tou_periods, weekend_schedules, 0, 6, tz)
        else:
            raise ValueError("At least one schedule is required")
    elif schedule_type == "multiday":
        start = 0
        last_schedules = None
        for i in range(7):
            schedules = week_schedules.get_schedules(i, export)
            if schedules:
                if last_schedules:
                    populate_tou_periods(tou_periods, last_schedules, start, i-1, tz)
                    start = i
                last_schedules = schedules
        if last_schedules:
            populate_tou_periods(tou_periods, last_schedules, start, 6, tz)
    else:
        raise ValueError(f"Invalid schedule type: {schedule_type}")

    seasons = {"Summer": {"fromMonth": 1, "fromDay": 1, "toDay": 31,
                          "toMonth": 12, "tou_periods": tou_periods},
               "Winter": {"fromMonth": 0, "fromDay": 0, "toDay": 0,
                          "toMonth": 0, "tou_periods": {}}}
    return seasons


def get_price_info(schedules):
    price_info = {}
    for schedule in schedules:
        price_info[schedule.charge_name] = schedule.get_value()
    return price_info


def to_tariff_data(provider_name, import_plan, import_standing_charge, import_schedule_type, export_plan, export_standing_charge, export_schedule_type, week_schedules, day_date, tz=None):
    weekday = day_date.weekday()
    current_import_schedules = week_schedules.get_schedules(weekday)
    current_export_schedules = week_schedules.get_schedules(weekday, export=True)
    import_seasons = schedules_to_tariff(week_schedules, import_schedule_type, weekday, tz=tz)
    buy_price_info = get_price_info(current_import_schedules);

    if current_export_schedules:
        export_seasons = schedules_to_tariff(week_schedules, export_schedule_type, weekday, tz=tz, export=True)
        sell_price_info = get_price_info(current_export_schedules);
    else:
        export_seasons = import_seasons
        sell_price_info = {charge_name: 0 for charge_name in buy_price_info}

    demand_changes = {"ALL": {"ALL": 0}, "Summer": {}, "Winter": {}}
    import_daily_charges = [{"name": "Charge", "amount": import_standing_charge}]
    export_daily_charges = [{"name": "Charge", "amount": export_standing_charge}]
    tariff_data = {
        "name": import_plan,
        "utility": provider_name,
        "daily_charges": import_daily_charges,
        "demand_charges": demand_changes,
        "seasons": import_seasons,
        "energy_charges": {"ALL": {"ALL": 0},
                        "Summer": buy_price_info,
                        "Winter": {}},
        "sell_tariff": {"name": export_plan,
                     "utility": provider_name,
                     "daily_charges": export_daily_charges,
                     "demand_charges": demand_changes,
                     "seasons": export_seasons,
                     "energy_charges": {"ALL": {"ALL": 0},
                                        "Summer": sell_price_info,
                                        "Winter": {}}}
    }
    return tariff_data
