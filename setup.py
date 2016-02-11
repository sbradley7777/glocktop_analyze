#!/usr/bin/python
from distutils.core import setup

# Additional Files in MANIFEST.in

################################################################################
if __name__ == "__main__":
    setup(
        name="glocktop_analyze" ,
        version="0.1-3",
        author="Shane Bradley",
        author_email="sbradley@redhat.com",
        url="https://github.com/sbradley7777/glocktop_analyze",
        description="A tool that analyzes files outputted by glocktop.",
        license="GPLv3",
        packages=["parsers"],
        scripts=["glocktop_analyze.py"],
        package_dir={"":"glocktop_analyze"},
        data_files = [("", ["LICENSE"])]
    )
################################################################################

