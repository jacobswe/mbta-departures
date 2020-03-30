class MBTACard extends HTMLElement {
	set hass(hass) {
		const icon_path = this.config.icon;
		if (!this.content) {
			const card = document.createElement('ha-card');
			card.header = name;
			this.content = document.createElement('div');
			const style = document.createElement('style');
			style.textContent = `
        table {
            width: 100%;
            padding: 1px 4px;
            font-family: 'Roboto';
        }

        td.expand {
            width: 80%
        }

        td.contract{
            width: 15%
        }

        td.img{
            width: 5%
        }`;
			card.appendChild(style);
			card.appendChild(this.content);
			this.appendChild(card);
		}
		let tablehtml = ``;
		this.config.entities.forEach(function(entity_dict) {
			tablehtml += `\n<table>`;

			let sensor = hass.states[entity_dict["entity"]];
			let attr = sensor["attributes"];
			let label = attr['label'];
			let color = attr['color'];
      let line = attr['line'];

			let stop_array = attr['upcoming_departures'];

			tablehtml += `<div style="width: 100%; border-bottom: 4px solid #${color}; text-align: center; font-weight: bold">
                    <span style="font-size: 15px;">
                      ${label}
                    </span>
                    </div>`;

      stop_array.forEach(function(stop) {
				let arrival = stop['Arrival']
				let departure = stop['Departure']
				let until = stop['Until']
				let boarding = stop['Is Boarding']

        if (boarding) {
					tablehtml += `<tr>
                        <td class="img"><img width="20px" src="/local/community/mbta-card-master/images/MBTA.png"></td>
                        <td class="expand" style="text-align:center;">Boarding</td>
                        <td style="text-align:center;">${until}</td>
                        </tr>`;
				} else {
					tablehtml += `<tr>
                        <td class="img"><img width="20px" src="/local/community/mbta-card-master/images/MBTA.png"></td>
                        <td class="expand" style="text-align:center;">Arrival: ${arrival.substring(0,5)}</td>
                        <td class="contract" style="text-align:center;">${until}</td>
                        </tr>`;
				}
			});

      if (stop_array.length == 0) {
				tablehtml += `<table>
                      <tr>
                      <td style="text-align:center;">No Upcoming Departures</td>
                      </tr>`;
			}
		});

    tablehtml += `</table>`;
		this.content.innerHTML = tablehtml;
	}

  setConfig(config) {
		if (!config.entities) {
			throw new Error('You need to define at least one entity');
		}
		this.config = config;
	}

  getCardSize() {
		return 1;
	}
}

customElements.define('mbta-card', MBTACard);
