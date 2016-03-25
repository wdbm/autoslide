# autoslide: the next revolution in presentations and meeting technology

[![](http://img.youtube.com/vi/xAqiEC1YhyI/0.jpg)](https://www.youtube.com/watch?v=xAqiEC1YhyI)

# introduction

- [link to introduction presentation](https://www.youtube.com/watch?v=xAqiEC1YhyI)

# setup

The following Bash commands, that have been tested on Ubuntu 15.10, should install prerequisites and check out autoslide.

```Bash
sudo apt-get -y install festival
sudo apt-get -y install pandoc
sudo apt-get -y install sox
sudo pip install docopt
sudo pip install moviepy
sudo pip install pyfiglet
sudo pip install pyprel
sudo pip install shijian
sudo pip install technicolor
git clone https://github.com/wdbm/autoslide.git
cd autoslide/
./autoslide.py
```

# future

Under consideration is accepting PDFs as input. An existing set of slides in PDF form could be provided and from this could be generated a narrated video presentation.

```Bash
# Convert the PDF to text.
pdftotext slides.pdf slides.txt
# Convert form feed characters to Markdown headings.
cat slides.txt | sed -e 's/'$(printf "\014")'/# /g' > slides.md
```

Under consideration is automated generation of slides content using content theme parameters.
