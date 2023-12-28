import datetime as dt


EXCLUSIVE_OFFSET = 0.000001

ONE_DAY_INCREMENT = dt.timedelta(days=1)

CHARGE_NAMES = ["SUPER_OFF_PEAK", "OFF_PEAK", "PARTIAL_PEAK", "ON_PEAK"]


class Schedule:
    def __init__(self, charge_name):
        self.charge_name = charge_name
        self._periods = []
        self._value = None
        self._value_sum = 0.0
        self.rate_count = 0
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
        self._value_sum += rate["value_inc_vat"]
        self.rate_count += 1

    def get_periods(self):
        if self._start is not None:
            self._periods.append((self._start, self._end))
            self._start = None
            self._end = None
        return self._periods

    def get_value(self):
        if self._value is None:
            if self.rate_count > 0:
                self._value = self._value_sum/self.rate_count
                if self._value < 0.0:
                    self._value = 0.0
            else:
                self._value = 0.0

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


def get_schedules(config, day_date, rates):
    day_start = dt.datetime.combine(day_date, dt.time.min).astimezone(dt.timezone.utc)
    day_end = dt.datetime.combine(day_date + ONE_DAY_INCREMENT, dt.time.min).astimezone(dt.timezone.utc)

    # filter down to the given day
    rates = [rate for rate in rates if rate["start"] >= day_start and rate["end"] <= day_end]

    if len(rates) == 0:
        return None

    # pad rates to cover 24 hours
    rates[0]["start"] = day_start
    rates[-1]["end"] = day_end

    plunge_pricing = False
    for rate in rates:
        if rate["value_inc_vat"] < 0.0:
            plunge_pricing = True
            break

    if "plunge_pricing_tariff_breaks" in config and plunge_pricing:
        configured_breaks = config["plunge_pricing_tariff_breaks"]
    else:
        configured_breaks = config["tariff_breaks"]

    breaks = []
    for i in range(len(CHARGE_NAMES)-1):
        br = configured_breaks[i]
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
