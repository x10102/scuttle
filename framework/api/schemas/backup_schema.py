backup_config_schema = {
    'type': 'object',
    'properties': {
        'socks_proxy': {
            'type': ['string', 'null']
        },
        'http_proxy': {
            'type': ['string', 'null']
        },
        'blacklist': {
            'type': ['string', 'null']
        },
        'wikis': {
            'type': ['string', 'null']
        },
        'delay': {
            'type': ['integer', 'null'],
            'minimum': 0        
        },
        'ratelimit_size': {
            'type': ['integer', 'null'],
            'minimum': 0        
        },
        'ratelimit_refill': {
            'type': ['integer', 'null'],
            'minimum': 0        
        },
    }
}

status_message_schema = {
    'type': 'object',
    'properties': {
        'type': {
            'type': 'integer',
            'minimum': 0,
            'maximum': 7
        },
        'tag': {
            'type': 'string'
        }
    },
    'required': ['type', 'tag'],
    'oneOf': [ 
        { 'properties': {
            'type': { 'enum': [0, 5, 6, 7] }
        }},
        { 'properties': {
            'type': {'const': 1},
            'total': {'type': 'integer', 'minimum': 0}
        }, 'required': ['total']},
        { 'properties': {
            'type': {'enum': [3, 4]},
            'errorKind': {'type': 'integer', 'minimum': 0, 'maximum': 14}
        }, 'required': ['errorKind'],
            'oneOf': [
                {   'properties': {
                    'errorKind': {'enum': [0, 1, 5, 6, 7, 9, 10, 11, 12, 14]}
                }},
                {   'properties': {
                    'errorKind': {'enum': [2, 3, 4, 8, 13]},
                    'name': {'type': 'string'}
                }, 'required': ['name']}
        ]},
        { 'properties': {
            'type': {'const': 2},
            'status': {'type': 'integer', 'minimum': 0, 'maximum': 8}
        }, 'required': ['status'],
            'oneOf': [
                { 'properties': {
                    'status': {'enum': [0, 2, 3, 4, 5]}
                }},
                { 'properties': {
                    'status': {'const': 1},
                    'done': {'type': 'integer', 'minimum': 0},
                    'postponed': {'type': 'integer', 'minimum': 0}
                }, 'required': ['done', 'postponed']}
            ]}
    ]
}