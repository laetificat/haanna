from setuptools import setup

def readme():
    with open('README.rst') as f:
        return f.read()

setup(
    name='haanna',
    version='0.10.0',
    description='Plugwise Anna API to use in conjunction with Home Assistant.',
    long_description='Plugwise Anna API to use in conjunction with Home Assistant, but it can also be used without Home Assistant.',
    keywords='HomeAssistant HA Home Assistant Anna Plugwise',
    url='https://github.com/laetificat/haanna',
    author='Laetificat',
    author_email='k.heruer@gmail.com',
    license='MIT',
    packages=['haanna'],
    install_requires=['requests','datetime','pytz'],
    zip_safe=False
)
