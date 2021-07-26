from setuptools import setup, find_packages

setup(
    name='fractal-napari-plugins:hdf5_reader',
    version='1.1.0',
    author='Dario Vischi, Marco Franzon, Giuseppe Piero Brandino',
    author_email='dario.vischi@fmi.ch, marco.franzon@exact-lab.it, giuseppe.brandino@exact-lab.it',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    license='BSD3',
    description=(
        'Plugins for reading multi-scale/multi-dimensional hdf5 files into Napari.'
    ),
    long_description=open('README.md').read(),
    python_requires='>=3.7',
    install_requires=[
        "napari[all] == 0.4.7",
        "napari_plugin_engine >= 0.1.9",
        "magicgui >= 0.2.9",
        "dask[complete] >= 2021.4.0",
        "numpy >= 1.20.2",
        "h5py >= 3.3.0",
        "imagecodecs >= 2020.5.30",
    ],
    entry_points={
        'napari.plugin': [
            'napari_hdf5_reader = napari_hdf5_reader.napari_hdf5_reader',
        ],
    },
    setup_requires=['pytest-runner',],
    tests_require=['pytest',],

)
