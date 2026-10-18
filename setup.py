"""SEEM Geo — Professional ERT & MASW Processing Suite — installer.

Modern configuration lives in pyproject.toml. This file is kept for
backwards compatibility with older pip versions.
"""
from setuptools import setup, find_packages
from pathlib import Path

readme = (Path(__file__).parent / 'README.md').read_text(encoding='utf-8')

setup(
    name='seem-geo',
    version='1.1.0',
    description='SEEM Geo — Professional ERT & MASW Processing Suite',
    long_description=readme,
    long_description_content_type='text/markdown',
    author='SEEM Geo contributors',
    url='https://github.com/USERNAME/seem-geo',
    license='MIT',
    packages=find_packages(),
    python_requires='>=3.8',
    install_requires=[
        'numpy>=1.21',
        'pandas>=1.3',
        'scipy>=1.7',
        'matplotlib>=3.5',
    ],
    extras_require={
        'docs': ['mkdocs>=1.5', 'mkdocs-material>=9.0'],
        'test': ['pytest>=7.0'],
        'build': ['pyinstaller>=5.0'],
    },
    entry_points={
        'console_scripts': [
            'seem-geo = seem_geo.__main__:main',
            'seem-geo-gui = seem_geo.gui.main_window:main',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Scientific/Engineering :: GIS',
        'Topic :: Scientific/Engineering :: Physics',
    ],
    keywords='geophysics ert masw wenner resistivity shear-wave vs30 engineering-geology',
)
