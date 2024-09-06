# Hotel Management Module

## Overview

This project is a comprehensive hotel management odoo module, developed using Odoo's web framework. The dashboard provides key insights into hotel operations, including reservation statistics, room availability, popular services, and customer satisfaction metrics. It leverages Odoo's web library (OWL) framework for the frontend and integrates various components such as charts and KPIs to deliver actionable insights.

## Features

- **Reservation Statistics**: Displays key metrics such as total reservations, check-ins, check-outs, and stays.
- **Room Management**: Provides visualizations of room status including available, reserved, and under maintenance rooms.
- **Service Analytics**: Analyzes and visualizes popular services used by guests.
- **Customer Satisfaction & Financial Metrics**: Tracks Net Promoter Score (NPS) with detailed breakdowns of promoters, neutrals, and detractors. In addition to that, it showcase other important CRM metrics and key performance indicators like Revenue Per Available Room (RevPAR), Average Daily Rate (ADR), occupancy rate, and loyal guests.

## Docker Integration

This project is Dockerized for efficient deployment and operation across different devices. It uses Docker to create a consistent environment, ensuring that the application works seamlessly regardless of the host system.

## Components

- **XML Views**:
  - `hotel.xml`: Defines the OWL dashboard view.
  - `guest.xml`: Contains the guest tree and form views.
  - `room.xml`: Contains the room tree and form views.
  - `reservation.xml`: Contains the reservation tree and form views.
  - `services.xml`: Defines the services Kanban and form views.

- **JavaScript Components**:
  - **HotelDashboard**: Main dashboard component that initializes state, fetches data, and renders the dashboard using various KPIs and charts.
  - **ChartRenderer**: Component for rendering different types of charts.
  - **Kpi**: Component for displaying key performance indicators.
  - **NPSKpi**: Component for displaying NPS-related metrics.
  - **AnalysisKpi**: Component for displaying financial analysis metrics.

## Setup

1. **Install Dependencies**: Ensure you have all necessary Odoo modules and dependencies from the manifest file installed. Don't forget the JavaScript libraries.

2. **Data Models**:
   - Ensure the following models are available in your Odoo instance:
     - `hotel.analysis`: For analytical data related to hotel operations.
     - `hotel.reservation`: For reservation data.
     - `hotel.room`: For room management data.
     - `hotel.services`: For service usage data.
     - `hotel.guest`: For guest information.

3. **Update Menus and Actions**:
   - Integrate the XML actions and menu items into your Odoo interface to enable navigation to the dashboard and related views.

## Usage

- **Accessing the Dashboard**: Navigate to the "Hotel" menu to access the main hotel management dashboard.
- **Viewing Analytics**: Click on the "Analytics" section to view detailed financial metrics.
- **Managing Reservations**: Use the "Reservations" section to view and manage hotel reservations.
- **Room Management**: Access the "Rooms" section to view room availability and status.
- **Service Analysis**: Go to the "Services" section to see data on popular services.

## Contributing

Feel free to submit issues, feature requests, or pull requests. Contributions are welcome to improve the functionality and usability of the module.

## License

This project is licensed under the MIT License. 

## Contact

For any questions or support, please contact Saber Guerricha at [saberguerricha@gmail.com].
