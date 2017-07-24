""" 
Console scripts and associated helper functions for imageio.
"""
import argparse

from . import plugins


def download_bin(plugin_names=["all"]):
    """ Download binary dependencies of plugins
    
    This is a convenience method for downloading the binaries
    (e.g. `ffmpeg.win32.exe` for Windows) from the imageio-binaries
    repository.
    
    Parameters
    ----------
    plugin_names: list
        A list of imageio plugin names. If it contains "all", all
        binary dependencies are downloaded.
    """
    if plugin_names.count("all"):
        # Create a list of all plugins
        # TODO:
        # - do this automatically by searching e.g. `formats`?
        plugin_names = ["avbin", "ffmpeg", "freeimage"]
    
    plugin_names.sort()
    
    for plg in plugin_names:
        mod = getattr(plugins, plg)
        # TODO:
        # - Let `download` take *args and **kwargs that are then
        #   passed to `fetching.get_remote_file`
        mod.download()


def download_bin_main():
    """ Argument-parsing wrapper for `download_bin` """
    description = "Download plugin binary dependencies"
    phelp = "Plugin name for which to download the binary. "\
          +"If no argument is given, all binaries are downloaded."
    example_text = "examples:\n"\
                  +"  imageio_download_bin all\n"\
                  +"  imageio_download_bin ffmpeg\n"\
                  +"  imageio_download_bin avbin ffmpeg\n"
    parser = argparse.ArgumentParser(
                description=description,
                epilog=example_text,
                formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("plugin", type=str, nargs="*", default="all",
                        help=phelp)
    args = parser.parse_args()
    download_bin(plugin_names=args.plugin)
