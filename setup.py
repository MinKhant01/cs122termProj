from setuptools import setup, find_packages

setup(
    name='YetAnotherClockApp',
    version='0.1.1',
    author='Edward Khant',
    author_email='minthwin2000@gmail.com',
    description='A helpful clock app',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/MinKhant01/cs122termProj',
    packages=find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
