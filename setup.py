import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='pyservices',
    version='0.0.5',
    author="Alberto Fanton",
    author_email="alberto.fanton@argo.vision",
    description="Pyservices",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "persist-queue==0.4.1",
        "falcon==1.4.1",
        "pymongo==3.7.2",
        "requests==2.21.0",
        "google-cloud-tasks==1.1.0"

    ]
)
