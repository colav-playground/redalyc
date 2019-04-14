from setuptools import setup
setup(
    name='redalyc',
    version='0.0.1',
    # Dependent packages (distributions)
    install_requires=[
        'requests',
        'pandas',
        'bs4'
    ],
    entry_points={
        'console_scripts': [
            'redalyc=redalyc:run'
        ]
    }
)
