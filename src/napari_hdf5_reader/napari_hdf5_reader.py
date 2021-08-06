"""System module."""
import os
# from functools import lru_cache
# import random
import dask.array as da
from napari_plugin_engine import napari_hook_implementation
# from dask import delayed
import h5py
# import numpy as np
from magicgui.widgets import FunctionGui
# pylint: disable=E0611
from qtpy.QtWidgets import QMessageBox, QFileDialog
from napari.utils.notifications import show_info
from napari.types import LayerDataTuple


class Hdf5PickerWidget(FunctionGui):
    # pylint: disable=R0901
    """
    MagicGUI ValueWidget for picking a HDF5 file.
    """
    def __init__(self, value="", name="hdf5_picker", **kwargs):
        # pylint: disable=W0613
        """
        Initialization method.
        :param value: The hdf5 to initialize the widget with.
        :param name: The name of the widget.
        :param kwargs: Additional keyworded arguments.
        """
        value = value or ""
        super().__init__(
            Hdf5PickerWidget.apply,
            call_button=False,
            layout='horizontal',
            param_options={
                "hdf5_file": {"choices": [""]},
                "add_button": {
                    "widget_type": "PushButton", "text": "Add_hdf5",
                }
            },
            labels=False,
            name=name
        )

        self.files = {value, }

        self.hdf5_file.choices = self.files
        self.hdf5_file.value = value

        @self.add_button.changed.connect
        def on_press_import_button(event):
            # pylint: disable=W0613
            """
            Callback method for change events on the add_button widget.
            :param event: The change event.
            """
            h5_path, _ = (
                QFileDialog.getOpenFileName(
                    caption="Choose Hdf5 file", filter="HDF5 (*.h5 *.hdf5)"
                )
            )
            if not h5_path or not os.path.exists(h5_path):
                return

            self.hdf5_file.reset_choices()
            self.files.add(h5_path)
            self.hdf5_file.choices = self.files
            self.hdf5_file.value = h5_path

        self.hdf5_file._default_choices = self.files

        self.native.layout().setContentsMargins(0, 0, 0, 0)

    def __setitem__(self, key, value):
        """Prevent assignment by index."""
        raise NotImplementedError("magicgui.Container does not support item setting.")

    @staticmethod
    def apply(hdf5_file="", add_button=True):
        """
        Method which is invoked when picking a hdf5 file.
        This widget does not implement any functionality.
        :param hdf5_file: Defines a LineEdit widget for the feature set.
        :param add_button: Defines the PushButton widget for the add button.
        """

    @property
    def value(self):
        """
        The value of the widget.
        This method is called by magicgui when resolving the widget to a value.
        """
        return self.hdf5_file.value


class HDF5VisualizerWidget(FunctionGui):
    # pylint: disable=R0901
    """
    MagicGUI ContainerWidget for picking a hdf5 file.
    """
    def __init__(self, name="hdf5_visualizer", **kwargs):
        # pylint: disable=W0613
        """
        Initialization method.
        :param name: The name of the widget.
        :param kwargs: Additional keyworded arguments.
        """
        super().__init__(
            HDF5VisualizerWidget.apply,
            call_button="Load Channel",
            layout="vertical",
            param_options={
                "hdf5_file": {"widget_type": Hdf5PickerWidget, "name": "hdf5_picker"},
                "keys": {"choices": [""], "label": "Channels"},

            },
            name=name
        )

        def get_keys(*args):

            # pylint: disable=W0613
            """
            Method for extracting the keys from the hdf5 file.
            :param args: Additional arguments.
            """

            if self.hdf5_picker.hdf5_file.value != "":
                k = []
                file = HDF5VisualizerWidget.read_hdf5(self.hdf5_picker.hdf5_file.value)
                for key in file.keys():
                    if isinstance(file[str(key)], h5py.Dataset):
                        if file[str(key)].attrs["stain"] != "":
                            name = file[str(key)].attrs["stain"]
                        else:
                            name = key
                    else:
                        if file[str(key)+"/0"].attrs["stain"] != "":
                            name = file[str(key)+"/0"].attrs["stain"]
                        else:
                            name = key
                    k.append(name)
                return sorted(k)
            return [""]

        self.keys._default_choices = get_keys

        @self.hdf5_picker.hdf5_file.changed.connect
        def on_update_hdf5_file(event):
            """
            Callback method for change events on the hdf5_file widget.
            :param event: The change event.
            """
            self.keys.reset_choices()

        self.native.layout().addStretch()

    @staticmethod
    # @lru_cache(maxsize=16)
    def read_hdf5(path):
        """
        Method for reading hdf5 files.

        :param path: The path to the hdf5 file.
        :return: a h5py type
        """
        return h5py.File(path, 'r')

    def __setitem__(self, key, value):
        """Prevent assignment by index."""
        raise NotImplementedError("magicgui.Container does not support item setting.")

    @staticmethod
    def ret_image(key, file, val=""):
        """
        Method to extract the image or label map from hdf5 file.
        It takes the key choosen or the stain name to select the correct channel
        to load in napari.

        :param key: the key of the hdf5 file choose
        :param file: the hdf5 file selected
        :param val: the name of the attribute "stain" in case the key is the stain attribute
        :return: the dask object, the scale attribute, type (labels or image), the layer name.
        """
        dask_image = []
        if isinstance(file[str(key)], h5py.Dataset):
            dataset = file[str(key)]
            dask_image = da.from_array(dataset, chunks=(1, 256, 256))
            scale = file[str(key)].attrs["element_size_um"]
            type_layer = "labels"
            if val != "":
                name = val
            else:
                name = key
            return dask_image, scale, type_layer, name

        else:
            for level in range(len(file[str(key)])):
                dataset = file[str(key)+"/"+str(level)]
                data_arr = da.from_array(dataset, chunks=(1, 256, 256))
                dask_image.append(data_arr)
                scale = file[str(key) + "/0"].attrs["element_size_um"]
                type_layer = "image"
                if val != "":
                    name = val
                else:
                    name = key
            return dask_image, scale, type_layer, name

    @staticmethod
    def load_channel(path, key):
        file = HDF5VisualizerWidget.read_hdf5(path)
        dask_image = []
        dict_ks = {}
        if not hasattr(file, "keys"):
            show_info("Bad HDF5 file format, no keys were found")
            return
        for keys in file.keys():
            if isinstance(file[keys], h5py.Dataset):
                dict_ks[keys] = file[keys].attrs['stain']
            else:
                dict_ks[keys] = file[keys + "/0"].attrs['stain']

        key_list = list(dict_ks.keys())
        val_list = list(dict_ks.values())
        if key in val_list:
            pos = val_list.index(key)
            chan = key_list[pos]
            dask_image, scale, type, name = HDF5VisualizerWidget.ret_image(chan, file, val=key)
            return dask_image, scale, type, name
        else:
            dask_image, scale, type, name = HDF5VisualizerWidget.ret_image(key, file)
            return dask_image, scale, type, name

    @staticmethod
    def apply(
        hdf5_file="",
        keys=""
    ) -> LayerDataTuple:
        # pylint: disable=W0105,R0913
        """
        Method which is invoked when applying a color map.
        :param hdf5_file: Defines the Hdf5PickerWidget for the feature set.
        :param keys: Defines the ComboBox widget for the keys column.
        """
        if hdf5_file == "":
            show_info("No hdf5 file was selected for visualization!")
            return
        elif keys == "":
            show_info("No key was selected for visualization!")
            return
        dask_image, scale, type, name = HDF5VisualizerWidget.load_channel(hdf5_file, keys)
        return (dask_image, {'scale': scale, 'name': name, 'blending': 'additive'}, type)


@napari_hook_implementation
def napari_experimental_provide_dock_widget():
    """
    Napari plugin that returns a widget for reading features from a hdf5 file.
    :return: A HDF5VisualizerWidget class
    """
    return HDF5VisualizerWidget


# Implentation of multiscale view in tiles. At the moment OCTREE does not support
# tiles of 3D data

    # @staticmethod
    # def read_tile(dt, x, y, width, height,image_length,image_width,z):
    #     data = np.zeros((height, width), dtype=np.uint8)
    #     height = height if y+height < image_length else image_length - y
    #     width = width if x+width < image_width else image_width - x
    #     if height!=0 and width!=0:
    #         data[:width, :height]= dt[z][x:x+width, y:y+height]
    #     return data


#tile_size=256
# for level in range(len(file[str(key)])):
#     dataset=file[str(key)+'/'+str(level)]
#     read_tile2=partial(read_tile,dataset)
#     lazy_read=delayed(read_tile2)
#     z_ind=dataset.shape[0]
#     image_height=dataset.shape[1]
#     image_width=dataset.shape[2]
#     if (
#         (image_height< tile_size) or
#         (image_width< tile_size)
#     ):
#         break
#
#
#     y_tiles = (image_height// tile_size)
#     x_tiles = (image_width // tile_size)
#     if image_height % tile_size != 0  :
#         y_tiles += 1
#
#     if image_width % tile_size != 0  :
#         x_tiles += 1
#
#     z_tiles=[]
#     for z in range(z_ind):
#
#         dask_tiles = []
#
#
#         for x in range(x_tiles):
#
#             dask_tiles.append(
#                 [
#
#                 da.from_delayed(lazy_read(x*tile_size,
                                            # y*tile_size,
                                            # tile_size,
                                            # tile_size,
                                            # image_height,
                                            # image_width,
                                            # z),
#                     shape=(tile_size, tile_size), dtype=np.uint8
#                 )
#                 for y in range(y_tiles)
#
#                 ]
#             )
#         z_tiles.append(dask_tiles)
#
#
#
#     dask_image.append(da.block(z_tiles))
