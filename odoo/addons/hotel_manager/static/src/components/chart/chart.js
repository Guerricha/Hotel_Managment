/** @odoo-module */

import { loadJS } from "@web/core/assets";
const { Component, onWillStart, useRef, onMounted } = owl;

export class ChartRenderer extends Component {
    setup(){
        this.chartRef = useRef("chart")
        onWillStart(async ()=>{
            await loadJS("https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js")
        })

        onMounted(()=>this.renderChart())
    }

    renderChart(){
        new Chart(this.chartRef.el,
        {
          type: this.props.type,
          data: this.props.data,
          options: {
            responsive: true,
            plugins: {
              legend: {
                position: 'bottom',
              },
              title: {
                display: true,
                text: this.props.title,
                position: 'bottom',
              }
            }
          },
        }
      );
    }
}

ChartRenderer.template = "hotel.chart";
