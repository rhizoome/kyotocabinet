load(
    '@common//:steps.star',
    'branch_off',
    'generate_build_num_file',
    'notify_author',
    'proceed_if_file_touched',
    'stop_if_new_version_branch',
)
load('@common//:utils.star', 'retrieve_parameter')

VALIDATION_COMMANDS = {
   'lint': ['make pep8'],
   'run tests': ['make test'],
}
INSTALL_DEPENDENCIES = [
    'build-essential',
    'curl',
    'kyotocabinet-utils',
    'libc-dev',
    'libkyotocabinet-dev',
]
RUNTIME_DEPENDENCIES = [
    'kyotocabinet-utils',
    'libkyotocabinet-dev',
    'make',
]
WORKSPACE_PATH = '/drone/src'
POETRY_CACHE_DIR = WORKSPACE_PATH + '/.poetry_cache'
POETRY_HOME = WORKSPACE_PATH + '/.poetry'
POETRY_VERSION = '1.1.13'


def main(ctx):
    return [
        retrieve_parameter('PYPI_USERNAME'),
        retrieve_parameter('PYPI_PASSWORD'),
        retrieve_parameter('PYPI_URL'),
        retrieve_parameter('DRONE_SLACK_BOT_TOKEN'),
        retrieve_parameter('DRONE_PEOPLEFORCE_API_KEY'),
        pr_pipeline(),
        publish_pipeline(),
        branch_off_pipeline(),
    ]


def pr_pipeline():
    validation_steps = [
        docker_run(name, commands)
        for name, commands in VALIDATION_COMMANDS.items()
    ]
    return {
        'kind': 'pipeline',
        'type': 'docker',
        'name': 'pull request',
        'steps': [
            install(),
        ] + validation_steps,
        'trigger': {
            'event': [
                'pull_request',
            ]
        },
        'workspace': {
            'path': WORKSPACE_PATH,
        },
    }


def install():
    return {
        'name': 'install',
        'image': 'python:3.9-slim',
        'commands': [
            'apt update',
            'apt install -y ' + ' '.join(INSTALL_DEPENDENCIES),
            'curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python',
            '. $POETRY_HOME/env && make install',
        ],
        'environment': {
            'POETRY_CACHE_DIR': POETRY_CACHE_DIR,
            'POETRY_HOME': POETRY_HOME,
            'POETRY_VERSION': POETRY_VERSION,
        }
     }


def docker_run(name, commands):
    return {
        'name': name,
        'image': 'python:3.9-slim',
        'commands': [
            'apt update',
            'apt install -y ' + ' '.join(RUNTIME_DEPENDENCIES),
            '. $POETRY_HOME/env',
            '. `poetry env info -p`/bin/activate',
        ] + commands,
        'environment': {
            'POETRY_CACHE_DIR': POETRY_CACHE_DIR,
            'POETRY_HOME': POETRY_HOME,
        }
    }


def publish_pipeline():
    return {
        'kind': 'pipeline',
        'type': 'docker',
        'name': 'publish',
        'steps': [
            stop_if_new_version_branch(),
            generate_build_num_file(),
            publish(),
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


def publish():
    return {
        'name': 'publish_python:3.9-slim',
        'image': 'python:3.9-slim',
        'commands': [
            'export BUILD_NUM=$(cat build_num)',
            'apt update',
            'apt install -y ' +  ' '.join(INSTALL_DEPENDENCIES),
            'curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python',
            '. $HOME/.poetry/env && make build',
            '. $HOME/.poetry/env && make publish',
        ],
        'environment': {
            'PYPI_USERNAME': {'from_secret': 'pypi_username'},
            'PYPI_PASSWORD': {'from_secret': 'pypi_password'},
            'PYPI_URL': {'from_secret': 'pypi_url'},
        }
    }
