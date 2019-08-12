def get_path(comp_name):
    base_path = 'test.context.components'
    return f'{base_path}.{comp_name}'


configurations = {
    'micro-service1': {
        'services': [get_path('service1'), get_path('service2')],
        'address': 'localhost',
        'port': '1234'
    },
    'micro-service2': {
        'services': [get_path('service3')],
        'address': 'localhost',
        'port': '7890'
    },
    'micro-service-broken': {
        'services': [get_path('service_broken')],
        'address': 'localhost',
        'port': '12347'
    },
    'micro-service-circular': {
        'services': [get_path('service_circular1')],
        'address': 'localhost',
        'port': '12348'
    },
    'micro-service-empty': {
        'services': [],
        'address': 'localhost',
        'port': '12349'
    },

}
