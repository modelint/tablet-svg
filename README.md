# Tablet SVG

TabletSVG is an intermediate graphics rendering layer intended to support the generation of model diagrams such
as UML or SysML V2.

It establishes an intermediate layer between a model diagram tool and any particular graphics library or 
text format. (the latter for the SVG incarnation of Tablet)

Consequently, the model diagram tool is not affected by any change in the chosen graphics library as
long as all the required functionality is supported.

For example, the Flatland model diagram generator, was originally implemented on top of
Tablet which was built on the Cairo graphics library. I later moved it to TabletQt, and now have settled on
the simplier text path straight to SVG.  At no point was it necessary to change anying in Flatland except for
the statement that imports this package.

Here the focus is on installation.

Please see the wiki for this repository for details about the interface, features, and other documentation.

### Installation

Create or use a python 3.14+ environment.

% pip install tablet-svg

#### From your python script

Take a look at the scripts in the demo directory to see some example drawing calls to Tablet

#### From the command line

This is not the intended usage scenario, but may be helpful for testing or exploration. Since scrall may generate
some diagnostic info you may want to create a fresh working directory and cd into it first. From there...

    % tablet

You should also see a file named `tabletsvg.log`