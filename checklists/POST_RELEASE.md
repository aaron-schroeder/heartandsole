## Post-release action checklist

Congrats, you just released your latest version. 
Here's what to do next, in case you forgot.

* Create the new changelog page
  * Copy the [whatsnew template](../docs/_templates/whatsnew.rst) to the
    [whatsnew folder](../docs/source/whatsnew), and rename to 
    `v{major}.{minor}.{patch}.rst`.
  * In the newly-created document, rename every instance of {major},
    {minor}, and {patch}.
  * In the [whatsnew index document](../docs/source/whatsnew/index.rst),
    add this document's name to the toc.

* Update the package's [`__version__`](../heartandsole/__init__.py).

* Commit directly to master, with a message like:

  ```markdown
  Version bump
  - Update `__version__`
  - Create changelog page
  ```

