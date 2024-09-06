FROM odoo:17.0

# Switch to root user to install dependencies
USER root

# Install Node.js and npm
RUN apt-get update && apt-get install -y nodejs npm

# Switch back to odoo user
USER odoo

# Create app directory
WORKDIR /usr/src/app

# Install luxon
RUN npm install luxon

# Copy your custom modules
COPY ./addons /mnt/extra-addons
