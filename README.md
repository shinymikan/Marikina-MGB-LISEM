# Marikina-MGB-LISEM

Before cloning this repository, make sure that you install git-lfs in windows via:

```
winget install -e --id GitHub.GitLFS
```

This allows the large files to be cloned as well. Alternatively, you may manually download the landsat bands and the training samples. 

Make sure that you have all the dependencies installed in `requirements.txt`, if not, install them first. If an error occurs during installation, it may be wise to install in a freshly created virtual environment (conda recommended).

Finally, to generate all the maps, simply run:

```
python main.py
```

