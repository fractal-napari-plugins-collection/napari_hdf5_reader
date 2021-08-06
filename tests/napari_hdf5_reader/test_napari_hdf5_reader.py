"""
Unittests for napari_hdf5_reader.napari_hdf5_reader module.
"""
from unittest.mock import MagicMock
import sys
import h5py

# mock imports which are not available in the test environment
sys.modules['napari'] = MagicMock()
sys.modules['napari.utils'] = MagicMock()
sys.modules['napari.utils.notifications'] = MagicMock()

import pytest

from napari_hdf5_reader.napari_hdf5_reader import HDF5VisualizerWidget


@pytest.fixture(scope='module')
def feature_vis_widget():
    """
    Module-wide feature visualizer widget fixture.
    """
    # setup fixture
    yield HDF5VisualizerWidget()
    # teardown fixture


def _check_empty_layer(feature_vis_widget, mocked_show_info):
    feature_vis_widget.apply(hdf5_file="")
    call_name, call_args, call_kwargs = mocked_show_info.mock_calls.pop()
    assert (
        call_args[0] == "No hdf5 file was selected for visualization!"
    )


def _check_empty_keys(feature_vis_widget, mocked_show_info):
    feature_vis_widget.apply(hdf5_file="data.hdf5",keys="")
    call_name, call_args, call_kwargs = mocked_show_info.mock_calls.pop()
    assert (
        call_args[0] == "No key was selected for visualization!"
    )



def _check_wrong_obj(feature_vis_widget,mocker, mocked_show_info):
    mocker.patch(
        'napari_hdf5_reader.napari_hdf5_reader.HDF5VisualizerWidget.read_hdf5',
        return_value = ["test", "123"]
    )
    channel = feature_vis_widget.load_channel(path="data.hdf5",key=0)

    assert (
        channel == None
    )



def test_feature_visualizer_widget(feature_vis_widget, mocker):
    """
    Integration test for the napari_hdf5_reader.HDF5VisualizerWidget.
    """
    mocked_show_info = mocker.patch(
        'napari_hdf5_reader.napari_hdf5_reader.show_info',
        new_callable = mocker.PropertyMock
    )

    _check_empty_layer(feature_vis_widget, mocked_show_info)
    _check_empty_keys(feature_vis_widget, mocked_show_info)
    _check_wrong_obj(feature_vis_widget,mocker, mocked_show_info)
