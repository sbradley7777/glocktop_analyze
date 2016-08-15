# glocktop_analyze
The utility glocktop_analyze.py analyzes the output generated by [`glocktop`](https://git.fedorahosted.org/cgit/gfs2-utils.git/tree/gfs2/glocktop)
monitoring a GFS2 filesystems. The output is printed to console or to html format which can include graphs.

### Install
Clone the `git` repo [sbradley7777/glocktop_analyze](https://github.com/sbradley7777/glocktop_analyze).
```
$ mkdir ~/github
$ git clone https://github.com/sbradley7777/glocktop_analyze.git
```

###Requriements
The only requires for `glocktop_analyze` is `python` to do basic analyzing of [`glocktop`](https://git.fedorahosted.org/cgit/gfs2-utils.git/tree/gfs2/glocktop) files. For generating graphs and clean html files then the following is required:
- `python-beautifulsoup4`: For pretty formatted html.
- `pygal`: For graph support when html files are created. Graphs are created in `.svg` format by default.
- `lxml`, `cairosvg`, `tinycss`, `cssselect`: For creating graphs in `.png` format.

### Setup for development
Add the `glocktop_analyze` to your `PYTHONPATH` enviroment variable. Edit `~/.bash_profile` and add the following to `PYTHONPATH`. If the variable does not exist then create and export the varaible.
```
export PYTHONPATH=$HOME/github/glocktop_analyze:
```
Add an `alias` for `glocktop_analyze.py` to the file `~/.bashrc`.
```
alias glocktop_analyze.py='~/github/glocktop_analyze/glocktop_analyze.py ';
```
Log out of console or run the following command:
```
$ source ~/.bash_profile; source ~/.bashrc
```
Then run the following to see if script works and loads libraries.
```
$ glocktop_analyze.py -h
```
### Building an `rpm`
There is an RPM spec file in the repo that can be used to build an `glocktop_analyze` rpm.
```
$ rpmbuild -ba glocktop_analyze.spec
```
Install the `rpm`
```
$ sudo rpm -ivh glocktop_analyze*.rpm
```

### Usage
Analyze a directory containing glocktop files and output to a directory.\n"
```
$ glocktop_analyze.py -p /tmp/glocktop_files/ -o /var/www/html/glocktop_data
```
Analyze multiple files.
```
$ glocktop_analyze.py -p /tmp/glocktop_files/glocktop.node*
```
Analyze a single file and configure some of the plugins options.
```
$ glocktop_analyze.py -p /tmp/glocktop_files/glocktop.node1 -k glocks_activity.mininum_waiter_count=7 -k glocks_in_snapshots.mininum_glocks_in_snapshots=11
```
Analyze a single file and disable html format and show ended processes.
```
$ glocktop_analyze.py -p /tmp/glocktop_files/glocktop.node1 -T -I
```
Analyze a particular filesystem only.
```
$ glocktop_analyze.py -p /tmp/glocktop_files/glocktop.node1 -n mygfs2fs
```
Analyze a single file and enable only a specific set of plugins and disable html format.
```
# glocktop_analyze.py -p /tmp/glocktop_files/glocktop.node1  -e snapshots-multiply_nodes -e snapshots -T
```

### `glock_dump_merge.py`
The utility merges GFS2 filesystem lockdumps (glocks files) captured with
[`gfs2_lockcapture`](http://git.fedorahosted.org/cgit/gfs2-utils.git/tree/gfs2/scripts/gfs2_lockcapture)
to a format that can be processed with `glocktop_analyze.py` script.

This command will create files that `glocktop_analyze` can read in the current
working directory of `./glock_dump_merge` from the files that are found under
directory `glocktop_analyze`. The command `glock_dump_merge.py` expects the
files in that directory were captured with
[`gfs2_lockcapture`](http://git.fedorahosted.org/cgit/gfs2-utils.git/tree/gfs2/scripts/gfs2_lockcapture).
```
$ glock_dump_merge.py -p ./gfs2_lockcapture-2016-04-22/ -o ./glock_dump_merge
```

### References
- [Source Code gfs2-utils.git - `glocktop`](https://git.fedorahosted.org/cgit/gfs2-utils.git/tree/gfs2/glocktop)
- [How can I view glock contention on a GFS2 filesystem in real-time in a RHEL 5, 6, or 7 Resilient Storage cluster?](https://access.redhat.com/articles/666533)
