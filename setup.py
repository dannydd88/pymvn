from setuptools import setup

setup(
    name="pymvn",
    version="1.0.24",
    description="A python implement of mvn",
    author="dannygod",
    author_email="dannygodii@gmail.com",
    url="https://github.com/dannygod/pymvn.git",
    packages=['pymvn'],
    package_data={},
    install_requires=[],
    entry_points={
        'console_scripts': [
            'pymvn = pymvn.mvn:main',
        ],
    },
)
