from setuptools import setup, find_packages


setup(
    name='Grounded',
    version='1.0',
    packages=find_packages(),
    install_requires=open('requirements.txt').read(),
    entry_points={
        'console_scripts': [
            'grounded = grounded:main',
        ],
    },
    include_package_data=True,
)
