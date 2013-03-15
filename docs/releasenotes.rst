Release notes
-------------

Version 0.3.2:
    
    * Fix in dicom reader (RescaleSlope and RescaleIntercept were not found)
    * Fixed that progress indicator made things slow

Version 0.3.1:
    
    * Fix installation/distribution issue.

Version 0.3.0:

This was a long haul. Implemented several plugins for animation and
volumetric data to give an idea of what sort of API's work and which 
do not. 
    
    * Refactored for more conventional package layout 
      (but importing without installing still supported)
    * Put Reader and Writer classes in the namespace of the format. This
      makes a format a unified whole, and gets rid of the
      _get_reader_class and _get_write_class methods (at the cost of
      some extra indentation).
    * Refactored Reader and Writer classes to come up with a better API
      for both users as plugins.
    * The Request class acts as a smart bridging object. Therefore all
      plugins can now read from a zipfile, http/ftp, and bytes. And they
      don't have to do a thing.
    * Implemented specific BMP, JPEG, PNG, GIF, ICON formats.
    * Implemented animated gif plugin (based on freeimage).
    * Implemented standalone DICOM plugin.

Version 0.2.3:
    
    * Fixed issue 2 (fail at instal, introduced when implementing freezing)

Version 0.2.2:
    
    * Improved documentation.
    * Worked on distribution.
    * Freezing should work now.

Version 0.2.1:

    * Introduction of the :ref:`imageio.help<insertdocs-imageio-help>` function.
    * Wrote a lot of documentation.
    * Added example (dummy) plugin.
    
Version 0.2:
    
    * New plugin system implemented after discussions in group.
    * Access to format information.

Version 0.1:

    * First version with a preliminary plugin system.
