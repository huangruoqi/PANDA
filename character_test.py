from panda3d.core import *
from CCDIK.ik_actor import IKActor
from CCDIK.utils import *
from math import pi, sin, cos, atan

from direct.showbase.ShowBase import ShowBase

from mapping import name_mapping, index_mapping
import cv2
import mediapipe as mp
import numpy as np

mp_pose = mp.solutions.pose
'''
    xs=[-landmark.z],
    ys=[landmark.x],
    zs=[-landmark.y],
'''

def convert(landmark):
    return -landmark.x, -landmark.z, -landmark.y

class RiggedChar():

    def __init__( self ):

        self.root_node = render.attach_new_node("Torso")
        geom = create_axes( 0.3 )
        self.root_node.attach_new_node( geom )

        # How high the root node should currently be (Determined by the average position of all
        # grounded feet):
        self.root_height = 0.956756    # Distance between root node and the ground
        #self.root_height = 0
        self.root_node.set_pos( 0, 0, self.root_height )
        self.cur_target_height = self.root_height

        self.cap = cv2.VideoCapture(0)
        self.pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
        self.landmark = None
        base.taskMgr.add(self.videoTask, "videoTask")


        ##################################
        # Set up body movement:

        #geom = create_axes( 0.2 )
        #self.target_node.attach_new_node( geom )
        self.walk_speed = 0.5  # m/s
        self.turn_speed = 1
        self.height_adjustment_speed = self.walk_speed

        ##################################
        # Set up legs:

        self.model = loader.load_model( "Meshes/person.bam" )

        # Standard material:
        m = Material()
        m.set_base_color((0.1, 0.5, 0.1, 1))
        m.set_ambient((0.1,0.1,0.1,1))
        m.set_specular((0.1,0.7,0.1,1))

        self.ik_actor = IKActor( self.model )
        self.ik_actor.reparent_to( self.root_node )
        self.ik_actor.actor.set_material(m)
        #################################################
        # Set up arm chains:

        self.ik_chain_arm_left = self.ik_actor.create_ik_chain( ["Shoulder.L", "UpperArm.L", "LowerArm.L", "Hand.L"] )
        self.ik_chain_arm_left.set_hinge_constraint( "Shoulder.L", axis=LVector3f.unit_z(),
                min_ang=-math.pi*0.05, max_ang=math.pi*0.05 )
        self.ik_chain_arm_left.set_hinge_constraint( "UpperArm.L", axis=LVector3f.unit_y(),
                min_ang=-math.pi*0.5, max_ang=math.pi*0.5 )
        self.ik_chain_arm_left.set_hinge_constraint( "LowerArm.L", axis=LVector3f.unit_z(),
                min_ang=-math.pi*0.5, max_ang=0 )
        self.ik_chain_arm_left.set_hinge_constraint( "Hand.L", axis=LVector3f.unit_x(),
                min_ang=-math.pi*0.3, max_ang=math.pi*0.3 )

        self.ik_chain_arm_right = self.ik_actor.create_ik_chain( ["Shoulder.R", "UpperArm.R", "LowerArm.R", "Hand.R"] )
        self.ik_chain_arm_right.set_hinge_constraint( "Shoulder.R", axis=LVector3f.unit_z(),
                min_ang=math.pi*0.05, max_ang=math.pi*0.05 )
        self.ik_chain_arm_right.set_hinge_constraint( "UpperArm.R", axis=LVector3f.unit_y(),
                min_ang=-math.pi*0.5, max_ang=math.pi*0.5 )
        self.ik_chain_arm_right.set_hinge_constraint( "LowerArm.R", axis=LVector3f.unit_z(),
                min_ang=0, max_ang=math.pi*0.5 )
        self.ik_chain_arm_right.set_hinge_constraint( "Hand.R", axis=LVector3f.unit_x(),
                min_ang=-math.pi*0.3, max_ang=math.pi*0.3 )

        self.ik_chain_arm_left.debug_display( line_length=0.1 )
        self.ik_chain_arm_right.debug_display( line_length=0.1 )


        self.hand_base_pos_left = self.root_node.attach_new_node("Hand_target_left")
        self.hand_base_pos_left.set_pos( -0.3, 0, -0.3 )
        self.hand_target_left = self.hand_base_pos_left.attach_new_node("Hand_target_left")

        self.hand_base_pos_right = self.root_node.attach_new_node("Hand_target_right")
        self.hand_base_pos_right.set_pos( 0.3, 0, -0.3 )
        self.hand_target_right = self.hand_base_pos_right.attach_new_node("Hand_target_right")

        self.ik_chain_arm_left.set_target( self.hand_target_left )
        self.ik_chain_arm_right.set_target( self.hand_target_right )

        self.hand_target_left.attach_new_node( geom )
        self.hand_target_right.attach_new_node( geom )
        

        ###########################################
        ## Set up lights:

        light = PointLight("PointLight")
        light.set_color_temperature( 9000 )
        #light.attenuation = (1, 0.5, 0.5)
        light.attenuation = (0.75, 0, 0.05)
        light_node = render.attach_new_node( light )
        light_node.set_pos( 0, 0, 3 )
        render.set_light( light_node ) 
        #light.set_shadow_caster(True, 1024, 1024, -2000 ) # low sort value to render early!

        alight = AmbientLight('alight')
        alight.set_color((0.2, 0.3, 0.2, 1))
        alnp = render.attach_new_node(alight)
        render.set_light(alnp)

        #################################################


        base.taskMgr.add( self.walk, "Rigged_char_walk")


        ##################################
        # Control upper body:
        self.torso_bone = self.ik_actor.get_control_node( "LowerSpine" )


    def videoTask(self, task):
        if not self.cap.isOpened(): return task.cont
        success, image = self.cap.read()
        if not success:
            print("Ignoring empty camera frame.")
            return task.cont
        image.flags.writeable = False
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.pose.process(image)
        if results.pose_landmarks is None: return task.cont
        self.landmark = results.pose_world_landmarks.landmark
        return task.cont

    def walk( self, task ):

        #############################
        # Update arms:

        if self.landmark:
                self.hand_target_left.set_pos(*convert(self.landmark[index_mapping["HandL"]]))
                self.hand_target_right.set_pos(*convert(self.landmark[index_mapping["HandR"]]))

        self.ik_chain_arm_left.update_ik()
        self.ik_chain_arm_right.update_ik()

        return task.cont


    
    def new_random_target( self ):

        self.target_node.set_pos(
                LVector3f( random.random()*9-4.5,
                    random.random()*9-4.5,
                    0 ) )


if __name__ == "__main__":

    from direct.showbase.ShowBase import ShowBase
    from CCDIK.camera_control import CameraControl

    class MyApp(ShowBase):

        def __init__(self):

            #####################################
            ## Set up scene

            ShowBase.__init__(self)
            base.disable_mouse()
            base.set_frame_rate_meter(True)

            wp = WindowProperties()
            wp.set_size(1800, 960)
            self.win.request_properties(wp)

            base.set_background_color(0,0,0)

            grid = create_grid( 20, 1 )
            render.attach_new_node( grid )
            axes = create_axes( 1000, bothways=True, thickness=3 )
            render.attach_new_node( axes )

        #     terrain = CollisionTerrain( 5, 0.25, render, height=1 )

            self.character = RiggedChar( )
         
            self.cam_control = CameraControl( camera, self.mouseWatcherNode, speed = 0.02 )
            self.cam_control.focus_point = LVector3f( 0, 0, 1 )
            
            self.taskMgr.add( self.cam_control.move_camera, "Move_camera_task")

            self.accept( "wheel_down", self.cam_control.wheel_down )
            self.accept( "wheel_up", self.cam_control.wheel_up )



    app = MyApp()
    app.run()
