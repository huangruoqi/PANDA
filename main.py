from math import pi, sin, cos

from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.actor.Actor import Actor


class MyApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        # Load the environment model.
        self.scene = self.loader.loadModel("models/environment")
        # Reparent the model to render.
        self.scene.reparentTo(self.render)
        # Apply scale and position transforms on the model.
        self.scene.setScale(0.25, 0.25, 0.25)
        self.scene.setPos(-8, 42, 0)

        # Add the spinCameraTask procedure to the task manager.
        self.taskMgr.add(self.spinCameraTask, "SpinCameraTask")

        # Load and transform the panda actor.
        self.pandaActor = Actor("models/panda-model")
        self.pandaActor.setScale(0.005, 0.005, 0.005)
        self.pandaActor.setPos(0, 0, 0)
        self.pandaActor.reparentTo(self.render)
        # Loop its animation.
        self.pandaActor.listJoints()
        self.dummy = self.pandaActor.controlJoint(None, "modelRoot", "Dummy_hips")


    # Define a procedure to move the camera.
    def spinCameraTask(self, task):
        # angleDegrees = task.time * 6.0
        angleRadians = (pi / 180.0)
        self.camera.setPos(20 * sin(angleRadians), -20 * cos(angleRadians), 3)
        # self.camera.setHpr(angleDegrees, 0, 0)
        self.dummy.setPos(task.time*100)
        return Task.cont


app = MyApp()
app.run()