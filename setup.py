import setuptools

_url = 'https://github.com/mbiemann/scrawler-banco-itau'

with open('README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()
long_description = str(long_description) + '\n___\n' + 'Check on GitHub: ' + '\n' + _url

setuptools.setup(
    name='scrawler_itau',
    version='0.0.1',
    author='Marcell Biemann',
    author_email='mbiemann@gmail.com',
    description='Extrator de dados bancários do Itaú utilizando Selenium',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url=_url,
    project_urls={
        'Bug Tracker': 'https://github.com/mbiemann/scrawler-banco-itau/issues',
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    packages=['scrawler_itau'],
    python_requires='>=3.6',
    install_requires=[
        'selenium==3.141.0'
    ],
)
