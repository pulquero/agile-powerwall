# Agile Powerwall
Home Assistant Pyscript-based integration that uploads dynamic pricing to Tesla Powerwalls.

This is primarily designed to sync Octopus Agile prices to Tesla Powerwalls.
It glues together two pieces of software

*   [Home Assistant Octopus Energy](https://github.com/BottlecapDave/HomeAssistant-OctopusEnergy)
*   [TeslaPy](https://github.com/tdorssers/TeslaPy)

using

*   [Pyscript](https://github.com/custom-components/pyscript).


## Installation

1.   Install Octopus Energy.
2.   Install Pyscript.
3.   Copy `powerwall/*` to the Home Assistant directory `/config/pyscript/apps/powerwall/*`.
4.   Add Pyscript app configuration:

	pyscript:
	    apps:
	        powerwall:
	            email: <username/email>
	            refresh_token: <refresh_token>
	            tariff_breaks: [0.10, 0.20, 0.30]

## Configuration

`email`: E-mail address of your Tesla account.

`refresh_token`: One-off refresh token (see e.g. <https://github.com/DoctorMcKay/chromium-tesla-token-generator>)

`tariff_breaks`: Powerwall currently only supports four pricing levels: Peak, Mid-Peak, Off-Peak and Super Off-Peak.
Dynamic pricing therefore has to be mapped to these four levels.
The `tariff_breaks` represent the thresholds for each level.
So, by default, anything below £0.10 is mapped to Super Off-Peak, between £0.10 and £0.20 to Off-Peak, between £0.20 and £0.30 to Mid-peak, and above £0.30 to Peak.
The price of each level is set to be the average of all the actual prices assigned to a level.
If the average turns out to be negative, it is set to zero.
