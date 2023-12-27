import datetime as dt


EXCLUSIVE_OFFSET = 0.000001

CHARGE_NAMES = ["SUPER_OFF_PEAK", "OFF_PEAK", "PARTIAL_PEAK", "ON_PEAK"]


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


def lowest_rates(rates, hrs):
    prices = [r["value_inc_vat"] for r in rates]
    prices.sort()
    n = 2*int(hrs)
    limit = prices[n-1] if n <= len(prices) else prices[-1]
    return limit + EXCLUSIVE_OFFSET


def highest_rates(rates, hrs):
    prices = [r["value_inc_vat"] for r in rates]
    prices.sort(reverse=True)
    n = 2*int(hrs)
    limit = prices[n-1] if n <= len(prices) else prices[-1]
    return limit + EXCLUSIVE_OFFSET


RATE_FUNCS = {
    "lowest": lowest_rates,
    "highest": highest_rates
}


def calculate_tariff_data(config, rates):
    today = dt.date.today()
    today_start = dt.datetime.combine(today, dt.time.min).astimezone(dt.timezone.utc)
    today_end = dt.datetime.combine(today + dt.timedelta(days=1), dt.time.min).astimezone(dt.timezone.utc)

    # filter down to today's rates
    rates = [rate for rate in rates if rate["start"] >= today_start and rate["end"] <= today_end]

    if len(rates) == 0:
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
