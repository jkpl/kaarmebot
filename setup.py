from distutils.core import setup

setup(
    name='kaarmebot',
    version='0.0.1',
    author='Jaakko Pallari',
    author_email='jkpl@lepovirta.org',
    packages=['kaarmebot'],
    url='https://github.com/jkpl/kaarmebot',
    license='2-clause BSD',
    description='A naive, silly little IRC bot framework made in Python',
    long_description=open('README.rst').read(),
    install_requires=[
        'python-irclib == 0.4.8',
        'venusian == 1.0a7'
    ],
    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Topic :: Communications :: Chat :: Internet Relay Chat',
        'Topic :: Software Development :: Libraries :: Application Frameworks'
    ])
