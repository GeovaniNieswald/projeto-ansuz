import tkinter as tk
import queue
import argparse
import cv2
import dlib
import imutils
import json
import numpy as np
import os
import time as tm
import threading

from hugin.hugin import Hugin
from firebase.firebase import Firebase

from pyimagesearch.centroidtracker import CentroidTracker
from pyimagesearch.trackableobject import TrackableObject
from pyimagesearch.utils import Conf

from imutils.video import VideoStream
from imutils.video import FPS
from imutils.io import TempFile

from datetime import datetime

conf_path = "ansuz/odin/config/config.json"
uuid_path = "ansuz/odin/config/uuid.json"
data_path = "ansuz/odin/sample_data/V_20200421_112520.mp4"

class Odin():

    def __init__(self, master, conf):
        self.master = master

        self.conf = conf

        if self.conf:
            self.running = 1

            self.queue = queue.Queue()
            self.hugin = Hugin(master, self.queue, self.conf["speed_limit"])

            self.tempo_ultima_velocidade = 0
        
            self.thread1 = threading.Thread(target=self.tracker_speed)
            self.thread1.start()
        else: 
            self.running = 0
            
        self.periodic_call()
       
    def periodic_call(self):
        if not self.running:
            import sys
            sys.exit(1)

        if self.tempo_ultima_velocidade >= 10:
            self.queue.put(-99)
            self.hugin.process_incoming()
            self.tempo_ultima_velocidade = 0
        else:
            self.tempo_ultima_velocidade += 1

        self.master.after(1000, self.periodic_call)

    def tracker_speed(self):
        # initialize the list of class labels MobileNet SSD was trained to detect
        CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat",
            "bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
            "dog", "horse", "motorbike", "person", "pottedplant", "sheep",
            "sofa", "train", "tvmonitor"]

        # load our serialized model from disk
        print("[INFO] carregando modelo...")
        net = cv2.dnn.readNetFromCaffe(self.conf["prototxt_path"], self.conf["model_path"])

        if self.conf["camera"]:
            print("[INFO] iniciando câmera...")
            vs = VideoStream(src=0).start()
        else:
            print("[INFO] iniciando vídeo...")
            vs = cv2.VideoCapture(data_path)

        tm.sleep(2.0)

        # initialize the frame dimensions (we'll set them as soon as we read the first frame from the video)
        H = None
        W = None

        # instantiate our centroid tracker, then initialize a list to store
        # each of our dlib correlation trackers, followed by a dictionary to
        # map each unique object ID to a TrackableObject
        ct = CentroidTracker(maxDisappeared=self.conf["max_disappear"], maxDistance=self.conf["max_distance"])
        trackers = []
        trackable_objects = {}

        # keep the count of total number of frames
        total_frames = 0

        # initialize the list of various points used to calculate the avg of the vehicle speed
        points = [("A", "B"), ("B", "C"), ("C", "D")]

        # start the frames per second throughput estimator
        fps = FPS().start()

        # loop over the frames of the stream
        while True:
            # grab the next frame from the stream, store the current timestamp, and store the new date
            if self.conf["camera"]:
                frame = vs.read()
            else:
                ret, frame = vs.read()
            
            ts = datetime.now()

            # check if the frame is None, if so, break out of the loop
            if frame is None:
                break

            # resize the frame
            frame = imutils.resize(frame, width=self.conf["frame_width"])
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # if the frame dimensions are empty, set them
            if W is None or H is None:
                (H, W) = frame.shape[:2]
                meter_per_pixel = self.conf["distance"] / W

            # initialize our list of bounding box rectangles returned by
            # either (1) our object detector or (2) the correlation trackers
            rects = []

            # check to see if we should run a more computationally expensive
            # object detection method to aid our tracker
            if total_frames % self.conf["track_object"] == 0:
                # initialize our new set of object trackers
                trackers = []

                # convert the frame to a blob and pass the blob through the
                # network and obtain the detections
                blob = cv2.dnn.blobFromImage(frame, size=(300, 300), ddepth=cv2.CV_8U)
                net.setInput(blob, scalefactor=1.0/127.5, mean=[127.5, 127.5, 127.5])
                detections = net.forward()

                # loop over the detections
                for i in np.arange(0, detections.shape[2]):
                    # extract the confidence (i.e., probability) associated with the prediction
                    confidence = detections[0, 0, i, 2]

                    # filter out weak detections by ensuring the `confidence`
                    # is greater than the minimum confidence
                    if confidence > self.conf["confidence"]:
                        # extract the index of the class label from the detections list
                        idx = int(detections[0, 0, i, 1])

                        # if the class label is not a car, ignore it
                        if CLASSES[idx] != "car":
                            if CLASSES[idx] != "motorbike":
                                continue

                        # compute the (x, y)-coordinates of the bounding box for the object
                        box = detections[0, 0, i, 3:7] * np.array([W, H, W, H])
                        (start_x, start_y, end_x, end_y) = box.astype("int")

                        # construct a dlib rectangle object from the bounding
                        # box coordinates and then start the dlib correlation
                        # tracker
                        tracker = dlib.correlation_tracker()
                        rect = dlib.rectangle(start_x, start_y, end_x, end_y)
                        tracker.start_track(rgb, rect)

                        # add the tracker to our list of trackers so we can
                        # utilize it during skip frames
                        trackers.append(tracker)

            # otherwise, we should utilize our object *trackers* rather than
            # object *detectors* to obtain a higher frame processing throughput
            else:
                # loop over the trackers
                for tracker in trackers:
                    # update the tracker and grab the updated position
                    tracker.update(rgb)
                    pos = tracker.get_position()

                    # unpack the position object
                    start_x = int(pos.left())
                    start_y = int(pos.top())
                    end_x = int(pos.right())
                    end_y = int(pos.bottom())

                    # add the bounding box coordinates to the rectangles list
                    rects.append((start_x, start_y, end_x, end_y))

            # use the centroid tracker to associate the (1) old object
            # centroids with (2) the newly computed object centroids
            objects = ct.update(rects)

            # loop over the tracked objects
            for (object_id, centroid) in objects.items():
                # check to see if a trackable object exists for the current object ID
                to = trackable_objects.get(object_id, None)

                # if there is no existing trackable object, create one
                if to is None:
                    to = TrackableObject(object_id, centroid)

                # otherwise, if there is a trackable object and its speed has
                # not yet been estimated then estimate it
                elif not to.estimated:
                    # check if the direction of the object has been set, if not, calculate it, and set it
                    if to.direction is None:
                        y = [c[0] for c in to.centroids]
                        direction = centroid[0] - np.mean(y)
                        to.direction = direction

                    # if the direction is positive (indicating the object is moving from left to right)
                    if to.direction > 0:
                        # check to see if timestamp has been noted for point A
                        if to.timestamp["A"] == 0 :
                            # if the centroid's x-coordinate is greater than
                            # the corresponding point then set the timestamp
                            # as current timestamp and set the position as the
                            # centroid's x-coordinate
                            if centroid[0] > self.conf["speed_estimation_zone"]["A"]:
                                to.timestamp["A"] = ts
                                to.position["A"] = centroid[0]

                        # check to see if timestamp has been noted for point B
                        elif to.timestamp["B"] == 0:
                            # if the centroid's x-coordinate is greater than
                            # the corresponding point then set the timestamp
                            # as current timestamp and set the position as the
                            # centroid's x-coordinate
                            if centroid[0] > self.conf["speed_estimation_zone"]["B"]:
                                to.timestamp["B"] = ts
                                to.position["B"] = centroid[0]

                        # check to see if timestamp has been noted for point C
                        elif to.timestamp["C"] == 0:
                            # if the centroid's x-coordinate is greater than
                            # the corresponding point then set the timestamp
                            # as current timestamp and set the position as the
                            # centroid's x-coordinate
                            if centroid[0] > self.conf["speed_estimation_zone"]["C"]:
                                to.timestamp["C"] = ts
                                to.position["C"] = centroid[0]

                        # check to see if timestamp has been noted for point D
                        elif to.timestamp["D"] == 0:
                            # if the centroid's x-coordinate is greater than
                            # the corresponding point then set the timestamp
                            # as current timestamp, set the position as the
                            # centroid's x-coordinate, and set the last point
                            # flag as True
                            if centroid[0] > self.conf["speed_estimation_zone"]["D"]:
                                to.timestamp["D"] = ts
                                to.position["D"] = centroid[0]
                                to.lastPoint = True

                    """
                    # if the direction is negative (indicating the object
                    # is moving from right to left)
                    elif to.direction < 0:
                        # check to see if timestamp has been noted for point D
                        if to.timestamp["D"] == 0 :
                            # if the centroid's x-coordinate is lesser than
                            # the corresponding point then set the timestamp
                            # as current timestamp and set the position as the
                            # centroid's x-coordinate
                            if centroid[0] < self.conf["speed_estimation_zone"]["D"]:
                                to.timestamp["D"] = ts
                                to.position["D"] = centroid[0]

                        # check to see if timestamp has been noted for point C
                        elif to.timestamp["C"] == 0:
                            # if the centroid's x-coordinate is lesser than
                            # the corresponding point then set the timestamp
                            # as current timestamp and set the position as the
                            # centroid's x-coordinate
                            if centroid[0] < self.conf["speed_estimation_zone"]["C"]:
                                to.timestamp["C"] = ts
                                to.position["C"] = centroid[0]

                        # check to see if timestamp has been noted for point B
                        elif to.timestamp["B"] == 0:
                            # if the centroid's x-coordinate is lesser than
                            # the corresponding point then set the timestamp
                            # as current timestamp and set the position as the
                            # centroid's x-coordinate
                            if centroid[0] < self.conf["speed_estimation_zone"]["B"]:
                                to.timestamp["B"] = ts
                                to.position["B"] = centroid[0]

                        # check to see if timestamp has been noted for point A
                        elif to.timestamp["A"] == 0:
                            # if the centroid's x-coordinate is lesser than
                            # the corresponding point then set the timestamp
                            # as current timestamp, set the position as the
                            # centroid's x-coordinate, and set the last point
                            # flag as True
                            if centroid[0] < self.conf["speed_estimation_zone"]["A"]:
                                to.timestamp["A"] = ts
                                to.position["A"] = centroid[0]
                                to.lastPoint = True
                    """

                    # check to see if the vehicle is past the last point and
                    # the vehicle's speed has not yet been estimated, if yes,
                    # then calculate the vehicle speed and log it if it's
                    # over the limit
                    if to.lastPoint and not to.estimated:
                        # initialize the list of estimated speeds
                        estimated_speeds = []

                        # loop over all the pairs of points and estimate the vehicle speed
                        for (i, j) in points:
                            # calculate the distance in pixels
                            d = to.position[j] - to.position[i]
                            distance_in_pixels = abs(d)

                            # check if the distance in pixels is zero, if so, skip this iteration
                            if distance_in_pixels == 0:
                                continue

                            # calculate the time in hours
                            t = to.timestamp[j] - to.timestamp[i]
                            time_in_seconds = abs(t.total_seconds())
                            time_in_hours = time_in_seconds / (60 * 60)

                            # calculate distance in kilometers and append the calculated speed to the list
                            distance_in_meters = distance_in_pixels * meter_per_pixel
                            distance_in_km = distance_in_meters / 1000
                            estimated_speeds.append(distance_in_km / time_in_hours)

                        # calculate the average speed
                        to.calculate_speed(estimated_speeds)

                        # set the object as estimated
                        to.estimated = True
                        
                        print("[INFO] Velocidade do veiculo que passou é: {:.2f} km/h".format(to.speedKMPH))

                        self.queue.put(int(to.speedKMPH))
                        self.hugin.process_incoming()
                        self.tempo_ultima_velocidade = 0

                # store the trackable object in our dictionary
                trackable_objects[object_id] = to

                # draw both the ID of the object and the centroid of the object on the output frame
                text = "ID {}".format(object_id)
                cv2.putText(frame, text, (centroid[0] - 10, centroid[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                cv2.circle(frame, (centroid[0], centroid[1]), 4, (0, 255, 0), -1)

            # if the *display* flag is set, then display the current frame
            # to the screen and record if a user presses a key
            if self.conf["display"]:
                cv2.imshow("frame", frame)
                key = cv2.waitKey(1) & 0xFF

                # if the `q` key is pressed, break from the loop
                if key == ord("q"):
                    break

            # increment the total number of frames processed thus far and then update the FPS counter
            total_frames += 1
            fps.update()

        fps.stop()

        print("[INFO] tempo decorrido: {:.2f}".format(fps.elapsed()))
        print("[INFO] FPS aproximado: {:.2f}".format(fps.fps()))

        print("[INFO] limpando...")

        cv2.destroyAllWindows()

        if self.conf["camera"]:
            vs.stop()
        else:
            vs.release()
        
        self.running = 0

conf_local = None
uuid = None
local = ""
primeiro_acesso = False

if os.path.exists('./{}'.format(uuid_path)): 
    uuid = json.loads(open(uuid_path).read())["uuid"]
else: 
    primeiro_acesso = True

    uuid_txt = input("Informe o UUID: ")
    local_txt = input("Informe o Local do Sistema: ")

    uuid_json = {
        'uuid': uuid_txt
    }

    with open(uuid_path, 'w') as file_uuid:
        json.dump(uuid_json, file_uuid)

    uuid = uuid_txt
    local = local_txt

if uuid:
    if primeiro_acesso:
        conf_local = json.loads(open(conf_path).read())
        conf_local["local"] = local

        if not Firebase().gravar_conf_inicial(uuid, conf_local):
            conf_local = None
    else:
        conf_local = Firebase().obter_conf(uuid)
      
root = tk.Tk()
odin = Odin(root, conf_local)
root.mainloop()