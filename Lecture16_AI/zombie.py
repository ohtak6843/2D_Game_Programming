from pico2d import *

import random
import math
import game_framework
import game_world
from behavior_tree import BehaviorTree, Action, Sequence, Condition, Selector
import play_mode


# zombie Run Speed
PIXEL_PER_METER = (10.0 / 0.3)  # 10 pixel 30 cm
RUN_SPEED_KMPH = 10.0  # Km / Hour
RUN_SPEED_MPM = (RUN_SPEED_KMPH * 1000.0 / 60.0)
RUN_SPEED_MPS = (RUN_SPEED_MPM / 60.0)
RUN_SPEED_PPS = (RUN_SPEED_MPS * PIXEL_PER_METER)

# zombie Action Speed
TIME_PER_ACTION = 0.5
ACTION_PER_TIME = 1.0 / TIME_PER_ACTION
FRAMES_PER_ACTION = 10.0

animation_names = ['Walk', 'Idle']


class Zombie:
    images = None

    def load_images(self):
        if Zombie.images == None:
            Zombie.images = {}
            for name in animation_names:
                Zombie.images[name] = [load_image("./zombie/" + name + " (%d)" % i + ".png") for i in range(1, 11)]
            Zombie.font = load_font('ENCR10B.TTF', 40)
            Zombie.marker_image = load_image('hand_arrow.png')


    def __init__(self, x=None, y=None):
        self.x = x if x else random.randint(100, 1180)
        self.y = y if y else random.randint(100, 924)
        self.load_images()
        self.dir = 0.0      # radian 값으로 방향을 표시
        self.speed = 0.0
        self.frame = random.randint(0, 9)
        self.state = 'Idle'
        self.ball_count = 0

        self.build_behavior_tree()

        self.patrol_locations = [(43, 274), (1118, 274), (1050, 494), (575, 804), (235, 991), (575, 804), (1050, 494),
(1118, 274)]
        self.loc_no = 0

        self.target_ball = None


    def get_bb(self):
        return self.x - 50, self.y - 50, self.x + 50, self.y + 50


    def update(self):
        self.frame = (self.frame + FRAMES_PER_ACTION * ACTION_PER_TIME * game_framework.frame_time) % FRAMES_PER_ACTION
        # fill here
        self.bt.run()

    def draw(self):
        if math.cos(self.dir) < 0:
            Zombie.images[self.state][int(self.frame)].composite_draw(0, 'h', self.x, self.y, 100, 100)
        else:
            Zombie.images[self.state][int(self.frame)].draw(self.x, self.y, 100, 100)
        self.font.draw(self.x - 10, self.y + 60, f'{self.ball_count}', (0, 0, 255))
        draw_rectangle(*self.get_bb())

    def handle_event(self, event):
        pass

    def handle_collision(self, group, other):
        if group == 'zombie:ball':
            self.ball_count += 1


    def set_target_location(self, x=None, y=None):
        if not x or not y:
            raise ValueError('Location should be given')
        self.tx, self.ty = x, y
        return BehaviorTree.SUCCESS

    def distance_less_than(self, x1, y1, x2, y2, r):
        distance2 = (x1 - x2) ** 2 + (y1 - y2) ** 2
        return distance2 < (PIXEL_PER_METER * r) ** 2


    def distance_more_than(self, x1, y1, x2, y2, r):
        distance2 = (x1 - x2) ** 2 + (y1 - y2) ** 2
        return distance2 > (PIXEL_PER_METER * r) ** 2

    def move_slightly_to(self, tx, ty):
        self.dir = math.atan2(ty - self.y, tx - self.x)
        self.speed = RUN_SPEED_PPS
        self.x += self.speed * math.cos(self.dir) * game_framework.frame_time
        self.y += self.speed * math.sin(self.dir) * game_framework.frame_time

        pass

    def move_to(self, r=0.5):
        self.state = 'Walk'
        self.move_slightly_to(self.tx, self.ty)
        if self.distance_less_than(self.tx, self.ty, self.x, self.y, r):
            return BehaviorTree.SUCCESS
        else:
            return BehaviorTree.RUNNING

    def set_random_location(self):
        self.tx, self.ty = random.randint(100, 1280 - 100), random.randint(100, 1024 - 100)
        return BehaviorTree.SUCCESS
        pass

    def is_boy_nearby(self, r):
        if self.distance_less_than(play_mode.boy.x, play_mode.boy.y, self.x, self.y, r):
            return BehaviorTree.SUCCESS
        else:
            return BehaviorTree.FAIL
        pass


    def is_boy_less_ball(self):
        if self.ball_count >= play_mode.boy.ball_count:
            return BehaviorTree.SUCCESS
        else:
            return BehaviorTree.FAIL


    def is_boy_more_ball(self):
        if self.ball_count < play_mode.boy.ball_count:
            return BehaviorTree.SUCCESS
        else:
            return BehaviorTree.FAIL

    def move_to_boy(self, r=0.5):
        self.state = 'Walk'
        self.move_slightly_to(play_mode.boy.x, play_mode.boy.y)
        if self.distance_less_than(play_mode.boy.x, play_mode.boy.y, self.x, self.y, r):
            return BehaviorTree.SUCCESS
        else:
            return BehaviorTree.RUNNING


    def flee_from_boy(self, r = 7):
        self.state = 'Walk'
        dx, dy = play_mode.boy.x - self.x, play_mode.boy.y - self.y
        tx, ty = self.x - dx, self.y - dy
        if tx < 0: tx = 0
        if tx > 1280: tx = 1280
        if ty < 0: ty = 0
        if ty > 1024: ty = 1024

        self.move_slightly_to(tx, ty)
        if self.distance_more_than(play_mode.boy.x, play_mode.boy.y, self.x, self.y, r):
            return BehaviorTree.SUCCESS
        else:
            return BehaviorTree.RUNNING

    def get_patrol_location(self):
        self.tx, self.ty = self.patrol_locations[self.loc_no]
        self.loc_no = (self.loc_no + 1) % len(self.patrol_locations)
        return BehaviorTree.SUCCESS


    def run_slightly_away(self, tx, ty):
        self.dir = math.atan2(self.y - ty, self.x - tx)
        self.speed = RUN_SPEED_PPS
        self.x += self.speed * math.cos(self.dir) * game_framework.frame_time
        self.y += self.speed * math.sin(self.dir) * game_framework.frame_time

    def run_away_from_boy(self):
        self.state = 'Walk'
        self.run_slightly_away(play_mode.boy.x, play_mode.boy.y)
        return BehaviorTree.RUNNING


    def is_weak(self):
        if self.ball_count < play_mode.boy.ball_count:
            return BehaviorTree.SUCCESS
        else:
            return BehaviorTree.FAIL

    def is_ball_nearby(self, r):
        for ball in play_mode.balls:
            if self.distance_less_than(ball.x, ball.y, self.x, self.y, r):
                self.target_ball = ball
                return BehaviorTree.SUCCESS
            else:
                return BehaviorTree.FAIL


    def move_to_ball(self):
        self.state = 'Walk'
        self.move_slightly_to(self.target_ball.x, self.target_ball.y)
        if self.distance_less_than(self.target_ball.x, self.target_ball.y, self.x, self.y, 0.5):
            return BehaviorTree.SUCCESS
        else:
            return BehaviorTree.RUNNING

    def build_behavior_tree(self):
        a1 = Action('Set target location', self.set_target_location, 500, 50)
        a2 = Action('Move to', self.move_to)
        SEQ_move_to_target_location = Sequence('Move to target Location', a1, a2)

        a3 = Action('Set random location', self.set_random_location)
        SEQ_wander = Sequence('Wander', a3, a2)

        c1 = Condition('소년이 근처에 있는가?', self.is_boy_nearby, 7)
        # c2 = Condition('소년의 공의 개수가 좀비의 공의 개수 이하인가?', self.is_boy_less_ball)
        a4 = Action('소년한테 접근', self.move_to_boy)
        SEQ_chase_boy = Sequence('소년을 추적', c1, a4)

        # c3 = Condition('소년의 공의 개수가 좀비보다 많나?', self.is_boy_more_ball)
        # a5 = Action('소년한테서 멀어지기', self.flee_from_boy)
        # SEQ_flee_from_boy = Sequence('소년한테서 도망', c1, c3, a5)
        # SEL_chase_or_flee_or_wander = Selector('추적 또는 도망 또는 배회', SEQ_chase_boy, SEQ_flee_from_boy, SEQ_wander)

        SEL_chase_or_wander = Selector('추적 또는 배회', SEQ_chase_boy, SEQ_wander)

        c2 = Condition('좀비가 약한가?', self.is_weak)
        a6 = Action('소년으로부터 멀어지기', self.run_away_from_boy)
        SEQ_flee = Sequence('top', c2, a6)

        SEL_flee_or_chase = Selector('도망가거나 추적 셀렉터', SEQ_flee, a4)
        SEQ_flee_or_chase = Sequence('도망가거나 추적 시퀀스', c1, SEL_flee_or_chase)

        c3 = Condition('공이 근처에 있는가?', self.is_ball_nearby, 7)
        a7 = Action('공에 접근', self.move_to_ball)
        SEQ_chase_ball = Sequence('공을 추적', c3, a7)

        SEL_flee_or_chase_or_wander = Selector('도망 또는 추적 또는 공 먹기 또는 배회', SEQ_flee_or_chase, SEQ_chase_ball, SEQ_wander)
        SEL_ball_or_wander = Selector('공 먹기 또는 배회', SEQ_chase_ball, SEQ_wander)

        root = SEL_ball_or_wander

        self.bt = BehaviorTree(root)
        pass