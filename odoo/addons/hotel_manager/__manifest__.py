{
    # The name of the Odoo module as it will appear in the interface
    'name': 'Hotel Management',
    
    # The version of the module, which can be updated as the module evolves
    'version': '1.0',
    
    # A brief summary of what the module does
    'summary': 'Manage your reservations, guests, rooms and services in your hotel efficiently.',
    
    # A detailed description of the module's functionality (you can expand this further)
    'description': 'Module Description',
    
    # The author or creator of the module
    'author': 'Saber Guerricha',
    
    # The website of the module or the company/individual who created it
    'website': 'HotelERP',
    
    # The category under which the module will be listed in the Odoo apps store or modules list
    'category': 'Category',
    
    # List of modules that this module depends on
    # These dependencies must be installed for this module to work properly
    'depends': ['base', 'web', 'account'],
    
    # List of data files to be loaded when the module is installed
    # These files include views, security rules, data records, and reports
    'data': [
        'views/hotel.xml',                # View for hotel management
        'views/reservations.xml',         # View for reservations management
        'views/rooms.xml',                # View for rooms management
        'views/analysis.xml',             # View for data analysis
        'views/guest.xml',                # View for guest management
        'security/security.xml',          # Security rules for the module
        'security/ir.model.access.csv',   # Access control for different user roles
        'data/data.xml',                  # Initial data or configuration settings
        'data/cron.xml',                  # Scheduled actions or cron jobs
        'reports/reservation_rep.xml'     # Custom report for reservations
    ],
    
    # Indicates whether the module can be installed
    'installable': True,
    
    # Indicates whether the module should be automatically installed when its dependencies are installed
    'auto_install': False,
    
    # Indicates whether the module is an application (will be shown in the main app dashboard)
    'application': True,
    
    # Defines the static assets (JavaScript, CSS, XML files) to be included in the Odoo backend
    'assets': {
        'web.assets_backend': [
            'hotel_manager/static/src/components/**/*.js',   # JavaScript components
            'hotel_manager/static/src/components/**/*.xml',  # XML templates for components
            'hotel_manager/static/src/components/**/*.css'   # CSS styles for components
        ],
    },
}
