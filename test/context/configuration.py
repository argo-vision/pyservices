def get_path(comp_name):
    base_path = 'test.context.components'
    return f'{base_path}.{comp_name}'


configurations = {
    'micro-service1': {
        'services': [get_path('service1'), get_path('service2')]
    },
    'micro-service2': {
        'services': [get_path('service3')]
    },
    'micro-service-broken': {
        'services': [get_path('service_broken')]
    },
    'micro-service-circular': {
        'services': [get_path('service_circular1')]
    },
    'micro-service-empty': {
        'services': []
    },

}
