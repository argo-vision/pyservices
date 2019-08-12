def get_path(comp_name):
    path = 'test.service_descriptors.components'
    return f'{path}.{comp_name}'


configurations = {
    'micro-service1': {
        'services': [get_path('service1'), get_path('service2')]
    },
    'micro-service2': {
        'services': [get_path('service3')]
    },
    'micro-service-exposition1': {
        'services': [get_path('service_exposition1')]
    },
    'micro-service2-exposition2': {
        'services': [get_path('service_exposition1')]
    },
    'micro-service2-exposition3': {
        'services': [get_path('service_exposition3')]
    },
}
