from math import pi, sin, cos, atan

from direct.showbase.ShowBase import ShowBase
from panda3d.core import DirectionalLight, AmbientLight
from direct.task import Task
from direct.actor.Actor import Actor
from panda3d.core import Vec4
from mapping import name_mapping, index_mapping
import cv2
import mediapipe as mp

mp_pose = mp.solutions.pose
'''
    xs=[-landmark.z],
    ys=[landmark.x],
    zs=[-landmark.y],
'''

class MyApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        ambientLight = AmbientLight("ambient light")
        ambientLight.setColor(Vec4(0.2, 0.2, 0.2, 1))
        self.ambientLightNodePath = self.render.attachNewNode(ambientLight)
        self.render.setLight(self.ambientLightNodePath)
        mainLight = DirectionalLight("main light")
        mainLight.setColor(Vec4(2))
        self.mainLightNodePath = self.render.attachNewNode(mainLight)
        # Turn it around by 45 degrees, and tilt it down by 45 degrees
        self.mainLightNodePath.setHpr(45, -45, 0)
        self.render.setLight(self.mainLightNodePath)
        # self.render.setShaderAuto()
        self.cap = cv2.VideoCapture(0)
        self.pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
        self.landmark = None


        # Load the environment model.
        self.scene = self.loader.loadModel("models/environment")
        # Reparent the model to render.
        self.scene.reparentTo(self.render)
        # Apply scale and position transforms on the model.
        self.scene.setScale(0.25, 0.25, 0.25)
        self.scene.setPos(-8, 42, 0)
        # Add the spinCameraTask procedure to the task manager.
        self.taskMgr.add(self.animateTask, "animateTask")
        # self.taskMgr.add(self.videoTask, "videoTask")


        # Load and transform the panda actor.
        self.actor = Actor("person.bam")
        # self.actor.setScale(0.005, 0.005, 0.005)
        self.actor.setScale(3)

        self.actor.setPos(0, 0, 0)
        self.actor.setHpr(180, 0, 0)
        self.actor.reparentTo(self.render)
        # Loop its animation.
        self.actor.listJoints()
        self.joints = {k:self.actor.controlJoint(None, "modelRoot", v) for k, v in name_mapping.items() }


    # Define a procedure to move the camera.
    def animateTask(self, task):
        angle = pi/2
        angle = 0
        self.camera.setPos(20 * sin(angle), -20 * cos(angle), 6)
        self.camera.lookAt(0, 0, 2)
        # if self.landmark is None: return Task.cont
        # self.solve_face_rotation()
        # self.solve_shoulder_rotation(task)
        return Task.cont

    def videoTask(self, task):
        if not self.cap.isOpened(): return Task.cont
        success, image = self.cap.read()
        if not success:
            print("Ignoring empty camera frame.")
            return Task.cont
        image.flags.writeable = False
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.pose.process(image)
        if results.pose_landmarks is None: return Task.cont
        self.landmark = results.pose_world_landmarks.landmark
        return Task.cont

    def solve_face_rotation(self):
        fc = self.landmark[index_mapping["Face"]] 
        sl = self.landmark[index_mapping["ShoulderL"]]
        sr = self.landmark[index_mapping["ShoulderR"]]
        mid = tuple(map(lambda x: x/2, (sl.x + sr.x, sl.y + sr.y, sl.z + sr.z)))
        angle = atan((fc.x - mid[0]) / (fc.z - mid[2])) * 180 / pi
        faceJoint = self.joints["Face"]
        faceJoint.setHpr(0, 0, angle)

    def solve_shoulder_rotation(self, task):
        # sl = self.landmark[index_mapping["ShoulderL"]]
        # el = self.landmark[index_mapping["ElbowL"]]
        slJoint = self.joints["ShoulderL"]
        # slJoint.setH(90)
        elJoint = self.joints["ElbowL"]
        elJoint.setHpr(0,0,0)






        # sr = self.landmark[index_mapping["ShoulderR"]]
        # er = self.landmark[index_mapping["ElbowR"]]
        srJoint = self.joints["ShoulderR"]



    def close(self):
        self.cap.release()
        self.pose.close()

app = MyApp()
app.run()
app.close()
