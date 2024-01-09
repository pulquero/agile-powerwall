import datetime as dt
import itertools


EXCLUSIVE_OFFSET = 0.000001

ONE_DAY_INCREMENT = dt.timedelta(days=1)

CHARGE_NAMES = ["SUPER_OFF_PEAK", "OFF_PEAK", "PARTIAL_PEAK", "ON_PEAK"]

PRICE_CAP = 1.00


class Rates:
    def __init__(self):
        self.previous_day = None
        self.current_day = None
        self.next_day = None

    def is_valid(self):
        if self.previous_day is None or self.current_day is None or self.next_day is None:
            raise ValueError("Waiting for rate data")

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

    def iter(self):
        return itertools.chain(self.previous_day, self.current_day, self.next_day)

    def clear(self):
        self.previous_day = None
        self.current_day = None
        self.next_day = None


class Schedule:
    def __init__(self, charge_name, pricing):
        self.charge_name = charge_name
        self.pricing = pricing
        self._periods = []
        self._value = None
        self._start = None
        self._end = None

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
        self.pricing.add(rate["value_inc_vat"])

    def get_periods(self):
        if self._start is not None:
            self._periods.append((self._start, self._end))
            self._start = None
            self._end = None
        return self._periods

    def get_value(self):
        if self._value is None:
            self._value = self.pricing.get_value()
        return self._value


def lowest_rates(rates, hrs):
    prices = [r["value_inc_vat"] for r in rates]
    prices.sort()
    n = round(2.0*float(hrs))
    limit = prices[n-1] if n <= len(prices) else prices[-1]
    return limit + EXCLUSIVE_OFFSET


def highest_rates(rates, hrs):
    prices = [r["value_inc_vat"] for r in rates]
    prices.sort(reverse=True)
    n = round(2.0*float(hrs))
    limit = prices[n-1] if n <= len(prices) else prices[-1]
    return limit + EXCLUSIVE_OFFSET


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


PRICING_FUNCS = {
    "average": AveragePricing,
    "minimum": MinimumPricing,
    "maximum": MaximumPricing,
}

def get_schedules(config, day_date, rates):
    day_start = dt.datetime.combine(day_date, dt.time.min).astimezone(dt.timezone.utc)
    day_end = dt.datetime.combine(day_date + ONE_DAY_INCREMENT, dt.time.min).astimezone(dt.timezone.utc)

    # filter down to the given day
    day_rates = [rate for rate in rates.iter() if rate["start"] >= day_start and rate["end"] <= day_end]

    if len(day_rates) == 0:
        return None

    # pad rates to cover 24 hours
    day_rates[0]["start"] = day_start
    day_rates[-1]["end"] = day_end

    plunge_pricing = False
    for rate in day_rates:
        if rate["value_inc_vat"] < 0.0:
            plunge_pricing = True
            break

    if "plunge_pricing_tariff_breaks" in config and plunge_pricing:
        configured_breaks = config["plunge_pricing_tariff_breaks"]
    else:
        configured_breaks = config["tariff_breaks"]
    if len(configured_breaks) != len(CHARGE_NAMES)-1:
        raise ValueError(f"{len(CHARGE_NAMES)-1} breaks must be specified")

    breaks = []
    for br in configured_breaks:
        if isinstance(br, float) or isinstance(br, int):
            v = br
        elif isinstance(br, str) and '(' in br and br[-1] == ')':
            sep = br.index('(')
            func_name = br[:sep]
            func_args = br[sep+1:-1].split(',')
            v = RATE_FUNCS[func_name](day_rates, *func_args)
        else:
            raise ValueError(f"Invalid threshold: {br}")
        breaks.append(v)

    configured_pricing = config["tariff_pricing"]
    if len(configured_pricing) != len(CHARGE_NAMES):
        raise ValueError(f"{len(CHARGE_NAMES)} pricing functions must be specified")

    schedules = []
    for i, charge_name in enumerate(CHARGE_NAMES):
        pricing_type = PRICING_FUNCS[configured_pricing[i]]
        pricing = pricing_type()
        schedules.append(Schedule(charge_name, pricing))

    for rate in day_rates:
        v = rate['value_inc_vat']
        schedule = None
        for i, br in enumerate(breaks):
            if v < br:
                schedule = schedules[i]
                break
        if schedule is None:
            schedule = schedules[-1]
        schedule.add(rate)

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


def calculate_tariff_data(config, day_date, rates):
    schedules = get_schedules(config, day_date, rates)
    if schedules is None:
        return

    tou_periods = {}
    buy_price_info = {}
    sell_price_info = {}
    for schedule in schedules:
        charge_periods = []
        for period in schedule.get_periods():
            charge_periods.append(to_charge_period_json(0, 6, period))
        tou_periods[schedule.charge_name] = charge_periods
        buy_price_info[schedule.charge_name] = schedule.get_value()
        sell_price_info[schedule.charge_name] = 0.0

    plan = config["tariff_name"]
    provider = config["tariff_provider"]
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
    return tariff_data
