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
	            tariff_breaks: [0.10, 0.20, 0.30]
	            import_tariff_pricing: ["average", "average", "maximum", "maximum"]
	            plunge_pricing_tariff_breaks: [0.0, 0.10, 0.30]

5.   Optionally, create an `input_text` helper called `powerwall_tariff_update_status` if you want status messages.


## Configuration

`email`: E-mail address of your Tesla account.

`refresh_token`: One-off refresh token (see e.g. <https://github.com/DoctorMcKay/chromium-tesla-token-generator>)

`tariff_name`: name of the tariff.

`tariff_provider`: name of the tariff provider.

`import_mpan`: MPAN to use for import rates

`export_mpan`: MPAN to use for export rates if you have one

`tariff_breaks`: Powerwall currently only supports four pricing levels: Peak, Mid-Peak, Off-Peak and Super Off-Peak.
Dynamic pricing therefore has to be mapped to these four levels.
The `tariff_breaks` represent the thresholds for each level.
So, by default, anything below £0.10 is mapped to Super Off-Peak, between £0.10 and £0.20 to Off-Peak, between £0.20 and £0.30 to Mid-peak, and above £0.30 to Peak. **Use** `tariff_breaks: jenks` **to optimally calculate the breaks.**

`plunge_pricing_tariff_breaks`: similar to above, but applied if there are any plunge (negative) prices.

`import_tariff_pricing`: determines how to calculate the price of each import pricing level from the actual prices assigned to a level.

`export_tariff_pricing`: determines how to calculate the price of each export pricing level from the actual prices assigned to a level.


### Computed thresholds

As well as numeric thresholds, the following computed thresholds are also supported:

`lowest(num_hours)`: sets the threshold at the price to include the cheapest `num_hours` hours.

`highest(num_hours)`: sets the threshold at the price to exclude the most expensive `num_hours` hours.

e.g.:

	            tariff_breaks: ["lowest(2)", 0.20, 0.30]


### Pricing formulas

`average`: the average of all the prices. If the average is negative, it is set to zero.

`minimum`: the minimum of all the prices. If the minimum is negative, it is set to zero.

`maximum`: the maximum of all the prices.
