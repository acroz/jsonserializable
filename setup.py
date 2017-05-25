from setuptools import setup, find_packages


setup(
    name='jsonserializable',
    description='Automatic serialization of your data structures',
    author='Andrew Crozier',
    author_email='wacrozier@gmail.com',
    classifiers=[
        'Programming Language :: Python :: 3',
    ],
    keywords='json model',
    packages=find_packages(),
    install_requires=[
        'jsonschema'
    ]
)
