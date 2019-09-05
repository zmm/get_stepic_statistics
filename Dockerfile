FROM tknerr/baseimage-ubuntu:18.04
RUN apt-get update
RUN apt-get -y install python3.7 python3-dev python3-pip
RUN apt-get clean

ADD ./ /sources
WORKDIR /sources
RUN python3.7 -m pip install -r ./requirements.txt

# --sheet Google table id
# --id Stepik course id
# --list Google table sheet name where score should be placed
# --cell_range cells countaining stepik_id for students (in --sheet)
# --stepik_id_source_sheet - sheet name where --cell_range is located

CMD python3.7 course_statistics.py --id 4792 --key ./key --sheet 1puJGoK8noG8_sAFSkmIhiwBfHcnxqKiRMgEd8BaiyxU --list Users --cell_range 'C10:C19' --stepik_id_source_sheet Sheet1 
