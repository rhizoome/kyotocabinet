load(
    '@common//:steps.star',
    'branch_off',
    'generate_build_num_file',
    'notify_author',
    'proceed_if_file_touched',
    'stop_if_new_version_branch',
)
load(
    '@common//:utils.star',
    'retrieve_parameter',
)


def main(ctx):
    return [
        retrieve_parameter('PYPI_USERNAME'),
        retrieve_parameter('PYPI_PASSWORD'),
        retrieve_parameter('PYPI_URL'),
        retrieve_parameter('DRONE_SLACK_BOT_TOKEN'),
        retrieve_parameter('DRONE_PEOPLEFORCE_API_KEY'),
        publish_pipeline(),
        branch_off_pipeline(),
    ]


def publish_pipeline():
    return {
        'kind': 'pipeline',
        'type': 'docker',
        'name': 'publish',
        'steps': [
            stop_if_new_version_branch(),
            generate_build_num_file(),
            publish('python:3.8-slim'),
            publish('python:3.9-slim'),
            notify_author(
                {'from_secret': 'drone_slack_bot_token'},
                {'from_secret': 'drone_peopleforce_api_key'}
            ),
        ],
        'trigger': {
            'branch': [
                'master',
                # Only basic glob patterns allowed, can match things like v0aa.1bb
                'v[0-9]*.[0-9]*',
            ],
            'event': ['push'],
        },
    }


def branch_off_pipeline():
    return {
        'kind': 'pipeline',
        'type': 'docker',
        'name': 'branch-off',
        'steps': [
            proceed_if_file_touched('VERSION'),
            branch_off(),
            notify_author(
                {'from_secret': 'drone_slack_bot_token'},
                {'from_secret': 'drone_peopleforce_api_key'}
            ),
        ],
        'trigger': {
            'branch': [
                'master',
            ],
            'event': ['push'],
        },
    }


def publish(image):
    return {
        'name': 'publish_%s' % image,
        'image': image,
        'commands': [
            'export BUILD_NUM=$(cat build_num)',
            'apt update',
            'apt install -y gcc libc-dev build-essential libkyotocabinet-dev',
            'make build',
            'make publish',
            'make distclean',
        ],
        'environment': {
            'PYPI_USERNAME': {'from_secret': 'pypi_username'},
            'PYPI_PASSWORD': {'from_secret': 'pypi_password'},
            'PYPI_URL': {'from_secret': 'pypi_url'},
        }
    }
