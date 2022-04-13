Test CLF
========

Apply a Common LUT Format (CLF) transform to input RGB data to test its
accuracy. Recommended image format: OpenEXR.

Usage
-----

For full documentation, run:

`python testclf.py --help`

To apply a CLF to an image, run:

`python testclf.py transform.clf input.exr -o output.exr`

To apply a CLF to one or more RGB float triplets, run:

`python testclf.py transform.clf R,G,B R,G,B ...`

which will print to the shell:

```
R,G,B -> R,G,B
R,G,B -> R,G,B
```

To apply a CLF inverse, add the `-i` or `--inverse` option to either
command.

Dependencies
------------

* Python (>=3.7)
* `pip install requirements.txt`
  * Installs [numpy](https://pypi.org/project/numpy/)
  * Installs [opencolorio](https://pypi.org/project/opencolorio/)
  * Installs [imageio](https://pypi.org/project/imageio/)
* `imageio_download_bin freeimage`
  * Installs [imageio FreeImage plugin](https://imageio.readthedocs.io/en/stable/_autosummary/imageio.plugins.freeimage.html) to enable OpenEXR support
