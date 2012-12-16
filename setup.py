from setuptools import setup

setup(
    name='lsp',
    version='0.1',
    description='A little lisp in python',
    license='MIT',
    author='Lucian Branescu Mihaila',
    package='lsp',
    entry_points=dict(
        console_scripts= [
            'lsp = lsp:main',
        ]
    )
)
