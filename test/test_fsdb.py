import datetime
import sys

from lettucethink.db import fsdb

if len(sys.argv) != 2:
    print("Usage: test_fsdb scan-directory")
    sys.exit(1)


# Instantiate the database
db = fsdb.DB(sys.argv[1])

# Run through all the scans, filesets, and files in the scan directory
if len(db.get_scans()) == 0:
    print("No scans, yet")
else:
    for scan in db.get_scans():
        print("Scan '%s'" % scan.get_id())
        for fileset in scan.get_filesets():
            print("- Fileset '%s'" % fileset.get_id())
            for file in fileset.get_files():
                print("      File '%s'" % file.get_id())


# Create a new scan            
now = datetime.datetime.now()
id =  now.strftime("%Y%m%d-%H%M%S")

hardware = {
    "version": "0.1",
    "camera": "RX0",
    "gimbal": "dynamixel"}

biology = {
    "species": "A. thaliana",
    "plant": "GT1"}

scan = db.create_scan(id)
scan.set_metadata("hardware", hardware)
scan.set_metadata("biology", biology)

# Create a fileset to store the images
fileset = scan.create_fileset("images")
file = fileset.create_file("00001")

# Using write_text() for convenience to store the file content. You
# can use file.write_image("jpg", image) to store a jpeg. Or
# file.import_file("myfile.jpg") to import an existing file.
file.write_text("jpg", "any textual data\n")

# Add some metadata to the image file.
file.set_metadata("position", [73, 120, 0]) # Millimeter by default? Or meter?
file.set_metadata("orientation", [120, 10])    # pan-tilt, or roll-pitch-yaw?

# It would also have been possible to store the positions in the
# fileset:
#
# positions = {}
# positions['00001'] = [73, 120, 0]
# fileset.set_metadata("positions", positions)


