# Agile Powerwall
Home Assistant Pyscript-based integration that uploads dynamic pricing to Tesla Powerwalls.

This is primarily designed to sync Octopus Agile prices to Tesla Powerwalls.
It glues together two pieces of software

*   [Home Assistant Octopus Energy](https://github.com/BottlecapDave/HomeAssistant-OctopusEnergy)
*   [TeslaPy](https://github.com/tdorssers/TeslaPy)

using

*   [Pyscript](https://github.com/custom-components/pyscript).


## Installation

1.   Install Home Assistant Octopus Energy integration.
2.   Install Pyscript integration.
3.   Unzip the [release zip](https://github.com/pulquero/agile-powerwall/releases/latest) into the Home Assistant directory `/config`.
4.   Add Pyscript app configuration:

	pyscript:
	    apps:
	        powerwall:
	            email: <username/email>
	            refresh_token: <refresh_token>
	            tariff_name: Agile
	            tariff_provider: Octopus
	            import_mpan: <mpan>

5.   Optionally, create an `input_text` helper called `powerwall_tariff_update_status` if you want to see status messages.


## Configuration

`email`: E-mail address of your Tesla account.

`refresh_token`: One-off refresh token (see e.g. <https://github.com/DoctorMcKay/chromium-tesla-token-generator>)

`tariff_name`: name of the tariff.

`tariff_provider`: name of the tariff provider.

`import_mpan`: MPAN to use for import rates

`export_mpan`: MPAN to use for export rates if you have one

`import_standing_charge`: sensor name or value (default 0), e.g. `import_standing_charge: "sensor.octopus_energy_electricity_xxxxxxxxx_current_standing_charge"`.

`export_standing_charge`: sensor name or value (default 0).

`time_zone`: if you encounter time zone issues, you can either set this to an explicit time zone, e.g. `time_zone: "Europe/London"` or the name of a sensor that provides the time zone (e.g. https://community.home-assistant.io/t/how-to-obtain-ha-timezone-in-lovelace/393449/2)


### Advanced

Not suitable for most use-cases.

	pyscript:
	    apps:
	        powerwall:
	            email: <username/email>
	            refresh_token: <refresh_token>
	            tariff_name: Agile
	            tariff_provider: Octopus
	            import_mpan: <mpan>
	            import_tariff_breaks: [0.10, 0.20, 0.30]
	            import_tariff_pricing: ["average", "average", "maximum", "maximum"]
	            plunge_pricing_tariff_breaks: [0.0, 0.10, 0.30]
	            plunge_pricing_tariff_pricing: ["average", "maximum", "maximum", "maximum"]

`import_tariff_breaks`: The Powerwall app UI currently only supports four pricing levels: Peak, Mid-Peak, Off-Peak and Super Off-Peak.
Therefore to be compatible with the UI, dynamic pricing has to be mapped to these four levels.
The `import_tariff_breaks` represent the thresholds for each level.
So, in the example above, anything below £0.10 is mapped to Super Off-Peak, between £0.10 and £0.20 to Off-Peak, between £0.20 and £0.30 to Mid-peak, and above £0.30 to Peak. (You can use `import_tariff_breaks: jenks` to calculate optimal breaks, but this may not give optimal behaviour.)

`export_tariff_breaks`: same as `import_tariff_breaks`, but for export.

`plunge_pricing_tariff_breaks`: same as `import_tariff_breaks`, but applied if there are any plunge (negative) prices.

`import_tariff_pricing`: determines how to calculate the price of each import pricing level from the actual prices assigned to a level.

`plunge_pricing_tariff_pricing`: same as `import_tariff_pricing`, but applied if there are any plunge (negative) prices.

`export_tariff_pricing`: determines how to calculate the price of each export pricing level from the actual prices assigned to a level.

`import_tariff_pricing_names`: names to assign to the pricing levels.

`plunge_pricing_pricing_names`: same as `import_tariff_pricing_names`, but applied if there are any plunge (negative) prices.

`export_tariff_pricing_names`: same as `import_tariff_pricing_names`, but for export pricing levels.

`schedule_type`: one of:

 - `week` - current day rates are used for the week (default).

 - `weekend` - same as `week`, but when possible, current day rates are used for midweek/weekend and next day rates are used for weekend/midweek.

 - `multiday` - current day rates are used to span one part of the week, and next day rates are used to span the rest (not compatible with in-app editor).

`maintain_history`: keep previous schedules, don't calculate schedule afresh (default: false).


#### Computed thresholds

As well as numeric thresholds, the following computed thresholds are also supported:

`lowest(num_hours)`: sets the threshold at the price to include the cheapest `num_hours` hours.

`highest(num_hours)`: sets the threshold at the price to exclude the most expensive `num_hours` hours.

`states(sensor_name)`: uses the value of the specified sensor as a threshold.

`state_attr(sensor_name, attr_name)`: uses the value of the specified state attribute as a threshold.

e.g.:

	            import_tariff_breaks: ["lowest(2)", 0.20, 0.30]


#### Pricing formulas

`average`: the average of all the prices. If the average is negative, it is set to zero.

`nonNegativeAverage`: the average of all the prices. If a price is negative, it is taken to be zero.

`minimum`: the minimum of all the prices. If the minimum is negative, it is set to zero.

`maximum`: the maximum of all the prices.
