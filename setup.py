from setuptools import find_packages, setup

setup(
    name='musicutil',
    version='0.1.3-alpha1',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'beautifulsoup4','requests', 'html5lib', 'spotipy'
    ],
)