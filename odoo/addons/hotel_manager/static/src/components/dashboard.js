/** @odoo-module */

import { registry } from "@web/core/registry";
import { Layout } from "@web/search/layout";
import { useService } from "@web/core/utils/hooks";
import { ChartRenderer } from "./chart/chart.js";
import { Kpi } from "./kpi/kpi.js";
import { NPSKpi } from "./kpi/nps_kpi.js";
import { AnalysisKpi } from "./kpi/analysis_kpi.js";

const { DateTime, Settings } = luxon ;
const { Component, onWillStart, useState, onMounted } = owl;

class HotelDashboard extends Component {
    setup() {
        this.state = useState({
            reservations: {
                totalReservations: [],
                numReservations: 0,
                checkIns: 0, 
                checkOuts: 0,
                stays: 0,
            },
            nps: {
                score:0,
                promotersPercentage: 0,
                neutralsPercentage: 0,
                detractorsPercentage: 0,
            },
            company: {
                name: '',
            },
            anaytics: {
                revpar:0,
                adr:0,
                occupancy_rate:0,
                loyal_guests:0,
            },
            revenuChartData: null,
            roomChartData: null,
            servicesChartData: null,
        });

        this.orm = useService("orm");
        this.actionService = useService("action");

        onWillStart(async () => {            
            const today = DateTime.now();
            const lastMonth = today.minus({ months: 1 });
            await this.fetchCompanyData();
            await this.fetchReservationData();
            await this.fetchRoomsData();
            await this.fetchServicesData();
            await this.fetchAnalytics();
        });
        onMounted(async () => {
            
        });
    }

    async fetchAnalytics() {
        function formatnumber(number) {
            if (number >= 1000000) {
                return (number / 1000000).toFixed(1) + 'M'; 
            } else if (number >= 1000) {
                return (number / 1000).toFixed(1) + 'k'; 
            } else {
                return Math.floor(number); 
            }
        }
        try {
            const analysis = await this.orm.call('hotel.analysis', 'search_read', [[]]);
            const last_update = analysis.length-1;
            console.log(analysis);
            if (analysis) {
                this.state.anaytics.revpar = formatnumber(analysis[last_update].revpar);
                this.state.anaytics.adr = formatnumber(analysis[last_update].adr);
                this.state.anaytics.occupancy_rate = (analysis[last_update].occupancy_rate * 100).toFixed(1) + '%';
                this.state.anaytics.loyal_guests = analysis[last_update].loyal_guests;
            }
        } catch (error) {
            console.error('Error fetching analysis data:', error);
        }
    }

    async fetchCompanyData() {
        try {
            const company = await this.orm.call('res.company', 'read', 
                [this.env.companyId], // Get the ID of the current company
                ['name']  // Only fetch the 'name' field
            );
            if (company) { // No need to check length, as we expect a single company record
                this.state.company.name = company.name;
            }
        } catch (error) {
            console.error('Error fetching company data:', error);
        }
    }

    async fetchReservationData() {
        try {
            const totalReservations = await this.orm.call('hotel.reservation', 'search_read', [[]]);
            if (totalReservations) {
                this.state.reservations.totalReservations = totalReservations;
                const today = DateTime.now();
                const lastMonth = today.minus({ months: 1 });
                this.state.reservations.numReservations = totalReservations.length;
                const nps = totalReservations.reduce((accumulator, reservation) => {
                    const rating = reservation.nps_score;
                    if (rating == -1) {                       
                    } else if (rating >= 9) {
                        accumulator.promoters++;
                    } else if (rating >= 7) {
                        accumulator.neutrals++;
                    } else {
                        accumulator.detractors++;
                    }
                    return accumulator;
                }, { promoters: 0, neutrals: 0, detractors: 0 });
                const  totalfeedback = nps.promoters + nps.detractors + nps.neutrals;
                this.state.nps.score = Math.round(((nps.promoters - nps.detractors) / totalfeedback) * 100);
                this.state.nps.promotersPercentage = Math.round((nps.promoters / totalfeedback) * 100);
                this.state.nps.neutralsPercentage = Math.round((nps.neutrals / totalfeedback) * 100);
                this.state.nps.detractorsPercentage = Math.round((nps.detractors / totalfeedback) * 100);
                
                this.state.reservations.checkIns = totalReservations.filter((reservation) => {
                    return (
                        DateTime.fromISO(reservation.check_in_date, { zone: this.userTimeZone }).hasSame(today, 'day')
                    );
                }).length;

                this.state.reservations.checkOuts = totalReservations.filter((reservation) => {
                    return (
                        DateTime.fromISO(reservation.check_out_date, { zone: this.userTimeZone }).hasSame(today, 'day')
                    );
                }).length;

                this.state.reservations.stays = totalReservations.filter((reservation) => {
                    const checkInDate = DateTime.fromISO(reservation.check_in_date, { zone: this.userTimeZone });
                    const checkOutDate = DateTime.fromISO(reservation.check_out_date, { zone: this.userTimeZone });
                    return (checkOutDate >= today && checkInDate <= today);
                }).length;
            }
        } catch (error) {
            console.error('Error fetching reservation data:', error);
        }
    }

    async fetchServicesData() {
        function countServiceOccurrences(serviceIds, services) {
            const occurrenceCounts = {};

            for (const service of services) {
              const serviceId = service.id;
              occurrenceCounts[serviceId] = 0; 

              for (const reservation of serviceIds) {
                if (reservation.service_ids.includes(serviceId)) {
                  occurrenceCounts[serviceId]++;
                }
              }
            }
            return occurrenceCounts;
          }

        try {
            const reservations = await this.orm.searchRead('hotel.reservation', [], ['service_ids']);
            const services = await this.orm.searchRead('hotel.services', [], ['service_id']);
            const servicesCount = countServiceOccurrences(reservations, services);

            this.state.reservations.servicesCount = Object.entries(servicesCount).map(([id, occurance]) => ({ id , occurance }));
            this.state.servicesChartData = {
                labels: services.map(x => x.service_id),
                datasets: [{
                    label: 'Services',
                    data: this.state.reservations.servicesCount.map(x => x.occurance),
                }],
            };
        }
        catch (error) {
            console.error('Error fetching services:', error);
        }
    }
    
    async fetchRoomsData() {
        try {
            const totalRooms = await this.orm.call('hotel.room', 'search_read', [[]]);
            if (totalRooms) {
                const availableRooms = totalRooms.filter((room) => room.state === 'available').length;
                const occupiedRooms = totalRooms.filter((room) => room.state === 'reserved').length;
                const underMaintenanceRooms = totalRooms.filter((room) => room.state === 'under_maintenance').length;

                this.state.roomChartData = {               
                    labels: ['Reserved', 'Free', 'Under Maintenance'],
                    datasets: [{
                        label: 'Rooms',
                        data: [availableRooms, occupiedRooms, underMaintenanceRooms],
                    }]
                };

            }
        } catch (error) {
            console.error('Error fetching rooms data:', error);
        }
    }
    onClickNewReservation() {
        try {
            this.actionService.doAction("hotel_manager.action_form_reservations");
        } catch (error) {
            console.error("Error creating reservation:", error);
        }
    }

    viewAnalytics() {
        this.actionService.doAction("hotel_manager.action_hotel_analysis_dashboard");
    }
    viewReservations() {
        this.actionService.doAction("hotel_manager.action_reservations");
    }
    viewServices() {
        this.actionService.doAction("hotel_manager.action_services");
    }
    viewRooms() {
        this.actionService.doAction("hotel_manager.action_rooms");
    }
}

HotelDashboard.components = { Layout, Kpi, ChartRenderer, NPSKpi, AnalysisKpi };
HotelDashboard.template = "hotel_dashboard";

registry.category("actions").add("hotel.dashboard", HotelDashboard);
