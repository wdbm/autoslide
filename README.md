# autoslide: the next revolution in presentations and meeting technology

[![](http://img.youtube.com/vi/xAqiEC1YhyI/0.jpg)](https://www.youtube.com/watch?v=xAqiEC1YhyI)

- [link to introduction presentation](https://www.youtube.com/watch?v=xAqiEC1YhyI)

# setup

The following Bash commands, that have been tested on Ubuntu 14.10, should install prerequisites and check out abstraction.

```Bash
sudo apt-get -y install pandoc
sudo apt-get -y install festival
sudo apt-get -y install sox
sudo pip install docopt
sudo pip install pyfiglet
sudo pip install moviepy
git clone https://github.com/wdbm/autoslide.git
cd autoslide/
wget https://raw.githubusercontent.com/wdbm/pyprel/master/pyprel.py
wget https://raw.githubusercontent.com/wdbm/shijian/master/shijian.py
wget https://raw.githubusercontent.com/wdbm/technicolor/master/technicolor.py
```
