# Swiss Grid Tools

Coordinate transformations involving the Swiss reference frames are
not terribly well covered in many standard GIS tools and
libraries. Here I aim at making available some Python code, which is
supposed to help speed-up people's coordinate transformation tasks.


## WGS84-LV03.py
The class `Convert` provides:

+ a method `convert (points, typ=['proj4'|'rest'])`, which converts
    coordinates from LV03 to WGS84 and vice versa.<br />
    `convert` detects automatically which direction of conversion is desired.<br />
    `points` is a list with tuples (easting, northing), or (x,y).<br />
	`typ`indicates whether the REST-service of swisstopo or the local
	 PROJ.4 - libraryis used. 

+ The method `check_conversion` creates an arbitratry number of random coordinates
    in Switzerland, both in LV03 and WGS84, and converts them using both,
	the REST-service and the local projection librtary. The differences
	(which seem to be always on the order of 1 cm) are returned.


The "shiftgrid" file `chenyx06etrs.gsb`is essential for a good
transformation. It is contained in this repo, but you might want to
rename it. This is because if the file is not found, the latest one
will be downloaded from the swisstopo site. But beware: There is no
guarantee that the respective URL wll remain valid.

## Example

~~~Python
from WGS84-LV03 import Convert

bern = (7.43861, 46.951)
zurich = (8.55, 47.37)
C = Convert()
C.convert([bern, zurich])
Out[1]: 
[(599998.2101365564, 199990.7321469287),
 (683940.6285646699, 247167.5578803884)]
~~~

## TODO

+ Deal with the "new" LV95.

## References
+ [swisstopo REST-service](http://www.swisstopo.admin.ch/internet/swisstopo/en/home/products/software/products/m2m.html)
+ [swisstopo LV03 documentation](http://www.swisstopo.admin.ch/internet/swisstopo/en/home/topics/survey/sys/refsys/switzerland.parsysrelated1.37696.downloadList.97912.DownloadFile.tmp/swissprojectionen.pdf)
+ [swisstopo LV95 documentation](http://www.swisstopo.admin.ch/internet/swisstopo/en/home/topics/survey/sys/frames.parsysrelated1.91518.downloadList.64544.DownloadFile.tmp/broschlv95de.pdf)
+ [The PROJ.4 library](http://trac.osgeo.org/proj/)
+ ["pyproj" the python intrface to PROJ.4](http://jswhit.github.io/pyproj/)

