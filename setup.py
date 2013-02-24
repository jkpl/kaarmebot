from setuptools import setup, find_packages

requires = [
    'python-irclib == 0.4.8',
    'gevent >= 0.13.8',
    'venusian >= 1.0a7'
]

tests_require = [
    'nose >= 1.0',
    'mockito'
]

setup(
    name='kaarmebot',
    version='0.0.3',
    author='Jaakko Pallari',
    author_email='jkpl@lepovirta.org',
    packages=find_packages(exclude='tests'),
    url='https://github.com/jkpl/kaarmebot',
    license='2-clause BSD',
    description='A naive, silly little IRC bot framework made in Python',
    long_description=open('README.rst').read(),
    install_requires=requires,
    tests_require=requires + tests_require,
    setup_requires=tests_require,
    test_suite='kaarmebot.tests',
    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Topic :: Communications :: Chat :: Internet Relay Chat',
        'Topic :: Software Development :: Libraries :: Application Frameworks'
    ])
