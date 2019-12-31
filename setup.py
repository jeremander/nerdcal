import setuptools

setuptools.setup(
    name = "nerdcal",
    version = "0.0.1",
    author = "Jeremy Silver",
    description = "A datetime library for alternative (non-Gregorian) calendars.",
    url = "https://github.com/jeremander/nerdcal",
    packages = setuptools.find_packages(),
    classifiers = [
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires = '>=3.7',
)